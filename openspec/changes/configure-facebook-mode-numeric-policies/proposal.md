## Why

Facebook 规则模式与慢启动目前把运行数字固化在 Cloud/Edge 代码中，运营只能开关模式；调整浏览阈值、入群节奏或七日额度必须发版，且客户端展示可能与 Cloud 真正执行的数字漂移。需要在不开放动作编排、Prompt 或安全闸的前提下，为这些数字建立可审计、可验证、可回滚到既有版本的管理后台配置能力。

## What Changes

- 新增全局 Facebook 模式数字策略管理：规则模式仅开放 `viewThreshold`、`joinEveryNRounds`；慢启动仅开放固定七日内受支持动作的 `dailyCap`。
- 策略采用严格类型、草稿校验、不可变发布版本和审计记录；不提供 DSL、动作列表、动作次数/顺序、Prompt、模板、七日时长、分钟/小时公式或风控闸门配置。
- 两类策略分别采用一个全局当前已发布版本；不新增客户级或环境级数字覆盖/版本选择。
- 已开始的规则收集周期与轮次按旧版本结算，并在所在 execution target 完整应用新 current 后从下一安全轮采用；已开启慢启动的环境固定使用启用时版本直至七日结束，新开启环境采用 API owner 当时的全局当前版本。
- Cloud API 写侧发布版本并同步到 automation 读镜像；运行时遇到缺失、未知、陈旧或不兼容版本时失败关闭，不从代码默认值静默代替。
- Console 新增数字策略管理、校验预览、发布、影响预览与审计界面；环境页和 Edge 只读展示 Cloud 返回的有效数字，现有模式写入仍只允许 `enabled`。
- 迁移时以当前实际运行数字创建初始不可变版本并保留既有 `slow_start_since`、规则进度与环境开关，避免上线即改变行为。
- DEV/OL 共用业务策略 current；非默认发布是同时影响两端的全局行为变更，不能作为 DEV-only 验收。兼容 Cloud runtime、受影响客户端能力与明确发布授权均满足前，OL API 的默认关闭服务端 publish gate 保持关闭，不能只靠 Console 隐藏按钮。

## Capabilities

### New Capabilities

- `facebook-mode-numeric-policy-management`: 定义受限数字字段、草稿/校验/发布/审计、全局当前版本、影响预览与迁移边界。

### Modified Capabilities

- `facebook-rule-mode`: 固定动作拓扑改为在安全边界消费全局当前的不可变数字策略版本，并明确在途轮次的版本切换语义。
- `interaction-risk-gating`: Facebook 七日慢启动额度改为消费环境启用时固定的已发布版本，同时保留既有派生公式与更严风控裁决。
- `platform-search-activity`: Facebook 慢启动 search 上限改为取已发布七日策略，不再由该能力写死一份曲线。
- `content-schedule`: 账号自动化投影改为展示权威策略版本、动态阈值和周期，不再描述固定 `5/2` 节奏。
- `console-panel-api`: 增加仅供内部 JWT 使用的策略草稿、校验、发布、影响预览和审计契约。
- `admin-console-navigation`: 增加可发现的“模式规则”管理入口。
- `admin-environment-lifecycle`: 环境页只读展示规则模式、慢启动的有效策略版本与权威回读，数字编辑仍集中在全局策略页。
- `client-customer-auth`: 客户端环境配置响应增加只读的有效策略摘要，写入范围仍仅为模式开关。
- `client-facebook-rule-mode-toggle`: 客户端不再内置固定节奏数字，改为诚实展示 Cloud 策略摘要且不得提交策略字段。
- `edge-companion-ui`: 慢启动七日额度与规则模式说明改为 Cloud 驱动，并对未知、陈旧或不兼容状态诚实呈现。
- `cloud-api-automation-sync-read-mirrors`: 全局数字策略定义与当前指针进入 API 到 automation 的版本化读镜像与陈旧失败关闭契约。

## Impact

- Control：新增 OpenSpec 契约并依赖 `environment-level-rule-mode-and-approval` 先完成环境级规则模式收口；实现前还须与正在修改同一热点的 `facebook-rule-mode-without-persona`、`split-cloud-automation-production-runtime`、`wechat-review-residuals` 串行集成并重核基线。
- Cloud：新增 API-owner 版本化策略存储/全局当前指针/慢启动 pin，automation-owner 规则快照与单向 writer rollout phase、Panel 管理 API、审计/影响预览、API→automation 镜像及 owner-specific 追加迁移；不新增跨库 trigger/read。
- Console：新增 `/mode-policies` 页面和 API/types/tests，并在环境页只读展示有效版本。
- Edge：扩展 customer-auth 只读投影并替换硬编码说明/七日表；Native 动作协议与动作执行器不变。
- 数据：追加迁移创建初始版本、全局当前指针和运行 pin/快照；不得改写既有迁移。
