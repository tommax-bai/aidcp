# Design · automation 独立生产运行时

> **接手先读 §0，再读 §2 的三个岔口。§2 未裁决前不要写代码。**
> 本文所有数字与位置都是 2026-07-29 本机实测，但 fleet 活跃——**一律自己重跑一遍再信**。

## 0. 接手第一件事：核对现状

```bash
cd /Users/baitianxing/codes/aidcp
git branch --show-current                      # 必须是 main
./scripts/task-preflight                       # 四个 canonical checkout 都在默认分支才放行
ls -d ../aidcp-cloud ../aidcp-api ../aidcp-automation ../aidcp-content ../aidcp-kernel ../aidcp-transport
./scripts/sync-split-repos --ref origin/master --tests    # 除组装根外应零差异
openspec status --change split-cloud-automation-production-runtime
```

**2026-07-29 的起点**（六仓已对齐 `aidcp-cloud@424834d`，五个派生仓首次同时全绿）：

| 仓 | HEAD | typecheck | 测试 |
| --- | --- | --- | --- |
| `aidcp` | `0788501d` | — | — |
| `aidcp-kernel` | `6bf0603` | 0 | 57 / 57 |
| `aidcp-transport` | `eeb6b3e` | 0 | — |
| `aidcp-api` | `6181771` | 0 | 470 / 470 |
| `aidcp-automation` | `21dfe08` | 0 | 1832 pass / 0 fail / 3 skip |
| `aidcp-content` | `b4b1bf6` | 0 | 455 / 455 |

**依赖装不上这条坑已经解决**：四个新仓的 `npm install` 会被内网 registry 对 `@types` 域的劫持打断，
绕法是 `npm install --userconfig /dev/null --no-audit --no-fund`。在此之前所有「已验证」都只是「看着对」。

### 0.1 三个仓的入口现状（别弄反）

| 仓 | 入口 | 现状 |
| --- | --- | --- |
| `aidcp-api` | `startApiService()`（`src/server.ts` 末尾） | **真入口**。owner routes + sync-read 三组 + 飞书入站；业务入口由 `startBusinessIfReady()` 闸在 `syncRead.consumer.readiness().state === 'ready'` 之后 |
| `aidcp-content` | `main()`（`src/server.ts` 末尾） | **真入口**。发布编排器 + 内部读 API（persona-generator / curated-content / publish-status / publish-generation），监听 `AIDCP_CONTENT_PORT` |
| `aidcp-automation` | `runAutomationEntry()` | **有意 fail-closed**：`readAutomationRootConfig(env)` 后直接 `throw new AutomationRootNotReadyError(...)`。`createAutomationCompositionRoot()` 是 4a/4b 的**有界**工厂，可加载可单测，但不是生产运行时 |

`aidcp-automation/src/server.ts` 只有 17 行，是薄壳：直接执行时调 `runAutomationEntry()`，
失败打一行 `startup_blocked` 结构化日志并置 `exitCode=1`。**这层壳是对的，不要改它的诚实语义。**

### 0.2 台账在哪、长什么样

- **权威副本**：`aidcp-cloud/boundaries/composition-root-independent-blockers.json`
  （`change: split-cloud-api-composition-root-4a`，`claimBlocked: true`，共 **52 条**）。
  每条带 `id / category / owner / consumer / closingChange / evidence[]`，
  evidence 是 `src/server.ts#segCAutomation:identifier:llm` 这种 **file#符号** 定位，不是行号。
- **派生仓收窄副本**：`aidcp-automation/src/automation-composition-root.ts` 的
  `AUTOMATION_ROOT_READINESS_BLOCKERS`，**12 条**——只含「阻止本仓交付完整生产 automation 进程」的那些。

52 与 12 的差别不是漏记：另外 40 条里，**27 条是单体 segA 的共享组装根问题**
（api 属主 store 被 automation/content 段共用），在派生仓里已由 4a 的 16 组 api HTTP 客户端解决；
13 条是 4b 的镜像，已由 4b 关闭。**清账时对着 12 条那份，别对着 52 条那份。**

12 条按类别：

| 类别 | 条数 | 属主 → 消费 | 本 change 的落点 |
| --- | ---: | --- | --- |
| `operator-command` | 4 | automation → api | §1 |
| `content-owner` | 7 | content → automation（其中 5 条 api 也消费） | §2 / §3 |
| `composition-root` | 1 | automation | §4 |

