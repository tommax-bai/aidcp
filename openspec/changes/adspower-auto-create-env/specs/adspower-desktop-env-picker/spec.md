## REMOVED Requirements

### Requirement: 桌面外壳提供「打开 AdsPower 新建环境」引导入口

**Reason**: 反转已归档决策 D4「面板不做 `user/create`、创建交给 AdsPower」。实践暴露「运营手工在 AdsPower UI 逐字段配指纹易错且错在暗处」是核心风险，故收回创建、由程序按验证过的规则守住正确性。原「best-effort 拉起 AdsPower 让人手动建号、MUST NOT 经本地 API 代建」的引导入口不再是主路径。

**Migration**: 建号改为程序化——见新增能力 `adspower-environment-provisioning`（委托生成 + 薄护栏 + OS 四者一致断言 + 写客户端 allowlist + write-ahead 台账）与 `environment-readiness-verification`（创建后自检置 `verifyState`），及本 spec 新增的「桌面外壳「创建环境」程序化建号入口与就绪态呈现」需求。「打开 AdsPower 手动新建」可作诚实降级保留（本地 API 不可达 / 写失败时），但不再是承诺路径。

## ADDED Requirements

### Requirement: 桌面外壳「创建环境」程序化建号入口 + 是否配代理提示

`adspower` 模式下，桌面外壳的「创建环境」入口 SHALL 触发 `adspower-environment-provisioning` 的程序化建号流程（而非仅拉起 AdsPower 客户端），运维 SHALL 只需挑一个「整机模板」，MUST NOT 被要求在面板内逐字段手配指纹。触发控件 SHALL 在创建在途时禁用（配合主进程单飞互斥）。**唯一的运营提示 = 「是否配置了代理」**：环境列表 SHALL 对每个环境如实呈现其代理配置状态，无代理（`user_proxy_config.proxy_soft` 为 `no_proxy` / 空）SHALL 给出「未配置代理」提示；该提示为纯提醒、MUST NOT 阻止任何操作（代理由运维手动在 AdsPower 侧配）。桌面外壳 MUST NOT 自动做运行时自检 / 投产硬闸 / 就绪判定——创建成功即如实呈现「已创建」，是否可用由运维登录时自行确认。本地 API 不可达或程序化创建失败时 SHALL 诚实降级（如实说明原因），MUST NOT 谎报已创建（不再提供「打开 AdsPower 手动新建」外链）。环境列表每行 SHALL 提供**删除入口**，其行为按 `adspower-environment-provisioning` 的「删除环境仅经界面逐个二次确认」需求（点两次确认、警示不可恢复）。

#### Scenario: 挑模板一键程序化创建，不必手配指纹
- **WHEN** 运维在「创建环境」入口选定一个整机模板并确认
- **THEN** 桌面外壳触发程序化建号流程，运维无需在面板内逐字段配指纹；创建在途时该控件禁用；成功后如实呈现「已创建」

#### Scenario: 无代理给提示但不拦
- **WHEN** 环境列表刷新，其中某环境未配置代理（`no_proxy` / 空）
- **THEN** 该环境如实标「未配置代理」提示，运维仍可对其做任何操作，MUST NOT 因无代理而拦截

#### Scenario: 创建失败诚实降级
- **WHEN** 本地 API 不可达或 `user/create` 返回错误
- **THEN** 桌面外壳如实说明失败原因，MUST NOT 谎报已创建

#### Scenario: 每行删除入口二次确认
- **WHEN** 运维点击某环境行的删除按钮
- **THEN** 第一次仅进入「确认删除?」待确认态、第二次才真删；删除后刷新列表
