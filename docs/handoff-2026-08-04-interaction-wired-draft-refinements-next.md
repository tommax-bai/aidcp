# 交接：互动能力已接通，下一拍是 draftRefinements（2026-08-04 19:00–20:15）

> **新 session 从这份看起。**
> 上一份 `handoff-2026-08-04-client-auth-dependency-recovery.md` 仍然有效、且已就地更新过，
> 它写的是「依赖补齐」这条线的全貌与那些会咬人的坑；本文件只写**这一拍做了什么 / 下一拍怎么做**。
> 再往前的切流全过程在 `handoff-2026-08-04-derived-services-cutover.md`，只用于追溯。

---

## 0. 一句话现状

dev 上跑三个派生服务，单体已停 **且已 disable**。
桌面客户端的 23 个依赖**接了 22 个**，只剩 `draftRefinements`。
互动能力（客户端收件箱）这一批已接通、已部署 dev、已逐条实打。

**接手先做两件事，别信下面任何数字：**

```bash
# ① 三服务 + 端口 + 就绪度 + 单体必须是 disabled
ssh -i ~/codes/dev-0722.pem root@121.89.85.150 \
  'for s in api automation content; do printf "%-12s %s NRestarts=%s\n" "$s" \
     "$(systemctl is-active aidcp-$s)" "$(systemctl show aidcp-$s -p NRestarts --value)"; done;
   printf "cloud        %s/%s\n" "$(systemctl is-active aidcp-cloud)" "$(systemctl is-enabled aidcp-cloud)";
   ss -ltn | grep -cE ":8787|:8090|:8091|:8092|:8093|:8094";
   T=$(grep -m1 "^AIDCP_AUTOMATION_INTERNAL_TOKEN=" /opt/aidcp/automation/.env | cut -d= -f2-);
   curl -s -X POST -H "Authorization: Bearer $T" -H "Content-Type: application/json" -d "{}" \
     http://127.0.0.1:8094/internal/automation/sync-read/readiness'

# ② 六仓对账（这一步是硬要求，理由见 §3）
scripts/sync-split-repos

# 还差哪几个依赖（这张表是权威，别数正文）
cd ../aidcp-api && grep -nE "^  [a-zA-Z_]+:" test/acceptance/client-auth-deps-inventory.test.ts
```

20:05 实测：三服务 active、`NRestarts=0`、六端口在、就绪 `state=ready` `blockers=[]`、
`aidcp-cloud` = `inactive/disabled`、isales 四服务未碰。

各仓 head：`aidcp@17533b1e` / `aidcp-cloud@becc468` / `aidcp-kernel@030d805` /
`aidcp-transport@f187486` / `aidcp-api@c16dcd1` / `aidcp-automation@65c88c8` / `aidcp-content@32c65f4`。
openspec change `deploy-derived-services-to-dev` 31/42（本拍的记录在 tasks 8.6 / 8.7）。

---

## 1. `draftRefinements` 是什么（下一拍的正题）

### 1.1 功能

**客户端里的「稿件精修」**：客户在桌面客户端打开一条待审稿，输入一句自然语言指令
（「第二段改短一点」「第三张图换掉」），选一个作用域，提交；云端起一个异步作业，
跑模型（可能还要重出图）产出一个补丁、改回稿件、刷新预览；客户端轮询这个作业看进度。

作用域是闭集合五个：`whole` / `body` / `images` / `selected_image` / `selected_text`。

**今天它在客户端上是一句 503**（`draft_refinement_unavailable`），
因为接口进程的组装根里这一格是空的。

### 1.2 三条客户端路由（全在 `aidcp-api/src/client-auth/client-auth-server.ts`）

| 方法 | 路径 | 缺席时 |
| --- | --- | --- |
| POST | `/environments/:envKey/publish-drafts/:recordId/refinements` | 503 `draft_refinement_unavailable` |
| GET | `/environments/:envKey/publish-drafts/:recordId/refinements/:jobId\|latest` | 503 同上 |
| GET | 待审稿列表（`listPendingPublishPreviewsForAccount`）**顺带**给每条挂 `latestForAccountRecords` | **不 503**，静静地不带精修状态 |

⚠ 第三条要注意：它是 `deps.draftRefinements ? … : new Map()` ——
**缺席时列表照常 200，只是每条稿子看起来「从没被精修过」**。
这一条不会有人报障，只会让人以为功能没被用过。

### 1.3 东西都在哪（实读，不是推测）

| 件 | 位置 | 状态 |
| --- | --- | --- |
| 端口 `DraftRefinementReadWritePort`（4 方法） | `kernel/publish-draft-contract.ts:158` | 在 |
| 表 `publish_draft_refinement_jobs` | `aidcp-content/migrations/0057_*.sql` | 在（**content 属主**） |
| `DraftRefinementStore` | `aidcp-content/src/publish-agent/draft-refinement.ts` | 文件在，**全仓零 `new`** |
| `DraftRefinementWorker` | `aidcp-content/src/publish-agent/draft-refinement-worker.ts` | 文件在，**全仓零 `new`** |
| api→content 的传输通道 | — | **零**（transport 里一条都没有） |
| 单体里的装配 | `aidcp-cloud/src/server.ts:3021`（store）/ `:6885`（worker + 1.5s 泵） | 可照抄形态 |

