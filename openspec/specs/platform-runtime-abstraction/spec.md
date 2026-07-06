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

平台抽象 SHALL 复用现有平台无关命令语义。新增平台 MUST NOT 引入以平台名命名的协议消息类型来表达通用动作；除非新增真实通用语义，否则 `docs/protocol.md` 的消息计数与两端 protocol 枚举 SHALL 保持不变。

#### Scenario: 平台抽象不改变协议计数
- **WHEN** 完成 xhs driver 提取并运行协议契约验收
- **THEN** 两端 protocol 枚举和 `docs/protocol.md` 计数保持 Change 0 前一致，AC-PROTO 类检查通过

### Requirement: xhs 提取必须零行为回归

Change 0 SHALL 仅把现有 xhs 页面能力移入 driver 装配边界，不改变 xhs 的浏览、评论、人审、发布、通知巡视、定位、风控或节奏行为。归档前 MUST 通过 edge/cloud 相关 acceptance、full test 和 typecheck。

#### Scenario: xhs 回归门全绿才允许后续平台工作
- **WHEN** `platform-abstraction-layer` 实现完成
- **THEN** xhs acceptance、full test、typecheck 和 OpenSpec strict validation 全部通过，才能开始依赖该抽象实现 Facebook 能力

