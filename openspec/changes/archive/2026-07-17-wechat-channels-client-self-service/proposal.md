## Why

视频号互动工作区已经能读取和处理入站评论/私信，但客户无法在客户端开启收取、看不见读取门禁的真实状态，并会在默认关闭的发送能力下遇到队列动作静默失效。回复配置首次初始化、配置就绪引导和新互动提醒也缺少可达页面，导致一个安全上 fail-closed 的系统在产品上表现成“没有消息”或“按钮没反应”。

## What Changes

- 在 customer-auth 增加仅允许当前客户修改评论/私信读取开关的 env-scoped CAS API；发送 capability、账号写总闸、自动发送与风险配额继续只允许 internal 管理域修改。
- 在 interaction list/detail 投影中增加回复配置就绪状态，并继续返回运行开关的 stored/applied/effective 三层真态。
- 在 Electron 视频号工作区增加“互动设置/运行状态”卡：总收取、评论收取、私信收取、配置应用状态、平台读取能力和回复配置状态均可见且可解释。
- 把保存、重新生成、忽略、转人工、批准与平台发送 capability 解耦；只有真正的发送动作要求对应发送 capability，所有动作仍受登录、scope、CAS 和 Cloud 权威校验。
- 使用既有 `unread` 投影增加列表未读标记、当前环境角标和一次性系统通知；切换环境时不得串号或重复通知。
- 在回复配置管理页增加新账号的显式安全初始化动作，并提供无已发布配置时的可达引导；初始化只创建默认关闭发送/自动化的 draft，不冒充已发布。
- 保留完整内部回复配置工作区；客户端只提供配置就绪状态与进入管理页/联系管理员的引导，不向 customer-auth 暴露写总闸、发送 capability、自动发送、完整私信审计或硬风控配置。

## Capabilities

### New Capabilities

<!-- No new standalone capability; this change extends existing customer API, desktop UI and panel configuration capabilities. -->

### Modified Capabilities

- `client-customer-auth`: 增加当前客户环境范围内的读取开关 CAS 修改和回复配置就绪投影，保持发送与内部配置权限隔离。
- `edge-companion-ui`: 增加视频号互动设置真态、读取自助开关、正确动作门禁、未读角标/通知和配置阻断引导。
- `console-panel-api`: 增加缺少配置头时的显式安全初始化语义，并保证初始化与发布状态诚实分离。

## Impact

- Control: OpenSpec delta、customer-auth JSON schema 与合成 fixtures。
- Cloud: `interaction-customer-api`、运行开关 CAS、回复配置就绪投影、首次配置初始化 internal API 与测试。
- Edge: named IPC、InteractionWorkspace、环境角标/系统通知与 Electron 测试。
- Console: 回复设置抽屉的初始化状态、动作和测试。
- Runtime: Cloud 与 Console 需部署到 `dev`；Edge 代码提交推送但不默认构建安装包。
