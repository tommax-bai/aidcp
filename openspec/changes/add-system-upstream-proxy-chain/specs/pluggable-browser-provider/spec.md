## ADDED Requirements

### Requirement: AdsPower 新浏览器代际 SHALL 使用 profile 单一代理权威

当目标环境已配置代理时，`adspower` provider SHALL 在每次新浏览器代际调用 `browser-profile/start` 前，把 AdsPower profile 代理同步为该代际目标：系统前置模式写受管 loopback，直接模式写 AIDCP 加密保存的原环境代理。provider SHALL 读回并验证完整路由与认证字段一致后才启动，MUST NOT 同时注入 `--proxy-server` 或保留第二套浏览器代理权威。

原环境代理和本代际目标代理 SHALL 经主进程私有 pipe 交付，不得进入 argv、环境变量、renderer 或日志。AdsPower 已报告 profile active 时，provider 无法证明该浏览器代际应用了当前配置，因而只要环境存在代理权威就 MUST 拒绝接管并要求关闭重启。明确未配置代理的环境 SHALL 跳过 profile 更新、读回和此限制，保持既有启动/接管行为。

#### Scenario: 双跳新浏览器先同步 loopback
- **WHEN** AdsPower profile 为 inactive、环境已配置代理且本代际使用系统前置模式
- **THEN** provider 先把 profile 更新为合法受管 loopback 并读回一致，再调用 `browser-profile/start`，启动参数中不含 `--proxy-server`

#### Scenario: 直接模式每次启动恢复原代理
- **WHEN** AdsPower profile 为 inactive、环境已配置代理且本代际使用直接模式
- **THEN** provider 在启动前把 profile 更新为 AIDCP 权威中的原环境代理并读回一致，即使上次异常退出留下 loopback 也能纠正

#### Scenario: 冷待机唤醒再次同步
- **WHEN** 同一 Edge 子进程在浏览器关闭后从冷待机唤醒并再次调用 provider launch
- **THEN** provider 按该代际冻结模式再次完成 profile 更新和读回，不复用上一次启动的配置证明

#### Scenario: 明确无代理时零更新
- **WHEN** 环境明确未配置代理
- **THEN** provider 不调用 profile update/readback、不增加 `--proxy-server`，并保持既有 inactive 启动和 active 接管行为

#### Scenario: active 浏览器不能证明本代际配置
- **WHEN** AdsPower 报告已配置代理的目标 profile 已 active
- **THEN** provider 拒绝接管并显示需要关闭后重启，MUST NOT 声称直接或双跳模式已生效

#### Scenario: 更新或读回不一致阻止启动
- **WHEN** profile 更新失败、精确读回失败或读回字段与目标代理不一致
- **THEN** provider 在调用 `browser-profile/start` 前诚实失败，且不回落旧 profile、命令行覆盖、self 或直连

### Requirement: AdsPower 浏览器关闭后 SHALL 尽力恢复原环境代理

对于已配置代理的受管环境，provider SHALL 仅在确认浏览器调试端点已关闭后，尽力把 profile 代理恢复为 AIDCP 加密权威中的原环境代理并读回验证。恢复失败 SHALL 可观察但 MUST NOT 推翻已经取得的浏览器关闭事实；下一次启动前同步仍是唯一必要的一致性闸门。

#### Scenario: 确认关闭后恢复
- **WHEN** provider 已连续确认目标浏览器调试端点关闭
- **THEN** provider 写回原环境代理并读回验证，不在浏览器仍可能运行时改写

#### Scenario: 恢复失败不伪造浏览器仍运行
- **WHEN** 浏览器已确认关闭但 profile 恢复失败
- **THEN** provider 返回浏览器已关闭，并记录不含凭据的恢复失败状态；下次启动前仍重新同步

#### Scenario: 无代理环境无需恢复
- **WHEN** 明确无代理环境的浏览器关闭
- **THEN** provider 不调用 profile 更新或读回