## 1. 四条运营指令通道（`operator-command` × 4）

飞书**入站**整组判 api 属主（§10.3），但这四条指令的处理器在 automation。单体里它们是同进程调用，
拆开后 api 侧只能打出 `automation_operator_command_unavailable` 文案。

| blocker id | 证据（cloud `src/server.ts` / `src/feishu/api-owner-composition.ts`） |
| --- | --- |
| `feishu-operator-natural-language-delegate` | `segDApiServing:text:automation_operator_command_unavailable:delegate` |
| `feishu-operator-publish-comment` | 同上 `:publish` 与 `:comment` 两处 |
| `feishu-operator-delegated-card-actions` | `call:handleDelegatedTaskCardAction` + 同名文案 |
| `feishu-operator-dispatch-start-stop` | 同上 `:dispatch`；另有 `src/panel/panel-server.ts#call:deps.commandActions.dispatch` |

**形态照抄 4a 的 paired command**：automation 已有三个 receiver（`edgeResume` / `facebookScope` /
`publishUiUpdate`，见 `AUTOMATION_COMMAND_RECEIVER_GROUPS`）+ `registerXxxCommandRoutes`，
api 侧有对应 client。新增四条按同一形状扩，**不新造第二套机制**。

**两条必须守住的判据**：

1. **意图解析留在 automation。** 自由文本 `/delegate` 的入口方法在 4a 的委托端口方法面里
   **原本就漏了**（路由表只有 7 条、kernel 接口也只有 7 个方法，`createFromText` 不在其中——
   §10.6 automation 判错第 4 条）。api 侧 MUST NOT 自己拼 intent 再调结构化入口：
   那会把「解析错了」变成 api 的沉默行为，而所有的解析规则与语料都在 automation。
2. **面板的 dispatch 启停与飞书那条是同一条命令，不是两条。** `panel-server.ts` 的
   `deps.commandActions.dispatch` 与飞书 `:dispatch` 指向同一处理器；开两条 route
   会出现两份幂等键空间，重启后互相看不见对方在跑什么。

## 2. 三个岔口 —— **A / B 已于 2026-07-29 由用户裁定**

> **裁决结果（用户 2026-07-29）**
>
> - **岔口 A ＝ A1**：模型调用出口**提进 `aidcp-transport`**，三家各自 `new` 一个、密钥各自从 env 读。
> - **岔口 B ＝ B1**：四个内容属主角色工厂**改判归 automation**，它们对 content 存储的写走 §3 的写口。
> - **岔口 C**：按建议走 content 内部 HTTP 写口，在既有 `AIDCP_CONTENT_PORT` 监听上扩，不新造监听。
>
> 下面保留三条的完整选项与代价，供实施时追溯「为什么不是另一条」。

这三条都不是「加个 HTTP 客户端」，而是**归属裁决**。历史上同一类岔口出现过一次（§10.7 发帖调度器），
当时的判据值得复用：**端口修不了「同时需要两个对象」的守卫**，也修不了「需要一个工厂函数」的构造。

### 岔口 A · 模型调用出口（`content-generic-llm-authority` + `content-token-usage-authority`）

单体在 segA 建一个模型客户端，同时喂给 automation 段与 api 段
（evidence：`segAApiFoundation:new:QwenClient` / `segCAutomation:identifier:llm` / `segDApiServing:identifier:llm`）。
automation 的 37 个角色全部靠注入的模型接口工作。

| 方案 | 做法 | 代价 |
| --- | --- | --- |
| **A1（建议）** | 模型 HTTP 出口进 `aidcp-transport`，三家各自 `new` 一个，密钥各自从 env 读 | 符合 transport 准入判据（三家都可能调用 + 不含任何属主表 SQL）；热路径不加跳。需一次搬迁 + 三仓 pin |
| A2 | 每次模型调用经 content 的 HTTP 转发 | 一份实现，但给**每一次**模型调用加一跳内网 + 大 payload 往返，content 成为全域模型瓶颈与单点；与「单次模型调用天花板 180s」的看门狗联动更难判因 |
| A3 | automation 自建一份 | 两份实现必然漂移。CLAUDE §8.4 点名过这种形态：两侧各自编译通过、各自测试通过，只有真跑才发现对不上 |

