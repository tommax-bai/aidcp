## Why

3a/3b/4a/4b 已交付 api↔automation 的窄端口、双向命令、审批 authority 与 11 组同步读镜像，
`aidcp-api` 与 `aidcp-content` 各自有真的手写启动入口并已可独立启动。

**`aidcp-automation` 没有。** 它的可执行入口 `runAutomationEntry()` 读完配置即抛
`AutomationRootNotReadyError`（`aidcp-automation/src/automation-composition-root.ts`），
真正的生产运行时工厂在全仓零调用。**这是有意的 fail-closed，不是缺陷**——4a 明确要求
「blocker ledger 未清零时 MUST NOT 声称 full root closure、独立 typecheck/boot 或三进程可运行」
（`openspec/specs/cloud-automation-api-direct-ports/spec.md`）。

代价是：**批次 4 未完成，批次 5（dev 三服务真跑）无法开工**，而派生仓的 12 条 readiness blocker
全部标着 `closingChange: 'future'`、**没有任何 change 承接**。台账挂了三天没有主人，
既不会有人来清，也不会有任何机械手段提醒它还欠着。本 change 就是来当这个主人的。

同时，本 change 处置一个**端口解决不了**的问题：automation 的 37 个角色需要模型出口与四个内容
属主角色工厂，而两者都是 content 属主的**行为**。行为不能靠包 HTTP 客户端跨过去——这与 §10.7
「发帖调度器归属」是同一类岔口，必须先裁决归属，再写代码。

## What Changes

- **以派生仓自己的台账为准清零 12 条 blocker**：4 条运营指令通道（automation 属主、api 消费）、
  7 条内容属主 authority（content 属主、automation 消费）、1 条生产运行时未接线。
  台账的权威副本与逐条证据在 `aidcp-cloud/boundaries/composition-root-independent-blockers.json`；
  派生仓的收窄副本在 `aidcp-automation/src/automation-composition-root.ts`。
  **两处 MUST 同步收缩，且只许下降**（与豁免棘轮同一条纪律）。
- **四条运营指令通道**（飞书入站在 api、处理器在 automation）：自由文本委托（含意图解析）、
  发布/评论指令、委托任务卡片动作、调度启停。沿用 4a 已建立的 paired command 形态
  （api client → automation route + receiver），**MUST NOT 让 api 侧自己拼 intent 绕过去**
  （§10.6 automation 判错第 4 条：委托端口的方法面原本就漏了自由文本入口）。
- **七条内容属主 authority**：四个存储写（草稿精修 / FB 发帖素材 / 概念池 / 精选库）走 content
  内部 HTTP 写口；token 用量记账走同一形态；**模型调用出口与内容属主角色工厂两项须先裁决归属**
  （见 design.md §2 的三个岔口），裁决前 MUST NOT 动代码。
- **automation 生产运行时真接线**：边-云 WebSocket 服务端、事件总线与角色调度器、风控单写者、
  各调度器与监测体，全部由 `createAutomationCompositionRoot` 之上的真 `main()` 装配；
  启动 gate 与 api 同形——同步读镜像首次装载完成前**不放行业务入口**。
- **诚实语义不因接线而松动**：任一必需依赖缺席时，启动 MUST 停在具名原因上；
  MUST NOT 用空数组、`false`、未绑定或代码默认把缺席压成可用。
  跨进程后 `instanceof` 恒 false，错误识别 MUST 改结构化守卫（CLAUDE §8.5）。
- **验收按运行形态分层**：loopback HTTP 契约测试只证明 route/client；dev 单体部署只证明现网零回归；
  **只有 api/automation/content 三个独立进程都起来并互相说上话，才能声称本 change 生效**。

## Capabilities

### New Capabilities

- `cloud-automation-production-runtime`: 规定 automation 独立进程的生产运行时装配、启动 readiness
  gate、依赖缺席时的诚实终止语义，以及 blocker ledger 的清零与门禁纪律。
- `cloud-automation-content-owner-ports`: 规定 automation 访问 content 属主能力的窄端口
  （四个存储写 + token 用量 + 模型出口与角色工厂的归属落点）与失败语义。
- `cloud-automation-operator-command-ports`: 规定四条运营指令从 api 飞书入站到 automation
  处理器的跨进程通道、鉴权、幂等与结果未知语义。

## Impact

- `aidcp-cloud`：事实源——四条运营指令的 route/receiver、七条内容 authority 的 route/client、
  台账收缩与 acceptance 门禁。
- `aidcp-kernel`：新增窄接口与纯类型；**不放行为类**（CLAUDE §8.4）。
- `aidcp-transport`：内容 authority 的 route/client 三件套；模型出口若裁决为共享，落点在这里。
- `aidcp-automation`：真 `main()`、content 客户端组、四个指令 receiver、readiness gate、台账清零。
- `aidcp-api`：四条运营指令的 client 与飞书入站接线。
- `aidcp-content`：四个存储写 route + token 用量 route；模型出口按裁决结果调整归属。
- `aidcp` control：change 文档、派生对账、分层验收记录、真机项登记
  `docs/real-machine-acceptance-backlog.md`。
- **不含**：批次 5 的 dev 三服务部署与 soak，另起 change；ol 一律等用户明确要求。
