# platform-runtime-abstraction Specification

## Purpose
TBD - created by archiving change platform-abstraction-layer. Update Purpose after archive.
## Requirements
### Requirement: 平台运行时抽象保持共享基座单一事实源

系统 SHALL 引入显式平台运行时抽象，将平台无关基座与贴页面的能力实现分离。CDP 接入、LocatingEngine 三道闸、humanize、anti-detection、browser-provider、protocol v2 语义、RiskController、command pacing、账号主表、事件总线基础设施 MUST 保持共享单一实现，MUST NOT 按平台复制。

#### Scenario: 新增平台不复制共享基座
- **WHEN** 新增一个平台实现目录（如 `src/fb/*`）
- **THEN** 该平台只实现页面特定 driver 能力，CDP/locating/humanize/anti-detection/browser-provider/risk/protocol 基座仍从共享模块调用

### Requirement: edge 经 PlatformDriver 装配平台能力

edge SHALL 定义 `PlatformDriver` 契约，至少包含 `platform`、`capabilities`、`readIdentity()`、`detectOverlay()`，并以可选能力域表达 `browse`、`comment`、`publish`、`interact`、`patrol`。启动时 SHALL 通过显式平台配置选择 driver；未配置时默认保持现有 xhs 行为。driver 缺少某能力域时，系统 MUST 诚实报告该平台不支持该能力，MUST NOT 静默回落到 xhs 页面逻辑。

#### Scenario: xhs 默认 driver 保持现有行为
- **WHEN** edge 未显式设置平台或设置为 `xiaohongshu`
- **THEN** edge 装配 xhs driver，浏览/评论/发布/互动/巡视行为与抽象前一致

#### Scenario: 未实现能力诚实失败
- **WHEN** 某平台 driver 未声明 `publish` 能力却收到发布动作
- **THEN** edge 返回不支持该能力的诚实失败，MUST NOT 调用 xhs 发布路径或伪造成功

### Requirement: 平台 profile registry 参数化云端编排文案与限制

cloud SHALL 提供按 `PlatformId` 索引的平台 profile registry，用于描述站点名、内容名词、指标名词、评论长度、排序/时间窗口、locale、能力声明和调度入口。平台化文案与限制 MUST 通过 profile 注入现有角色/任务调用，MUST NOT 在角色 prompt 或 scheduler 内硬编码小红书术语后再用平台分支修补。普通主页关注能力与页面内联关注能力 MUST 分开声明；用量指标 MAY 由多个真实执行能力联合决定，但 MUST NOT 为展示一个指标而开启没有执行器的编排路径。

#### Scenario: xhs profile 注入后 prompt 默认不变
- **WHEN** xhs 评论相关角色生成搜索词、挑选目标或撰写评论
- **THEN** 它们经 xhs profile 得到与抽象前等价的小红书术语、长度限制和指标口径

#### Scenario: Facebook Reel 关注不误开启主页关注
- **WHEN** Facebook 声明 Reels-only 关注执行能力但仍不支持作者主页访问与主页关注
- **THEN** Cloud 可为当前 Reel 下发受闸关注并向客户端投影 `follow` 用量
- **AND** FollowAgent 的普通主页关注路径仍保持关闭

### Requirement: 协议语义保持平台无关

平台抽象 SHALL 优先复用具有相同业务含义和页面副作用的平台无关命令。新增平台 MUST NOT 引入以平台名命名的协议消息类型来表达相同固定语义；当同一业务意图在不同平台需要不同可观察副作用时，系统 SHALL 定义不同的固定副作用命令并由 Cloud 平台策略显式选择，MUST NOT 让同一命令或可选 mode/direct 字段按平台改变导航行为。

新增真实通用语义时，系统 MAY 增加平台无关消息类型，但 MUST 同步 Cloud/Edge `protocol.ts`、Cloud command mapping、Edge active-command routing、`docs/protocol.md`、能力协商与协议验收。浏览 surface 与 open purpose、以及派生 `noteId` 与独立 `observation` 见证包 SHALL 继续作为既有消息上的平台无关 optional 字段承载。

