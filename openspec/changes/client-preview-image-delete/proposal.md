## Why

客户端（Electron 陪伴客户端）的**稿件预览抽屉**今天是**只读**的：配图区把 `publishPreview.images` 逐张渲染成缩略图，除了「加载失败 → 图片暂不可用」的兜底外**没有任何逐图控件**（`aidcp-edge/src/electron/renderer/renderer.js:879-902`）；客户唯一能做的动作是整稿「发布 / 取消」（`renderer.js:993-1033`）。生成的配图偶有跑偏 / 多余 / 不合规的一张，客户在客户端里只能**带着坏图发**或**整稿取消重来**——缺一个「删掉这张、其余照发」的轻操作。

管理后台侧这个能力**早已存在**（archived change `pending-draft-image-delete`，2026-07-08）：走待审草稿的乐观 CAS 编辑通道（`PublishLogStore.editDraft` 的 `images` 保留子集补丁），带「只删不注入」红线。**缺的只是把这条已有的云端写通道接到客户端的 WS 链路上**——客户端不走面板 HTTP、渲染层不碰网络，必须经「渲染层 → 主进程 IPC → 核心子进程 stdin → 边-云 WS」这条既有链路，且必须补上面板路径**没有**的**账号归属闸**（面板只认运营 JWT、不校验 recordId 归属；客户端连接的身份是账号级的，绝不能照搬面板的宽松）。

顺带订正一处**已过期的 spec 条文**：`edge-companion-ui` 现行 spec 仍写着「端上 MUST NOT 提供任何审批授权控件、审批授权只在飞书」，而应用内审批（`publish.approval_action`，协议 72→74）**早已上线**、只是当时没走 openspec change。本 change 把该条改写成与现实一致的口径，否则新加的删图能力会与自己所在 capability 的 MUST NOT 直接冲突。

## What Changes

- **新增一对协议消息（74 → 76）**：`publish.draft_image_remove`（边→云请求）/ `publish.draft_image_remove.result`（云→边应答）。这是**客户端发起、按信封 id 关联的应答**，与 `publish.approval_action` 同型——**不需要**进边缘 onMessage 主动命令白名单，也**不需要**碰 `command-bridge` 动作映射。
- **云端一道完整的闸序**（复用既有 `handlePublishApprovalAction` 的闸序模板，绝不复制面板的宽松）：`requestId` 须匹配 `^publish-\d+$` → 会话须有 `accountId` → 草稿存在 → **`draft.accountId === session.accountId`（否则 `account_mismatch`，挡住猜 recordId 去删别的租户的图）** → 已有审批签名则 `already_decided` → 非 `pending_approval` 则 `not_pending` → **`contentVersion` 须等于库里活版本（否则 `version_stale` 并回带 `currentVersion`）** → 待删 URL 须是当前 `images` 成员（否则 `image_not_found`）。
- **写路径零新建**：由云端在同一份 DB 真态上算出「保留子集」后调用**既有单写方法** `PublishLogStore.editDraft(recordId, expectedVersion, { images: kept }, editor)`，事务内 `FOR UPDATE` + `content_version` CAS 再校验一遍；「只删不注入」「封面重算为 kept[0]」「`content_version + 1` 使旧飞书卡失效」全部沿用，MUST NOT 新起裸 SQL。`edited_by` 记为 `edge-client:<accountId>`。
- **最后一张不可删（新红线）**：删到 0 张 SHALL 被云端拒 `last_image`、客户端 UI 也不给入口。理由是**「删空 = 纯文字帖」在今天是假的**——发布下发段对 `imageUrls` 为空的草稿直接判 `failed`（`aidcp-cloud/src/publish-agent/publish-dispatcher.ts:309-316`），spec `publish-image-required` 也明写图文帖无图须诚实失败。给客户一个「删完最后一张 → 审批 → 稿子被烧成 failed」的按钮属于把红线「MUST NOT 静默假成功」外包给用户，绝不做。
- **成功后立刻让客户手上的预览变新**：应答**回带写后真态**（新 `images` + 自增后的 `contentVersion`），主进程据此就地更新该环境的 `publishPreview` 并广播；云端另外照旧调既有 `notifyPublishPreviewChanged` 推一帧 `ui.snapshot`（best-effort，可能落空）。两条路收敛到同一份真态，**以应答为准、推送为辅**——这样后续点「发布」不会因为版本号过期被 `version_stale` 弹回。
- **客户端 UI**：预览抽屉配图区在**可审批态且配图 ≥ 2 张**时，每张缩略图右上角出现删除角标；点击进入**就地二次确认**（不是乐观删除）；删除在途时整个抽屉（发布 / 取消 / 其余删除角标）互斥禁用，防「删除在途时点发布 → 版本号已变 → version_stale」的困惑态；只剩一张时不显示角标并给出「至少保留一张配图」的说明；失败按具名拒因诚实呈现中文原因，MUST NOT 先行乐观移除缩略图。
- **spec 订正**：`edge-companion-ui` 的「审批授权只在飞书」改写为「应用内审批为一等通道、飞书为并行通道、二者共享同一份 first-writer-wins 审批信号」——反映已上线的现实。

