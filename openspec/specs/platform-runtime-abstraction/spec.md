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

cloud SHALL 提供按 `PlatformId` 索引的平台 profile registry，用于描述站点名、内容名词、指标名词、评论长度、排序/时间窗口、locale、能力声明和调度入口。平台化文案与限制 MUST 通过 profile 注入现有角色/任务调用，MUST NOT 在角色 prompt 或 scheduler 内硬编码小红书术语后再用平台分支修补。

#### Scenario: xhs profile 注入后 prompt 默认不变
- **WHEN** xhs 评论相关角色生成搜索词、挑选目标或撰写评论
- **THEN** 它们经 xhs profile 得到与抽象前等价的小红书术语、长度限制和指标口径

### Requirement: 协议语义保持平台无关

平台抽象 SHALL 复用现有平台无关命令语义。新增平台 MUST NOT 引入以平台名命名的协议消息类型来表达通用动作；除非新增真实通用语义，否则 `docs/protocol.md` 的消息计数与两端 protocol 枚举 SHALL 保持不变。浏览 surface 与 open purpose、以及派生 `noteId` 与独立 `observation` 见证包 SHALL 作为既有消息上的**平台无关 optional 字段扩展**承载，不新增消息类型、不改变消息计数。

#### Scenario: 平台抽象不改变协议计数
- **WHEN** 完成 xhs driver 提取并运行协议契约验收
- **THEN** 两端 protocol 枚举和 `docs/protocol.md` 计数保持 Change 0 前一致，AC-PROTO 类检查通过

#### Scenario: surface 与 purpose 是平台无关字段扩展
- **WHEN** 为 `note.open` 增加 `surface`/`purpose`、为 `action.completed` 增加派生 `noteId`/`observation`
- **THEN** 两端 protocol 的 `MessageType` 枚举与计数不变，AC-PROTO 全绿
- **AND** 这些字段的语义不以任何平台名命名、缺省时逐位等于今天

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