### 1.4 为什么它是最贵的一个：**缺的是两个方向，不是一条通道**

**方向 A（api → content）**：4 个端口方法零通道。这一半是机械活，照
`interaction-store-reader-http.ts` 的形态写即可。

**方向 B（content 侧属主接线）**：store 与 worker 都没构造。而 worker 的构造参数**横跨两个域**：

```
worker deps          在哪           今天有没有
─────────────────────────────────────────────────────────
store                content        要新建
llm                  content        content main 里有
imageProvider        content        有（RoutingImageProvider，src/server.ts:718）
objectStore          content        有（ossUploader，src/server.ts:503）
drafts.loadForDispatch   api        **通道已有**（api-publish-interaction-http）
drafts.refineDraft       api        **零通道** ← 这条要新开
refreshPreview(recordId) api        见下，是个**判断题不是接线题**
```

**`refreshPreview` 那一格要先做判断、别照抄。** 派生 api 里它已经被显式写成 `() => {}`
（`aidcp-api/src/server.ts:1119`），注释写着「发布台账权威层已经为每次属主写入产出一份单向预览，
处理器 MUST NOT 再发第二份」。所以下一拍要先回答：**精修改完稿之后，那份预览是谁产出的、
会不会自动产出**。答错的后果不是报错，是[上一份交接文档 §4 第 1 条那个坑]——
**稿子真改了，但桌面端还显示旧的，用户以为没保存上**。

**还有一条别忘了核**：`publish_draft_refinement_jobs` 原先有一条指向 `publish_log` 的跨属主外键，
物理拆库时已降级（见 `draft-refinement.ts` 建表 SQL 里那段注释）。那条外键的两个作用
现在靠「创建入口的上游先读一次 publish_log」代偿——**而那次读在拆开之后是一次跨进程调用**。
接线时确认这条前置仍然成立，别让它变成「读不到就放行」。

### 1.5 建议的做法顺序

1. **先决定 `refreshPreview` 归谁**（上面那条），这决定了方向 B 的形状。
2. 新开 `content-draft-refinement-http`（api→content，4 方法），照 store-reader 的形态。
3. 给 `refineDraft` 补一条 content→api 的通道（可以并进已有的
   `api-publish-interaction-http` 那一族，它已经承载 `loadForDispatch`）。
4. content main 构造 store + worker + 那个 1.5s 有界泵（**照单体形态**：每轮最多 3 条）。
5. api 组装根把 `draftRefinements` 那一格填上 —— **写成对象字面量的顶层键、不要条件展开**，
   否则依赖清单闸看不见它（本拍踩过，见 §2 最后一条）。
6. 缺席表里那一行删掉；`AC-CADEPS-01` 会自动逼你两边一致。

---

## 2. 这一拍做了什么（互动能力 / 客户端收件箱）

提交链：`aidcp-cloud@cd465a1 / af3a3d2 / becc468` → `kernel@030d805` → `transport@f187486`
→ `automation@73ddd47 / 65c88c8` → `api@c16dcd1` → 控制仓 `02b2f95e / 17533b1e`。

- **前置：跨进程失败保真**（`transport/interaction-failure-wire.ts` + kernel 的
  `asInteractionFailure`）。互动失败自带 `httpStatus` / `retryable` / `details` 三格，
  通用搬运层只搬 code + message；丢了之后「已发出但核不到」（409、不可重试）
  会被折成可重试的 500 ⇒ 客户端重投一条**可能已经上墙的评论 / 私信**。
  **分档判据用补集**：只有「对面答没这条路由」「对面答鉴权没过」两条能证明处理函数没跑过，
  其余一律按「可能已发出」算。提交点名单是 kernel 里的运行时常量，传输层从它派生、不手抄。
- **21 条路由 + 1 条新通道**：store-reader 13（此前写好了但 automation 从没 register）、
  workflow 3、send 5、runtime-controls deliver 1（新写）。
  三族在互动能力不可用时**照样注册**，由具名缺席实现带原因拒绝
  ——不注册的现形方式是 404，而 404 只会被读成「对面漏注册」。
- **两个端口抬进 kernel**（`interaction-automation-ports.ts`）：传输包只许引 kernel，
  否则只能在传输层再声明一份结构相同的接口。
- `requestAuthReopen` / `requestBrowserControl` 改异步；三个提交点补 `!claim.fresh` 守卫；
  **恢复循环搬进 automation**（拆仓时漏搬、全仓零调用方 ⇒ 一条 queued 回复只要那次
  fire-and-forget 下发失败就再没有任何东西会派发它，而客户端一直显示「已批准、在发」）；
  工作流那三个方法单独拿一条 90s 超时的连接（它们各跑一次模型调用，
  对着 15s 默认必然超时，**而属主侧照常把任务推进** —— 看起来失败其实成功）。
