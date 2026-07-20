## MODIFIED Requirements

### Requirement: 桌面外壳「创建环境」程序化建号入口 + 是否配代理提示

`adspower` 模式下，桌面外壳的「创建环境」入口 SHALL 触发 `adspower-environment-provisioning` 的程序化建号流程（而非仅拉起 AdsPower 客户端），运维 SHALL 只需挑一个「整机模板」，MUST NOT 被要求在面板内逐字段手配指纹。触发控件 SHALL 在创建在途时禁用（配合主进程单飞互斥）。创建与环境列表阶段的运营提示 SHALL 只陈述“是否配置了代理”：环境列表 SHALL 对每个环境如实呈现其代理配置状态，无代理（`user_proxy_config.proxy_soft` 为 `no_proxy` / 空）SHALL 给出“未配置代理”提示；该提示为纯提醒、MUST NOT 阻止任何操作（代理由运维手动在 AdsPower 侧配）。桌面外壳在创建阶段 MUST NOT 做运行时自检、投产硬闸或就绪判定——创建成功即如实呈现“已创建”；当 Facebook 环境真正启动后，系统 SHALL 可按 `proxy-runtime-observability` 对当前浏览器会话生成独立的出口证据和接收流量，MUST NOT 把创建成功或已保存代理配置当作运行时验证成功。本地 API 不可达或程序化创建失败时 SHALL 诚实降级（如实说明原因），MUST NOT 谎报已创建（不再提供“打开 AdsPower 手动新建”外链）。环境列表每行 SHALL 提供**删除入口**，其行为按 `adspower-environment-provisioning` 的“删除环境仅经界面逐个二次确认”需求（点两次确认、警示不可恢复）。

#### Scenario: 挑模板一键程序化创建，不必手配指纹
- **WHEN** 运维在“创建环境”入口选定一个整机模板并确认
- **THEN** 桌面外壳触发程序化建号流程，运维无需在面板内逐字段配指纹；创建在途时该控件禁用；成功后如实呈现“已创建”

#### Scenario: 无代理给提示但不拦
- **WHEN** 环境列表刷新，其中某环境未配置代理（`no_proxy` / 空）
- **THEN** 该环境如实标“未配置代理”提示，运维仍可对其做任何操作，MUST NOT 因无代理而拦截

#### Scenario: 创建态与运行时证据分离
- **WHEN** 一个 Facebook 环境已创建且保存了代理配置，但尚未启动或当前浏览器探测未形成完整证据
- **THEN** 环境列表只陈述配置态，运行页 MUST NOT 显示“已验证”；环境启动后由当前浏览器会话独立生成出口状态

#### Scenario: 创建失败诚实降级
- **WHEN** 本地 API 不可达或 `user/create` 返回错误
- **THEN** 桌面外壳如实说明失败原因，MUST NOT 谎报已创建

#### Scenario: 每行删除入口二次确认
- **WHEN** 运维点击某环境行的删除按钮
- **THEN** 第一次仅进入“确认删除?”待确认态、第二次才真删；删除后刷新列表
