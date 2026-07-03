## ADDED Requirements

### Requirement: 操作间隔按最小间隔 gating，等待与兜底不累加

边缘在执行「操作类」命令（`note.open` / `profile.open` / `interaction.*` / `note.browse_images` / `note.scroll_comments`）前 SHALL 采用**最小间隔**语义而非无条件附加固定等待：维护**单一锚点**记录上次操作完成时刻（`lastActionEndAt`，取自**单调时钟**），收到下一个操作时计算 `elapsed = monoNow() − lastActionEndAt`、`remaining = max(0, floor − elapsed)`，仅补足 `remaining` 后执行。云端决策/网络往返耗时 MUST 计入 `elapsed`——已达兜底则立即执行、**MUST NOT** 在其之上再叠加兜底（不累加）。动作前犹豫 `thinkMs`（若下发）与最小间隔测同一「now→执行本动作」跨度，两者取 `max`、**MUST NOT** 相加。锚点在进程启动 / 断连重连 / CDP 重连时重置为空（首操作跳过间隔，由会话起点扫描延迟兜底）。详情页停留（`ensureDetailDwell`）与 feed 停留（`ensureFeedDwell`）测另一跨度，保留各自锚点，MUST NOT 与操作间隔叠闸（防双计）。

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

### Requirement: 兜底 floor 全局后台可配置，经握手下发并热加载

系统 SHALL 支持在后台（console）编辑每类操作的兜底 floor 区间 `{minMs, maxMs}`，存于云端 PostgreSQL（`pacing_floor_config`，schema 启动自建、无迁移器），作用域为**全局一套**，覆盖四类操作 `action` / `scroll` / `card_gap` / `detail_dwell`。云端 SHALL 在 `welcome` 握手响应中携带可选 `pacing` 快照（`tempo` 标量 + 每类操作 floor 区间 `opFloorsMs`），供边缘最小间隔 gating 与详情页停留兜底取用。配置更新 SHALL 在各边缘**下次握手 / 重连**时生效（连接级热加载，无需重启云端）。表内无某 op 行时 SHALL 逐项回落内置非零默认（= 现役预设量级），保证零回归。边缘 SHALL 在**重连复用同一会话对象**时经 `applyPacingSnapshot` 重新注入新快照（MUST NOT 让连接级快照在重连路径退化成进程级）。

#### Scenario: 后台改值下次握手生效

- **WHEN** 运营在 console 把 `action` 的兜底区间调大并保存，随后某边缘重连握手
- **THEN** 该边缘取到新区间，其后续 `action` 类操作的最小间隔按新值 gating

#### Scenario: 配置缺某 op 逐项回落内置默认

- **WHEN** `pacing_floor_config` 表中缺 `scroll` 行、其余 op 有行
- **THEN** 边缘对 `scroll` 用内置非零默认、对其余 op 用下发值（逐字段回落、非全有全无）

#### Scenario: 重连重注入配置

- **WHEN** 边缘因身份翻转触发重连、复用同一会话对象，且期间云端配置已变更
- **THEN** 边缘经 `applyPacingSnapshot` 灌入新握手的 floors/tempo，新值在重连后立即生效

#### Scenario: 旧边缘忽略 pacing 快照

- **WHEN** 边缘版本早于本 change、收到带 `pacing` 的 `welcome`
- **THEN** 边缘忽略该字段、用内置非零默认运行，行为不劣化（向后兼容）

### Requirement: 绝不零延迟经三道夹逼保证，防指纹经反射采样

无论后台如何配置，系统 SHALL 保证有效兜底间隔恒大于每类操作的非零防呆下限——**配置只能抬高延迟、永远抬不穿非零下限**。该保证 SHALL 由三道夹逼共同实现：① facade 写入校验（`min/max` 非负整数、`min ≤ max`、`max ≥ min × 1.5` 最小展宽、`≤ CAP`，整块拒不部分落库）；② 云端读出口 `clamp(v, 防呆下限, CAP)`（权威夹点，即便有人绕过面板 psql 直插 0/负数/超界，离开云端进程前已夹成非零合法）；③ 边缘 `Math.max(防呆下限, ·)` 二次夹。CAP SHALL 为全局小常量（`CAP_MS = 15000`），结构上 MUST < 云端 idle 看门狗下限（`IDLE_NUDGE_MIN_MS = 200000`），并由不变量测试断言该常量关系。边缘每次现采样兜底目标，采样 SHALL 用**反射**而非硬裁（越界样本反弹回分布内），使被补齐的间隔散布成自然分布、MUST NOT 在固定 floor 值处堆积成尖峰（消除机器指纹左壁）。功能性 settle（等页面加载/编辑器出现/重渲染）与有界轮询/复检 MUST NOT 被折进最小间隔 gating（否则会打断真实前置条件 → 静默假成功）。

#### Scenario: 后台配零被夹回非零下限

- **WHEN** 运营（或直接 psql 写库）把某 op 的 `minMs` 设为 0 或负数
- **THEN** 经三道夹逼后边缘实测该 op 间隔仍 ≥ 其非零防呆下限，不出现零延迟

#### Scenario: 最小展宽校验拒绝零展宽

- **WHEN** 运营提交某 op 的 `min_ms == max_ms`（零展宽）
- **THEN** facade 拒绝该写入（`max_ms ≥ min_ms × 1.5` 不满足），不落库，防指纹分布不退化为单点

#### Scenario: 配大值不误触看门狗

- **WHEN** 运营把某 op 兜底配到很大
- **THEN** 经 `clamp(·, ·, CAP=15000)` 后有效间隔恒 ≤ 15s ≪ 200s，单次前台等待不触发 idle 看门狗杀会话

#### Scenario: 间隔分布不堆尖峰

- **WHEN** 大量操作因云端快回被补差额到兜底附近
- **THEN** 边缘反射采样使这批间隔散布成分布而非堆在同一固定值，无可识别的竖直左壁

## MODIFIED Requirements

### Requirement: 缺时间指令时的安全降级

边缘在未收到时间字段（旧云端 / 断连 / 自主动作）时 SHALL 回退到内置默认下限，
MUST NOT 退化为零延迟。兜底默认经 `welcome` 握手响应的可选 `pacing` 快照下发
（`tempo?` 标量 + 每类操作 floor 区间 `opFloorsMs?`）供边缘最小间隔 gating、详情页停留兜底
与断连兜底使用；该快照 MUST NOT 包含 read / pause / fatigue 系数（这些收口在云端，随决策指令
以 `dwellMs` / `thinkMs` 下发）。快照缺失或某字段缺失时边缘 SHALL 逐字段回落内置非零默认，
MUST NOT 回落零。已废弃的 `session.budget.pacing` 通道 MUST NOT 再作为兜底默认的下发路径
（该通道边缘从不消费、携带即被丢弃）。

#### Scenario: 断连仍非零延迟

- **WHEN** 边缘在没有任何时间指令、且无 `welcome` pacing 快照的情况下运行
- **THEN** 各决策节点与详情页返回仍使用边缘内置非零默认下限，不出现零延迟秒退

#### Scenario: 握手快照仅含兜底参数

- **WHEN** 云端在 `welcome` 下发 `pacing` 快照
- **THEN** 该对象仅含 `tempo` 与每类操作 floor 区间等兜底字段，不含内容相关的 read / pause / fatigue 系数

#### Scenario: 不经废弃通道下发

- **WHEN** 云端需要向边缘提供兜底默认
- **THEN** 经 `welcome` 快照下发，MUST NOT 依赖 `session.budget.pacing`（边缘不消费该通道）
