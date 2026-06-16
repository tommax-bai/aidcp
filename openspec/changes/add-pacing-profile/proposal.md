# 指令级节奏（Command Pacing）：云端算停留时长，随决策指令下发；边缘抖动+兜底

## Why

- 现象：访问详情页时，若内容无价值，边缘会**几乎瞬时返回**（`navigation.back`），快到不像
  真人能完成"扫一眼 → 判断 → 退出"，容易被行为风控识别。
- 根因：详情页缺少最小停留兜底，且**没有任何管道把"该停多久"告诉边缘**。`session.budget`
  只携带 `quotaLevel/viewOnly/durationMs/maxActions`，时间节奏散落在边缘、无法被内容与风控状态联动。
- 关键设计取舍（已修正一次误判，见下）：**内容相关的停留 / 思考时长，应由云端在做决策时一并算出、
  随指令下发**，而不是云端发系数、边缘自己套公式。理由：
  1. **云端本来就有内容**——`note.detail`（edge → cloud）已上报完整正文 `content` 与点赞/收藏计数；
     `ContentCurator` / `InteractionAppraiser` 本来就要读它做评估。
  2. **不增加往返**——云端评估完本来就要回 `interaction.like` / `navigation.back`，把 `dwellMs` /
     `thinkMs` 挂在**同一条响应**上是免费的；那次 round-trip 本就发生。
  3. **更符合「边轻云重」**——"思考停多久"是思考的一部分，放在已经在思考的云端才 DRY。
- 但有三样**仍必须留在边缘**，搬到云端会出新问题：
  1. **反指纹抖动**：云端若确定性算出 dwell，两个账号看同一篇笔记会停得分毫不差——这本身是指纹。
     最终一层 lognormal 抖动留在边缘（或云端按 账号×会话 加随机种子）。
  2. **子动作运动时序**：滚动逐帧 wheel、鼠标贝塞尔轨迹、打字逐键（§3.3/§3.5）——是"动作怎么执行"，
     属边缘拟人化执行层。
  3. **断连 / 自主动作兜底**：边缘自己刷 feed、没等云端回话的微节奏，以及断网时，需本地下限托底。

## What Changes

- **协议（核心）**：云端 → 边缘的**决策指令**新增**可选时间字段**，由云端基于已上报内容 + 风控状态 +
  会话进度算出"中心值"：
  - `navigation.back` / `note.close` 增 `dwellMs?`——离开当前页前应达到的**总停留时间**；
  - `interaction.like` / `interaction.collect` / `interaction.follow` / `note.open` 增 `thinkMs?`——
    动作前的**犹豫 / 感知时间**。
  - 语义统一定义为「时间指令（timing directive）」，全部可选、向后兼容（旧端忽略）。
- **云端**：§3（`docs/risk-control.md`）的时间系数（停顿对数正态、`read_time = base+k_text·len+k_img·img`、
  疲劳曲线）**收口在云端一处**；评估角色产出决策时一并算 `dwellMs`/`thinkMs`，乘以风控状态驱动的
  `tempo`（`normal=1.0 / warned≈1.3 / restricted≈1.6`）与会话进度疲劳因子。
- **边缘**：收到时间指令 → 叠一层 lognormal 抖动 → 保证 `dwell` 类**实际停留达标**、`think` 类**动作前等够**；
  纯机械连续帧不挂；**返回前永远确保达标，详情页不秒退**。
- **降级**：未携带时间字段（旧云端 / 断连 / 自主动作）→ 边缘用内置默认下限兜底，**永不零延迟**。
  `session.budget` 可选保留一个**极薄**的 `pacing` 默认块（`tempo?` / `dwellFloorMs?`），仅供边缘自主
  动作与断连兜底用；缺失则用边缘内置常量。
- **不做**：不在 `session.budget` 下发整套系数让边缘套公式（已否决）；时间中心值不在边缘重算；不做
  跨账号节奏协同、不做会话中途热更（留作后续）。

## Impact

- Affected specs（新增能力）：`command-pacing`。
- Affected code：
  - `aidcp-cloud`：`src/comm/protocol.ts`（角色指令 payload 增可选时间字段；`SessionBudget` 增极薄
    `pacing` 默认）、`src/risk/` + 评估角色（算 `dwellMs`/`thinkMs`，应用 `tempo`/疲劳）。
  - `aidcp-edge`：`src/comm/protocol.ts`（同名投影）、拟人化 / 浏览执行（消费时间指令、叠抖动、返回达标、
    默认兜底）。
  - `ai-dcp`：`docs/protocol.md §3.7/§3.9`（指令时间字段 + `session.budget` 默认）与 `docs/risk-control.md §3`
    （标注系数收口云端、经指令下发）回写。
- 向后兼容：纯增量可选字段，旧边缘忽略时间字段并走默认兜底，行为不劣化。
