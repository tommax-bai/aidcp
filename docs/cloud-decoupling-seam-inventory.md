# Cloud 代码解耦 · 剩余边接缝地图（Seam Inventory）

> 2026-07-24。`aidcp-cloud` 拆三仓的 **Block ① 代码解耦** 收尾产物。跨边界 import 从 **266 → 101（消除 62%）**，全部 land + dev 部署 + 逐刀全量测试通过、行为零变更。本文件把**剩余 101 条**逐条按「物理拆进程后会变成什么」分类，是 **Block ② 拆进程** 的设计输入。
>
> 权威数字以 `aidcp-cloud` 的 `boundaries/import-exemptions.json` `frozenTotal` 为准（本文写作时 = 101，master `8296cbe`）。分类脚本口径见文末。

## 0. 一句话结论

**代码解耦已到自然地板。** 剩余 101 条**没有一条是「该消而未消的错层耦合」**——它们是三类**已定性**的东西：共享契约、真 RPC 接缝、拆完自动消失。再往下清就要违反项目自订的 §2（协议 edge↔cloud 逐字同步）/ §9（平台单写）/ kernel 门禁——即被否掉的「激进口径」。所以 62% 是干净解耦的正确终点，不是半途。

## 1. 剩余 101 条按处置分类

| 处置类别 | 边数 | 拆进程后变成 |
| --- | --- | --- |
| RPC 接缝 · 行为/存储 | 37 | 跨服务同步调用（api/panel 读 automation/content 的数据与行为） |
| RPC 接缝 · 风控单写 | 13 | 提交事件 / 读投影，跨进程（宜异步） |
| RPC 接缝 · orchestration | 5 | comm/feishu handler 跨层调 |
| 共享契约 · 热（protocol/RoleName） | 12 | 进共享包（protocol.ts 6 + event-bus/types RoleName 6） |
| 共享契约 · §9 平台数据 | 8 | 共享参考数据（platform/index 7 + registry 1） |
| 共享契约 · LLM 客户端接口 | 7 | 共享基础设施（llm/qwen 3 + index 2 + providers 2；门禁挡 `LlmClient` 名字） |
| 同服务归位即消失 · 基类 | 7 | agents/base-role 5 + publish-agent/roles/base-role 2 |
| 同服务归位即消失 · panel hub | 2 | panel/types，留 api 服务内部 |
| 模块状态 · config-mirror | 10 | mirror-version-store 4 + config-mirror-freshness 3 + mirror-stop-work 3 |

## 2. 归成三个上位处置

- **共享契约（27 条）**：protocol/RoleName/平台数据/LLM 接口。**不是要消除的耦合，是本就该放共享包的共享定义**。只因 §2/§9/门禁规则挡着没搬进 kernel，概念上无问题。拆进程时随 kernel 演进成三仓共享的内部包。
- **真 RPC 接缝（55 条）**：三服务之间**真实的行为耦合数**。集中在 **api/panel 层读 automation/content 的数据与行为**（行为/存储 37 条为主）。拆进程时逐条决定：同步 RPC（读数据）还是异步事件（风控 13 条宜异步）。
- **拆完自动消失 / 机械决定（19 条）**：基类继承 9 条随模块归位消失；config-mirror 10 条做个「每服务一份 vs 共享配置总线」的小决定。

## 3. 对 Block② 拆进程的直接含义

1. **真实跨服务耦合 = 55 处**，可控但不小，**主战场是 api↔automation 边界**（api/panel 读 automation 拥有的数据）。拆进程设计的第一决定：**api/panel 层要不要收口成一个「数据网关」**统一向 automation/content 取数，而不是散点直连。
2. **风控 13 条宜走异步事件**（本就是「单写 + 提交事件/读投影」模型，见 `docs/risk-control.md`），不要做成同步 RPC。
3. **共享契约 27 条随 kernel 走**：kernel 已积累约 44 个纯共享文件，拆三仓时它成为三仓共享的内部包；protocol/RoleName 因 edge↔cloud 逐字同步（§2）留在 comm/，作为共享包的特例登记。
4. **基类 9 条不用管**，模块归位后消失。

## 4. 不再往下清的理由（守 §2/§9/门禁）

- **protocol.ts / RoleName**：cloud 的 protocol.ts 必须与 edge 那份**逐字一致**（§2 跨仓手工同步）。从它析出类型 = 一次跨 edge+cloud 的协议改动，正是 §2 最警惕的高风险，不做。
- **§9 平台注册表 / 风控**：数据/最终状态单写，硬搬进 kernel 违反单写不变量。
- **kernel 门禁（AC-BOUND-03）**：禁模块级 `new Set`/`new Map`（活状态）、禁 `LlmClient`/`ChatLlmClient` 标识符、禁 `setTimeout`（定时器）、禁 SQL/HTTP。LLM 接口与若干带查表 Set 的纯函数因此进不了 kernel，留作共享契约/接缝。

## 5. 解耦执行档案（本轮 7 刀，均 land+dev 部署+全量绿）

266→233 纯契约 → 233→222 互动端口 → 222→209 类型批抬 → 209→173 store 簇（pg-config 搬 kernel + schemaEnsurer 端口）→ 173→156 llm/lang 契约 → 156→138 platform 类型闭包 → 138→122 行为类接口抽取 → 122→108 长尾抬取 → 108→101 prompt 构建器。kernel 4→约 44 文件。每刀手法/residual 见各 `scratchpad/docpatch-*.md`，请求 §4.7 kernel 名册回写（RK1..RK-prompt-final，待套用）。

## 6. 分类脚本口径

从 `boundaries/import-exemptions.json` 的 `entries`（from,to）+ `boundaries/module-ownership.json` 的 layer 映射，按 to 目标归类：protocol/event-bus-types→热契约；platform/*→§9；llm/*→LLM 契约；risk/*→风控接缝；*base-role→基类；panel/types→panel hub；mirror-*→config-mirror；handler 及其余 store/service→RPC 接缝。逐层方向分布：api→automation 37、automation→api 21、api→content 18、content→automation 13、automation→content 7、content→api 5。
