## Why

云端唯一文本模型出口的单次请求超时默认 60s，是按当时非 thinking 模型的峰值（25–30s）留 2 倍余量定的。改用 thinking 类模型（qwen3 thinking / deepseek-r1 类）后，复杂提示常需 60–150s+，60s 会把大量合法慢调用误判超时。更糟的是发布链路有几处**外层秒表比模型真实耗时还短**：4 个发布角色的执行超时（15/20/30s）远短于模型预算且未把短超时同步传给模型请求，峰值必误超时走静默降级（审批闸失效、退化公式打分、不去 AI 味、退化纯文发布）；发布流水线总闸（180s）比其内部角色预算串行和还小，慢一点整篇发布被总闸掐断判失败、已付费的正文生成作废。而把单次天花板抬高又会与浏览闭环空转看门狗冲突——看门狗轻推阈值（130s）会小于新的单次上限，导致模型还没答完就被注入恢复滚动、滚走正要返回决策的页面。故需把「单次模型调用天花板 + 各外层时限 + 看门狗轻推阈值」作为一组自洽不变量一起抬。

## What Changes

- **单次模型调用天花板 60s → 180s**：抬高文本 LLM 客户端构造默认请求超时至 180s（给 thinking 模型留足），并新增 env 旋钮使部署可调；per-call 覆盖语义不变。
- **发布 4 角色外层闸对齐模型预算**：`ApprovalGatekeeper`(15s)/`QualityScorer`(20s)/`ContentCleaner`(20s)/`ImagePlanner`(30s) 外层执行超时抬到 180s，并把该值**同步传进各自的模型调用**（外层秒表绝不短于其所包裹的模型预算）；标杆角色 `ContentScout`/`ContentCreator`/`TitleCreator` 随天花板抬到 180s。各配独立 env 旋钮。
- **发布流水线总闸 ≥ 关键路径角色预算之和**：`AIDCP_PUBLISH_PIPELINE_TIMEOUT_MS` 180s → ≥600s（容器不得小于其内容物），顺带消解「生图 200s 角色闸够不到 180s 总闸」的错位。
- **看门狗轻推阈值联动抬高**：浏览闭环空转看门狗**恢复轻推**阈值须**严格大于单次模型调用天花板**（130s → ≥240s），下限相应抬高（91s → ≥200s），**放弃结束**阈值生产值须显著大于轻推（→ ≥480s）。此为抬高天花板的强制联动不变量。
- **边→云 选元素等待对齐**（实现级）：v1 兼容路径 edge 侧等待 15s → ≥200s（须大于云端模型天花板，否则边缘先放弃）。
- **（低优/健壮性）** 万相生图 submit/poll 增加单请求快速失败超时；生图轮询/角色闸仅在换更慢 thinking 生图模型时再等比放大（本次不改，列非目标）。

## Capabilities

### New Capabilities
<!-- 无新增能力，纯为既有能力调整超时策略不变量 -->

### Modified Capabilities
- `role-llm-config`: 文本 LLM 客户端**构造默认请求超时**从按非 thinking 模型定的短值，改为按 thinking 模型定的天花板（≥180s）且经 env 旋钮可调；per-call 覆盖（角色/模型/温度/超时）语义与向后兼容不变。
- `publish-pipeline`: 新增不变量——任何**调用模型的发布角色**其执行超时 MUST NOT 短于所包裹的模型调用预算，且 MUST 把该超时同步传进底层模型请求；**流水线总预算 MUST ≥ 关键路径上各模型角色预算之和**（容器 ≥ 内容物）。
- `browse-loop-resilience`: 强化看门狗恢复轻推阈值约束——除「MUST 大于详情页停留上限」外，MUST **严格大于单次模型调用天花板**，使一次合法的 thinking 决策进行中绝不被轻推打断。

## Impact

- **aidcp-cloud（主）**：`src/llm/qwen.ts`（默认超时 + env）、`src/server.ts`（QwenClient 构造处读 env、发布总闸、ContentCleaner 的 `complete` 传超时）、`src/publish-agent/roles/{approval-gatekeeper,quality-scorer,content-cleaner,image-planner,content-scout,content-creator,title-creator}.ts`（外层闸 + 传超时 + env）、`src/risk/resume-limits.ts`（看门狗轻推默认 + 下限）；看门狗结束阈值生产值经后台配置同步（与既有 change `restore-auto-resume-and-global-safety-config` 的配置管线相邻，本 change 只调数值不变量、不重复其管线）。
- **aidcp-edge**：`src/client/cloud-selector.ts`（选元素等待 ≥200s）。
- **文档/回归**：新增 env 旋钮需在部署文档登记；回归红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必过 + `npm run typecheck`（两仓）。
- **非目标**：不改协议、不改风控状态机、不改万相生图轮询/角色闸数值（仅列健壮性 backlog）。
