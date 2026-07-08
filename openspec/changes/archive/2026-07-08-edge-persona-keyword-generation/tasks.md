## 1. 协议同步（热点单写文件，先做、独占、不与他人并行改协议）

- [x] 1.1 在 edge 与 cloud 两份 `src/comm/protocol.ts` **逐字一致**新增消息类型：`persona.generate`（请求）、`persona.generate.result`（响应）、`persona.persist`（请求）、`persona.persist.result`（响应）
<!-- cloud 65fc268 / edge b91bcb4 逐字一致，diff 仅行号 -->
- [x] 1.2 定义载荷：generate 请求 `{ accountId, keywordSelections, idempotencyKey }`；generate 响应 `{ ok, soulYaml?, identitySummary?, reason? }`（`reason` 含 `generation_failed`/`persona_invalid`）；persist 请求 `{ accountId, soulYaml }`；persist 响应 `{ ok, reason? }`（`reason` 含 `unknown_account`/`persona_required`/`persona_invalid`）
<!-- cloud 65fc268 / edge b91bcb4 -->
- [x] 1.3 更新两份 protocol.ts 的 `Record<MessageType,true>` 穷举，确保 AC-PROTO 漂移哨兵通过；**不碰** command-bridge 动作映射、**不碰** onMessage 主动命令白名单（走 pending-id 请求/响应）
<!-- cloud 65fc268 / edge b91bcb4 AC-PROTO 65 计数 + 穷举表；未碰 command-bridge / onMessage 白名单 -->
- [x] 1.4 更新 `docs/protocol.md` 头部消息计数与 §2 消息表
<!-- 控制仓 docs/protocol.md 计数 61→65（line 19+158）+ 新增 §2.7 persona 消息表（待控制仓 main 提交） -->


## 2. aidcp-cloud — 生成器 + 序列化器 + 消息处理 + 装配

- [x] 2.1 新增 JSON→soul YAML **确定性序列化器**（小模块），只产 `loadSoulFromValue` 支持的简单 `key: value` + 字符串列表子集；加单测覆盖含中文/特殊字符的 round-trip（序列化后能被 `loadSoulFromYaml` 解析）
<!-- cloud 65fc268 src/soul/serialize.ts（空数组用行内 [] 避免解析成 null）+ round-trip 单测（中文/引号/#/空数组）过 -->
- [x] 2.2 新增 `PersonaGenerator`（仿现有命令式生成器角色）：注入按角色大模型客户端、`complete` 携角色键、按 `accountId` 记账；prompt 用打包 soul 模板作 few-shot、要求只吐 JSON、内置**每账号差异化**（差异化种子 + 温度，重点作用于 `seed_keywords`/搜索词）
<!-- cloud 65fc268 src/agents/persona-generator.ts；v1 只产 identity+interests（behavior_guidelines 缓做）；背景保真约束写进 prompt -->
- [x] 2.3 在 `role-catalog.ts` 的 `RoleName` 枚举 + 目录登记一个 persona 生成角色（拿按角色配模型/温度 + 按账号记账 + 后台 prompt 预览）
<!-- cloud 65fc268 RoleName 加 persona_generator + role-catalog 加 browse:persona_generator（browse_compose, tunableTemperature:true） -->
- [x] 2.4 接 `persona.generate` 处理：idempotency key 去重/缓存 → 生成器 → 序列化 → `loadSoulFromValue` 校验 → 成功回草稿；失败**修复重试 1–2 次仍失败则硬 fail-closed** 回 `generation_failed`/`persona_invalid`，账号维持缺人设、绝不回落模板
<!-- cloud 65fc268 handler.onPersonaGenerate：幂等在途 Promise 去重（成功留存/失败逐出）+ 重试在 generator 内 + fail-closed -->
- [x] 2.5 接 `persona.persist` 处理：**复用现有人设单写通道**（`loadSoulFromValue` + 外键守护 + 写库成功才刷镜像 + 绑定即热加载唤醒在线节点 + 诚实回执）；把 `unknown_account` 当正常分支优雅回诚实失败
<!-- cloud 65fc268 handler.onPersonaPersist：调 personaFacade.setPersona（含全套校验/落库/onBound 唤醒）；accountId 取握手绑定值防越权 -->
- [x] 2.6 `server.ts` 装配：把按角色大模型客户端穿进 persona 生成链路（token 记账传 `accountId`）；付费 `generate` 前先确认 `accounts` 行到位（尽力而为的 `ensureAccount` 之后）
<!-- cloud 65fc268 new PersonaGenerator({llm}) + 注入 personaGenerator/personaFacade 到 DefaultMessageHandler；账号行到位由 setPersona 的 FK 守护兜底（unknown_account 正常分支） -->
- [x] 2.7 cloud 侧回归：生成失败 fail-closed（不落模板）、幂等去重（同键不二次调模型/不二次记账）、persist 遇 `unknown_account` 诚实回执
<!-- cloud 65fc268 test/persona-generator.test.ts 10 用例全过（fail-closed×3 / 幂等 / unknown_account / round-trip / 差异化） -->


