# Tasks — facebook-write-action-visibility

> 改动全部落 `aidcp-edge`（worktree `../aidcp-edge.wt/facebook-write-action-visibility`）。
> **无协议 / 云端改动，不碰热点文件**；**不部署 ECS**（edge 不部署），**不出安装包**（按 CLAUDE.md §6 属用户显式触发）。

## 1. aidcp-edge — 叙述器下沉与扩展

- [x] 1.1 新建 `src/facebook/companion-ui.ts`：从 `facebook-session.ts` **逐字搬入** `FacebookCompanionUiEvent`（:151-158）、`clipFacebookUiText`（:202-206）、`facebookReadUiText`（:208-220）、`facebookLikeUiText`（:222-240）、`emitCompanionUiEvent`（:738-740，logger 改入参），连同其编码诚实理由的文档注释（:146-149、:221）。只依赖协议类型 + `FacebookLikeObservation`，**确认无循环依赖**。
- [x] 1.2 扩展类型联合：`type` 增 `comment | comment_pending | comment_failed | join_group | join_pending | join_failed | search | search_failed`；`statsDelta` 增 `comments?`。**确认壳侧无需改**（`main.cjs:3414` 已汇 `d.comments`、`:3421` 已 bump dailyUsage comment）。
- [x] 1.3 新增 `isAttempted(reason)`：**拒绝集**（`busy` / `preempted_by_task` / `session_closing` / `browse_disabled` / `capability_unsupported` / `observation_only`）。**MUST NOT 用白名单**——未知 reason 必须默认可见。
- [x] 1.4 新增 `reasonText(reason)`：机器码→人话，未知回落通用文案、**绝不猜**。
- [x] 1.5 新增 `facebookGroupName(obs)`：只用现读页面标题剥 Facebook 后缀（注意 `(3) 群名 | Facebook` 这类通知前缀 / 分隔符 / 语言差异），读不到回落「一个小组」，**绝不把 URL 当群名**。

## 2. aidcp-edge — 会话侧

- [x] 2.1 `facebook-session.ts`：删本地类型 / 三构造器 / emit 方法，改 import；**保留私有包装** `emitCompanionUiEvent(e)` 使 4 个既有发射点（:345 / :704 / :714 / :727）**逐字不变**（对唯一在工作的 like 路径零风险）。
- [x] 2.2 `searchBrowse`（:949-975）：成功返回处（:974）发 `search`（关键词 + 真实卡数，一手）；失败返回处（:951 / :959 / :964 / :969）经 `isAttempted` 发 `search_failed`。**无 statsDelta**（搜索全系统不计数：云端确认它不进 `interaction.occurred` 也不进 `dailyUsage`）。
- [x] 2.3 改 `profile.open direct`（:1102）日志措辞，使小红书专属规则（`ui-events.cjs:213`）不再误命中。**这是有意打破一条老规则**——presence-only、不丢条目、无测试断言它；在此显式记账。

## 3. aidcp-edge — 委托处理器（修复主体）

> 两个构造点已传 `logger: (m) => console.log(m)`（`main.ts:863` / `:1046`）→ **零接线改动**。

- [x] 3.1 `comment-handler.ts` `onSearch`：候选≥1 / ok 但 0 候选 → `search`（用执行器已回传的真实 `containerName`，回落「群」）；`!r.ok` → `search_failed`；`!container` → **不产**（`permission_gated` 是配置问题、非一次动作）。
- [x] 3.2 `onOpen`：成功处复用**与浏览路径同一个** `facebookReadUiText` → `note_open` + `views:1`（消除两路不对称）。`editor_not_found` → **不产**（帖子真开了也真读了；发失败条目会被误读成「读失败」）。
- [x] 3.3 `onComment`：`ok` → `comment` + `comments:1`；`pending_group_approval` → `comment_pending`（**无计数**）；其余经 `isAttempted` → `comment_failed`；`busy`/`preempted_by_task` → 不产。主语用**打进去的评论文本**，**绝不用 permalink**。
- [x] 3.4 `onJoin`：**镜像云端证据闸** `ok && clicked===true`（cloud `handler.ts:531-536`）→ `join_group`；`pending` / `questionnaire_required` → `join_pending`；`already_member` / `observation_only` → 不产；其余经 `isAttempted` → `join_failed`。**无 statsDelta**（stats/dailyUsage 无 `joins` 字段，新增会与云端权威投影漂移）。

## 4. aidcp-edge — FB 验证码盲区（既有 `edge-fleet-console` 规格违反）

- [x] 4.1 FB 阻断检测（`main.ts:996`）发**结构化** `popup` 事件（不靠中文正则）——今天该行不含「弹窗」「暂停操作」故 `overlayBlocked` 从不置真（`main.cjs:3438`）。
- [x] 4.2 FB 清除处理器（`main.ts:1001-1010`，今天**什么都不打**）发结构化 `popup_cleared`。
- [x] 4.3 `main.cjs:3438-3439`：把 `overlayBlocked` 清除**收紧为只认显式 `popup_cleared`**，不再由 statsDelta 顺带清（今天一次正常点赞就把「需要人工」抹绿）。**核对不回归小红书**——XHS 两侧本来就有显式 popup / popup_cleared。

