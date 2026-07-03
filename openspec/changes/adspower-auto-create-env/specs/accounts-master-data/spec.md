## ADDED Requirements

### Requirement: 握手载荷携带并持久化 ads_profile_id 与 machine_label，建立账号↔分身↔机器可审计对应

`accounts` 主表 SHALL 新增 `ads_profile_id`（可空，TEXT）列以记录账号当前所在的 AdsPower 分身 id，并 SHALL **激活既有 `machine_label` 死列的写入**（记录账号当前所在机器）。二者 SHALL 经加性自愈迁移引入（`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，与本表既有惯例一致），MUST NOT 另起绑定表、MUST NOT 破坏 `account_id` 主键或已按账号 keyed 的风控/发布/概念表。边缘握手载荷 SHALL 携带 `ads_profile_id` 与 `machine_label`，云端在握手自动登记/幂等 upsert 时 SHALL 一并落库这两字段；缺字段 SHALL 按 NULL 处理（向后兼容）。该对应 SHALL 使后台可按账号看到「它坐在哪个分身、哪台机器」，为跨机校验与逐账号可观测提供数据地基。落库 MUST NOT 覆盖运营已配置的其它账号字段（沿用既有幂等 upsert 不抹既有配置的语义）。

#### Scenario: 握手落库分身与机器绑定
- **WHEN** 边缘以携带 `ads_profile_id` 与 `machine_label` 的载荷握手上线一个账号
- **THEN** 云端幂等 upsert 把这两字段落进 `accounts` 主表，后台账号列表可见「该账号所在分身与机器」，且不覆盖运营已配置的其它字段

#### Scenario: 加性迁移向后兼容
- **WHEN** 对 `accounts` 表执行增 `ads_profile_id` 列 / 激活 `machine_label` 写入的自愈迁移，且旧边缘握手未带这两字段
- **THEN** 迁移为加性、经 `ADD COLUMN IF NOT EXISTS` 自建，缺字段按 NULL 落库，旧行为零破坏

### Requirement: 登录握手回写真实 accountId 并与环境的 intendedAccountLabel 比对

当一个由 `adspower-environment-provisioning` 创建、预填了 `intendedAccountLabel` 的环境在登录后握手上线时，边缘 SHALL 把从登录态读出的真实 accountId 与该环境台账的 `intendedAccountLabel` **比对**。一致 SHALL 正常登记；不一致 SHALL **诚实告警**（登进了不该由它承载的账号）并使该环境不进入投产路径，MUST NOT 静默把错配的绑定当作成立。此比对 SHALL 为「一 profile = 一账号」契约的强制点，MUST NOT 缺省跳过。

#### Scenario: 账号与意图一致正常登记
- **WHEN** 环境预填 `intendedAccountLabel=A`，登录后握手读出的真实 accountId 即 A
- **THEN** 正常登记，绑定成立

#### Scenario: 扫错账号诚实告警不投产
- **WHEN** 环境预填 `intendedAccountLabel=A`，但人手把账号 B 扫登进了该环境
- **THEN** 边缘比对发现不一致，诚实告警并使该环境不进入投产路径，MUST NOT 静默接受错配绑定
