# 设计：Facebook 写动作在客户端的诚实可见性

## 1. 现状坐实（带 `文件:行`）

活动流的完整管线（**边缘端本地投影，云端不参与**）：

```
核心子进程 console.log
  → Electron 主进程 child.stdout（main.cjs:2629-2630）
  → 按行切分（main.cjs:3219-3223）
  → 每环境独立解析器 handle.uiEvents.push(line)（main.cjs:968-969, :3350）
  → 有 sentence 才广播（main.cjs:3426-3433）＋盖 envId（main.cjs:1731-1736）
  → IPC 'ui:activity' → preload（preload.cjs:52-56）
  → 渲染层 routeActivity（renderer.js:1694-1699）→ 每环境缓冲 + 前插（renderer.js:1652-1676）
```

**关键闸门只有一个**：`if (evt.sentence)`（`main.cjs:3426`）。`kind` **不是**闸；渲染层也**不按 type 过滤**（`routeActivity` / `domPrependActivity` 都只看 `sentence`，`evIcon` 未命中回落 `['·','ic-sys']`）。**所以：只要发得出带 sentence 的结构化行，管子现成，一路直达。**

解析器双层契约（`ui-events.cjs:6-9`）：
- **结构化优先且绝对**：`push()` 命中 `[ui-event]` 前缀即 `tryParseStructured` 并**立即返回**（`:263-288`，返回点 `:281`）；只有结构化解析返回 null 才落到 22 条正则表（`:283-286`，首个命中生效）。
- 结构化解析只要求 `kind` 是 string（`:38-39`）——**新 type 无需改解析器**。

三个互相独立的卡点（本次要拆的就是这三个）：

| # | 卡点 | 证据 |
|---|---|---|
| 1 | 类型联合封闭 4 值且用满 | `facebook-session.ts:151-158`；发射点 `:345` / `:704` / `:714` / `:727` |
| 2 | `emit()` 硬编码只放行 like+ok | `facebook-session.ts:723-735`（`:725` 即闸） |
| 3 | 写动作**根本走不到** `emit()` | `facebook-session.ts:512-531` 委托 → `comment-handler.ts:116/137/160/179` 直接回报 |

`emit()` 各分支的实际产出：
- `cards`（`:701-710`）→ **presence-only，无 sentence** → 不产条目。覆盖首屏 / 滚动 / 刷新 / 返回 / 浏览侧搜索**全部**。
- `detail`（`:711-721`）→ 唯一产「读」+ views:1 的路径。
- `profile`（`:722`）→ **什么都不发**。
- `action`（`:723-735`）→ 只有 like+ok。`feed_exhausted` / `not_refreshed` / `close ok` / 全部 `capability_unsupported` / 全部超时——**全部隐形**。

中文兜底表对 FB 的实际覆盖：**唯一命中的是 `/命令: profile\.open/`**（规则 `ui-events.cjs:213` ← 日志 `facebook-session.ts:1102`），且 presence-only 不产条目、**文案还是错的**（说「顺路去作者主页看看…」，FB 是就地读）。`[fb-like] ✓ 点赞成功` 被负向前瞻**有意排除**（`ui-events.cjs:142`）以防与结构化 like 重复计数——**这是对的，不要动**。

## 2. 为什么修在边缘、不碰协议与云端

- 活动流按设计就是**边缘对自身一手观察的本地投影**（`facebook-session.ts:146-149` 的注释已把这条写死：云端 `dailyUsage` 才是当日总量权威，这里只即时投影已确认动作、**不能据此猜测成功**）。
- 云端**已经知道**评论 / 加群的成败（`handler.ts:531-536` 的 `interaction.occurred` 闸），但 `ui.snapshot` 只有 7 个聚合字段（`protocol.ts:299-329`）、无逐条事件面，且 `dailyUsage` 只有 6 个动作 × 4 窗口的计数、**无时间戳无标题无加群无搜索**。把逐条活动改由云端下发＝新增协议字段 + 动热点文件 + 引入网络时序，**收益为零**（边缘本来就握着更全的一手证据）。
- 壳侧解析器 kind-agnostic 透传 → **零改动**。

**结论：改动面收敛在边缘两个文件 + 一个新叶子模块。**

## 3. 诚实分档（本设计的核心）

红线是「MUST NOT 静默假成功」。对应到叙述，四档：

