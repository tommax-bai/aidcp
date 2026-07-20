## Context

当前存在三种被混称为“昵称”的数据：平台验证得到的 `accounts.nickname`、后台运营标签 `accounts.label`、以及 Electron 本机花名册里覆盖 `name` 的人工环境昵称。Console 自己按 `nickname → label → accountId` 解析；Cloud 飞书装配多处直接读 `getNickname()` 或由卡片回落 `accountId`；Electron 则按本地 `nameSource: manual` 解析。人工名没有 Cloud 真源，也没有稳定账号键，因此管理后台、飞书与客户端必然漂移。

客户端编辑入口以 AdsPower `profileId/envKey` 为键，后台、飞书、风控和任务则以 `accountId` 为键。Cloud 已持久化 `client_environments.env_key → account_id` 且客户鉴权端点能校验 `client_env_scope` 归属，可用这条既有可信映射把环境编辑安全地落到账号级别，无需增加 Edge↔Cloud WebSocket 协议消息。

## Goals / Non-Goals

**Goals:**

- Cloud 持久化独立账号级运营别名，并成为客户端、Console、飞书人类可见账号名的权威来源。
- 显示名优先级和来源判定只在 Cloud 的一个纯解析模块定义，存储缓存、Panel DTO 与飞书装配复用它。
- 客户端人工改名具备 pending、Cloud 确认和完整失败回滚；空内容表示清除人工别名并恢复系统昵称。
- 保持 `accountId` 作为路由/风控/任务/回调唯一机器身份，保持平台昵称自动刷新。

**Non-Goals:**

- 不修改平台账号昵称，不把运营别名写回 AdsPower 或社交平台。
- 不允许用显示名替代账号主键、放宽客户环境归属，或在重名时猜测账号。
- 不新增批量改名、历史版本或别名审计 UI；数据库只保留当前值。
- 不构建或发布桌面安装包，除非另行明确要求。

## Decisions

### 1. `accounts.operator_alias` 与平台昵称物理分列

新增 nullable `operator_alias TEXT`，trim 后空值写 `NULL`。统一解析器 `resolveAccountDisplayName(record)` 返回 `{ name, source }`，来源限定为 `operator_alias` / `platform_nickname` / `label` / `account_id`，优先级固定为运营别名 → 平台昵称 → 非空运营标签 →账号 ID。平台身份链只写 `nickname`，人工编辑只写 `operator_alias`，两者互不覆盖。

直接复用 `nickname` 虽然改动更小，但会被下一次已验证平台握手覆盖，还会改变飞书昵称选号和委托任务对“平台昵称”的既有语义，因此拒绝。

### 2. Cloud 账号显示名目录是唯一决策点

在 Cloud 建立进程内账号显示记录缓存，由 `PgAccountStore.init()` 预热 `operator_alias/nickname/label`，所有对应写接口成功后同步更新。缓存与 Panel 查询都调用同一个纯解析模块；前者服务飞书和运行时同步取名，后者生成 `PanelAccount.displayName/displayNameSource`。Console 只消费服务端字段，不再实现 `nickname → label → accountId` 优先级。

显示名目录同时提供所有可匹配名字（运营别名、平台昵称、非空运营标签），飞书昵称选号可接受旧平台昵称或新运营别名；命中多个账号时继续 fail closed。人类可见卡片若解析来源仅为 `account_id`，使用“未获取昵称”而不是泄露内部 ID；机器字段仍保留 `accountId`。

### 3. 通过客户鉴权的 env-scoped HTTP 窄接口写别名

增加 `PUT /environments/:envKey/operator-alias`，body 仅含 `alias: string | null`。服务端先用 token 确认客户，再在存储层确认该 `envKey` 当前归属该客户且存在无冲突的 `account_id` 绑定，最后调用账号存储写 `operator_alias`。返回账号级解析后的显示名与来源；未归属、未绑定、账号不存在和写库失败分别返回可判断的失败，不静默降级成本地成功。

