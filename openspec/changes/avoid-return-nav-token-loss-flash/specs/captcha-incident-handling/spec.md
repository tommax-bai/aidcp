## ADDED Requirements

### Requirement: 低置信未知遮罩的云端上报必须经一轮持续性确认

边缘对**最低置信的 `unknown` 阻断遮罩**（旁路监测按形状 / 尺寸 / iframe 启发式归类、无语义文案命中的那类）向云端上报 `risk.captcha_detected` 前 MUST 经**一轮持续性确认**：翻转进 `unknown` 时 MUST NOT 第一轮探测差异即上报，须延后约一个监测轮询周期后**复核遮罩仍在**才发。**单轮即消失的瞬时 `unknown`**（如离页返回途中一闪即被自愈掉的坏页）MUST NOT 上报 `risk.captcha_detected`、MUST NOT 触发账号风控状态迁移、MUST NOT 使云端暂停该 edge 下发。

`kind:'captcha'`（验证码厂商指纹命中）与登录墙类 MUST 保持**即时 fail-CLOSED**：MUST NOT 因本确认闸而延后，一经检出立即本地停手并即时上报 / 升级。本确认闸只作用于最低置信的 `unknown` 桶。

本要求约束的是**边缘何时上报**（上游），云端收到 `risk.captcha_detected` 后的 `kind→signal→state` 映射（`unknown→light→warned`、`captcha→confirmed→restricted`）、传输层暂停、告警、恢复语义**全部不变**。不新增 / 改动任何消息类型，两份 `protocol.ts` 消息总数仍为 44。

#### Scenario: 一闪而过的未知遮罩不惊动云端

- **WHEN** 边缘旁路监测某一轮把页面判成 `unknown` 阻断遮罩，但在确认窗内（约一个轮询周期）遮罩已消失、页面回到非阻断态
- **THEN** 边缘 MUST NOT 发 `risk.captcha_detected`，归属账号维持 `normal`、会话不被暂停；且因从未发过 `detected`，MUST NOT 发出无配对的孤儿 `risk.captcha_cleared`

#### Scenario: 持续存在的未知遮罩照常上报

- **WHEN** 一堵真实持续的未知阻断遮罩在确认窗后复核仍在
- **THEN** 边缘照常发一次 `risk.captcha_detected{kind:'unknown'}`，云端按既有映射迁移该账号 `normal→warned` 并暂停该 edge（行为不变）

#### Scenario: 验证码指纹类不被确认闸延后

- **WHEN** 边缘检出 `kind:'captcha'`（厂商滑块指纹）或登录墙
- **THEN** 边缘 MUST 即时本地停手并按现状即时上报 / 升级，MUST NOT 因低置信确认闸而延后（真验证码仍走 `confirmed→restricted`）

### Requirement: 瞬时阻断自愈时边缘自动上报清除且不留孤儿

边缘旁路监测从阻断态翻回非阻断态时 MUST 自动发 `risk.captcha_cleared`（现役行为，保留）。结合上条确认闸，边缘 MUST 保证 `detected` 与 `cleared` **配对**：只有真正发过 `risk.captcha_detected` 的阻断态，其自愈才发对应 `risk.captcha_cleared`；被确认闸抑制、从未上报过的瞬时 `unknown`，其消失 MUST NOT 触发孤儿 `cleared`，也 MUST NOT 遗留一条已发但永不清除的 `detected`。

#### Scenario: 上报过的阻断自愈后发配对 cleared

- **WHEN** 边缘曾就一堵持续遮罩发过 `risk.captcha_detected`，该遮罩随后自行消失
- **THEN** 边缘发一次 `risk.captcha_cleared`，云端解除该 edge 暂停、恢复下发（风控状态按既有语义不自动回滚）

#### Scenario: 被抑制的瞬时遮罩消失不发孤儿 cleared

- **WHEN** 一次被确认闸抑制、从未上报的瞬时 `unknown` 遮罩消失
- **THEN** 边缘 MUST NOT 发 `risk.captcha_cleared`（无配对 `detected`），云端侧无任何暂停 / 恢复扰动
