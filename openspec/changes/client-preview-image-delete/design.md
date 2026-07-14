# Design — client-preview-image-delete

## 1. 现状坐实（带 文件:行）

| 事实 | 出处 |
| --- | --- |
| 客户端预览抽屉逐张渲染 `<img src=url>`，**无任何逐图控件**（只有加载失败兜底） | `aidcp-edge/src/electron/renderer/renderer.js:879-902` |
| 客户端对草稿的**唯一**写动作是整稿发布 / 取消 | `renderer.js:993-1033` → `preload.cjs:58` → `main.cjs:2959-2974` → `main.cjs:1377-1398` → `src/client/publish-approval-onboarding.ts:23-72` → WS |
| 应答走**信封 id pending 表**，不经主动命令白名单 | `aidcp-edge/src/client/edge-client.ts:466-478`（白名单在 `:487-530`，未列即在 `:558` 静默丢弃） |
| 预览 payload 的 `images` 是**裸 URL 字符串数组、无稳定 id**；index 0 = 封面 | `protocol.ts` `UiPublishPreviewPayload`；`aidcp-cloud/src/publish-agent/publish-log-store.ts:170` |
| 配图对象是**对象级 public-read**（`x-oss-object-acl: public-read`），客户端能真显示 | `aidcp-cloud/src/storage/oss-object-store.ts:46` |
| 云端已有的单写编辑方法**已支持删图**：`images` = 保留子集、事务内 `FOR UPDATE` + `content_version` CAS、非成员整块拒 `invalid_field`、封面重算 `kept[0] ?? null`、`content_version + 1` | `publish-log-store.ts:397-556`（子集校验 `:490-498`、保序过滤 `:500`、封面 `:501`、UPDATE `:504-530`） |
| 云端审批闸序模板（含账号归属闸） | `aidcp-cloud/src/server.ts:1839-1895`（`account_mismatch` 在 `:1853`、`version_stale` 在 `:1868-1872`） |
| **面板编辑路径没有账号归属闸**——任何运营 JWT 可编辑任意 recordId | `aidcp-cloud/src/panel/panel-server.ts:1055-1126` |
| 编辑后**唯一**会重推预览的路径 | `server.ts:3021-3027` `notifyPublishPreviewChanged`，今天只被面板 PUT 调用（`panel-server.ts:1116`） |
| 预览推送是 **best-effort**：账号无在线边缘就丢、`sent<=0` 只告警不重试 | `aidcp-cloud/src/comm/ui-snapshot.ts:186-199, 225-232` |
| **M=0 是雷**：下发段对零配图草稿直接 `failed`（终局） | `aidcp-cloud/src/publish-agent/publish-dispatcher.ts:309-316`；spec `publish-image-required` |
| 抽屉 DOM 每帧 snapshot 全量重建（`replaceChildren`） | `renderer.js:876`，由 `renderer.js:1389` 驱动 |
| 主进程是 `status.publishPreview` 的**唯一写者**（整对象覆盖） | `main.cjs:2472-2474` |

## 2. 关键设计决策（及被否掉的替代）

### 2.1 传输：新增一对 `publish.draft_image_remove` / `.result`，不复用 / 不泛化

- **否掉「泛化成 `publish.draft_edit` 通用编辑通道」**：客户端连接的身份（`session.accountId`）是**边缘 hello 里自报**的、无 per-account 密钥（`aidcp-cloud/src/comm/handler.ts:439`、`connection-runtime.ts:87-137` 且未知账号自动注册）。在这样一条信道上开一个能改标题 / 正文的通用写口，攻击面与产品语义都远超「删掉这张图」。用户没要，YAGNI 砍掉。扩展缝留在 **capability 契约**（`publish-draft-client-edit` 定的是闸序，不是消息形状），将来要加编辑再加消息，不预留空字段。
- **否掉「复用 `publish.approval_action` 加个 action 字段」**：会把「审批决定」与「草稿编辑」两种语义压进同一条消息，两者的闸序不同（审批要 preflight 边缘在线；编辑要拒 `already_decided`），压在一起必然长出分支地狱。
- **否掉「客户端直连面板 HTTP」**：渲染层不碰网络是硬约束（`preload.cjs:59-60` 就地写死此意），且面板 JWT 是运营身份、客户没有。

