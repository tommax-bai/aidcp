## Context

Cloud 已在 `page.cards.arrived` 的可信 Reel 呈现边界对点赞执行 25% 的一次性随机选择；Edge 已具备 `FacebookReelsReader.follow(noteId, shadow)`，会在点击前后绑定同一规范 Reel、唯一作者和唯一 Follow/Following 控件。但两个能力没有接起来：Cloud 没有自动 Reel 关注策略，Edge 握手也没有声明该构建是否包含 Reel 关注执行器。

同时，Cloud 平台注册表把 Facebook 通用 `follow` 声明为 `no_follow_actuator`。该声明对普通主页关注仍然正确，却也被用量投影误当成“Facebook 完全没有任何关注能力”，导致 `dailyUsage.follow` 的计数、配额和窗口全部被摘掉。客户端渲染器本身已经按 Cloud 提供的键动态显示指标。

## Goals / Non-Goals

**Goals:**

- 每个会话内首次确认的唯一 Facebook Reel 独立执行一次 10% 关注意图选择。
- 在意图下发前保留本轮预算、RiskController 分时/每日配额、冷却、同账号去重、会话抑制和 Edge 版本能力门禁。
- 仅用 Edge 的同 Reel Following 后置证明确认新关注；失败、shadow、already-followed 均不计数。
- 区分 Facebook 的普通主页关注与 Reel 内联关注，使今日关注总量/配额可见但不误开启主页链路。
- 让确认的新 Reel 关注立即出现在客户端活动流和本地兜底计数中，随后由 Cloud 权威今日数据校准。

**Non-Goals:**

- 不为 Facebook 普通 Feed 或作者主页增加关注执行器。
- 不根据作者内容质量或 LLM 评分选择关注，也不改变现有 25% 点赞策略。
- 不改变配额数值、慢启动曲线、RiskController 计数语义或数据库结构。
- 不新增协议消息/字段，不在本变更中构建 Edge 安装包。

## Decisions

### 1. Cloud 在可信 Reel 呈现边界做独立决策

`page.cards.arrived{listKind:'reels', cards:[one]}` 是 Edge 已证明当前视频发生切换的唯一边界。Cloud 新增独立的 Reel-follow 决策集合；规范 `/reel/<id>`、非空作者和新身份三条件满足后先占决策坑，任何后续弃权、配额阻断或命令抑制都不会因重复上报重抽。

关注与点赞分别持有决策集合并分别调用一次注入随机源。关注只有在随机值有限、位于 `[0,1)` 且严格小于 `0.10` 时命中；等于 `0.10` 时弃权。两项策略互不替代，命中关注不改变点赞决策，反之亦然。

替代方案是放在 Edge 端切卡后随机。拒绝该方案，因为主节奏、配额、风控和多节点去重均由 Cloud 权威管理；Edge 只应执行页面动作和验证终态。

### 2. 配额门禁在随机意图下发前逐层执行

决策坑占用后依次检查：连接是否声明 `facebook_reel_follow_v1`、本轮 `remainingBudget('follow')`、`canInteract('follow')` 的 RiskController 裁决、关注冷却，然后才掷关注骰并通过现有 `sendCommand` 下发 `{action:'follow', params:{authorId,noteId,thinkMs}}`。`sendCommand` 继续负责评论支线抑制和 `InteractionGuard` 同账号作者去重。

这意味着配额已经耗尽的 Reel 不下发、不计成功，也不在配额恢复后靠同卡重报补抽；下一条新 Reel 才是新的决策机会。下发不乐观扣预算，仍只在 `action.completed{action:'follow',ok:true,reason!='already_followed'}` 时扣本轮预算并由 `interaction.occurred` 记录风控事实。

### 3. 用独立 `reel_follow` 平台能力解决“显示与普通关注”冲突

Cloud 平台注册表新增 `reel_follow`：Facebook 为 true，小红书/视频号为 false；原 `follow` 继续表示 FollowAgent 的主页关注，并保持 `follow => profile_visit => browse` 不变量。用量投影对 `follow` 指标采用 `follow OR reel_follow`，因此 Facebook 会收到关注计数、配额和各时间窗口，但 FollowAgent 仍看到普通 `follow:false`，不会启动主页关注。

Edge 的 `facebook_reel_follow_v1` 是构建能力位，不是业务配额或成功信号。Cloud 只对声明它的连接启用自动 Reel 关注，避免已部署旧客户端收到无法执行的命令。未声明时每日关注指标仍可显示历史/权威计数，但不会自动下发关注。

### 4. 客户端即时活动与 Cloud 权威总量分工

Facebook 会话仅在 follow 回执 `ok:true` 且不是 `already_followed` 时发结构化 `follow` 活动和 `statsDelta.follows=1`。shadow、目标歧义、状态未变、验证不确定和 already-followed 均不产生成功活动。活动使用通用“关注了一位 Reel 作者”文案，不展示可能是机器标识的 `authorId`。

客户端“今日进展”仍按 Cloud `dailyUsage` 提供的键渲染；Cloud 投影开始提供 Facebook `follow` 后，现有渲染器无需平台硬编码即可显示总数、配额和窗口。活动图标把关注与点赞分开，使用“关”记号。

## Risks / Trade-offs

- [10% 只是意图概率，真实成功率会更低] → 配额、冷却、重复作者、already-followed 和平台验证都会进一步减少真实关注；客户端只显示确认事实，不承诺命中数。
- [Reel 卡片只有作者展示名，没有稳定作者 ID] → 缺作者时直接弃权；展示名仅用于同账号保守去重，真正写入目标仍由 Edge 的规范 Reel + 同页唯一作者/控件验证绑定。重名最多造成少关注，不会点错后声称成功。
- [Cloud 与 Edge 版本偏斜] → `facebook_reel_follow_v1` 未声明时 Cloud 不下发自动关注；Cloud 部署可先行，Edge 新活动展示等待后续安装包。
- [平台能力表新增维度影响其它平台] → Record 全覆盖与平台投影测试固定小红书、Facebook、视频号的逐键形状，未知平台继续保持既有 fail-safe。

## Migration Plan

1. 在隔离 Cloud/Edge worktree 实现能力声明、随机策略、投影和 UI 活动并完成测试。
2. 先快进合入 Edge 源码但不构建安装包；再合入 Cloud 和控制仓。
3. 从干净 Cloud 默认 checkout 部署到 `dev`。旧 Edge 未声明能力时只获得关注指标展示，不收到自动关注命令。
4. 回滚 Cloud 时撤销随机策略和 `reel_follow` 投影声明即可立即停止自动关注；Edge 的能力位和活动处理保持休眠、无副作用。

## Open Questions

无。10% 阈值、Reels-only 范围、配额约束和客户端展示均由本次请求明确。
