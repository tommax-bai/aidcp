# browser-cold-standby Delta

## ADDED Requirements

### Requirement: 受限账号的待机提示携带真实恢复时刻

自动恢复接活后,`restricted` 属于**有固定恢复时刻**的阻塞。云端产出待机提示时:续场闸对 `restricted` 的裁决 SHALL 携带由恢复策略同源推导的恢复时刻;待机提示 SHALL 据此产出带真实等待时长的定时让位提示(等待 ≥ 让位阈值即 eligible),MUST NOT 再对 restricted 走「回访」语义,也 MUST NOT 因 `state:restricted` 不带 `quota:` 前缀而落进「硬阻塞不让位」兜底。`frozen` 与周历整周全关等仍无恢复时刻的阻塞 SHALL 维持既有回访语义。

#### Scenario: full_pause 受限产出定时让位

- **WHEN** 全局策略为 `full_pause`,账号 `restricted` 且距恢复时刻尚余大于让位阈值的等待
- **THEN** 待机提示 eligible=true、等待时长 = 恢复时刻 − 当前时刻,边缘据此关闭浏览器让出槽位

#### Scenario: browse_only 受限在会话结束后同样让位

- **WHEN** 全局策略为 `browse_only`,受限账号当前会话已结束、续场闸以 `risk_state` 拦停
- **THEN** 待机提示按续场闸携带的恢复时刻产出定时让位,而非回访

#### Scenario: 冻结维持回访

- **WHEN** 账号为 `frozen`
- **THEN** 待机提示维持既有回访语义(让位 + 无恢复承诺的回访时刻)

### Requirement: 受限让位不得越过「解除阻塞需要浏览器」一票否决

「正卡在验证码 / 阻断弹窗、解除需要该浏览器」的一票否决 SHALL 保持压在包括受限定时让位在内的所有提示来源之前。受限往往正由弹窗信号触发,MUST NOT 出现「信号升级为 restricted → 定时让位 → 关掉运维正要去解弹窗的浏览器」的路径;弹窗清除、验证码暂停解除后,后续周期链才可以产出受限的定时让位提示。

#### Scenario: 受限 + 验证码待解时不让位

- **WHEN** 账号因阻断弹窗升级为 `restricted`,该边缘的验证码暂停仍未解除
- **THEN** 待机提示为硬阻塞、不让位;弹窗清除后的下一跳才可能产出定时让位

### Requirement: 受限账号恢复后经既有唤醒路径归队

受限账号冷待机期间,恢复 SHALL 复用既有唤醒路径,MUST NOT 新增边缘侧机制:周期链健在时,扫描器把状态翻回 `warned` 后的下一跳提示不再 eligible,边缘据此唤醒;周期链断掉时按提示 `wakeAt`(= 恢复时刻)兜底唤醒。本 change 对 `ui.snapshot` 的待机载荷 MUST NOT 新增或删除字段。

#### Scenario: 状态翻转经周期链唤醒

- **WHEN** 冷待机中的受限账号被扫描器恢复为 `warned`
- **THEN** 下一跳周期链提示不再 eligible,边缘唤醒浏览器并恢复浏览闭环
