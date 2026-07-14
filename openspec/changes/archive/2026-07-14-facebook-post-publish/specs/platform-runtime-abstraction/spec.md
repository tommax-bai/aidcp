## ADDED Requirements

### Requirement: Facebook publish 能力必须与云端 profile 和边缘执行器同落

Facebook 平台 SHALL 仅在云端平台 registry 具备 Facebook publish profile、edge Facebook driver 具备实际发帖执行器、并且 no-submit 探针通过后，才声明 `publish` 能力。任一侧缺失时，系统 MUST 对 Facebook 发布请求返回不支持或门禁未通过的诚实失败，MUST NOT 静默回落到 Xiaohongshu 发布路径，也 MUST NOT 仅在 registry 裸声明能力而没有边缘执行器。

#### Scenario: 未声明 publish 时诚实失败
- **WHEN** Facebook 账号收到发布动作，但 Facebook driver 或 cloud registry 尚未声明 `publish`
- **THEN** 系统 SHALL 返回 unsupported capability，MUST NOT 调用 XHS 发布器、MUST NOT 伪造成功

#### Scenario: 能力声明与执行器同落
- **WHEN** change 启用 Facebook `publish` 能力
- **THEN** cloud registry、platform publish profile、edge driver capabilities、Facebook 发帖执行器和对应测试 SHALL 同时存在并一致

#### Scenario: registry 裸声明被拒绝
- **WHEN** 有实现只在 cloud registry 加入 `publish`，但 edge Facebook driver 没有发帖执行器
- **THEN** MUST 视为违规；Facebook publish 能力必须云端路由、边缘执行器和探针门禁同落