#### Scenario: 相同副作用复用平台无关命令
- **WHEN** 多个平台都能以相同前置条件、页面副作用与结果合同执行一个动作
- **THEN** 它们复用同一个不含平台名的协议命令并由各平台 adapter 实现

#### Scenario: 不同副作用拆成不同命令
- **WHEN** 本人身份采集在 Facebook 必须留在当前页、在 Xiaohongshu 必须进入本人主页
- **THEN** Cloud 分别选择 `identity.read_current` 与 `identity.read_self_profile`
- **AND** MUST NOT 通过同一个 `profile.open` 的平台分支或 `direct` 字段表达差异

#### Scenario: 新真实语义跨协议同步
- **WHEN** 新增 `identity.read_current`、`identity.read_self_profile` 与 `identity.observed`
- **THEN** 两端协议枚举、命令映射、主动路由、协议文档、能力协商与验收测试同步更新

#### Scenario: surface 与 purpose 是平台无关字段扩展
- **WHEN** 为 `note.open` 增加 `surface`/`purpose`、为 `action.completed` 增加派生 `noteId`/`observation`
- **THEN** 这些字段的语义不以任何平台名命名、缺省时逐位等于既有行为

### Requirement: xhs 提取必须零行为回归

Change 0 SHALL 仅把现有 xhs 页面能力移入 driver 装配边界，不改变 xhs 的浏览、评论、人审、发布、通知巡视、定位、风控或节奏行为。归档前 MUST 通过 edge/cloud 相关 acceptance、full test 和 typecheck。

#### Scenario: xhs 回归门全绿才允许后续平台工作
- **WHEN** `platform-abstraction-layer` 实现完成
- **THEN** xhs acceptance、full test、typecheck 和 OpenSpec strict validation 全部通过，才能开始依赖该抽象实现 Facebook 能力

### Requirement: 存量未标注平台环境的只读兜底推断与显式改平台

（扩展活跃 change `edge-environment-platform-select` 的「未标注平台的历史环境 MUST 回落 xiaohongshu」行为：在回落之前插入只读信号推断，remark 语义与权威地位不变；本 change 归档 SHALL 排在其后。）

edge 桌面应用在读回环境列表时，对 remark 无平台标注的环境 SHALL 按只读信号做平台兜底推断，优先级固定为：remark `plat`（权威，永远最高）→ 分身 `domain_name` 命中平台域名（facebook.com/fb.com → facebook；xiaohongshu.com → xiaohongshu）→ `open_urls` 任一 URL 命中同规则 → 分组名/环境名关键词 → 回落 `xiaohongshu`。推断 SHALL 纯只读——MUST NOT 因推断结果程序化回写 remark（写面限定见 `adspower-environment-provisioning` 的 update 两键约束）；推断函数对缺失字段 SHALL 安全降级（缺 `domain_name`/`open_urls` 时跳过该级，不抛错）。列表 SHALL 同时输出平台来源（remark / 推断 / 回落），UI 对非 remark 来源 SHALL 可视化标注「平台未标注（推断）」，避免误推断被当成权威标注。桌面应用 SHALL 提供逐环境的**显式改平台入口**（加入面板环境行），人工选定的平台经既有 settings 环境通道持久化到本机并覆盖推断结果（remark 有标注时以 remark 为准，入口用于纠正无标注环境）。误推断的纠正路径 SHALL 始终可用，因为平台字段会以 `AIDCP_PLATFORM` 功能性注入核心、决定启动流程，不是纯展示。

#### Scenario: 手工建的 FB 环境被域名信号正确识别
- **WHEN** 一个运维手工在 AdsPower 建的环境（remark 无 `plat`）其 `domain_name` 为 `facebook.com`，客户端拉取环境列表
- **THEN** 该环境平台判定为 `facebook`、来源标注为推断，UI 按 Facebook 呈现且启动时注入 `AIDCP_PLATFORM=facebook`

