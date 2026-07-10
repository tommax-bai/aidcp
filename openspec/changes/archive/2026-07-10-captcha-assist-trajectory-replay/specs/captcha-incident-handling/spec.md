## ADDED Requirements

### Requirement: 远程协助可复刻运营真实鼠标轨迹

系统 SHALL 允许控制台采集运营在协助页画面上的真实鼠标轨迹，并把它随既有 `captcha.assist.click` 命令上送、由原边缘复刻到原浏览器。轨迹 MUST 作为既有命令的**可选附加字段**承载，MUST NOT 新增 MessageType。**离散落点始终是落点的权威来源**；轨迹仅贡献移动路径与按下时机。无轨迹或轨迹无效时，系统 MUST 诚实回落到合成拟人路径（见"协助注入点击必须达到不低于日常点击的合成拟人度"），MUST NOT 谎称使用了轨迹。风控语义（detected→restricted、cleared 不自动回 normal、只有真实清除才发 `risk.captcha_cleared`）MUST 保持不变。

#### Scenario: 控制台采集轨迹并与落点同基准
- **WHEN** 运营在协助页画面上移动并点击
- **THEN** 控制台 MUST 节流采样归一化坐标 `{x,y}`（[0,1]）+ 相对首样本毫秒 `t`，采样基准 MUST 与落点采集用**同一元素的 rect**
- **AND** MUST 在 `pointerdown` 时记录当前样本下标进 `clicks`，与 `points` 顺序对齐
- **AND** 画面 `snapshotId` 变更时 MUST 连同已选落点一起重置轨迹缓冲；不可交互态 MUST 不采样

#### Scenario: 落点权威，样本仅供移动时序
- **WHEN** 边缘回放轨迹
- **THEN** 每个 `mousePressed`/`mouseReleased` 的坐标 MUST 取权威落点 `points[i]` 的缩放值，MUST NOT 取样本漂移坐标（运营点完把鼠标移开也不受影响）

#### Scenario: 按下前必须补一帧移动到权威落点
- **WHEN** 边缘将在某个落点按下
- **THEN** 在 `mousePressed` 之前 MUST 补发一帧 `mouseMoved` 到该权威落点，保证 mousedown 坐标 == 最后一次 mousemove 坐标，MUST NOT 出现"mousedown 落在鼠标从未移动到的坐标"的瞬移伪影

#### Scenario: clicks 与 points 语义校验
- **WHEN** 收到带 `trajectory` 的点击
- **THEN** `clicks.length` MUST 等于 `points.length`；回放 MUST 按样本下标建 press 查找表、允许 `clicks` 非单调（运营先点 B 再点 A）
- **AND** 任一不满足（长度不等/下标越界）MUST 丢弃 trajectory 并诚实回落合成路径

#### Scenario: 缩时只裁剪长停顿，不等比压缩
- **WHEN** 轨迹总时长超过上限或含超长停顿
- **THEN** 系统 MUST 通过裁剪单个大 `Δt`（clamp 长停顿）来收敛，MUST NOT 等比压缩全程时序（避免产生超人速度）

#### Scenario: 回放叠抖动不做 verbatim 原样重放
- **WHEN** 边缘逐帧派发轨迹
- **THEN** 帧间 `dt` MUST 叠对数正态抖动、坐标 MUST 叠 ±1px 亚像素，去除零 `dt`；MUST NOT verbatim 原样重放固定节流采样节奏

#### Scenario: 三层守卫与可观测丢弃
- **WHEN** 轨迹在 panel 入口 / 云端 `submitClick` / 边缘消费端任一层被判畸形或超限
- **THEN** 系统 MUST 钳制（降采样/单调化/时长上限/坐标范围）或丢弃 trajectory 并**保留 `points` 继续**
- **AND** 丢弃 trajectory MUST 产生可观测日志/计数，MUST NOT 静默丢

#### Scenario: 回放模式回执用于度量
- **WHEN** 边缘完成一次协助点击并回报结果
- **THEN** `captcha.assist.click_result` MUST 携带 `replayMode`（`trajectory` 或 `synthetic`），使云端可把复检结果与所用输入模式关联

#### Scenario: 回放异常诚实回报
- **WHEN** 回放中途抛错，或轨迹为空/极短（运营秒点无移动）
- **THEN** 抛错 MUST 走既有 catch 如实回 `failed`；空/极短轨迹 MUST 回落合成、MUST NOT 当作有效轨迹硬回放
