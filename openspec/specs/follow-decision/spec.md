# follow-decision Specification

## Purpose
TBD - created by archiving change fix-browse-action-fidelity. Update Purpose after archive.
## Requirements
### Requirement: 关注决策只依据平台真实提供的信号

关注（follow）决策 SHALL 只依据小红书主页**实际提供**的信号——粉丝数、获赞与收藏数、以及内容 / 作者与兴趣的相关性——来判定；MUST NOT 依赖平台**不提供**的字段（作品数 / 笔记数）。由于小红书主页不公开作品数，决策 prompt MUST NOT 摆出"作品数"项，也 MUST NOT 以"作品数未知"为由 skip。

#### Scenario: 健康创作者被关注而非因作品数未知 skip
- **WHEN** 作者主页显示粉丝数与获赞收藏数均健康（如 130 粉丝 / 6707 获赞与收藏）、内容与兴趣相关，而作品数不可得（平台不提供）
- **THEN** follow-agent 依据粉丝 + 获赞收藏 + 相关性判定关注，MUST NOT 以"作品数未知，无法判断质量"为由 skip

#### Scenario: prompt 不含作品数项
- **WHEN** 构造 follow-agent 的决策 prompt
- **THEN** prompt 中不出现"作品数"信号项，避免 LLM 据一个永不可得的字段做判定

### Requirement: 获赞与收藏须被抽取并送达关注决策

边缘 SHALL 从作者主页 `.user-interactions` 抽取"获赞与收藏"计数，并经协议（`profile.detail` → profile 角色 → follow-agent）串到关注决策；该字段缺失时合法（按未知处理），但只要主页提供就 MUST 被采集与使用。

#### Scenario: 获赞与收藏进入决策
- **WHEN** 作者主页 `.user-interactions` 含"获赞与收藏"计数
- **THEN** 边缘抽取该值并上报，云端 follow-agent 的决策输入包含它