### 2.2 payload：删「哪一张」用 **URL**，不用 index，也不由客户端提交保留子集

```ts
// 边→云
export interface PublishDraftImageRemovePayload {
  requestId: string;      // `publish-<recordId>`，与审批同一 id 空间
  contentVersion: number; // CAS：客户端**当时看到的**版本
  imageUrl: string;       // 要删的那一张，MUST 是该稿当前 images 成员
}
// 云→边（按信封 id 关联的应答）
export interface PublishDraftImageRemoveResultPayload {
  requestId: string;
  ok: boolean;
  images?: string[];       // 成功：写后真态（保序）
  contentVersion?: number; // 成功：自增后的版本
  reason?: string;         // 失败：可区分拒因
  currentVersion?: number; // version_stale 时回带活版本
}
```

- **不用 index**：index 的含义随任意一次快照重推而漂移（后台同时删了一张 → 客户端手上的 index 2 指向了另一张）。URL 是稳定值键，且与云端既有子集校验（按 URL 成员判定）同口径。
- **保留子集由云端算，不由客户端提交**：客户端只表达「删这一张」的**意图**，云端在**同一份 DB 真态**上算 `kept = current.filter(u => u !== imageUrl)` 再交给 `editDraft`。这样「客户端手上是旧列表」这一整类 bug 被 CAS 一刀切掉——任何导致 images 变化的写都会 `content_version + 1`，所以旧版本号必然先撞 `version_stale`，不可能拿着旧子集把别的图误删。（面板路径让前端提交保留子集，是因为它同时要支持改标题 / 正文；客户端没这个需要。）
- **已知残留（诚实记下，不修）**：若一稿的 `images` 里有**两个完全相同的 URL**，删「其中一张」在值键语义下会把两张一起删。云端 `editDraft` 的成员校验本身就是 Set 语义（`publish-log-store.ts:499-500`），这是既有契约的性质，不是本 change 引入的；发生概率极低（同一张图重复入库），且应答回带真态、UI 不会假装只删了一张。

### 2.3 云端闸序（照抄审批的模板，补面板缺的那道）

`handlePublishDraftImageRemove(payload, session)`，顺序即拒因优先级：

1. `requestId` 匹配 `^publish-(\d+)$` 且 `imageUrl` 非空字符串、`contentVersion` 是非负整数 → 否则 `invalid_request`
2. `session.accountId` 缺失 → `account_unavailable`
3. `loadForDispatch(recordId)` 空 → `not_found`
4. **`draft.accountId !== session.accountId` → `account_mismatch`**（面板没有这道，客户端必须有）
5. 已存在审批签名（`readPublishApproval('publish-'+id)`）→ `already_decided`（决定已落，稿子不可再改；否则会绕过「审=发」）
6. `draft.status !== 'pending_approval'` → `not_pending`
7. `payload.contentVersion !== draft.contentVersion` → `version_stale` + `currentVersion`
8. `imageUrl ∉ draft.imageUrls` → `image_not_found`（这张图已经不在稿件里了，请刷新）
9. `kept = draft.imageUrls.filter(u => u !== imageUrl)`；**`kept.length === 0` → `last_image`**（见 2.4）
10. `editDraft(recordId, payload.contentVersion, { images: kept }, 'edge-client:' + session.accountId)` —— 事务内 `FOR UPDATE` 再校验一遍 status / CAS / 子集，把步骤 5–8 的 TOCTOU 窗口收死；store 拒因映射回具名拒因（`version_conflict → version_stale`、`invalid_field → image_not_found`、`not_pending → not_pending`、`not_found → not_found`）
11. 成功 → 调既有 `notifyPublishPreviewChanged(recordId)`（best-effort 重推预览）→ 应答 `{ ok: true, images, contentVersion }`（**取 store 回读的真态，不取本地推算值**）

`ok:true` 的语义严格等于「这张图已经从待审稿件里删掉了」，不等于「已发布」——与审批那条 `ok:true` 只代表「决定已受理」同属一类纪律。

