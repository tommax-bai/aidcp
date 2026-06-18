# AIDCP 验收测试用例

本文是三仓（aidcp-edge / aidcp-cloud / 协议契约）的**验收测试主索引**：把已有的 ~90 个
可执行测试与新增的验收用例，按**功能域 × 环境层级**组织成可追溯矩阵，作为联调与交付的
checklist。验收用例以**可执行测试脚本**为主交付，本文做编号、归口与判据说明。

## 0. 三个验收环境层级

| 层级 | 含义 | 依赖 | 默认是否运行 |
| --- | --- | --- | --- |
| **离线 / 逻辑级** | 纯逻辑断言（定位、风控、协议、拟人化分布等） | jsdom + 内存桩，无网络/Chrome/PG | 是（`npm test`） |
| **模拟集成** | 跨模块串联，mock CDP/LLM/飞书/PG | 进程内 mock | 是（`npm test`） |
| **本地真机联调** | edge + 真 Chrome + ECS cloud + 真飞书，真实小红书页面 | 外部环境 | 否（gated，`AIDCP_E2E=1`） |

> 现有单元/集成测试已覆盖**离线**与**模拟集成**两层的绝大部分；新增验收用例补齐了
> **协议契约一致性**、**风控安全闸红线**、**发布审批跨层契约**与**真机联调可执行脚本**。

## 1. 如何运行

```bash
# 边缘端（aidcp-edge）/ 云端（aidcp-cloud）各自：
npm install
npm test                 # 全部测试（离线 + 模拟集成；真机用例自动跳过）
npm run test:acceptance  # 仅跑 test/acceptance/ 下的验收用例
npm run typecheck        # 类型检查（协议契约漂移会在此暴露）

# 真机联调（gated，需云端可达 / 本机 Chrome）：
AIDCP_E2E=1 AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm test
```

新增验收用例位于 `aidcp-edge/test/acceptance/` 与 `aidcp-cloud/test/acceptance/`，
文件顶部 JSDoc 标注了 AC 编号、守护点与环境层级。

## 2. 全功能验收矩阵

环境层标记：`L`=离线逻辑级，`S`=模拟集成，`E`=真机联调。证据列给出对应测试文件
（相对各自代码仓 `test/`）。

### 2.1 边缘端 aidcp-edge

| 功能域 | 验收点 | 层 | 证据（test/…） | 通过判据 |
| --- | --- | --- | --- | --- |
| 定位引擎·三道闸 | 缓存命中+校验通过；命中失败自愈走 LLM；多重试升级 | L | `locating/engine.test.ts` | 校验失败绝不判成功，连续失败→escalated |
| 定位·反污染缓存 | 暂存→阈值晋升、校验失败重置、读写模式 | L | `locating/cache.test.ts` | 低质锚点不污染主缓存 |
| 定位·消歧 | 唯一高置信 hit / 多候选 ambiguous / miss | L | `locating/matcher.test.ts` | 模糊时不武断点击，降级 LLM |
| 定位·元素抽取 | 可见性/role/text/作用域/路径 | L | `locating/extractor.test.ts` | — |
| 定位·小红书特化 | 语义 class、作用域 modal 优先 | L | `locating/xhs-semantic-class.test.ts`、`xhs-scoped-search.test.ts` | 只认语义 class，不依赖混淆 class |
| CDP·原生 WS 客户端 | 连接、请求/响应 id 关联、事件订阅 | L/S | `cdp/client.test.ts` | — |
| CDP·DOM 快照 | Runtime.evaluate → jsdom | S | `cdp/dom-provider.test.ts` | — |
| CDP·Chrome 启动 | 路径发现/参数/复用/登录检测 | L | `cdp/chrome-launcher.test.ts` | — |
| 反检测·stealth | webdriver/plugins/languages/permissions 抹除 | L | `cdp/stealth-injector.test.ts` | 自动化特征被覆盖 |
| 浏览执行·会话 | 启动上报、云端命令路由、note.open/scroll/end | S | `browse/browse-session.test.ts` | 命令正确分发 + 结构化上报 |
| 浏览·卡片过滤 | likes 阈值/关键词/无关模式 | L | `browse/card-filter.test.ts` | — |
| 浏览·滚动/弹层/提取/搜索 | 惯性滚动、modal 轮询、笔记提取、搜索输入 | L/S | `browse/feed-scroller`、`modal-controller`、`note-extractor`、`search-handler.test.ts` | — |
| 边-云客户端 | hello/welcome 握手、publish/note.content 收发、命令路由 | S | `client/edge-client.test.ts` | id 正确关联 |
| 拟人化 | 对数正态停顿、贝塞尔鼠标、键盘节奏、滚动物理、疲劳曲线 | L | `humanize/*.test.ts`（5 个） | 分布统计性质成立 |
| 业务流·点赞 | 校验点赞态翻转、缓存+LLM 选择 | L/S | `flows/like-post.test.ts`、`like-runner.test.ts` | 后置校验通过才算成功 |
| 业务流·发布六步 | 进入→标题→正文→标签→提交→postId | S | `flows/publish-post.test.ts` | — |
| 发布·审批阻断 | approval gate 阻断、信号读写、超时/拒绝 | L/S | `flows/publish-post-approval.test.ts`、`publish/approval-gate.test.ts` | 未授权绝不发布 |
| 发布·端到端 | FakeWebSocket 模拟云端、publish.request→result | S | `integration/publish-e2e.test.ts` | — |
| **协议契约·边缘** | 版本=2、42 消息类型穷举、信封往返、坏帧 | L | `acceptance/protocol-contract.test.ts` `AC-PROTO-01..05` | 与云端契约逐字一致 |
| **发布审批·跨层契约** | 信号路径格式、approved/拒绝/超时/串号 | L | `acceptance/publish-approval-contract.test.ts` `AC-PUB-01..06` | 路径与云端一致，未授权不发 |
| **真机·边-云握手/心跳** | 连 ECS 发 hello 收 welcome、ping/pong | E | `acceptance/real-e2e.test.ts` `AC-E2E-01..02` | gated；真实连通 |