| 档 | 判据 | 产条目 | 计数 |
|---|---|---|---|
| **成功** | 执行器**已有的**后置校验判成（点赞看反应真翻转 / 评论看 own-identity 服务器确认 / 加群看成员信号或结构确认） | ✅ | 仅评论 `comments:1` |
| **待批准** | 一手 DOM 观察到待审徽章 / 参与审批弹层 | ✅ 单列一档 | ❌ |
| **结构性失败** | 结构上做不到（评论框没找到 / 没权限 / 没结果） | ✅ | ❌ |
| **未开始** | 资源被占 / 被抢占 / 会话关闭中 / 能力不支持 / 只观察 | ❌ | ❌ |

三条纪律：

1. **不新增任何成功判定**。只叙述执行器**已经做出、且已回报云端**的判断。`ok:true` 的语义完全沿用现状。
2. **「未开始」用拒绝集实现，不用白名单**。新造的 reason 字符串默认落到「可见的失败」而非被静默吞掉——白名单会让未来新增的失败原因**静默消失**，那正是本次要修的病。
3. **待批准绝不计数**。它是「还没上墙」，计数会让本地兜底与云端权威打架。

`pending_group_approval` 是本次的**诚实枢轴**：执行器看到待审徽章后**有意不刷新**、正是为了保住这个证据（`comment-executor.ts:602-605`），这个事实值得告诉运营，且**永远不能**说成已发布。

## 4. 落点

### 4.1 新增 `aidcp-edge/src/facebook/companion-ui.ts`（叶子模块）

存在的唯一理由是**打通触达**：叙述器今天是会话私有方法（`facebook-session.ts:738-740`），而执行写动作的处理器拿不到它；从处理器 import 会话会**倒置既有依赖方向**（会话 → 处理器，`facebook-session.ts:521`）。故下沉为两者都 import 的叶子。只 import 协议类型 + `FacebookLikeObservation`，**无环**。

逐字搬入（连同其编码了诚实理由的文档注释一起）：`FacebookCompanionUiEvent`、`clipFacebookUiText`、`facebookReadUiText`、`facebookLikeUiText`、`emitCompanionUiEvent(log, event)`（logger 改为入参）。

联合扩展：`type` 增 `comment | comment_pending | comment_failed | join_group | join_pending | join_failed | search | search_failed`；`statsDelta` 增 `comments?`。**两者都安全**：`main.cjs:3414` 已经在把 `d.comments` 汇入 stats、`:3421` 已经在 bump dailyUsage 的 comment——管子**早于本次就存在**，无需改。

新增：`isAttempted(reason)`（拒绝集）、`reasonText(reason)`（机器码→人话，未知回落通用文案、**绝不猜**）、`facebookGroupName(obs)`（只用现读页面标题剥 Facebook 后缀，读不到回落「一个小组」，**绝不把 URL 当群名**——沿用 `facebook-session.ts:221` 已立的规矩）。

### 4.2 `facebook-session.ts`

- 删本地类型 / 三个文案构造器 / emit 方法，改 import。**保留私有包装** `emitCompanionUiEvent(e)`，使 4 个既有发射点（`:345` / `:704` / `:714` / `:727`）**逐字不变**——diff 最小，对唯一在工作的 like 路径零风险。
- `searchBrowse`（`:949-975`）：成功返回处（`:974`）发 `search`（关键词与卡数此刻均为一手）；失败返回处（`:951`/`:959`/`:964`/`:969`）经 `isAttempted` 后发 `search_failed`。**无 statsDelta**——搜索在全系统都不是被计数的互动（云端确认它从不进 `interaction.occurred` 也不进 `dailyUsage`，只经会话预算 `budget.searches` 记账）。
- 改 `profile.open direct`（`:1102`）的日志措辞，使小红书专属规则（`ui-events.cjs:213`）不再误命中。presence-only，**不丢任何条目**。

### 4.3 `comment-handler.ts`（修复主体）

两个构造点都已传 `logger: (m) => console.log(m)`（`main.ts:863` / `:1046`）→ 发出的行**直达 stdout → 每环境解析器，零接线改动**。

