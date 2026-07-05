# Proposal: Token Usage Estimated Cost Column

## Why

管理后台已经能按日期 / 账号 / 角色 / 模型查看 token 消耗，但运营判断规模化成本时还要手动把输入、输出 token 乘以各厂商单价。这个计算不需要精确到财务账单，只需要在用量明细里给出一个接近量级的成本信号，帮助及时发现高成本角色或模型。

## What Changes

- 在 console `/usage` 的 token 消耗明细表中，在「总 token」后新增「预估成本」列。
- 预估成本按行内 `promptTokens` / `completionTokens` 和内置公开刊例价粗算，单位为人民币元。
- 已知模型显示 `~¥...`；未知模型显示空值，不伪造成本。
- 估算明确不覆盖缓存命中、Batch、免费额度、资源包、合同折扣、区域差异和按输入长度分段等账单细节。

## Non-goals

- 不新增云端 API 字段或数据库字段。
- 不从费用中心实时拉价格，也不做财务级对账。
- 不改变 token 用量采集、聚合、筛选或排序语义。

## Validation

- `openspec validate estimate-token-cost-column --strict`
- console: helper unit test, `npm run typecheck`, `npm test`