### 2.4 最后一张不可删（本 change 唯一的新红线）

`publish-dispatcher.ts:309-316` 对 `imageUrls` 为空的草稿**直接判 `failed`（终局、不重试）**，spec `publish-image-required` 亦明写图文帖无图须诚实失败（小红书图文编辑器「先传图门控」下标题 / 正文框根本不渲染）。所以：

- 云端拒 `last_image`（**服务端是权威**，不能只靠 UI 藏按钮）；
- 客户端在 `images.length <= 1` 时不渲染删除角标，并给一行说明「至少保留一张配图」。

管理后台今天允许删空、且向运营宣称「本帖将作为纯文字帖发布」——**那是个既有的错误**（见 proposal「顺带发现」），本 change 不把这个错误复制到客户面前。

### 2.5 版本刷新：以应答为准、以推送为辅

删图必然 `content_version + 1`。若客户端手上的 `contentVersion` 不跟着更新，下一次点「发布」会被 `version_stale` 弹回（`server.ts:1868-1872`）——这是本功能最容易踩的坑。两条收敛路径：

- **主路径（可靠）**：应答回带 `images` + `contentVersion`；**主进程**据此就地更新 `handle.status.publishPreview` 并 `updateStatus` 广播（`main.cjs:1062-1074`）。
  - 为什么必须在**主进程**改而不是只在渲染层改：`status.publishPreview` 的唯一写者是主进程（`main.cjs:2472-2474`），渲染层任何本地补丁都会被下一帧 `status:update` 广播**整体顶掉**（抽屉每帧 `replaceChildren` 重建，`renderer.js:876/1389`）。只改渲染层 = 删完过几秒图又「长回来」。
  - 更新前须校验应答里的 `requestId` 对应的 recordId **等于**当前 `publishPreview.recordId`，避免把过期应答写进新草稿。
- **辅路径（best-effort）**：云端 `notifyPublishPreviewChanged` 推一帧只含 `publishPreview` 的 `ui.snapshot`。它可能落空（账号无在线边缘 / `sent<=0` 不重试，`ui-snapshot.ts:225-232`），所以**绝不能**把它当作唯一刷新手段。两条路的内容一致，后到者覆盖同一份真态，收敛无冲突。

### 2.6 边缘链路：复用同一座桥，不新起

核心侧 stdin↔WS 桥今天**只认** `type === 'publish.approval_action'`，其余**静默丢弃**（`publish-approval-onboarding.ts:37`）——若主进程发了新 type 而核心不认，症状是「主进程 pending 表 35s 后超时」，一个字的错误都不会打。故：

- 把该桥的准入从「等于某一个 type」放宽为「属于客户端发起的 publish RPC 白名单集合」（本期两条：`publish.approval_action`、`publish.draft_image_remove`），**转发逻辑不变**（`client.request(type, payload, 30_000)`），**回执前缀不变**（`[publish-approval-reply]`），**pending 表 / 拦截点不变**（`main.cjs:2347-2356`）。
- 好处：不新增第三个 `process.stdin` 监听器、不新增回执前缀（新前缀若忘了在 `handleEdgeLogLine` 拦截，JSON 回执会当日志泄进活动流）。
- **超时阶梯必须保持**：主进程 35s > 核心 WS 30s（`main.cjs:1388` / `publish-approval-onboarding.ts:21`）。新 IPC 沿用同一对数字，MUST NOT 在主进程侧也写 30s（否则主进程先超时，核心的诚实拒因永远送不回来）。

### 2.7 UI：非乐观、就地确认、忙态互斥

