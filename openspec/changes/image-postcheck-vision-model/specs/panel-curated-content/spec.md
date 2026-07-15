## ADDED Requirements

### Requirement: 精选素材 SHALL 可解释地展示整组视觉反推

精选素材 API 与详情 SHALL null-safe 返回/展示视觉反推状态、provider/model/schema version、整组风格摘要、风格簇及逐图类型/关键结构。旧行或旗标关闭时 SHALL 显示“未分析/已关闭”，不可报错；失败时 SHALL 显示 unavailable/partial 及原因，MUST NOT 用空对象冒充已分析。文字卡、UI、图表的展示 MUST 使用各自专业维度，MUST NOT 全部显示摄影相机参数，也 MUST NOT 展示模型从原图抄出的具体文字。

#### Scenario: 非摄影素材显示对应维度
- **WHEN** 一组素材含插画、UI 截图和信息图
- **THEN** 详情分别展示媒介/造型、组件/网格、图形编码/层级摘要，不显示虚构焦距和相机型号

#### Scenario: 历史行没有视觉分析
- **WHEN** 面板读取尚无 visualAnalysis 字段的历史精选行
- **THEN** 页面显示未分析，不报错、不渲染假风格摘要

### Requirement: 发布详情 SHALL 区分参考使用、槽位绑定与保真通过

发布详情 SHALL 展示每个输出槽的主参考来源、附加参考角色、生成路由、provider 是否使用参考图、视觉审计状态、五项分数、风险、重试与丢弃原因。界面 MUST 明确区分 `referenceStatus='used'` 与 `visualAudit.status='passed'`；未核验、旗标关闭、历史无字段均 SHALL 有不同的 null-safe 状态，MUST NOT 把“已传参考图”表述成“保真通过”。

#### Scenario: 使用参考图但审计未通过
- **WHEN** 某槽 provider 记录 used，视觉审计记录 failed/retried/discarded
- **THEN** 详情同时呈现两个事实，不显示“保真通过”

#### Scenario: 视觉模型不可用
- **WHEN** 某槽 audit.status=`unverified` 且带失败原因
- **THEN** 详情显示“未经视觉核验”与原因，MUST NOT 显示绿色通过态
