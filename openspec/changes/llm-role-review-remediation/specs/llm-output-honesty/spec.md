# llm-output-honesty (delta)

## ADDED Requirements

### Requirement: 判定类 LLM 输出必须做域内校验

系统对判定类角色返回的「从给定候选中选择」型输出 SHALL 做域内校验：卡片择选返回的序号 MUST 为整数且落在本屏候选范围内，越界或非法时 MUST 按 skip 如实处理（携带独立失败原因），MUST NOT 静默替换为任何其他卡片；搜索关键词决策返回的词 MUST 属于提示词中给定的候选集，编造词 MUST NOT 被真实搜索，按解析失败走既有安全回退。

#### Scenario: 卡片序号越界
- **WHEN** 卡片择选 LLM 返回 `verdict=valuable` 且 `index` 超出本屏候选数组范围（或非整数）
- **THEN** 系统按 skip 处理并携带可区分的原因（如 `index_out_of_range` / 解析失败），不打开任何卡片，绝不静默落到第一张

#### Scenario: 搜索词不在候选集
- **WHEN** 搜索关键词决策 LLM 返回的 `keyword` 不属于提示词给定的候选集合
- **THEN** 系统视同解析失败走既有安全回退（skip / 种子词回退），该编造词绝不进入真实搜索

### Requirement: 生成类 LLM 输出的解析修复与输出约束

标题创作的 JSON 解析 MUST 在 `JSON.parse` 前执行与正文创作同源的裸控制字符修复；去 AI 味重写的提示词 MUST 明确约束模型只输出重写后的正文本身（不得含前言、解释或格式包裹），防止非正文内容逐字进入发布正文。

#### Scenario: 标题 JSON 含裸换行
- **WHEN** 标题创作模型输出的 JSON 字符串值内含裸换行/控制字符
- **THEN** 解析层先修复再解析，标题正常产出，不触发「解析失败→整篇 abort」

#### Scenario: 重写模型带前言
- **WHEN** 去 AI 味重写被触发
- **THEN** 提示词包含「只输出重写后正文」的显式约束，重写产物即正文本身

### Requirement: 质量评审对象必须是将发布文本

内容质量评分角色 SHALL 以清洗（去 AI 味重写）后的正文作为评审对象；发生重写时 MUST NOT 继续以重写前草稿为评审文本。

#### Scenario: 重写后评分
- **WHEN** 正文经去 AI 味重写（rewritten=true）后进入质量评分
- **THEN** 评分提示词中嵌入的正文为清洗稿（将发布的文本），评分结果反映真实待发布内容

### Requirement: 代码兜底默认模型必须现役

全局模型配置缺行/存储不可用时的代码级兜底默认 SHALL 指向当前在售模型；被平台公告下架的模型名 MUST NOT 继续充当兜底默认。

#### Scenario: 配置行缺失时兜底
- **WHEN** 全局 `model_config` 行缺失或 PG 不可用
- **THEN** 兜底默认模型为现役在售模型（`qwen3.7-plus`），调用不因兜底模型已下架而失败