#### Scenario: remark 标注永远压过其它信号
- **WHEN** 某环境 remark 标注 `plat=xiaohongshu`，但环境名含「fb」
- **THEN** 平台判定为 `xiaohongshu`（remark 权威），关键词信号不参与

#### Scenario: 全部信号缺失回落小红书
- **WHEN** 某环境 remark 无标注、`domain_name`/`open_urls` 缺失、名称无平台关键词
- **THEN** 平台回落 `xiaohongshu`，行为与本需求引入前逐位等价，UI 标注为未标注

#### Scenario: 人工纠正误推断
- **WHEN** 某小红书环境因名称含「fb」被误推断为 facebook，运维在加入面板对该环境显式改平台为小红书
- **THEN** 人工选择持久化到本机 settings 并覆盖推断，此后列表与启动注入均按小红书，MUST NOT 被下次推断悄悄改回

### Requirement: Facebook publish 能力必须与云端 profile 和边缘执行器同落

Facebook 平台 SHALL 仅在云端平台 registry 具备 Facebook publish profile、edge Facebook driver 具备实际发帖执行器、并且 no-submit 探针通过后，才声明 `publish` 能力。任一侧缺失时，系统 MUST 对 Facebook 发布请求返回不支持或门禁未通过的诚实失败，MUST NOT 静默回落到 Xiaohongshu 发布路径，也 MUST NOT 仅在 registry 裸声明能力而没有边缘执行器。

#### Scenario: 未声明 publish 时诚实失败
- **WHEN** Facebook 账号收到发布动作，但 Facebook driver 或 cloud registry 尚未声明 `publish`
- **THEN** 系统 SHALL 返回 unsupported capability，MUST NOT 调用 XHS 发布器、MUST NOT 伪造成功

#### Scenario: 能力声明与执行器同落
- **WHEN** change 启用 Facebook `publish` 能力
- **THEN** cloud registry、platform publish profile、edge driver capabilities、Facebook 发帖执行器和对应测试 SHALL 同时存在并一致

#### Scenario: registry 裸声明被拒绝
- **WHEN** 有实现只在 cloud registry 加入 `publish`，但 edge Facebook driver 没有发帖执行器
- **THEN** MUST 视为违规；Facebook publish 能力必须云端路由、边缘执行器和探针门禁同落

### Requirement: 边缘平台按 AdsPower 环境选择并在启动时注入核心

edge 桌面应用 SHALL 支持按 AdsPower 环境选择运行时平台（小红书 / Facebook），并在启动核心进程时把该平台注入为进程配置（`AIDCP_PLATFORM`），使核心据此选平台驱动、决定启动打开哪个平台首页与握手上报的平台。平台 MUST 与该环境持久绑定（写入 AdsPower 分身 remark、随环境列表读回），MUST NOT 依赖操作者每次手动设进程环境变量。未标注平台的历史环境 MUST 回落 `xiaohongshu`，保持零回归。

#### Scenario: 创建 Facebook 环境并从 Facebook 启动
- **WHEN** 操作者在创建环境时选择 Facebook 平台，随后选中该环境点启动
- **THEN** 桌面壳把 `AIDCP_PLATFORM=facebook` 注入核心，核心以 Facebook 平台驱动启动、打开 facebook 首页并在握手上报 `platform=facebook`

#### Scenario: 旧环境与默认零回归
- **WHEN** 一个在本能力之前创建、remark 无平台字段的环境被选中启动
- **THEN** 平台回落 `xiaohongshu`，注入 `AIDCP_PLATFORM=xiaohongshu`，与本能力上线前逐位等价（核心默认即 xhs 驱动）