### 2.2 云端 aidcp-cloud

| 功能域 | 验收点 | 层 | 证据（test/…） | 通过判据 |
| --- | --- | --- | --- | --- |
| 协议·信封 | makeEnvelope/parseEnvelope/isEnvelope | L | `protocol.test.ts` | — |
| WS 服务端 | 坏帧→error、合法帧路由、handler 抛错兜底 | S | `ws-server.test.ts` | 不崩连接 |
| 消息处理器 | hello/plan/select/anchor/note.content、反污染晋升、暂停账号跳过 | S | `handler.test.ts` | 两次确认才晋升主缓存 |
| 任务规划 | 规则命中/LLM 兜底/非法步骤过滤 | L/S | `planner.test.ts`、`like-command.test.ts` | 防幻觉，op 合法 |
| 事件总线 | on/once/off/emitAsync/onAny、错误隔离 | L | `event-bus.test.ts` | 一个 handler 抛错不影响其他 |
| 账号状态 | pause/resume/isPaused/status | L | `account-state.test.ts` | — |
| 人设 Soul | soul.yaml 装载、行为准则/会话上限 | L | `soul.test.ts` | — |
| 缓存·锚点指纹 | fingerprint 一致性、schema | L | `cache.test.ts`、`concept-store.test.ts` | — |
| 事件驱动编排 | 6 条浏览闭环路径 + SessionMonitor 配额终止 | S | `integration/role-dispatcher.test.ts` | 事件链回到 feed.entered；超预算终止 |
| 15 角色 | 各角色订阅/产出事件正确 | L/S | `agents/*.test.ts`（14 个） | — |
| 风控·控制器 | 三档配额、分/时/日窗口、点赞率 35% | L | `risk-controller.test.ts` | 超限拒绝 |
| 风控·状态机 | normal→warned→restricted→frozen、恢复窗口 | L | `risk-state-machine.test.ts` | 迁移与恢复正确 |
| 风控·去重/频控/预算/PG | 互动去重、搜索频控、会话预算、持久化 | L | `risk-dedup`、`risk-session-scheduler`、`risk-pg-store.test.ts` | — |
| 飞书·Token/卡片/命令/记群 | token 续期、卡片构建、命令路由、卡片回调写信号 | L/S | `feishu-token`、`feishu-cards`、`feishu-commands`、`feishu-ws-receiver.test.ts` | — |
| 发布·6 角色管道 | scout→creator→director→assembler→gate→executor、超时/防重入 | S | `publish-agent/*.test.ts`（9 个）、`publish-post-processor.test.ts` | scout 否决则早停；禁用词检测 |
| **协议契约·云端** | 版本=2、42 消息类型穷举、信封往返、坏帧 | L | `acceptance/protocol-contract.test.ts` `AC-PROTO-01..05` | 与边缘契约逐字一致 |
| **风控·防自残安全闸** | 配额硬上限、状态降级链、致命冻结、record 拒绝返 false | L | `acceptance/risk-guard.test.ts` `AC-RISK-01..03` | 被禁止时绝不放行/不静默执行 |
| **发布审批·跨层契约** | 信号路径格式、卡片回调解析 | L | `acceptance/publish-approval-contract.test.ts` `AC-PUB-01/07/08` | 路径与边缘一致 |
| **真机·部署握手** | 连已部署 cloud 发 hello 收 welcome | E | `acceptance/real-e2e.test.ts` `AC-E2E-03` | gated；服务健康 |

### 2.3 边-云端到端 / 跨仓契约