- **闸**：`AC-INTXP-01..07`（做过两次变异测试：摘掉 details 搬运 / 把提交点分档改成恒 read，
  各自当场红且点名）；automation 路由清单闸补四族（同样变异测试过）；
  api 依赖清单闸缺席表 2 → 1。
- **顺带修好一条自上一批起就红着的闸**：automation 的派生归属账本比代码旧 4 条，
  `boundaries:refresh` 因一个自 content-scheduler change 起就未裁定的文件而一直拒跑。
  登记现状（非重新裁决）后回到 273/273、forbidden=0。
- ⚠ **依赖清单闸只认对象字面量的顶层键**：我第一版用 `...(x ? {k:v} : {})` 条件展开，
  闸看不见、照旧要求一条缺席声明。**直写那一格**。

---

## 3. 会咬人的两条（本拍新踩，都已拆）

### 3.1 派生仓上的修改必须回流事实源，否则下一次同步静默冲掉

上一批修互动能力自检那两处**只提交在 `aidcp-automation`**。派生仓 `src/` 是
`aidcp-cloud` 归属清单的重放 ⇒ 下一次 `--apply` 会原样还原成旧内容，
把互动能力在 dev 上重新整体关上，而且**编译过、测试过、启动日志不吭声**。

**判据**：改 `src/` 里任何有 cloud 对应物的文件，就改 cloud 那份再同步；
派生仓只许改组装根与私有件（`server.ts` / `index.ts` / `*-service-entry.ts` /
`automation-*.ts` / 各仓私有测试）。**任何收尾前 MUST 跑一次对账**——
这类漂移只有对账看得见。

### 3.2 单体 unit 停了但没 disable，会把 dev 抢回去

`aidcp-cloud.service` 在切流后仍是 `enabled`，从那时起一直在崩溃重启（计数到 31），
每 5 秒抢一次自动化写者锁。于是**任何一次 `systemctl restart aidcp-automation`
都会把 dev 交回单体**：重启的几秒空窗里单体拿到锁与 8787，派生自动化反而永久起不来
（8094 消失），而 `systemctl is-active aidcp-automation` 仍显示 `active`（它在无限重试等锁）。

已 `stop` + `disable`。退役第二拍（tasks 8.0）只处理了那四个按角色切段的 unit，**主 unit 漏了**。
**动 ECS 前先查 `systemctl is-enabled aidcp-cloud`，必须是 `disabled`。**

---

## 4. 没验到的（**别声称它们好了**）

1. **没有一次调用真的走到自动化进程的收件箱**。本拍用真客户 token 证明了
   **路由族真的在**（收件箱路径回的是互动 API 自己的错误信封，非收件箱路径回的是
   客户鉴权的裸 `{"error":"not_found"}`——**两个 404 响应体不同**，这就是判别式），
   但验证账号 `cutover-verify-0804` 不拥有任何环境，归属闸在任何 store 调用之前就短路了。
   要走通得给它绑一个真环境（对客户环境归属的写入），本拍刻意不做。
2. **边缘从切流至今一台都没连上 dev**（8787 established 恒 0）。
   互动这一批的生成 / 下发 / 同步 / 浏览器控制**全部需要在线边缘** ⇒
   端到端行为一次都没被真实执行过。
3. **「用户的客户端现在好了」仍然没有证据** —— 请用户在客户端上点一次
   （慢启动、今日进展、发布队列、收件箱）再下结论。

验证账号收口状态：`cutover-verify-0804` **已停回 disabled、零环境**；
本拍轮换出的 key 只存在于那次会话，**未落盘**。

---

## 5. 已知既有失败（干净树上一样红，与本拍无关）

`aidcp-automation` 4 条：发布填充预算 / 命令序列器（XHS set_schedule）/ 抢占分档。
原为 5 条，「边界记录」那条本拍已修（见 §2 倒数第二点）。

`aidcp-api` 537/537 全绿；`aidcp-cloud` 全量 4195（0 fail）+ acceptance 204/204 全绿。
⚠ cloud 的 typecheck 期间会看到并发 session 在改 `facebook-operation-policy-store`
造成的红——**那不是你的**，先看报错文件名。

---

## 6. 指针

| 东西 | 在哪 |
| --- | --- |
| 依赖补齐这条线的全貌 + 六个会咬人的坑 | `docs/handoff-2026-08-04-client-auth-dependency-recovery.md` |
| 切流当天（含回滚、18 分钟停摆） | `docs/handoff-2026-08-04-derived-services-cutover.md` |
| change 本体与逐条进度 | `openspec/changes/deploy-derived-services-to-dev/`（31/42，本拍在 8.6 / 8.7） |
| 还差哪几个依赖（**权威**） | `aidcp-api/test/acceptance/client-auth-deps-inventory.test.ts` 的缺席表 |
| 本进程服务哪些路由（**权威**） | `aidcp-automation/test/acceptance/served-route-inventory.test.ts` |
| 拆仓不变量 | `CLAUDE.md` §8（OVERRIDE 级） |
| 部署序列 | 属主域先起、接口域后起（同秒重启会撞出同步读启动竞态，实测过） |
