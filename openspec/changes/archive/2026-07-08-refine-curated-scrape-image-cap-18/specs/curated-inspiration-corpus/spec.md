# curated-inspiration-corpus Specification (delta)

## MODIFIED Requirements

### Requirement: 精选参考图默认保留平台上限

精选语料保存图文笔记参考图时，默认 SHALL 保留最多 18 张有序图片引用（18 = 小红书单帖图片数上界，等于把一篇笔记的图全存下来），作为洗稿创作的视觉参照池。该上限与发布侧配图张数（小红书图文帖硬上限 9）**解耦**——参照池按整篇存、发布生成仍只取其中 ≤9 张。系统仍 MUST 保持硬上限 18、URL 去重、无效 URL 过滤、状态诚实和账号隔离；不得因提高默认数量而允许无界存储。

当后续观测提供非空图片快照时，精选行 MAY 用该快照刷新已有图片；当后续观测没有图片或图片刷新失败时，系统 MUST 保留已有非空 `reference_images`，MUST NOT 用空数组擦除已保存图片。

#### Scenario: 默认保留全源稿图片（含超过旧上限九张）
- **WHEN** 一篇图文笔记上报 18 张有效图片并进入精选
- **THEN** `curated_content.reference_images` 保留全部 18 张有序图片，而不是只保存前九张

#### Scenario: 超过硬上限仍被截断
- **WHEN** 上游异常上报超过 18 张图片
- **THEN** 精选库最多保存 18 张，且保留前 18 张规范化后的有序图片

#### Scenario: 空刷新不擦除已有图片
- **WHEN** 某精选行已保存非空 `reference_images`，后续观测未带图片或抽取失败
- **THEN** 系统保留已有图片快照，MUST NOT 写成空数组
