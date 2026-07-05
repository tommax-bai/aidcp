## ADDED Requirements

### Requirement: 内容面板展示参照配图使用审计

`GET /api/content/published` SHALL 在发布记录投影中加性返回参考图使用审计字段。该字段在新参照洗稿记录上反映生成候审段落库的参考图使用状态，在普通发布或历史无审计记录上为 `null`。管理后台内容详情 SHALL 在参照洗稿记录的配图区域展示该审计：当状态为 `unsupported` 时，必须明确提示当前图片厂商未实际使用参考图、配图是按文本重新生成；当状态为 `used` 时，显示参考图已被图片模型使用；当状态为 `unavailable` 或 `skipped` 时，显示对应降级原因。前端 MUST NOT 因请求中带过参考图就宣称图片模型已使用参考图。

#### Scenario: unsupported 状态在内容详情可见
- **WHEN** 内容接口返回某参照洗稿记录 `imageReferenceAudit.status='unsupported'`
- **THEN** 内容详情在配图说明附近展示“当前图片厂商不支持参考图，已按文本重新生成”一类文案，并显示参考图数量

#### Scenario: used 状态在内容详情可见
- **WHEN** 内容接口返回 `imageReferenceAudit.status='used'`
- **THEN** 内容详情展示参考图已实际用于生成，并显示参考图数量

#### Scenario: 历史无字段不编造状态
- **WHEN** 内容接口返回 `imageReferenceAudit=null`
- **THEN** 内容详情不展示“已使用参考图”，也不把历史记录误标为 unsupported

