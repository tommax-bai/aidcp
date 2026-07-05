## ADDED Requirements

### Requirement: 精选参考图默认保留平台上限

精选语料保存图文笔记参考图时，默认 SHALL 保留最多 9 张有序图片引用，以覆盖小红书图文轮播平台上限。系统仍 MUST 保持硬上限 9、URL 去重、无效 URL 过滤、状态诚实和账号隔离；不得因提高默认数量而允许无界存储。

当后续观测提供非空图片快照时，精选行 MAY 用该快照刷新已有图片；当后续观测没有图片或图片刷新失败时，系统 MUST 保留已有非空 `reference_images`，MUST NOT 用空数组擦除已保存图片。

#### Scenario: 默认保留九张以内图片
- **WHEN** 一篇图文笔记上报 9 张有效图片并进入精选
- **THEN** `curated_content.reference_images` 保留 9 张有序图片，而不是只保存前三张

#### Scenario: 超过平台上限仍被截断
- **WHEN** 上游异常上报超过 9 张图片
- **THEN** 精选库最多保存 9 张，且保留前 9 张规范化后的有序图片

#### Scenario: 空刷新不擦除已有图片
- **WHEN** 某精选行已保存非空 `reference_images`，后续观测未带图片或抽取失败
- **THEN** 系统保留已有图片快照，MUST NOT 写成空数组