#### Scenario: 平台驱动缺失时诚实失败
- **WHEN** 选择的平台在当前 edge 构建里没有对应驱动
- **THEN** 核心启动即诚实报错（如「platform=… has no edge driver in this build」），MUST NOT 静默回落其它平台或伪装启动成功

### Requirement: 平台注册表必须声明委托动作支持级别与限制

cloud 与 edge 平台注册表 SHALL 为 Phase 1 委托动作声明 `supported`、`beta` 或 `unsupported` 及非空限制原因。任务创建与每次执行前 MUST 以账号平台事实源查表；无声明、平台不一致或 runtime gate 不满足时 MUST fail-closed，MUST NOT 回落到小红书路径或其他平台目标。

#### Scenario: Facebook 受限动作在 UI 中可辨识
- **WHEN** 用户在 Facebook 环境打开委托入口
- **THEN** 普通发布和已配置范围评论显示 Beta/能力闸说明，今日灵感与任意 URL 评论显示不可用原因
- **AND** 客户端与 cloud 准入结论保持一致

#### Scenario: 未知平台不路由
- **WHEN** 任务绑定的平台值不在注册表或执行时账号平台已改变
- **THEN** 系统 deferred/failed 并记录平台事实不一致
- **AND** MUST NOT 尝试任何已知平台执行器

### Requirement: Video-channel environment scope precedes platform identity binding
The platform runtime abstraction SHALL allow a `wechat_channels` environment to connect with a stable logical account scope derived from its environment key before finder authorization. This exception SHALL NOT change XHS/Facebook identity resolution, and Cloud SHALL still validate `accounts.platform='wechat_channels'` before creating the interaction runtime.

#### Scenario: Multi-environment supervisor starts a new video-channel profile
- **WHEN** the supervisor removes inherited account overrides and starts a `wechat_channels` child with a valid environment/profile ID
- **THEN** the child derives a stable logical account scope from the environment ID, completes hello without a pre-known finder ID, and enters the local authorization state machine

#### Scenario: Platform metadata disagrees
- **WHEN** a video-channel Edge hello resolves to an existing account whose authoritative `accounts.platform` is not `wechat_channels`
- **THEN** Cloud rejects the handshake and MUST NOT issue controls, sync commands, or write commands

### Requirement: Video-channel identity changes do not mutate logical ownership
The platform runtime abstraction SHALL represent the public finder identity as an environment-bound authentication attribute rather than overwriting the logical account key. An identity mismatch SHALL be an authentication failure, not an account migration.

#### Scenario: User scans a different account during reauthorization
- **WHEN** the browser profile authorizes a finder identity different from the durable binding
- **THEN** the runtime keeps the original logical ownership and binding, reports a mismatch, and waits for the correct account instead of registering a second Cloud account

### Requirement: 平台运行时必须支持 wechat_channels 的非浏览器常驻 connector

平台运行时 SHALL 把 `wechat_channels` 加入 Edge/Cloud/环境配置的 `PlatformId`，并 SHALL 允许该平台同时装配 browser auth sidecar 与独立 `InteractionConnector`。浏览器 driver 负责身份/挑战/sidecar 生命周期，connector 负责 API probe、增量同步、发送和回查；浏览器关闭 MUST NOT 被解释为平台 runtime 停止。缺少 connector 或有效 capability 时 MUST 诚实 unsupported，MUST NOT 回落 XHS/Facebook 浏览逻辑。

#### Scenario: api-only runtime 不依赖打开页面
- **WHEN** 视频号账号已登录、身份验证通过且浏览器关闭
- **THEN** runtime 保持 online 并由 InteractionConnector 工作，MUST NOT 创建虚假的 browse session

#### Scenario: connector 缺失时 fail-fast
- **WHEN** 构建识别 `wechat_channels` 但没有 InteractionConnector
- **THEN** 该平台互动能力诚实不可用，MUST NOT 装配 XHS/Facebook driver 代替

