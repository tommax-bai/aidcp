## ADDED Requirements

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