| 验收点 | 层 | 证据 | 通过判据 |
| --- | --- | --- | --- |
| 协议契约一致性 | L | 两仓 `acceptance/protocol-contract.test.ts` 各自穷举 42 消息类型 | 任一端漂移 → 该端 `typecheck` 失败 |
| 发布审批信号契约 | L | edge `buildPublishApprovalSignalPath` 与 cloud `getApprovalSignalPath` 同断言 `/tmp/aidcp-publish-approve-<id>.json` | 两端路径格式一致 |
| 浏览闭环端到端 | S | cloud `integration/role-dispatcher.test.ts` + edge `browse-session.test.ts` | 上报→决策→下发指令链路成立 |
| 发布端到端 | S | edge `integration/publish-e2e.test.ts` + cloud `publish-agent/publish-orchestrator.test.ts` | publish.request→approval→result |
| 真机全链路 | E | 两仓 `acceptance/real-e2e.test.ts`（gated）+ 第 4 节人工清单 | 真实连通 + 真发一条 |

## 3. 新增验收用例说明

| 编号 | 名称 | 仓 | 守护的产品红线 |
| --- | --- | --- | --- |
| `AC-PROTO-01..05` | 协议契约一致性 | edge + cloud | 边/云两份 `protocol.ts` 不漂移（版本 2、42 消息类型、信封往返）；用 `Record<MessageType,true>` 穷举，漂移即 `typecheck` 失败 |
| `AC-PUB-01..08` | 发布审批信号契约 | edge + cloud | 信号文件路径/结构两端一致；**未授权绝不静默发布**（拒绝/超时/串号都不发） |
| `AC-RISK-01..03` | 风控防自残安全闸 | cloud | **绝不自残**：配额硬上限、状态降级（warned 停发布→restricted 停互动→frozen 全停）、致命信号一步冻结，被禁止时 `record` 返回 false |
| `AC-E2E-01..03` | 真机联调（gated） | edge + cloud | 真实边-云连通、握手、心跳；默认跳过，`AIDCP_E2E=1` 触发 |

当前自动化层（L+S）合计 **22 个新增用例 + ~90 个既有测试**，`npm test` 全绿即视为离线/模拟集成层验收通过。

## 4. 真机联调验收清单（人工执行，对应 Phase 1 收尾 / handoff 待办 A）

> 部署铁律：cloud 只在 ECS，本地只起 edge 连 ECS。任何 ECS 操作不得触碰同机 `isales`。

**前置**
1. ECS cloud 健康：
   ```bash
   ssh -i ~/codes/isales-4.pem root@121.89.85.150
   systemctl status aidcp-cloud.service          # active (running)
   ss -ltnp | grep 8787                           # 0.0.0.0:8787 监听
   psql -h 127.0.0.1 -U aidcp -d aidcp -c 'select 1;'
   journalctl -u aidcp-cloud -n 50 --no-pager     # 含"飞书长连接已建立"
   ```
2. 本机 Chrome 调试端口 + 登录小红书：
   ```bash
   chrome --remote-debugging-port=9222 --user-data-dir=~/.aidcp-chrome-profile \
     --disable-blink-features=AutomationControlled
   ```

**验收步骤与判据**

| # | 步骤 | 判据 |
| --- | --- | --- |
| E-1 | `AIDCP_E2E=1 AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm test`（两仓） | `AC-E2E-*` 全过：握手返回 sessionId、心跳 pong |
| E-2 | `AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm start`（edge） | 日志"已连接云端"；自动浏览启动 |
| E-3 | 观察浏览闭环 | edge 上报 `page.cards`/`note.detail`，云端下发 `interaction.like`/`page.scroll`/`navigation.back` |
| E-4 | 触发发布 → 飞书收到审批卡片 | 卡片含标题/正文/标签 + [授权发布]/[取消] |
| E-5 | 飞书点[授权发布] | `/tmp/aidcp-publish-approve-<id>.json` 出现，`approved=true` |
| E-6 | `AIDCP_REAL_PUBLISH=true` 真发一条测试笔记 | `publish.result` 回传 `ok=true` + `postId`；小红书出现该笔记 |
| E-7 | 风控真实拦截 | 配额耗尽/异常时 `risk.canDo` 返回 deny，edge 停手不互动 |

## 5. 验收准出标准

- **离线 + 模拟集成层**：两仓 `npm test` 全绿、`npm run typecheck` 无错（含协议契约穷举）。
- **安全红线**：`AC-RISK-*`（绝不自残）、`AC-PUB-*`（未授权不发布）必须全过。
- **真机层**：`AC-E2E-*` 全过 + 第 4 节 E-1..E-7 人工清单逐项达判据。
- **回归**：任何协议/风控/发布改动后，先跑 `npm run test:acceptance`，再跑全量 `npm test`。
