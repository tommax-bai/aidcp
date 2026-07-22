## Why

后台已经提供账号、渠道、排期与审批配置，但 Cloud 和 Edge 仍保留多层不可见环境变量，可在界面显示“已开启”时静默把真实动作降级或关闭。V11 视频号安装包因此可能在全部可见配置正确时仍永远不上报写能力；同一类重复门禁也存在于私信 AI、内容排期、Facebook 浏览/评论/加群和评论点赞路径。

## What Changes

- **BREAKING**：删除视频号自动发送账号白名单；自动发送只由已发布回复策略、渠道配置、可见运行控制、身份/能力、风控、限速和幂等门禁决定。
- **BREAKING**：删除视频号 Edge 的本地账号/渠道/写入环境变量授权层和“人工写探针已验证”环境变量；Cloud 的作用域化运行控制成为产品开关事实源，只读探针、身份校验、端点熔断和发送后核验继续 fail-closed。
- 删除私信 AI 的额外全局环境门禁；是否润色/自动发送由已发布渠道策略决定。
- 让内容排期调度器在合法 `dev|ol` 执行目标上常驻；账号周历、动作开关、审批模式、日上限和风控决定是否触发，删除旧自动发布扳机。
- 删除 Facebook 自动评论、加群和全量审批的全局 `AUTO/SHADOW/REVIEW_ALL` 环境门禁；使用账号排期、账号加群配置和结构化审批策略。
- 删除 Facebook 仅 dev 自动浏览策略和 Edge 环境注入；平台能力、账号活跃排期、生命周期和风险控制决定是否浏览。
- 删除评论点赞的全局灰度开关；现有配额、概率、候选、风险和确认成功门禁继续生效。
- 保留并明确：可投影的全局互动紧急停写、部署目标隔离、身份/能力校验、风险状态、限速、熔断、不可逆写前校验、诊断/测试专用开关和未形成产品承诺的能力实验开关。

## Capabilities

### New Capabilities

- `product-control-authority`: 定义产品可见配置对常规业务动作的唯一授权关系，以及允许保留的基础设施/安全门禁边界。

### Modified Capabilities

- `wechat-channels-interaction`: 视频号写能力不再依赖本机环境授权或人工写探针批准，仍由 Cloud 控制、只读证据、身份、熔断和发送核验约束。
- `comment-interaction`: Facebook 审批选择由结构化账号/来源策略决定，不再由全局环境变量覆盖。
- `facebook-scheduled-comment`: Facebook 评论不再依赖全局自动/影子环境变量，账号排期与人工命令各自按显式授权运行。
- `facebook-group-membership`: Facebook 自动加群不再依赖全局自动/影子环境变量，账号级自动加群配置成为产品授权。
- `facebook-dev-autobrowse-policy`: 删除仅 dev 才允许 Facebook 自动浏览的环境注入策略，改为跨环境一致服从产品配置和运行安全门禁。

## Impact

- Control：新增 OpenSpec 契约，更新部署/验收文档中已经失效的开关说明。
- Cloud：`InteractionSendOrchestrator`、`ReplyWorkflow`、`ContentScheduler` 装配、Facebook 评论/加群调度器、角色注册和平台能力声明。
- Edge：视频号 capability/probe 状态、Electron 启动环境、Facebook session 装配和两份平台 registry 镜像。
- Console：删除提示用户还需运维开启隐藏环境变量的文案。
- 部署：Cloud 与 Console 可部署 dev；Edge 源码修复需要后续桌面客户端发布后才进入已安装客户端，本 change 不自行构建安装包。
