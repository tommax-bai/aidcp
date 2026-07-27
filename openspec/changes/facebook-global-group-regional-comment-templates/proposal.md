## Why

Facebook 群目标目前只有“映射一个或多个账号分组”与“未设置范围”两种状态，无法表达“任意 Facebook 账号分组均可加入”；同时，账号没有显式评论方案或账号模板时，评论链路会默认生成或直接停止，无法按刚加入/本次选中群组的区域使用运营维护的通用模板。需要把群组适用范围和评论正文来源都改成显式、可回读、可审计的配置。

## What Changes

- 为 Facebook 群目标增加显式 `global` 适用范围；全局目标允许任意已分组或未分组的 Facebook 账号进入候选池，同时继续受启用态、自动化开关、配额、全局一群一账号锁及执行前重验约束。
- 群组管理页的导入、筛选、列表和批量范围设置支持“全局分组”，并清楚区分全局、指定账号分组和未设置范围。
- 增加按群组 `region` 管理的 Facebook 通用评论模板配置及面板 API；模板支持多条、去空去重和数据库真态回读。
- 调整 Facebook 评论正文解析：账号显式评论方案优先；账号未设置评论方案时默认按模板方案解析；模板方案下账号模板为空时，按当前目标群的区域使用通用模板。区域缺失、区域无模板或模板无效时诚实停止，不回退生成评论。
- 保留搜索关键词、目标群成员账本、确定性正文校验、审批策略、联系方式注入、平台确认和风险计数等既有闸。
- 提供一次性、可审计的数据迁移，把变更生效时现存的全部 Facebook 群目标批量设为 `global`；迁移前记录数量与范围分布，迁移后按数据库回读核验，不改 membership、enabled、priority、join gating 或区域元数据。

## Capabilities

### New Capabilities

- `facebook-regional-comment-templates`: 定义区域通用评论模板的配置、解析优先级、缺失结果和安全边界。

### Modified Capabilities

- `facebook-group-target-catalog`: 增加全局、指定分组、未设置三态范围及其列表、筛选和批量写入真态。
- `facebook-group-import-workflow`: 导入时可显式选择全局范围，并与未携带范围、显式清空范围保持可区分语义。
- `facebook-group-membership`: 自动认领与执行前重验接受全局目标，且不削弱现有一群一账号锁与投影新鲜度闸。
- `facebook-scheduled-comment`: 未显式设置评论方案时默认模板方案，账号模板为空时按实际目标群区域解析通用模板。
- `console-panel-api`: 暴露全局范围和区域通用评论模板的读写接口及数据库回读结果。

## Impact

- `aidcp-cloud`: Facebook 群目标/范围模型、数据库迁移、候选认领与重验 SQL、评论配置解析、区域模板存储、Panel API 和审计测试。
- `aidcp-console`: `/facebook-groups` 的范围三态、批量全局操作、区域通用模板配置和 API 类型/测试。
- `aidcp-edge`: 评论正文仍由 Cloud 下发，协议与执行器不需要改变。
- 数据：新增区域模板权威表或等价持久化结构，并对当前 Facebook 群目标执行一次全局范围数据迁移；不触碰已加入/失败等 membership 事实。
