## ADDED Requirements

### Requirement: 左栏环境显示名优先真实登录昵称

多环境模式下，左栏环境行的**显示名**解析 SHALL 在已读到该环境真实登录昵称时**优先显示昵称**，AdsPower 环境名 / 设备模板名仅作未读到真实昵称时的回落。显示名解析优先级 SHALL 为：真实登录昵称（`account-identity-resolution` 定义的显示名，来源标记表明为平台真实昵称）→ 环境名（花名册名 / AdsPower `user/list` 名）→ 「环境 …末4位」兜底。

实时名回填（把花名册名同步为 AdsPower live 名）MUST NOT 反过来遮蔽已知真实昵称：一旦某环境的真实昵称已知，左栏 SHALL NOT 因花名册名被回填成 AdsPower 模板名 / 默认名而回退显示模板名。此显示优先级 SHALL 与「环境名跟随真实昵称」（见 `adspower-environment-provisioning`）互补——即使 AdsPower 侧改名尚未完成或改名写失败，左栏也 SHALL 已显示真实昵称。

#### Scenario: 已知昵称优先显示昵称
- **WHEN** 某环境已登录且其真实昵称已读到，同时花名册名被实时名回填成 AdsPower 模板名
- **THEN** 左栏该环境行显示真实昵称，而非模板名

#### Scenario: 未知昵称回落环境名
- **WHEN** 某环境尚未登录 / 真实昵称未知，但花名册有非空环境名
- **THEN** 左栏该行显示该环境名（AdsPower 名）

#### Scenario: 全无则末4位兜底
- **WHEN** 某环境既无已知真实昵称，也无非空环境名
- **THEN** 左栏该行显示「环境 …末4位」兜底

#### Scenario: 实时名回填不遮蔽已知昵称
- **WHEN** 实时名回填把某个真实昵称已知的环境的花名册名刷成 AdsPower 模板名 / 默认名
- **THEN** 左栏该行仍显示真实昵称、MUST NOT 回退显示模板名