### Requirement: 平台能力 registry 必须区分编排能力与入站互动能力

Edge 与 Cloud registry SHALL 为 `wechat_channels` 声明 `identity/overlay/auth.browser_sidecar` 与 comment/DM read/write interaction capabilities，并对 browse/like/collect/follow/publish/patrol 显式 unsupported。Cloud 现有 note-scoped registry MUST NOT 被迫为视频号编造站点指标、surface 或调度入口；如果扩展 registry shape，旧 XHS/Facebook entries 和消费者 MUST 保持逐位兼容。

#### Scenario: 视频号不显示不存在的浏览能力
- **WHEN** Cloud/Edge 查询 `wechat_channels` registry
- **THEN** 只得到真实 interaction/auth 能力，MUST NOT 因满足旧 Record 类型而声明 collect/follow/publish

#### Scenario: 现有平台零回归
- **WHEN** registry 支持 InteractionConnector 后运行 XHS/Facebook contract tests
- **THEN** 两个平台的既有能力、surface、comment profile 与调度行为不变

### Requirement: 视频号平台归属必须随环境原子传递

环境创建、加入、列表、选择、settings 与核心启动注入 SHALL 支持 `wechat_channels` 并保持 `envKey/accountId/platform` 原子一致。已标注视频号环境 MUST NOT 被旧的二值 normalize 逻辑回落为 xiaohongshu；Cloud MUST 校验 edge hello platform 与 `accounts.platform`，不一致时拒绝同步和发送。

#### Scenario: 二值 normalize 不吞掉 wechat_channels
- **WHEN** Electron/Edge 从环境 remark/settings 读取 `wechat_channels`
- **THEN** 值原样注入 `AIDCP_PLATFORM=wechat_channels`，MUST NOT 归一化成 xiaohongshu

#### Scenario: 平台与账号不一致时拒绝派活
- **WHEN** hello 报 `wechat_channels` 但目标 account 的 `accounts.platform` 不是 `wechat_channels`
- **THEN** Cloud 拒绝注册 interaction route 并返回稳定配置错误

### Requirement: Facebook capability assembly resolves to Native execution
An Edge environment that declares Facebook browser capabilities SHALL assemble a compatible Native Facebook executor before advertising those capabilities. The existing Cloud capability names and product semantics remain unchanged; capability admission MUST fail honestly when the compatible Native adapter is unavailable.

#### Scenario: Compatible Native Facebook adapter is ready
- **WHEN** the Facebook driver, browser provider, and Native manifest all declare compatible support
- **THEN** Edge advertises the existing Facebook capabilities and routes them to Native execution

#### Scenario: Native Facebook adapter is incompatible
- **WHEN** the driver declares a Facebook capability but the Native manifest/protocol lacks its required command coverage
- **THEN** Edge withholds or rejects that capability rather than routing it to Xiaohongshu or JavaScript

### Requirement: 平台 driver 与 Native adapter 声明准确命令集

每个浏览器平台 driver SHALL 声明可路由的版本化语义页面命令；每个 Native adapter manifest SHALL 声明实际实现的准确命令集。Edge 对 Cloud 的命令能力声明 MUST 取两者交集。声明漂移、缺少命令或版本不匹配时，该命令能力 MUST 不可用，MUST NOT 仅凭 broad `browse`、`identity`、`profile_visit` 或 adapter version 推断支持。

#### Scenario: broad capability 不能替代准确命令
- **WHEN** Facebook driver 声明 `browse` 和 `identity`，但 Native adapter 未声明 `identity_read_current`
- **THEN** Edge 不向 Cloud 声明运行期当前页身份读取能力

#### Scenario: Native 拒绝平台外命令
- **WHEN** 一个语义命令不在当前 Native session 平台的准确命令集中
- **THEN** Native 在 CDP 派发前返回 `unsupported_command`
- **AND** MUST NOT 路由到其他平台 adapter 或 JavaScript fallback

