## MODIFIED Requirements

### Requirement: 决策指令携带可选时间指令

云端 → 边缘的决策指令 SHALL 支持可选的时间字段：`navigation.back` / `{platform}.note.close` 携带
`dwellMs`（离开当前页前应达到的总停留时间），`{platform}.note.like` / `xiaohongshu.note.collect` /
`{platform}.user.follow` / `{platform}.note.open` 携带 `thinkMs`（执行动作前的犹豫 / 感知时间）。时间字段
全部可选，缺失视为合法，边缘按内置默认兜底。云端 MUST NOT 在 `session.budget` 下发整套时间
系数要求边缘自行套公式计算内容相关时长。

#### Scenario: 返回指令带停留时长

- **WHEN** 云端评估某详情页后决定 `navigation.back`
- **THEN** 该 `navigation.back` 指令携带 `dwellMs`，其值由云端依据已上报内容与风控状态算出

#### Scenario: 旧边缘忽略未知时间字段

- **WHEN** 边缘版本早于本 change、收到带 `dwellMs` / `thinkMs` 的指令
- **THEN** 边缘忽略该字段、按内置默认兜底运行，行为不劣化（向后兼容）

### Requirement: 操作间隔按最小间隔 gating，等待与兜底不累加

边缘在执行「操作类」命令（`{platform}.note.open` / `xiaohongshu.profile.open` / 互动写命令（`{platform}.note.like`、`facebook.video.like`、`xiaohongshu.note.collect`、`{platform}.user.follow`、`{platform}.note.comment`、`xiaohongshu.comment.like`）/ `xiaohongshu.note.browse_images` / `xiaohongshu.note.scroll_comments`）前 SHALL 采用**最小间隔**语义而非无条件附加固定等待：维护**单一锚点**记录上次操作完成时刻（`lastActionEndAt`，取自**单调时钟**），收到下一个操作时计算 `elapsed = monoNow() − lastActionEndAt`、`remaining = max(0, floor − elapsed)`，仅补足 `remaining` 后执行。云端决策/网络往返耗时 MUST 计入 `elapsed`——已达兜底则立即执行、**MUST NOT** 在其之上再叠加兜底（不累加）。动作前犹豫 `thinkMs`（若下发）与最小间隔测同一「now→执行本动作」跨度，两者取 `max`、**MUST NOT** 相加。锚点在进程启动 / 断连重连 / CDP 重连时重置为空（首操作跳过间隔，由会话起点扫描延迟兜底）。详情页停留（`ensureDetailDwell`）与 feed 停留（`ensureFeedDwell`）测另一跨度，保留各自锚点，MUST NOT 与操作间隔叠闸（防双计）。

#### Scenario: 云端返回慢则立即执行、不再叠加

- **WHEN** 上次操作完成后，云端决策 + 往返耗时已达到本次操作的兜底 floor（`elapsed ≥ floor`）
- **THEN** 边缘立即执行本操作，不再额外等待（往返耗时被吸收，等待与兜底不累加）

#### Scenario: 云端返回快则只补差额

- **WHEN** 距上次操作完成的 `elapsed` 小于本次操作的兜底 floor
- **THEN** 边缘仅等待 `floor − elapsed` 补足差额后执行，实际间隔恰达 floor 而非 `elapsed + floor`

#### Scenario: 首操作与重连后无锚点跳过间隔

- **WHEN** 会话首个操作，或断连/CDP 重连后清空锚点后的首个操作
- **THEN** 不施加操作间隔（`thinkMs` 仍守非零下限），由会话起点扫描延迟兜底

#### Scenario: 单调时钟防跳变

- **WHEN** 运行期系统墙钟发生 NTP 校正或改表（后跳/前跳）
- **THEN** `elapsed` 由单调时钟计得、不受影响，不会因墙钟回拨变负导致卡死、也不会因前跳暴增导致间隔失效