- `onSearch`：候选≥1 / ok 但 0 候选 → `search`（用执行器已回传的**真实群名** `containerName`，回落「群」）；`!r.ok` → `search_failed`；`!container` → **不产**（`permission_gated` 是配置问题、不是一次动作）。
- `onOpen`：成功处复用**与浏览路径同一个** `facebookReadUiText` → `note_open` + `views:1`，消除两路不对称。`editor_not_found` → **不产**（帖子真开了也真读了，回非成功只是让云端换下一个候选；发失败条目会被误读成「读失败」，**沉默才是诚实投影**）。
- `onComment`：`ok` → `comment` + `comments:1`；`pending_group_approval` → `comment_pending`（**无计数**）；其余经 `isAttempted` → `comment_failed`；`busy`/`preempted_by_task` → 不产。主语用**我们打进去的评论文本**（一手），**绝不用 permalink**。
- `onJoin`：**镜像云端自己的证据闸** `ok && clicked===true`（`handler.ts:531-536`），使客户端与云端**永不就「有没有加进去」打架**。`pending` / `questionnaire_required` → `join_pending`；`already_member` / `observation_only` → 不产。**无 statsDelta**——stats / dailyUsage 形状里根本没有 `joins`（`main.cjs:3409-3416`；云端投影只覆盖 6 个动作），新增会让本地投影与云端权威计数漂移，**零收益，YAGNI**。

### 4.4 FB 验证码盲区（既有规格违反）

`edge-fleet-console` 已要求「验证码拦截 / 需人工的环境永远浮到最上」，但：
- FB 检测行 `main.ts:996` 打「⚠ Facebook 检测到验证码，已上报云端」——不含正则要的「弹窗」「暂停操作」（规则 `ui-events.cjs:234`）→ `overlayBlocked` **从不置真**（`main.cjs:3438`）。
- FB 清除处理器 `main.ts:1001-1010` **什么都不打**（小红书那侧 `main.ts:1230` 会打）→ 两侧都没有。
- 更糟：该标志会被**任何 statsDelta 顺带清除**（`main.cjs:3438-3439`）→ 一次正常点赞就把「需要人工」抹绿。

修法：FB 两侧各发**结构化** `popup` / `popup_cleared` 事件（不靠中文正则），并把 `overlayBlocked` 的清除**收紧为只认显式 `popup_cleared`**，不再由 statsDelta 顺带清。

### 4.5 渲染层（纯装饰）

渲染层**不是**卡点、也不设 type 过滤，新 type 今天就能上屏、只是掉成灰点。补记号提升可读：`comment|comment_pending|comment_failed` → 评；`join_group|join_pending|join_failed` → 群；`search|search_failed` → 搜。`_pending` / `_failed` **有意共用同族记号**——句子已经承载真相，逐档换记号是噪声。

## 5. 对抗性评审留下的账

| 风险 | 判断 |
|---|---|
| **计数重复**（本地 comments +1 与云端 `interaction.occurred` 各记一次） | **可接受**：本地只是兜底，云端 `dailyUsage` 每 ~60s 快照推送**覆盖**本地值——与既有 like / view 完全同构，不是新引入的模式。**首个要在真机核的点。** |
| **待批准可能是常态而非例外** | **这是修复在起作用**，不是回归：它把一直存在的现实翻出来。预期运营初见会觉得「怎么全是失败」——需在验收说明里讲清。 |
| **群名读错比不读更糟** | 页面标题受语言 / 截断 / 通知前缀（`(3) 群名 | Facebook`）影响。已用「读不到即回落通用文案」兜住；**不猜**。 |
| **改 `profile.open` 措辞＝有意打破一条老规则** | presence-only、不丢条目、无测试断言它。低风险——但这正是本次审计揭示的那类**静默耦合**，必须在 tasks 里显式记账。 |
| **记号表是无保障的手工耦合** | type 串在核心、记号表在壳，typecheck 跨不过去。退化仅为「掉成灰点」，纯装饰失败模式，接受。 |
| **动了唯一在工作的路径** | 用「保留私有包装、4 个发射点逐字不变」把 diff 压成纯搬移。 |

## 6. 测试策略（按仓内克制原则）

既有解析器测试（`test/electron/ui-events.test.ts`）**只测解析器、从不执行发射器**，全靠手敲字面量——**一次改措辞它照样全绿而条目静默消失**。所以新覆盖必须**压在发射器侧**：

- `test/facebook/comment-handler.test.ts`（桩 client + 捕获 logger）：`ok:true` → 一条 `comment` 且 `statsDelta.comments===1`；**`pending_group_approval` → `comment_pending`、句中含待批准语义、且 `statsDelta` 缺席**（红线用例）；`busy`/`preempted_by_task` → **零** `[ui-event]` 行；加群 `ok&&clicked` → `join_group`，加群 `pending` → `join_pending` 且句中**不含**「加入了」。
- `test/electron/ui-events.test.ts`：一条——结构化 `comment_pending` 行原样透传且 `sentence` 完整、无 statsDelta（证明解析器确为透传）。

顺序按 §4：`test:acceptance` → `test` → `typecheck`。