相比修改 WebSocket hello 或新增协议消息，这条路径已有客户授权、天然以人工操作为边界，也不把显示字段混进核心身份握手。

### 4. Electron 交互提交是一笔本地+Cloud 一致操作

renderer 在第一次 `await` 前按环境标记 pending 并乐观展示。main 保存前快照本地花名册：非空值设置 `nameSource: manual`；空值删除人工来源并回落系统名。随后调用 Cloud 窄接口；本地或 Cloud 任一步失败，main 恢复提交前花名册并回写磁盘，renderer 恢复所有环境身份锚点并显示真实原因。Cloud 成功后返回的显示名/来源用于确认。

提交前先比较 trim 后输入与编辑前当前显示昵称；两者相同则直接关闭编辑器，保持原来源并且不进入 pending、不调用主进程或 Cloud。该判断必须早于乐观写入，避免双击误触把系统昵称升级成人工昵称。空内容仅在当前已是人工来源时继续执行清除语义。

本地继续保留人工名字以支持启动时立即渲染，并增加受限的系统名影子字段：第一次设置人工名时保留原系统环境名；人工期间 AdsPower 列表刷新只更新影子系统名、不覆盖人工名；清除时用已验证平台昵称或影子系统名回落，绝不把刚清除的旧人工文本当系统名。升级前已有人工名在客户会话恢复后做一次有界后台同步；迁移同步失败保留旧本地人工名并明确标记未同步，不伪造已全局生效。

### 5. 飞书统一取名但机器载荷不变

所有带账号的飞书审批卡、告警、指令回执、委托任务卡及评论/发布终态通知，在发送前用账号显示名目录补齐 `accountName`。卡片模板不自行实现昵称优先级；缺可读名显示“未获取昵称”。审批 callback、任务记录、风控记录、Chat 路由和日志继续携带稳定 `accountId/requestId`，显示名只作为展示快照。

## Risks / Trade-offs

- [环境已归属但尚未绑定账号] → Cloud 返回 `account_unbound`，交互编辑回滚并提示先启动环境完成身份识别，绝不猜账号。
- [本地成功后 Cloud 失败] → main 以保存前快照回写；若回滚写盘也失败，返回包含两段原因的部分失败并保留显式未同步状态。
- [同一账号对应多个环境且输入不同人工名] → 账号级最后一次成功写为真源，Cloud 回包覆盖本地确认；其它在线环境下次 fleet/cloud 刷新或启动同步收敛。重名只影响人类选择，机器归因不变。
- [旧 Cloud 不认识新端点] → 先部署 Cloud，再启用新 Edge；旧 Edge/Console 忽略 additive 字段，新 Edge 遇 404 必须回滚并提示版本不兼容。
- [缓存与数据库漂移] → 所有应用内写通过 AccountStore 更新缓存；Panel 独立读库仍调用同一纯解析器；进程重启从数据库重建缓存。
- [飞书历史任务保存旧名字] → 新卡片发送时优先实时目录；已持久化任务名仅作审计快照，不改历史机器归因。

## Migration Plan

1. Cloud 先部署 additive `operator_alias` 自愈列、统一解析器、客户写接口和向后兼容的 Panel 字段；验证旧 Edge/Console 正常。
2. 部署 Console，切到 `displayName/displayNameSource`，验证账号表及只带 `accountId` 的页面一致。
3. 合入 Edge 并重启开发客户端；现存 `nameSource: manual` 成员经客户会话有界同步，交互新改名走确认/回滚。
4. 在 dev 用一个已归属、已绑定测试环境验证设置、清除、未绑定拒绝、飞书卡片与管理后台一致；不使用生产账号做破坏性验证。
5. 回滚顺序为 Edge → Console → Cloud；数据库 additive 列保留无害，旧代码忽略。

## Open Questions

无。
