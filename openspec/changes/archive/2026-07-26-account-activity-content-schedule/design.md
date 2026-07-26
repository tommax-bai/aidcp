## Context

当前全局三态周历由两个物理字段组成：浏览活跃掩码位于 `session_config_global.active_week_mask`，内容自动化掩码位于 `content_schedule_global.content_active_mask`。账号内容排期侧表 `account_content_schedule` 已有 nullable `content_active_mask`，Cloud 也按 `账号覆盖 ?? 全局` 解析，但管理后台没有编辑入口；账号活跃掩码则不存在，`RoleDispatcher` 和 `ContentScheduler` 仍直接读取全局值。

运行时以社媒账号 `accountId` 为浏览、风控、发布和互动调度单位，因此覆盖也以 `accountId` 为键。现有两种缺省极性必须保留：浏览活跃掩码缺失为全天开放（fail-open，零回归），内容掩码缺失为完全不自动（fail-closed）。

## Goals / Non-Goals

**Goals:**

- 让运营在排期页为任一真实账号添加、编辑或移除三态周历覆盖。
- 账号活跃与内容掩码分别支持覆盖；未覆盖的层独立继承全局。
- 让全部会话生命周期和内容调度消费同一账号生效活跃值，并保持热加载。
- 保持存量数据、自动化开关、风控、人审与手动触发行为不变。

**Non-Goals:**

- 不增加端用户 `client_user_id` 维度或客户端自助配置入口。
- 不把单场时长、互动预算、每日续场上限或旧单段日窗口改为账号级。
- 不改变 168 格、服务器本地时间、分钟错峰、内容生成或发布审批协议。
- 不构建 Edge 安装包，不部署 OL。

## Decisions

### 1. 复用账号内容排期侧表，新增 nullable 活跃列

在 `account_content_schedule` 增加 `active_week_mask TEXT NULL`，继续使用已有 `content_active_mask`。`NULL` 明确表示继承全局，不增加额外的 `inherit` 布尔字段，避免两份状态互相矛盾。账号保存沿用现有 UPSERT 单写与账号存在性校验；不做数据回填，存量行自然继承全局。

替代方案是新建账号活跃表，但同一三态编辑会跨两张账号表写入，增加部分成功与审计漂移；本次选择同一侧表原子保存两个账号掩码。

### 2. 两层独立继承，自动化以生效掩码交集判定

解析规则为：

```text
effectiveActive = valid(account.activeWeekMask) ? account.activeWeekMask : global.activeWeekMask
effectiveContent = account.contentActiveMask ?? global.contentActiveMask
canAutomate(now) = active(effectiveActive, now) && valid/content-active(effectiveContent, now)
```

活跃最终缺失或非法继续按既有语义视为全天开放；内容最终缺失或非法继续不自动。账号总开关、动作模式和日上限另行判定，保存掩码绝不隐式开启动作。

`ContentScheduleStore` 接受一个只读的全局活跃掩码提供者，只组合内存镜像，不直接读写 `session_config_global`。它公开账号生效活跃解析口，并在 catalog 中同时返回原始覆盖、来源和生效值，确保 Console 与运行时不各自实现继承规则。

### 3. RoleDispatcher 通过独立账号活跃提供者取值

`SessionLimitProvider` 的时长、预算和比率仍是全局语义，不把整个接口改为账号级。`RoleDispatcherOptions` 新增可选账号活跃掩码提供者；内部用一个 helper 统一解析当前/指定账号，启动、续场裁决、窗口唤醒、运行中监测和冷待机快照全部只调用该 helper。缺少新提供者时回落原全局 provider，保持测试与旧装配兼容。

### 4. ContentScheduler 的浏览活跃闸显式接收 accountId

把 `browseActiveAt(now)` 改为 `browseActiveAt(accountId, now)`，生产装配从账号生效排期解析口判断。保留该独立闸而不依赖 Console 裁剪，从而即使数据库由外部写出“内容开、活跃关”的组合，Cloud 仍强制不触发。

### 5. Console 在同一排期页提供账号三态编辑器

顶部全局周历保持不变。账号表新增“排期”列：未覆盖显示“跟随全局”与“添加排期”，存在任一覆盖显示“账号自定义”与“编辑”。账号弹窗复用 `WeekActiveGrid`：

- 新增时以当前全局生效两层为初始值；
- 保存自定义时一次 PUT 两个合法、已裁剪的 168 位掩码；
- “恢复全局”一次 PUT 将两个字段置 `null`；
- 成功后以服务端 catalog 回读真态，失败恢复/刷新，不显示假成功。

### 6. 全局双端点保持现状

全局活跃与内容掩码仍由各自 store/端点拥有，现有全局编辑的串行双写与 Cloud 交集闸保持不变。本次不为全局配置引入跨 store 事务，以控制范围；账号两个掩码则因同表而一次原子写入。

## Risks / Trade-offs

- [运行时某处漏用账号解析口] → 用账号 A 休眠、账号 B 活跃的对照测试覆盖启动、续场、唤醒、运行中结束和内容调度；生产装配只注入同一个 store 解析口。
- [全局变更使继承层与账号另一自定义层不再呈子集] → Console 预览取交集，Cloud 每次触发再强制 `active && content`；不静默改写用户保存的另一层。
- [外部脏账号活跃掩码绕过全局限制] → 账号活跃覆盖只有合法 168 位时才优先，否则回落全局；写入仍整块校验。
- [大账号表返回两个 168 位字段增加响应] → 排期 catalog 是低频内部管理接口，增量有界；无需给高频自动化通道下发。
- [多个账号仍可能配置同一小时形态] → 现有按账号/日期/动作分钟错峰继续生效；本能力提供差异化手段但不强制随机改写运营配置。

## Migration Plan

1. Cloud 自愈 schema 与人审 migration 增加 nullable `active_week_mask`，先部署 Cloud；旧 Console 不发送新字段，行为不变。
2. Cloud 验证账号覆盖/继承、会话闸与内容调度后，再发布 Console 静态资源开放入口。
3. 存量行不回填；部署后所有账号仍继承全局，只有运营显式添加的账号产生覆盖。
4. 回滚 Console 只会隐藏入口；Cloud 新列与读兼容可保留。若回滚 Cloud，新增 nullable 列不会影响旧 SQL，账号内容覆盖仍按旧行为工作。

## Open Questions

无。用户已确认配置维度为社媒账号 `accountId`，入口位于管理后台排期页。
