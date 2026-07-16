## Why

aidcp 目前没有视频号平台、入站评论/私信收件箱或可恢复的回复工作流；现有 `interaction_feed` 与 `comment-interaction` 只描述 aidcp 主动发起的互动，无法承载外部消息、审批、发送歧义和客户数据隔离。必须先冻结跨 Edge、Cloud、Console 与 Electron 客户端的单一契约，后续实现 Session 才能并行而不自行发明字段或把私有接口能力误写成稳定官方 API。

## What Changes

- 新增精确平台 ID `wechat_channels`，继续沿用“一账号一环境”，并把浏览器限定为登录/挑战处理 sidecar；正常同步和回复由 Edge 本地会话驱动的接口 connector 完成。
- 新建与 outbound `interaction_feed`、浏览闭环评论支线物理分离的入站互动域，冻结 thread、message、sync batch/cursor、reply job、send attempt、审计、唯一键和保留/清理不变量。
- 冻结模板 → 确定性渲染 → AI 受限润色 → 风险复核 → 人工/自动发送的状态机、CAS、幂等键、ambiguous send 回查和自动发送硬门禁。
- 在 WS v2 中新增平台无关的 `interaction.*` 消息，并补充显式 sync ack；通过 hello/welcome 可选能力协商保证新旧 Edge/Cloud 偏斜时不崩溃、不重试风暴、不误发。
- 冻结 customer-auth 与 internal API 的成功/错误 envelope、路径、分页游标、环境/账号归属、权限、版本冲突与 draft/published 配置语义。
- 冻结账号级 policy/template/rule/profile、模板变量白名单、AI role 输入/输出以及失败回退；图片私信发送保持未启用。
- 冻结 Electron 壳约束：左侧环境栏与全局标题栏不变，选择视频号环境时只替换右侧当前环境 workspace，且所有响应必须按 `envKey` 防串号。
- 视频号右侧 workspace 保留当前环境的显式生命周期入口，按真实状态显示启动、暂停或恢复；暂停态额外显示显式关闭入口，并且所有动作只操作当前 `envKey`。
- 设置中启用的“开发者详情”属于共享应用壳诊断面，切换到视频号 workspace 后继续展示当前环境原始日志，不被旧 workspace 的显隐状态吞掉。
- 提供版本化 JSON Schema、comment/dm fixtures、端到端走读与统一 handoff，作为 Session 01–04 的权威消费入口。
- 本 change 只冻结控制仓契约，不实现 Edge、Cloud、Console 业务代码，不部署，不调用真实视频号写接口。

## Capabilities

### New Capabilities

- `wechat-channels-interaction`: 视频号平台能力、浏览器鉴权 sidecar、本地凭证边界、Edge 同步/发送适配与私有接口诚实降级。
- `inbound-interaction-management`: 平台无关的入站 thread/message/cursor/reply-job/send-attempt 领域、状态机、幂等、API 投影和数据生命周期。
- `interaction-reply-configuration`: 账号级 policy/template/rule/profile、draft/published 版本、模板渲染、AI 润色/风险复核和无副作用预览。

### Modified Capabilities

- `platform-runtime-abstraction`: `PlatformId`、环境平台归属和能力装配扩展到 `wechat_channels`，且允许非浏览器常驻的 interaction connector。
- `interaction-risk-gating`: 评论回复复用 `comment` 风控动作，私信回复新增 fail-closed 的 `dm_reply` 动作；仅平台确认成功后记账，最终风险态仍只由 Cloud `RiskController` 单写。
- `client-customer-auth`: 增加当前客户环境范围内的互动列表、详情和人工动作 API，所有读写均回库复核 enabled user 与 env ownership。
- `console-panel-api`: 增加账号级回复配置、发布、预览与审计 API，区分查看/编辑/发布/私信原文权限并使用 CAS。
- `edge-companion-ui`: 新增视频号右侧互动 workspace 的进入条件、原子环境切换、状态诚实性和安全 IPC 边界。

## Impact

- 控制仓：`openspec/changes/wechat-channels-interaction-management/`、`docs/protocol.md`、`docs/contracts/wechat-channels-interaction/v1/`。
- 后续实现仓：`aidcp-edge` 的 platform/connector/WS 路由与 Electron workspace；`aidcp-cloud` 的 migrations、interaction domain、roles、WS/customer-auth/panel API；`aidcp-console` 的账号级配置 UI。
- 协议：WS v2 消息类型增加 7 个，`hello`/`welcome` 增加向后兼容的可选能力协商字段；两端 protocol 定义、Cloud mapping/handler、Edge active-command routing 必须同落。
- 安全：Cookie/session/二维码永不离开所属 Edge；私信正文按敏感客户数据处理；写能力、自动发送和图片发送默认关闭，只有显式配置与探针通过后逐级开启。
- 发布边界：本 Session 为 docs/spec-only，不触发 dev/ol 部署，也不构建 Edge 安装包。
