## ADDED Requirements

### Requirement: 协助注入点击必须达到不低于日常点击的合成拟人度

当运营通过云端协助页提交离散落点后，边缘把这些落点注入原浏览器时，注入动作的合成拟人度 MUST NOT 低于日常浏览点击。系统 MUST 复用既有贝塞尔 + ease-in-out + overshoot 拟人路径，且 MUST NOT 使用比日常点击更弱的参数（现状的 `jitter:0` + `overshoot:false` 被禁止作为常态）。所有随机与停顿 MUST 走可注入随机源以保证桩测确定性；回执与风控语义（见"远程协助后的恢复必须由 edge 复检清除驱动"）MUST 保持不变。

#### Scenario: 注入路径非瞬移且带人类特征
- **WHEN** 边缘对某个落点注入点击
- **THEN** MUST 沿贝塞尔曲线逐帧 `mouseMoved` 后再 `mousePressed`/`mouseReleased`（非瞬移）
- **AND** MUST 以适度概率保留 overshoot（越过目标再回拉）并叠加小幅落点 jitter，press 仍落在运营指定目标

#### Scenario: 多点之间光标连续
- **WHEN** 一次协助包含多个落点（依次点击）
- **THEN** 下一个落点的移动起点 MUST 取上一个落点的**真实落点**（含 jitter/overshoot 残差），MUST NOT 让每点各自从随机起点冒出

#### Scenario: 逐帧移动延迟带抖动
- **WHEN** 边缘逐帧派发 `mouseMoved`
- **THEN** 帧间延迟 MUST 带抖动（对数正态或等价），MUST NOT 是方差为 0 的固定周期

#### Scenario: 落点前读图停顿与点间对数正态停顿
- **WHEN** 边缘移动到目标后、按下之前
- **THEN** MUST 插入一段可注入的读图/瞄准停顿（dwell）
- **AND** 多点之间 MUST 用对数正态采样的停顿替代固定时距，仅在非末点后停顿

#### Scenario: 节奏参数按机器派生避免车队指纹
- **WHEN** 多台边缘对同类验证码执行协助注入
- **THEN** 节奏分布的中心值 MUST 含按 `edgeId` 派生的每机偏置，MUST NOT 让全 fleet 使用逐字相同的固定节奏常量

#### Scenario: 拟人化不改变诚实回执
- **WHEN** 注入后遮罩仍在或注入过程抛错
- **THEN** MUST 沿用既有 `settle → reprobe → still_blocked / failed / 回传新截图` 回执，MUST NOT 因拟人化改动而静默假成功；只有真实清除才发 `risk.captcha_cleared`
