## Why

运营在 dev 真机跑 Facebook 时报「触发了多次评论，但客户端的记录里一条都没有」。核查坐实：**Facebook 环境的客户端活动流只可能出现 5 类条目**——账号就位、已连接云端、开始自动浏览、读、赞。评论 / 加群 / 搜索**一条都不产**。

根因是两条产线都覆盖不到 Facebook 的写动作：

1. **委托绕过**：`interaction.comment` / `group.join` / 带 `taskId|container` 的 `search.execute` / `note.open{url}` 由 `FacebookBrowseSession.dispatch()` 直接委托给 `FacebookCommentHandler`（`facebook-session.ts:512-531`），该处理器自己调 `client.report*` 后返回，**根本走不到**唯一的叙述出口 `emit()`（`facebook-session.ts:700-736`）。这是**发射器绕过**，不是闸拒绝。
2. **叙述器天生窄**：`FacebookCompanionUiEvent.type` 是封闭 4 值联合（`facebook-session.ts:151-158`）且已用满，结构上没有「评论 / 加群 / 搜索」的位置；`emit()` 的 action 分支还硬编码只放行 `action==='like' && ok`（`:725`）。
3. **中文日志兜底表对 FB 几乎全失效**：22 条规则里 21 条的措辞只由小红书浏览会话或 `if (autoBrowse)` 块打印，而 `autoBrowse = wantsAutoBrowse && supportsBrowse && !useFacebookBrowse`（`main.ts:951`）**按构造排除 Facebook**。唯一命中的一条（`/命令: profile\.open/`）还**叙述错了**——它说「顺路去作者主页看看…」，而 FB 是就地读、从不跳转。

危害不止「少显示」。今天运营**分不清「没做」和「做了但没显示」**：那些评论里相当一部分很可能卡在群参与审批（`pending_group_approval`，评论已提交但未上墙）或评论框没找到（`editor_not_found`），这些**同样隐形**。

同批修一个**已被违反的既有规格**：`edge-fleet-console` 要求「验证码拦截 / 需人工的环境永远浮到最上」，但 FB 环境的 `overlayBlocked` **从不置真**——FB 检测行打的是「⚠ Facebook 检测到验证码，已上报云端」，不含兜底正则要的「弹窗」「暂停操作」；FB 的清除处理器则**什么都不打**。结果：卡在验证码上的 FB 机器在客户端里是绿的，而且那个标志还会被任何一次正常点赞 / 阅读**顺带清掉**（`main.cjs:3438` 由 statsDelta 触发）。运营不知道该去救哪台机器。

## What Changes

- **抽出 Facebook 叙述器**为叶子模块，让委托处理器够得着（今天它是会话私有方法，处理器无从调用；反向 import 会倒置既有依赖方向）。既有 like / read 发射点保持逐字不变。
- **按诚实边界补全写动作叙述**：评论 / 加群 / 搜索各自分「成功 / 待批准 / 结构性失败 / 未开始」四档。**不新增任何成功判定**——只叙述执行器已经做出、且已回报云端的判断。
- **待批准自成一档、且不计数**：`pending_group_approval`（评论已提交、等群管理员批准）与加群 `pending` / `questionnaire_required` 是**一手 DOM 观察到的真实事实**，MUST 如实单列，MUST NOT 说成已发布 / 已加入，MUST NOT 贡献计数。
- **未开始 ≠ 失败**：`busy` / `preempted_by_task` / `session_closing` / `browse_disabled` / `capability_unsupported` / `observation_only` 不产条目。实现为**拒绝集**而非白名单，使新造的 reason 默认**可见**而非被静默吞掉。
- **补齐评论路径开帖的「读」条目**：同一条 `note.open` 在浏览路径记「读」+ 浏览数 +1、在评论路径什么都不记，两路复用同一文案构造器消除该不对称。
- **修 `profile.open direct` 的错误叙述**：改日志措辞使小红书专属规则不再误命中 FB。
- **修 FB 验证码盲区（既有规格违反）**：FB 阻断检测 / 清除必须点亮与清除客户端「需要处理」态，且该态 MUST NOT 被无关的 statsDelta 顺带清除。
- 渲染层补「群」「搜」两个类型记号（纯装饰；渲染层不按 type 过滤，缺记号只是掉成灰点）。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-companion-ui`: Facebook 写动作（评论 / 加群 / 搜索）必须产结构化活动条目，且按「成功 / 待批准 / 结构性失败 / 未开始」如实分档；评论路径开帖与浏览路径共用同一「读」叙述。
- `edge-fleet-console`: 「需要处理」态检测必须平台中立（Facebook 验证码 / 阻断必须点亮），且 MUST NOT 被无关动作顺带清除。

## Impact

- `aidcp-edge`：新增 `src/facebook/companion-ui.ts`；改 `src/facebook/facebook-session.ts`、`src/facebook/comment-handler.ts`、`src/main.ts`（FB 阻断检测 / 清除日志）、`src/electron/main.cjs`（overlayBlocked 清除条件）、`src/electron/renderer/renderer.js` + `styles.css`（类型记号）、`src/electron/ui-events.cjs`（**仅文档注释，零逻辑**）。
- **无协议变化、无云端变化、不碰任何热点文件**：活动流是边缘端对自身已观察事实的本地投影；壳侧解析器已经是 kind-agnostic 的透传，管子现成。
- `aidcp` control repo：上述两份能力规格的 delta、设计、任务与验证记录。
- 运行时目标：edge 本地。**不涉及 ECS 部署**（edge 不部署到 ECS），**不出安装包**（按 §6，出包属用户显式触发）。
- 真机验收项登记 `docs/real-machine-acceptance-backlog.md`。

## Non-Goals

- **不动发布卡**：FB 发帖已经过平台中立的发布链到达 UI（驱动发布卡 / 在场感 / 发布计数），只是不产活动流「行」——那是既有的有意设计，不在本次范围。
- **不修小红书「关注」假成功**：核查中发现 `✓ 关注成功` 是点击 + 固定 1500ms 睡眠后**无条件打印**、无后置校验（`browse-session.ts:2653-2656`），而点赞 / 收藏都轮询到图标真翻转才打（`:2293-2296`）。这撞「绝不静默假成功」红线，但它在小红书主浏览循环这条另一路上，**另起 change 串行做**，不与本次并行。
- **不给小红书补搜索条目**：XHS 那条搜索日志打在**下发时**、搜索还没执行，转成活动条目等于断言一个未观察到的成功——正是红线所禁。只能诚实地做成在场感，价值低，不做。
