# facebook-reels-watch-pacing Delta

## ADDED Requirements

### Requirement: Reels 面翻页停留中心值来自重尾采样而非固定地板

云端为 `surface='reels'` 的 Facebook 翻页命令计算 `dwellMs` 时,SHALL 对每条命令独立采样一个观看时长中心值,采样自一个重尾加权混合分布:约 55% 权重的快划段(10–20s)、约 35% 权重的正常观看段(20–45s)、约 10% 权重的深看段(45–90s),段内均匀。采样结果 SHALL 乘以现役的 tempo(风控状态与配额档取更慢者)与 fatigue(会话进度)系数,并最终 clamp 到 [10_000ms, 90_000ms]。reels 面 MUST NOT 继续复用 feed 面的平台扫屏地板(`feedScrollDwellFloorMs`)作为唯一停留来源。

#### Scenario: 连续多条 Reel 的停留互不相同

- **WHEN** 同一会话内云端连续下发多条 reels 面翻页命令
- **THEN** 每条命令的 `dwellMs` 独立采样,长期分布覆盖 10–90s 全区间且呈重尾(多数落在快划/正常段、少数落在深看段),不再集中于任何单一常数附近

#### Scenario: 风控降档只放慢不加速

- **WHEN** 账号风控状态为 `warned` / `restricted`(tempo > 1)
- **THEN** 采样后的中心值按 tempo 放大后再 clamp,上限仍为 90_000ms;任何状态下 `dwellMs` MUST NOT 低于 10_000ms

#### Scenario: feed 与 search 面不受影响

- **WHEN** 云端下发 `surface='feed'` 或 `surface='search'` 的翻页命令
- **THEN** 停留计算走既有路径(卡片数地板与平台扫屏地板取 max),行为与本 change 之前逐字相同

### Requirement: 采样收口云端且不改协议与边缘

观看时长采样 SHALL 只发生在云端(与 Command Pacing「中心值收口云端、边缘只叠抖动」的既有边界一致);随命令下发继续复用既有 `dwellMs` 字段,MUST NOT 新增协议字段或 PacingOp 枚举成员,边缘的 lognormal 抖动层与停留达标逻辑 MUST NOT 因本 change 改动。

#### Scenario: 旧边缘零感知兼容

- **WHEN** 任意现役边缘版本收到带采样 `dwellMs` 的 reels 翻页命令
- **THEN** 边缘按既有逻辑(× tempo、叠 ±20% lognormal 抖动、锚定上屏内容到达时刻吸收评估耗时)保证实际停留达标,无需任何边缘改动

#### Scenario: 采样注入随机源可测

- **WHEN** 测试以确定性随机源调用采样函数
- **THEN** 段选择与段内取值完全可复现,且对随机源全域(0 与趋近 1)的输出都落在 [10_000ms, 90_000ms] 内