**token 用量记账是另一件事，不要跟着一起裁。** 它写的是 **content 属主表**，且是低频旁路，
走 content 的 HTTP 写口即可（形态同 §3）。注意 memory `token-cost-from-billing-not-price-table`：
成本 MUST 由厂商账单反算，**禁止**在这一层硬编码价目表。

### 岔口 B · 四个内容属主角色工厂（`content-role-factories`）

`CONTENT_ROLE_FACTORIES`（cloud `src/server.ts:108`）注册四个角色：
`concept_extractor` / `valuable_comment_archivist` / `curated_note_evaluator` / `curated_comment_evaluator`。
它是 automation 角色调度器的**构造输入**——一张工厂函数表。

| 方案 | 做法 | 代价 |
| --- | --- | --- |
| **B1（建议）** | 把这四个角色类的归属改判到 automation，写口走 §3 | 与 §10.7 同形：工厂函数包不进 HTTP。需改控制仓 `docs/cloud-service-decomposition-proposal.md` §4.x 再回写 `ownership-rules.json`（CLAUDE §8.1：归属的事实源是文档不是规则表） |
| B2 | content 侧起第二个角色调度器，跨进程事件接力 | 与「浏览闭环由 automation 单一调度器驱动、角色间纯靠进程内事件总线接力」正面冲突，要造跨进程事件总线。不建议 |

**B1 有一个必须一并裁的尾巴**：`curated_note_evaluator` 的工厂接受**可选**的
`textCardTranscriber`（content 属主的视觉行为类，旗标默认关，见 memory `textcard-ocr-content-gap`）。
可选依赖漏传**不编译失败、不报错**——见 §5 的第一条陷阱。要么一并改判，要么显式走 content 的调用口，
**不许默默不传**。

### 岔口 C · 四个内容属主存储写（争议最小，但有一个已知静默陷阱）

`content-draft-refinement-authority` / `content-facebook-publish-media-authority` /
`content-concept-write-authority` / `content-curated-write-authority`——
四个 content 属主 PG 存储，automation 今天在同进程里直接写。

**建议**：走 content 内部 HTTP 写口，形态与 4a 的 api authority 完全一致；content 已有内部 HTTP
服务端（`AIDCP_CONTENT_PORT`，已注册 persona-generator / curated-content / publish-status /
publish-generation 四组），在它上面扩，不新造监听。

automation 侧需要新增 `AIDCP_CONTENT_URL` 与 `AIDCP_CONTENT_INTERNAL_TOKEN`——
**这是 automation 第一次有 content 方向的出边**，`createAutomationApiClients` 目前 16 组全指向 api。

## 3. 落地形态（裁决后）

- content 属主写口一律**只报真态**：写了几行就返回几行，失败按结构化原因返回。
  MUST NOT 把「传输失败」染成「领域上没有这条」——这是 3b 已经写进规格的一条
  （`cloud-api-automation-bidirectional-ports`「传输失败不得改变领域结局」），此处照守。
- 跨进程后 `instanceof` 恒 false。所有跨边界的错误识别 MUST 改结构化守卫（按 `name` + 具名字段判），
  否则会静默退化成兜底原因、吞掉真实失败（CLAUDE §8.5）。
- 新增契约的「服务端注册 + 客户端 + 路径常量」三件套 MUST 进 `aidcp-transport`，
  **不许两端各写一份**：两侧各自编译通过、各自测试通过，只有真跑起来才 404。

## 4. automation 生产运行时（`automation-production-runtime-composition-unwired`）

真 `main()` 要装配的（以 automation 属主的 227 个 src 文件为准，逐段对着 cloud `segCAutomation` 核）：

- 边-云 WebSocket 服务端（`src/comm/ws-server.ts`，对外 8787）与协议处理器；
- 进程内事件总线 + 角色调度器（37 角色注册；含按开关注册的那几个）；
- 风控单写者（状态机 + 配额）；
- 评论 / 首作 / 通知巡视等调度器与监测体；
- 4a 的 16 组 api 客户端 + 4b 的同步读镜像 + 本 change 的 content 客户端组 + 四个指令 receiver。

**启动 gate 与 api 同形**：同步读镜像首次装载完成、readiness 到 `ready` 之前**不放行业务入口**
（api 的做法是 `businessIngressStarted` 闸，见 `startBusinessIfReady`）。
**缺依赖 MUST 停在具名原因上**，MUST NOT 以空值 / `false` / 默认值放行——
这正是现在那个 fail-closed 壳在替我们守的东西，接线时不能把它守的东西一起删掉。

