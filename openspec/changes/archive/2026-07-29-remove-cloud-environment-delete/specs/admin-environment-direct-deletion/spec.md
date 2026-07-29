## REMOVED Requirements

### Requirement: 管理后台环境删除由 Cloud 直接调用 AdsPower

**Reason**: 产品取消管理后台云端删除，Cloud 不再托管可达的 AdsPower Local API runtime。

**Migration**: 移除管理后台删除入口和 Panel 写路由；需要删除时只能在桌面客户端本地逐环境二次确认执行。

### Requirement: AdsPower 成功先于 AIDCP 环境删除终态

**Reason**: Cloud 不再发起 AdsPower 删除，也不再从管理后台推进 AIDCP 删除终态。

**Migration**: 既有终态和审计只读保留，不创建新的云端删除记录。

### Requirement: 直接删除在跨系统非原子窗口中幂等且诚实

**Reason**: Cloud 与 AdsPower 之间不再存在直接删除调用和跨系统收口窗口。

**Migration**: 删除相关幂等与串行化代码随写路由移除；历史 requestId/idempotencyKey 数据保留。

### Requirement: 删除环境保留账号域真态和最小审计

**Reason**: 管理后台不再产生新的环境删除；历史删除仍由既有审计数据表达。

**Migration**: 账号和环境只读投影继续保留，已有 deleted 行不复活、不硬删除。

### Requirement: Cloud AdsPower 出口是服务端受限接口

**Reason**: Cloud AdsPower 删除/查询出口整体移除，服务端不再持有该能力。

**Migration**: 删除 Cloud AdsPower 客户端和运行时凭据读取；不提供替代公网代理。
