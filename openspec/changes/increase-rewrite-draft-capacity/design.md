## Context

当前调度器使用两层互补门禁：自主生成以 `auto:<accountId>` 键保持同账号单飞；全部生成轮再受进程级 `maxConcurrentRuns` 与账号级 `pendingCapPerAccount` 约束。默认值分别为全局 2、账号在途 3，因此同账号第三篇跨来源洗稿无法并行，少量待审稿也会迅速占满账号容量。

## Goals / Non-Goals

**Goals:**

- 普通自主稿继续按账号单飞，同刻最多 1 轮。
- 在全局容量空闲时，同一账号允许 3 篇不同来源洗稿并行生成。
- 将“生成中 + 待审”账号在途默认帽提高到 20。
- 保持同源洗稿单飞、同步原子 claim、帽满不排队和 env 覆盖语义不变。

**Non-Goals:**

- 不建立普通稿与洗稿互相隔离的独立资源池；两者仍共享全局生成帽。
- 不改变发布审批、下发串行、账号日发帖上限或风控规则。
- 不修改帽满原因码与委托任务退避语义；后者由 `publish-claim-reject-defer-not-fail` 串行处理。

## Decisions

### D1：提高既有两项默认值，不引入第三套队列

将 `maxConcurrentRuns` 默认值从 2 调到 3，将 `pendingCapPerAccount` 默认值从 3 调到 20。现有 claim 表已经按账号与来源精确计数，直接调整默认值即可覆盖 console、飞书、排期与自动扳机，避免只改某个入口形成旁路。

### D2：普通稿的 1 由既有账号键单飞继续保证

普通稿仍使用 `auto:<accountId>` 键；同账号第二轮自主生成继续返回 `already_running`。洗稿使用 `rewrite:<accountId>:<sourceId>`，不同来源可占用三个全局槽。两者共享全局 3 槽，因此普通稿在跑时最多再并行两篇洗稿；本次不建设保留槽或双资源池。

### D3：代码缺省、生产接线和测试必须同值

同时修改 `PublishScheduler` 构造器缺省值与 `server.ts` env 回落值，防止测试桩和生产出现裂脑。新增默认配置回归，并保留显式小帽测试验证拒绝原因。

## Risks / Trade-offs

- **[三轮同时生图提高供应商峰值与 429 风险]** → 仍保留 `AIDCP_PUBLISH_MAX_CONCURRENT_RUNS` 与单帖生图并发环境变量，可在 dev 观察失败率后单独回调。
- **[账号待审堆积从 3 放大到 20]** → 帽仍是硬上界且覆盖所有入口；console 继续以 `publish_capacity` 引导先处理存量。
- **[与 claim 形状 change 冲突]** → 本 change 独占并先落 `publish-scheduler.ts`；`publish-claim-reject-defer-not-fail` 后续从更新后的 `master` 开工。

## Migration Plan

1. 先改代码与回归，运行发布验收、全量测试和 typecheck。
2. 串行合入 `aidcp-cloud/master` 并部署 dev，确认健康检查和启动日志。
3. 如供应商错误率异常，可仅在 dev `.env` 临时把 `AIDCP_PUBLISH_MAX_CONCURRENT_RUNS` 回调为 2；代码回滚则恢复两项原默认值。

## Open Questions

（无）