**端口与隔离**：automation 内部端口默认 `8093`（`AIDCP_AUTOMATION_PORT`）；
边-云 8787 与面板 8090 各有其主，**不要在本 change 里动它们的归属**。
所有后台扫描 / 认领 / 重试 / 恢复类持久任务仍按 `AIDCP_DEPLOY_ENV` 写 `execution_target`，
target 缺失或非法时**不启动那个 worker**（CLAUDE §2）。

## 5. 已知陷阱（每一条都真的踩过）

1. **optional 实参漏传不会编译失败。** `PublishDispatcher` 的第三个跨属主实参
   `FacebookPublishMediaStore` 是 optional：漏传不报错，只是 FB 发帖素材的预留释放 / 标记已用 /
   隔离三个写**全部静默消失**（预留泄漏 + 图片可能被重复选用）。§10.6 automation 判错第 1 条。
   **传递性检查 MUST 做，且 optional 参数是最难发现的形态。**
2. **复核自己也会错，MUST 逐条验。** §10.6 里最严厉的那条（委托执行链启动守卫「没有 else、没有 warn」）
   **证据是错的**——那里确实有 `else if (...) console.warn(...)`。但**结论方向仍成立**：
   告警只在启动时响一次，之后每条委托任务照常被接收、落库、永不执行，收任务那侧没有任何提示。
3. **`ReplyWorkflow` 的第三个实参是 content 属主的具体类**，不是模型客户端本身。
   就算岔口 A 裁成 A1，这个类仍然是 automation 仓里没有的东西，要单独处置。
4. **别在 `boundaries/` 上抄错方向。** 同目录两种相反规则：`module-ownership.json` 按本仓实际文件
   **收窄**（照抄云端全量会多出几百条陈旧条目）；`table-ownership.json` 是**全量生成物**。
   两者都 MUST 手工 Edit 增量追加，**绝不脚本整体重序列化**（CLAUDE §8.2）。
5. **加迁移不是搬一个文件。** 迁移与「收窄后的 schema 契约两个常量」「表归属登记」是一个耦合单元；
   只搬迁移会让该仓「已知最高版本 = 目录里最高版本」当场破。同步工具已能对账，但**搬动仍只报不改**。
6. **测试归属看两类证据。** import 说的是需要谁的代码，字面路径读说的是需要哪些文件在场。
   新写的验收测试若按路径读别属主的迁移或读组装根，它就**不可能**派进派生仓——
   要么用 import，要么明确让它留守 cloud。

## 6. 热点文件：需串行，不与并行 session 同时碰

- 两份 `protocol.ts` + `aidcp-cloud/src/comm/command-bridge.ts` 的动作映射（协议四处同步）；
- 角色注册（`src/event-bus/types.ts` 的 `RoleName` + `src/config/role-catalog.ts`）；
- 风控状态机 `src/risk/risk-state-machine.ts`；
- **本 change 独有**：`aidcp-automation/src/automation-composition-root.ts` 与
  `aidcp-cloud/boundaries/composition-root-independent-blockers.json`——
  台账两份必须同批收缩，任一单改都会让门禁与现实对不上。

## 7. 验收分层（**混层就是假成功**）

| 层 | 证明什么 | **不证明**什么 |
| --- | --- | --- |
| loopback HTTP 契约测试 | route / client 的方法面、鉴权、target 校验、失败语义 | 对面进程真的起得来 |
| dev 单体部署（`aidcp-cloud`） | 现网零回归 | 三进程能互相说上话 |
| **三进程真跑** | 本 change 生效 | 真实平台行为（那是真机项） |

**只有 api / automation / content 三个独立进程都启动并互相说上话，才能声称本 change 生效。**
三进程真跑属批次 5，本 change 只交付「automation 进程自己起得来且诚实」；
凡本地桩验不了的，登记 `docs/real-machine-acceptance-backlog.md`（簇 60）。

## 8. 与 `add-managed-automation-runtime` 的关系

那个 change 在运行模型层取代约 60 份已上线 spec，用户 2026-07-25 裁定「重叠处以本方案为准」。
**本 change 与它不冲突**：本 change 处置的是**进程装配与跨进程通道**（谁在哪个进程里被 new 出来），
不改任何自动化业务语义。动到排期 / 配额 / 仲裁 / 审批语义时，先查那个 change 的 `design.md` §24 处置映射表。