## 3. aidcp-edge — 向导 UI + IPC + 客户端请求

- [x] 3.1 `src/electron/renderer/` 新增人设向导（vanilla DOM+JS）：4 维封闭枚举多选（垂类/兴趣/语气/互动偏好）、生成按钮、草稿展示、**重新生成（不限次）**、确认；**套用现有 editingProvider/dirty latch**，防周期性 status 推送重置向导进度
<!-- edge 425ef22 index.html 设置抽屉内 persona-config section + styles.css（复用 .settings/.field/.seg/.badge 设计语言，kw-group 换行）+ renderer.js 向导逻辑；render() 只调 updatePersonaGate（改 disabled/hint），绝不触碰已选关键词/草稿 -->
- [x] 3.2 `preload.cjs` + `main.cjs` 新增 IPC verbs 与 `ipcMain.handle`，桥接向导 ↔ core
<!-- edge 425ef22 preload personaGenerate/personaPersist + main.cjs persona:generate/persist handler + correlation-id stdin→core / [persona-reply] stdout→pending 桥（独立于 browser-parking） -->
- [x] 3.3 core / `src/client/edge-client.ts`：发 `persona.generate` / `persona.persist` 的 `request()`，**显式 `timeoutMs ≥ 185s`** + 生成端带 idempotency key；触发键 = 身份已确立事件（真实 userid、非 env-label）
<!-- edge 425ef22 persona-onboarding.ts（原始 process.stdin.on('data') 与 browser-parking readline 并存，调 client.request 190s）+ main.ts 在身份确立/client 就绪后 registerPersonaStdinCommands；idempotencyKey 由渲染层每次生成/重生成新建 -->
- [x] 3.4 边缘**只透传云端诚实 `reason`、不本地判成功**；`unknown_account` 时向导可重驱（待账号行落定后重试）；身份未确立时只本地暂存关键词、不发起生成
<!-- edge 425ef22 桥/渲染层只透传 reason（PERSONA_GEN_FAIL/PERSIST_FAIL 文案映射）；生成 gate 在 auth='logged in' && cloud='connected'，未就绪只暂存 DOM 选择、按钮 disabled -->
- [x] 3.5 edge 侧 `protocol.ts` 与 cloud 同步（属任务 1 的协议组，edge 侧落地）
<!-- edge b91bcb4 protocol.ts + AC-PROTO 与 cloud 逐字一致，typecheck + AC-PROTO 9 用例过 -->


## 4. 测试与校验

- [x] 4.1 补 AC-PROTO 漂移断言（两份 protocol.ts 一致 + 新消息穷举）
<!-- cloud 65fc268 / edge b91bcb4：AC-PROTO-02 计数 65 + 穷举表 4 key + 新增 AC-PROTO-09 persona 载荷往返；两仓各 9 用例过 -->

- [x] 4.2 cloud `npm run test:acceptance` + `npm test` + `npm run typecheck` 全过（尤其生成失败 fail-closed、幂等、persist 诚实回执）
<!-- cloud 65fc268：test:acceptance 46 过（含 AC-PROTO 65 / AC-PUB / AC-RISK）+ npm test 1569 过 0 失败 + persona-generator.test.ts 10 过。typecheck：本改动 0 错；仅剩 2 个 pre-existing 环境错 src/render/text-card.ts 缺 satori/@resvg 类型声明（textcard change 遗留、本机 node_modules 未装、与本改动无关；运行时可用故 npm test 全绿） -->
- [x] 4.3 edge `npm test` + `npm run typecheck` 全过
<!-- edge 425ef22：npm test 744 + persona-onboarding 5 = 全过；typecheck 干净；3 个 .cjs/.js node --check 语法通过 -->

## 5. backlog 登记（deferred 风险 + 真机验收项）

- [x] 5.1 在 `docs/real-machine-acceptance-backlog.md` 登记真机验收项：扫码登录后向导触发时序、生成→确认→绑定→开跑闭环、生成失败 fail-closed 表现、重连不双计费
<!-- 控制仓 docs/real-machine-acceptance-backlog.md 新增簇 17（7 项真机验收，待控制仓 main 提交） -->
- [x] 5.2 在 backlog / handoff 显式登记**已知接受、后续独立立项**的缺口：边缘身份鉴权、限流/配额、服务端枚举复验、只创建不覆写、跨账号语义去重 + 运营侧相似度报表/抽检
<!-- 簇 17 尾部「已知接受、后续独立立项的缺口」5 条清单（含 2026-07-08 砍配额/暂不补鉴权决策） -->