## 5. aidcp-edge — 渲染层（纯装饰）

- [x] 5.1 `renderer.js` `EV_ICONS`（:1627-1634）补：`comment|comment_pending|comment_failed`→评、`join_group|join_pending|join_failed`→群、`search|search_failed`→搜。`_pending`/`_failed` **有意共用同族记号**（句子已承载真相）。确认新条目与既有 `^popup` / `^publish` 不冲突。
- [x] 5.2 `styles.css`（:999-1001 旁）补 `.ev-ic.ic-join` / `.ic-search`。
- [x] 5.3 `ui-events.cjs`：**仅更新形状文档注释**（:19-31，今天已漂移：列 6 kinds 而发射器产 9），记录「FB 走结构化层 / XHS 走兜底表」。**零逻辑改动。**

## 6. 测试（按仓内克制原则：关键行为少数用例）

> 既有 `test/electron/ui-events.test.ts` **只测解析器、从不执行发射器**，手敲字面量 → 改措辞照样全绿而条目静默消失。故新覆盖压在**发射器侧**。

- [x] 6.1 `test/facebook/comment-handler.test.ts`（桩 client + 捕获 logger）：`ok:true` → 一条 `comment` 且 `statsDelta.comments===1`。
- [x] 6.2 **红线用例**：`pending_group_approval` → `comment_pending`、句中含待批准语义、**`statsDelta` 缺席**。
- [x] 6.3 `busy` / `preempted_by_task` → **零** `[ui-event]` 行。
- [x] 6.4 加群 `ok&&clicked` → `join_group`；加群 `pending` → `join_pending` 且句中**不含**「加入了」。
- [x] 6.5 `test/electron/ui-events.test.ts` 补一例：结构化 `comment_pending` 行原样透传、`sentence` 完整、无 statsDelta（证明解析器确为透传）。
- [x] 6.6 回归序列：`npm run test:acceptance` → `npm test` → `npm run typecheck`（CLAUDE.md §4）。

> **全部实装落在一个提交**：`<!-- aidcp-edge 40aa902 已推送、merge-base 确认可达 origin/master -->`
> 回归：`test:acceptance` 22/22、`npm test` 1559/1559、`typecheck` 干净。
> **偏离设计的一处（有意）**：设计只说搜索成功发 `search` 条目，实装另给 `cards` 型终局报告加了可选
> `presence` 字段——否则「上报卡片」分支紧接着会把在场感覆盖成「正在浏览推荐流…」，而搜索结果页上
> 那句是假话，且会把刚发的搜索在场感冲掉。不加等于写一句立刻被覆盖的死代码。
>
> **land 时遇到的一次假红灯（记账，非本 change 问题）**：集成闸首跑 `test/facebook/publish-executor.test.ts`
> 「opens composer, fills content, …」失败；单跑该文件 26/26 过、纯上游基线 `ff6c1e1` 26/26 过、重跑全量
> 1559/1559 过 ⇒ **该用例在全量并发下 flaky**，与本 change 无因果。若再次出现，别当回归查本 change。

## 7. 收口

- [x] 7.1 land 到 `aidcp-edge` master（`scripts/land-change`），tasks.md 按 `<!-- <repo> <sha> 备注 -->` 回写**已推送**的 sha。
- [x] 7.2 真机验收项登记 `docs/real-machine-acceptance-backlog.md` <!-- 簇 90（共享环境同簇 82/88，建议合验） -->
- [x] 7.3 `openspec validate facebook-write-action-visibility --strict` → archive。 <!-- validate 通过 → 归档 2026-07-16 -->

## 8. 真机验收（**已登记 backlog 簇 90**，不在本地跑——此处保留原始条目供追溯）

- [ ] 8.1 **首个要核的点——计数是否重复**：一条真评论会同时 bump 本地 `comments` 与云端经 `interaction.occurred` 的计数。预期云端 ~60s `dailyUsage` 快照**覆盖**本地兜底（与既有 like / view 同构）。需在真机确认当日评论数不虚高。
- [ ] 8.2 **待批准是否为常态**：若群参与审批频繁命中，流里会出现大量 `comment_pending` 条目。**这是修复在起作用**（把一直存在的现实翻出来），不是回归——验收时向运营讲清，别误判为「现在全是失败」。
- [ ] 8.3 群名读取在越南语 / 多语言群、含通知前缀（`(3) 群名 | Facebook`）时是否可读；读不到须回落「一个小组」而非露 URL。
- [ ] 8.4 FB 验证码真机：拦住时客户端「需要处理」是否点亮并浮到最上；其后一次正常点赞**不得**把它抹绿；人工处理后显式解除才退出该态。
