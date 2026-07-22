## Why

账号目前没有统一的评论站立授权：排期与人设规则可局部免审，但普通浏览评论和飞书 `/comment` 仍重复发审批卡；与此同时，客户端已能独立读取和审批待审稿，仍强制给每个分组发送飞书稿件审批卡会给只运营少量账号的客户造成重复入口与消息噪音。

## What Changes

- 新增账号级评论审批覆盖策略：默认 `source_rules` 保持各来源既有规则；显式选择 `auto_approve_all` 后，普通浏览、排期、联系评论、强制互动、飞书 `/comment` 与结构化委托评论全部跳过按钮审批，先发送可审计的免审通知，再进入既有提交链。
- 账号级全局免审只改变授权等待，不绕过风险、配额、去重、目标复核、平台确认或终态回执；策略缺失、非法或读取失败一律回落 `source_rules`。
- 新增分组级稿件审批投递策略：默认 `client_and_feishu`；显式选择 `client_only` 后，无飞书来源会话的 `review` 待审稿只进入客户端稿件队列，不发送飞书按钮审批卡。
- 飞书命令直接触发的 `/publish` 继续把审批卡发回来源会话；免审通知、发布结果、失败和运维告警不受“仅客户端审核”影响。
- `client_only` 仅在账号仍有客户环境归属、可经 customer-auth HTTP 读取和审批稿件时生效；不满足或策略读取失败时回退发送飞书审批卡并输出可观测原因，绝不产生无人可见的待审稿。
- 后台新增账号与分组策略配置及生效态展示，并修正通知路由页仍声称“审批卡固定走默认管理群”的过期文案。
- 客户端审批、飞书审批继续共享 Cloud 的 first-writer-wins 授权信号；本变更不新增 Edge 协议或本地业务数据写路径。

## Capabilities

### New Capabilities

- `scoped-approval-policy`: 账号级全局评论免审与分组级稿件审批投递策略的持久化、解析优先级、默认/失败回退、审计和后台配置合同。

### Modified Capabilities

- `comment-interaction`: 普通浏览评论在账号全局免审时跳过按钮人审并走通知后授权。
- `content-schedule`: 排期评论与联系评论接受账号全局免审覆盖，同时保留未开启覆盖时的来源模式。
- `account-persona-config`: 账号全局免审覆盖强制互动规则内的评论审批模式。
- `user-delegated-tasks`: 飞书 `/comment` 与结构化委托评论在账号全局免审时不再强制二次人审。
- `feishu-notification-routing`: 分组策略可抑制无来源会话的稿件按钮审批卡，同时保留来源会话、回退和其它消息类型的统一路由。
- `edge-companion-ui`: 客户端稿件审核在分组仅客户端模式下成为唯一主动审批入口，但仍复用同一 Cloud first-writer-wins 决策与 HTTP 真态。

## Impact

- `aidcp-cloud`：新增账号/分组审批策略存储与面板 API；评论授权模式统一解析；发布审批卡发送前增加分组投递决策与客户端可达性回退。
- `aidcp-console`：账号页新增全局评论免审配置；通知路由页新增分组稿件审核入口配置、客户端覆盖提示并修正文案。
- `aidcp-edge`：无代码改动；复用现有 `publishDraftList` / `publishDraftGet` / `publish.approval_action` customer-auth HTTP 链。
- PostgreSQL：新增自愈式、带审计字段的窄策略表；存量数据默认保持既有行为。
- OpenSpec：新增 `scoped-approval-policy`，并修改六项现有行为合同。
- 部署：Cloud 与 Console 需部署 dev；不构建 Edge 安装包，不触及 OL。
