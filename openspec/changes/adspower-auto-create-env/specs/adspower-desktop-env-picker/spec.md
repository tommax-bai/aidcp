## REMOVED Requirements

### Requirement: 桌面外壳提供「打开 AdsPower 新建环境」引导入口

**Reason**: 反转已归档决策 D4「面板不做 `user/create`、创建交给 AdsPower」。实践暴露「运营手工在 AdsPower UI 逐字段配指纹易错且错在暗处」是核心风险，故收回创建、由程序按验证过的规则守住正确性。原「best-effort 拉起 AdsPower 让人手动建号、MUST NOT 经本地 API 代建」的引导入口不再是主路径。

**Migration**: 建号改为程序化——见新增能力 `adspower-environment-provisioning`（委托生成 + 薄护栏 + OS 四者一致断言 + 写客户端 allowlist + write-ahead 台账）与 `environment-readiness-verification`（创建后自检置 `verifyState`），及本 spec 新增的「桌面外壳「创建环境」程序化建号入口与就绪态呈现」需求。「打开 AdsPower 手动新建」可作诚实降级保留（本地 API 不可达 / 写失败时），但不再是承诺路径。

## ADDED Requirements

### Requirement: 桌面外壳「创建环境」程序化建号入口与就绪态呈现

`adspower` 模式下，桌面外壳的「创建环境」入口 SHALL 触发 `adspower-environment-provisioning` 的程序化建号流程（而非仅拉起 AdsPower 客户端），运维 SHALL 只需挑一个「整机模板」并（可选）预填 `intendedAccountLabel`，MUST NOT 被要求在面板内逐字段手配指纹。触发控件 SHALL 在创建在途时禁用（配合主进程单飞互斥）。环境列表 SHALL 如实呈现每个环境的**就绪态**——「仅配置层 / 未验证」「已验证 / 可投产」「验证失败（含失败项）」——以及「无代理」标注，MUST NOT 把仅创建成功的环境呈现为「已就绪」。本地 API 不可达或程序化创建失败时 SHALL 诚实降级（如实说明原因，并保留「打开 AdsPower 手动新建」兜底），MUST NOT 谎报已创建。

#### Scenario: 挑模板一键程序化创建，不必手配指纹
- **WHEN** 运维在「创建环境」入口选定一个整机模板（可选预填意图账号）并确认
- **THEN** 桌面外壳触发程序化建号流程，运维无需在面板内逐字段配指纹；创建在途时该控件禁用

#### Scenario: 环境列表如实呈现就绪态与无代理
- **WHEN** 环境列表刷新，其中含仅创建未验证的、已验证的、验证失败的、无代理的环境
- **THEN** 各环境如实标注其就绪态（仅配置层/未验证 / 已验证 / 验证失败）与「无代理」，MUST NOT 把未验证环境呈现为「已就绪」

#### Scenario: 创建失败诚实降级
- **WHEN** 本地 API 不可达或 `user/create` 返回错误
- **THEN** 桌面外壳如实说明失败原因并保留「打开 AdsPower 手动新建」兜底，MUST NOT 谎报已创建