## Capabilities

### New Capabilities
- `publish-draft-client-edit`: 客户端（边-云 WS 身份）对**自己账号名下**待审草稿的编辑通道。本期只含「逐张删配图」一种编辑，但把「账号归属闸 + 决定已落则不可改 + 版本 CAS + 只删不注入 + 写后回真态 + 拒因可区分」这套闸序定成契约，为将来可能的客户端侧编辑留干净扩展缝（本期 MUST NOT 提供改标题 / 正文 / 加图 / 换封面 / 重排）。

### Modified Capabilities
- `edge-companion-ui`: ①「发布等待卡纯展示、审批授权只在飞书」订正为与已上线的应用内审批一致；② 预览抽屉配图区从只读升为「可逐张删」——含二次确认、最后一张不可删、忙态互斥、非乐观回读真态刷新、拒因诚实呈现。

## Impact

- **aidcp-edge**：`src/comm/protocol.ts`（+2 MessageType、+2 payload 接口、+2 payload map 条目）；`src/client/publish-approval-onboarding.ts`（stdin↔WS 桥由「只认 `publish.approval_action`」放宽为认这两类客户端发起的 publish RPC，**复用同一条 `[publish-approval-reply]` 回执前缀与同一张 pending 表**，不新起第三个 stdin 监听、不新增回执前缀）；`src/electron/main.cjs`（新 IPC `publish:image-remove` + 入参校验；发送函数泛化为按 type 下发；应答成功后就地更新 `handle.status.publishPreview` 并广播）；`src/electron/preload.cjs`（暴露 `publishImageRemove`）；`renderer/renderer.js` + `renderer/styles.css`（删除角标 / 就地确认 / 忙态 / 最后一张禁用 / 拒因文案）；`test/acceptance/protocol-contract.test.ts`（Record + 计数 74→76）、`test/electron/companion-ui.test.ts`（jsdom 交互）。
- **aidcp-cloud**：`src/comm/protocol.ts`（与 edge 同步）；`src/comm/handler.ts`（新 dep + 路由 case，应答走信封 id）；`src/server.ts`（`handlePublishDraftImageRemove` 闸序 + 复用 `editDraft` + 复用 `notifyPublishPreviewChanged`）；`test/acceptance/protocol-contract.test.ts`（74→76）、`test/handler.test.ts`、`server` 侧闸序单测。**不碰** `PublishLogStore.editDraft` 本体（沿用其既有语义）、**不碰** `command-bridge`、**不碰** `RiskController`、**不碰**审批信号文件逐字节契约。
- **aidcp-console**：无改动（管理后台的删图能力保持原样）。
- **控制仓**：`docs/protocol.md` 头部计数与 §2 表（74→76）。
- **数据**：无 schema 迁移（`publish_log.images` / `image_url` / `content_version` 均已存在）；删图只移除记录引用、**不删 OSS 实体**（孤儿对象沿用既有取舍）。
- **部署**：cloud 纯代码落 dev；edge 只到 commit / push（按长期授权，打安装包不进自动收尾）。**注意**：真机验收要求客户端跑的是含本 change 的 edge 构建，dev 云端亦须是含本 change 的 cloud——两端协议计数须同为 76，否则新消息在旧云端会被当未知类型。

## 顺带发现（不在本 change 范围，另行处理）

- **`publish-image-required` 与 `console-write-operations` 现存互相矛盾**：管理后台侧允许把配图删空并向运营宣称「本帖将作为纯文字帖发布」（`aidcp-console/src/pages/ContentPage.tsx:466,730,1067`），而下发段对 M=0 直接判 `failed`（`publish-dispatcher.ts:309-316`）。archived change `pending-draft-image-delete` 的 proposal 里「发布管线已支持 M=0 降级」这句是**错的**，其真机项 4.4「删空发纯文字帖」至今未验证。本 change 在客户端侧用「最后一张不可删」绕开该雷，**但管理后台那条误导性路径依然带刺**，建议单开一个 change 收口（要么下发段按平台放开纯文字帖，要么后台也禁止删空并改掉文案）。
- **两份 `protocol.ts` 并非逐字一致**：风控 `action` 联合类型里 cloud 有 `'join_group'`、edge 没有；另有若干注释与字段位置漂移。`MessageType` 联合与计数是一致的（现 74），typecheck 也只守得住这一段。本 change 只动 `MessageType` 与 publish payload，**不顺手改这处既有漂移**（`protocol.ts` 是并行开发热点文件、单写者纪律），但值得单独收口。
