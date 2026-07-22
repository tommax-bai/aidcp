## MODIFIED Requirements

### Requirement: 平台 profile registry 参数化云端编排文案与限制

cloud SHALL 提供按 `PlatformId` 索引的平台 profile registry，用于描述站点名、内容名词、指标名词、评论长度、排序/时间窗口、locale、能力声明和调度入口。平台化文案与限制 MUST 通过 profile 注入现有角色/任务调用，MUST NOT 在角色 prompt 或 scheduler 内硬编码小红书术语后再用平台分支修补。普通主页关注能力与页面内联关注能力 MUST 分开声明；用量指标 MAY 由多个真实执行能力联合决定，但 MUST NOT 为展示一个指标而开启没有执行器的编排路径。

#### Scenario: xhs profile 注入后 prompt 默认不变
- **WHEN** xhs 评论相关角色生成搜索词、挑选目标或撰写评论
- **THEN** 它们经 xhs profile 得到与抽象前等价的小红书术语、长度限制和指标口径

#### Scenario: Facebook Reel 关注不误开启主页关注
- **WHEN** Facebook 声明 Reels-only 关注执行能力但仍不支持作者主页访问与主页关注
- **THEN** Cloud 可为当前 Reel 下发受闸关注并向客户端投影 `follow` 用量
- **AND** FollowAgent 的普通主页关注路径仍保持关闭