- **入口**：仅当 `publish.state ∈ {pending, reminded}`（既有 `syncPublishPreviewActions` 的可审批判据）**且** `images.length >= 2` 时，每张缩略图右上角渲染删除角标（复刻管理后台的形态：danger 圆形 ✕，`aria-label="删除配图 N"`）。
- **二次确认**：点角标 → **就地**把该张切成确认态（「删除这张？ 删除 / 取消」），不弹原生 `confirm()`（阻塞、样式不可控）、不引第三方弹层。确认态存在**模块级变量**里（键为 URL）而非只存 DOM——因为抽屉每帧重建，只存 DOM 会被下一帧 snapshot 抹掉。
- **非乐观**：确认后**不**先行移除缩略图；置忙态 → 等应答 → 用应答回带的真态重绘。这与管理后台的取舍一致（后台亦是回读真态刷新，`ContentPage.tsx:727`）。
- **忙态互斥**：删除在途时，「发布」「取消」与其余删除角标一并禁用。否则用户可在删除在途时点「发布」，云端会用**旧版本号**去审批 → 撞 `version_stale` → 用户看到一个莫名其妙的「内容已被修改」——不是数据 bug，但是纯自找的困惑。
- **拒因文案**（沿用 `publishPreviewActionReason()` 的映射风格，新增几条）：`version_stale`「稿件已更新，已为你刷新，请重试」；`image_not_found`「这张配图已经不在稿件里了」；`last_image`「至少保留一张配图」；`already_decided`「稿件已审批过，无法再修改」；`not_pending`「稿件已不在待审状态」；`account_mismatch` / `account_unavailable`「登录状态异常，请重新登录」；`edge_request_timeout` / `edge_not_running`「客户端未连上云端，请稍后重试」。**MUST NOT** 出现「删除成功」以外的乐观措辞。

## 3. 失败模式清单（逐条给出「用户看到什么」）

| 场景 | 系统行为 | 用户看到 |
| --- | --- | --- |
| 后台运营同时删了另一张 | 客户端 `contentVersion` 过期 → `version_stale` + `currentVersion` | 「稿件已更新，已为你刷新，请重试」；抽屉随即被重推的快照刷新成真态 |
| 飞书审批人同时批了 | 审批信号已落 → `already_decided` | 「稿件已审批过，无法再修改」；删除按钮消失（状态离开待审） |
| 双击 / 重复删同一张 | 忙态互斥挡住第二次；即便漏过，第二次撞 `image_not_found` | 「这张配图已经不在稿件里了」，不会误删别的图 |
| 只剩一张 | UI 无入口；即便伪造请求，云端拒 `last_image` | 「至少保留一张配图」 |
| 删的是封面（index 0） | `editDraft` 把封面重算为 `kept[0]`（`publish-log-store.ts:501`） | 第二张自动成为封面；无报错。**（真机需验：封面重算后发出去的帖确实以新首图为封面）** |
| 客户端离线 / 核心未跑 | 主进程 `edge_not_running`；或 WS 未连 → 核心侧 `request` 抛 | 「客户端未连上云端，请稍后重试」；**绝不**先在本地把图抹掉 |
| 云端不认新消息（旧 cloud） | handler 无该 case → 走既有 unknown 分支 / 无 dep 时诚实 `unavailable` | 报错而非静默；**部署纪律：cloud 必须先于 / 同时于 edge 上含本 change 的版本** |
| 应答超时 | 核心 30s → 主进程 35s → `edge_request_timeout` | 明确超时提示；图仍在（未删）。**MUST NOT** 假装删掉了 |
| 预览重推落空（账号无在线边缘） | best-effort 丢弃 | 无影响——主路径（应答回带真态）已经把 UI 刷新了 |
| 删完后 OSS 实体 | 只解引用、不删对象（既有取舍） | 无感知；孤儿对象沿用既有清理议题 |

## 4. 明确不做（YAGNI）

- 不做加图 / 换图 / 重排 / 改封面 / 改标题正文（用户只要了「删某张」；且 `editDraft` 的保序过滤本就会**静默忽略**重排，做了也是假的）。
- 不做删除撤销（客户端不持本地副本，云端已 `content_version + 1`，「撤销」= 重新注入 URL，正撞「只删不注入」红线）。
- 不做 OSS 实体清理（既有取舍，独立议题）。
- 不做管理后台侧的 M=0 收口 / `protocol.ts` 既有漂移的修复（见 proposal「顺带发现」，各自单开）。
- 不动 `PublishLogStore.editDraft` 本体、不动审批信号文件契约、不动风控与配额。
