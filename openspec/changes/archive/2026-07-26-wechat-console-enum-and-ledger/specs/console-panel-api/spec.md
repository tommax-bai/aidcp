## ADDED Requirements

### Requirement: Console 客户环境平台候选必须包含视频号并容忍未来值

Console 的客户环境注册与归属界面 SHALL 把 `wechat_channels` 作为受支持平台候选并显示中文“视频号”，同时继续支持 `xiaohongshu` 与 `facebook`。环境 registry DTO MUST 保持可接收未知字符串；未知未来平台值 MUST 显示原始值并保持可读取，MUST NOT 使页面白屏、擅自回落成其他平台或阻止既有归属加载。

#### Scenario: 管理员手动登记视频号环境
- **WHEN** 管理员在客户环境归属页手动登记环境并选择“视频号”
- **THEN** Console 提交稳定 wire 值 `wechat_channels`，保存回读后仍显示“视频号”

#### Scenario: Cloud 返回未来平台值
- **WHEN** 环境注册表返回当前 Console 尚未认识的平台字符串
- **THEN** Console 以中性样式显示原始值并保持页面可用，MUST NOT 把它标成视频号、小红书或 Facebook

### Requirement: Console 回复配置审计必须消费完整分页台账

Console SHALL 消费既有 `GET /api/accounts/:accountId/reply-config/audit` 的 opaque `nextCursor`，允许运营按需追加后续页，并明确显示加载中、可继续、已到底、权限拒绝和后续页失败状态。cursor MUST 只作为 opaque 字符串 URL 编码后回传，MUST NOT 由 Console 解析、改写或伪造；后续页失败 MUST 保留已经成功加载的记录并提供重试。

#### Scenario: 审计首屏还有后续页
- **WHEN** 首屏返回非空 `nextCursor` 且运营点击加载更多
- **THEN** Console 携该 cursor 请求同一账号的下一页，按服务端顺序追加事件，并以稳定 eventId 去重

#### Scenario: 审计已经加载到底
- **WHEN** 最近一次成功回包返回 `nextCursor=null`
- **THEN** Console 显示台账已全部加载且不再提供继续请求入口，MUST NOT 把首屏条数冒充总量统计

#### Scenario: 后续页加载失败
- **WHEN** 已展示首屏后追加请求返回错误
- **THEN** Console 保留已展示事件，明确提示后续审计加载失败并允许重试，MUST NOT 清空台账或显示已到底

### Requirement: Console 审计分页必须保持账号隔离和开放枚举回落

Console SHALL 将每次审计首屏与追加请求绑定当前 `accountId`。切换账号、关闭抽屉、重新加载或写后刷新时 MUST 中止旧的追加请求；旧账号或已中止回包 MUST NOT 追加到当前台账。Audit action/entity wire 值 MUST 按开放字符串处理：已知值可显示中文，未知值 MUST 显示原值，MUST NOT 空白、猜测含义或使页面崩溃。

#### Scenario: 加载更多期间切换账号
- **WHEN** 账号 A 的审计追加请求尚未完成时运营切换到账号 B
- **THEN** A 请求被中止或其回包被丢弃，B 的台账只包含 B 的事件与 cursor

#### Scenario: Cloud 先增加审计动作枚举
- **WHEN** Cloud 返回当前 Console 未认识的 audit action 或 entity type
- **THEN** Console 显示该原始 wire 值与事件其他事实，页面和后续分页保持可用
