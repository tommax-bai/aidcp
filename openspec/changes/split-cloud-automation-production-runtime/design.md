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

**2026-07-29 实测起点**（本 session 重新对齐后；**上一版记的 `424834d` 已过期，勿沿用**）：

| 仓 | HEAD | typecheck | 测试 |
| --- | --- | --- | --- |
| `aidcp` | `6a3006a0` | — | — |
| `aidcp-cloud`（事实源） | `babdd84` | — | — |
| `aidcp-kernel` | `d7153b3` | 0 | 57 / 57 |
| `aidcp-transport` | `6cd3339` | 0 | — |
| `aidcp-api` | `02396d8` | 0 | 470 / 470 |
| `aidcp-automation` | `71e5299` | 0 | 1841 pass / 0 fail / 3 skip（共 1844） |
| `aidcp-content` | `d72d653` | 0 | 455 / 455 |

**重新对齐时坐实了一条 pin 纪律的实际后果**（0.2 的产物，记下来免得下次再诊断一遍）：
cloud master 期间前进 4 个提交（`2564f47`/`e009c6f`/`ec4f6dd`/`babdd84`），其中一个改了
`src/kernel/scheduled-automation-catalog.ts` 与 `sync-read-facts.ts`（新增 `contactCommentDailyCap`）。
只跑 `sync-split-repos --apply` 把 src 与 test 同步过去，**automation 立刻 typecheck 红两条**——
同步来的 `test/platform-registry.test.ts` 引用了新字段，而 automation 的 `package.json`
仍 pin 在旧 kernel sha，`node_modules` 里的 kernel 没有那个字段。
**结论：kernel 的 src 一变，「同步」就不是一步而是三步**——
① kernel commit+push 拿到新 sha → ② transport 与三个业务仓的 pin 快进 + `npm install` 刷 lock
→ ③ 才轮到各仓 typecheck / test。跳过 ② 的表现不是「装了个旧版本」而是**当场编译红**，
所以它抓得到；但顺序做反会让人误以为是同步工具搬错了文件。

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

#### B1 的真实闭包（2026-07-29 实测，逐文件核过 import 与消费者）

**改判的不是四个文件，是七个**——四个角色类都 extends 同一个基类，两个 evaluator 还共用一个纯判定模块：

| 文件 | 今属 | 它 import 谁 | 改判代价 |
| --- | --- | --- | --- |
| `src/agents/concept-extractor-role.ts` | content | kernel×2 + `content-role` | 0 |
| `src/agents/valuable-comment-archivist.ts` | content | kernel×2 + `content-role` | 0 |
| `src/agents/curated-comment-evaluator.ts` | content | kernel×2 + `content-role` + `curated-gate` | 0 |
| `src/agents/curated-note-evaluator.ts` | content | 同上 + `curated-content-store`（**type-only**）+ `text-card-transcriber`（**value**） | 见下 |
| `src/agents/content-role.ts`（四者的基类） | content | **只 import kernel** | **0——§10.7 那条零代价机械判据在这里成立** |
| `src/publish-agent/curated-gate.ts` | content | **零 import** | 0 |
| `src/publish-agent/text-card-transcriber.ts` | content | `curated-content-store`（**value**）+ `llm/vision`、`cover-form-sensor`（type-only） | **这一条不成立，见 §2.5** |

**消费者闭包是干净的**（实测全仓扫描）：`content-role.ts` 的消费者**恰好只有这四个角色**；
`curated-gate.ts` 只被两个 evaluator + 组装根消费；`text-card-transcriber.ts` 只被
`curated-note-evaluator` + 组装根消费；四个角色类只被组装根消费。
**改判后 content 侧不留任何悬空消费者**——组装根本来就要三分。

**还有一处「假消边」残留必须一并修**：`curated-note-evaluator.ts` 与 `text-card-transcriber.ts`
的那些类型是从 `../cache/curated-content-store.js` 取的，而那个文件对这些类型只是
`export type { ... } from '../kernel/curated-content-types.js'` 的**再导出壳**——
类型早就抬进 kernel 了，消费方没有改指。扫描器认的是 import 说明符，所以这条边**在账面上仍然存在**
（CLAUDE §8.3：只把属主文件改成再导出、不 repoint 消费方 ＝ 假消边）。
**改判前先把这两个文件的类型 import 改指 kernel**，这条边就地消失，与改判无关也该做。

### 岔口 C · 四个内容属主存储写（争议最小，但有一个已知静默陷阱）

`content-draft-refinement-authority` / `content-facebook-publish-media-authority` /
`content-concept-write-authority` / `content-curated-write-authority`——
四个 content 属主 PG 存储，automation 今天在同进程里直接写。

**建议**：走 content 内部 HTTP 写口，形态与 4a 的 api authority 完全一致；content 已有内部 HTTP
服务端（`AIDCP_CONTENT_PORT`，已注册 persona-generator / curated-content / publish-status /
publish-generation 四组），在它上面扩，不新造监听。

automation 侧需要新增 `AIDCP_CONTENT_URL` 与 `AIDCP_CONTENT_INTERNAL_TOKEN`——
**这是 automation 第一次有 content 方向的出边**，`createAutomationApiClients` 目前 16 组全指向 api。

### 2.5 · 0.5a 的尾巴：文字卡转写器 —— **已于 2026-07-29 由用户裁定＝方案 A**

> **裁决：转写器留 content，automation 经 content 的内部调用口使用。**
> 理由＝它依赖的封面形态感知模块是真·双段共用（组装根在两段各建一个实例，另有两个 content 侧消费者），
> 搬会打断 content、复制会出现两份实现；而转写本身是「输入图片、输出转写」的一次调用，可包成 RPC。
> 下面保留三条完整选项与实测证据，供追溯「为什么不是另外两条」。

**无论走哪条都必须先做的一件事**（不随裁决变化）：把 `?.` 静默吞掉的那两处改成显式能力状态，
让「旗标关掉了」与「依赖没接上」可区分。见下。


**先说清它今天的样子**（实测）：`curated-note-evaluator.ts:145` 与 `:179` 两处都写成
`this.textCardTranscriber?.enabled()`。这正是 CLAUDE §8.5 点名的形态——**可选跨属主依赖缺席，
被 `?.` 静默吞掉**：单体里它恒在，拆开后若漏传，`enabled()` 根本不执行、表达式为 `undefined`、
判定为假，于是整条图内文字转写分支被跳过，而调用方一路拿到「评估成功」。
**「旗标关掉了」与「依赖没接上」在今天的代码里长得一模一样**——这是必须先修掉的，
无论下面选哪条。

**为什么它不能跟着角色一起走**（这是实测推翻了「一并改判」这条直觉）：

- `text-card-transcriber.ts` 值引用 `curated-content-store.ts` 的两个纯函数
  （`normalizeCuratedReferenceImages` / `orderedTextCardTexts`，实测零 SQL）。这两个抬进 kernel 是干净的，
  而且 `orderedTextCardTexts` **本来就还有一个 content 侧消费者**（发布链的封面卡撰写角色），
  不抬就必然出现两份实现。**这一步无论如何都该做。**
- 但它还依赖 `cover-form-sensor.ts`（封面形态感知）与 `llm/vision.ts`（视觉客户端抽象）。
  **`cover-form-sensor.ts` 是真·双段共用**：组装根在 content 段与 automation 段**各建了一个实例**
  （`src/server.ts:3664` 与 `:6479`），另有发布链的封面卡撰写角色与图片形态画像两个 content 消费者。
  搬它会当场打断 content；复制它就是 CLAUDE §8.4 点名的「两份实现各自编译通过、各自测试通过，
  只有真跑起来才对不上」。

| 方案 | 做法 | 代价 |
| --- | --- | --- |
| **A（建议）** | 转写器**留 content**；kernel 里定义窄接口，automation 侧经 content 内部 HTTP 口调用（形态同岔口 C，只是跨过去的是一次调用而不是一次写） | 开启 OCR 时每条带图笔记多一次内网往返。**旗标默认关**，且只对 `image_text` 且有图的笔记触发，属低频。视觉栈整体留在它本来就被共用的那一侧 |
| B | 把 `llm/vision.ts` + `cover-form-sensor.ts` + 转写器整套提进 `aidcp-transport` | 与 A1 同向，形式上也过得了 transport 准入；但封面形态感知含**业务判定**，塞进传输包等于扩大 transport 的语义边界，且它有 content 侧消费者 |
| C | automation 侧明确声明该能力不可用 | 旗标默认关，现状零回归；但等于**放弃**一个已上线能力在拆仓后的可用性。若选它，MUST 在构造期具名记录，不许用 `?.` 假装 |

**A 与「§10.7 端口修不了工厂函数」不矛盾**：那条判据针对的是「构造输入」与「同时需要两个对象的守卫」。
转写器两者都不是——它是一次输入图片、输出转写结果的调用，**天然可包成 RPC**。

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

## 5.5 Phase 0 侦察与对抗性复核的结论（2026-07-29，**覆盖上文若干原判**）

> 六路勘察 + 三路对抗性复核。**12 条 blocker 逐条重放，全部仍成立、无一条已被消解**——
> 而且这不是人工 grep 的结论：cloud 侧 11 条由 `test/acceptance/composition-root-4a-inventory.test.ts`
> 的 AST 派生探针钉住（任一条被端口解决，派生结果会自动少一条、`deepEqual` 当场失败），
> 实跑 6 pass / 0 fail。第 12 条由读 `runAutomationEntry` 源码确认。

### 5.5.1 台账其实有三份，第三份已经静默漂了

| 台账 | 条数 | 性质 |
| --- | ---: | --- |
| `aidcp-cloud/boundaries/composition-root-independent-blockers.json` | 52 | **AST 派生、自熄**——依赖真被解决就自动消失 |
| `aidcp-automation/src/automation-composition-root.ts` 的 TS 常量 | 12 | **手写**，无任何机械锚 |
| `aidcp-automation/boundaries/composition-root-independent-blockers.json` | **20** | **手写台账的陈旧快照，全仓零读取点** |

第三份多出的 8 条是 4b 已关闭的镜像项：TS 常量在 `842f56c` 删了 8 条，JSON 自 `e62c71f` 后再没重生成，
而它**没有任何消费者**（automation 全仓只有一个 `--refresh-ledger` 写出点，零读取点）。
**这解释了「为什么会漂」：automation 那侧压根没有任何机械力量把台账钉在现实上。**
所以 tasks §4「两份台账同批收缩」实际是**三份**，且必须一并给 automation 的台账加机械锚，
否则清零之后它照样会再漂一次。

### 5.5.2 岔口 C 要改：一条撤掉、两条补方法、两条补进台账

- **`content-draft-refinement-authority` 应撤出岔口 C**：`src/server.ts:6171` 的守卫是
  `seamMode !== 'automation' && ...`，那个 worker 在 automation 模式下**本来就不跑**；
  该条剩下的两条证据（`segA:new:DraftRefinementStore` / `segD:identifier:draftRefinementStore`）
  **都是 api 侧**。automation 方向的现存 runtime 边为零，**不该开 automation→content 写口**。
- **概念池端口面是 6 个方法不是 3 个**：除 `addCandidate` / `loadPool` / `markSearched`，
  还有 `countNewSince` / `getNewConceptsSince` / `getNewConceptsWithSourceSince?`
  （`aidcp-automation/src/publish-agent/publish-scheduler.ts:34-39`）。
  `getNewConceptsSince` 尤其危险——它是**回落分支**，漏了只有回落时才炸。
- **精选库还有跨界读**：`selectForCreation`，两个调用方（`PublishScheduler` 与 `CommentScheduler`），
  且**投影形状不同**。今天 `server.ts:7024` 已有 `: Promise.resolve([])` 这种降级形状——
  跨进程后它会把「连不上」也吃成「没有精选素材」，必须换成可区分的结果。
- **`server.ts:4986` 与 `:5311` 只把 store 当「有没有」用**（就绪闸）。跨进程后
  MUST 换成显式可用性查询，不能靠对象是不是 `undefined` 来判。

### 5.5.3 三条探针不具判别力（**摘 blocker 会变成假动作**）

`content-concept-write-authority` / `content-curated-write-authority` /
`content-facebook-publish-media-authority` 三条的 segC 探针都是 `kind: 'identifier'`，
而 `src/server.ts:3900` 是 segCAutomation 开头**一整行解构**，里面同时含这三个名字。
**把所有真实调用点改成 HTTP 客户端后，只要那行解构还在，三条探针照样命中**；
反过来，删掉解构里的名字、真实调用还在，探针就静默放行。
**改法要与 census 探针一起定，否则「台账清零」证明不了任何事。**

### 5.5.4 B1 顺带消掉了两条谁都没记的边（这是 B1 正确的额外证据）

- `resolveCuratedGateConfig`（`src/publish-agent/curated-gate.ts`，content）在 segC 的
  `server.ts:7225` 被调，automation 仓里没有这个文件。**任何 blocker 都没记它。**
  B1 把 `curated-gate.ts` 随四个角色迁到 automation，这条边就地消失。
- **一条反方向的边**：content 角色 `valuable_comment_archivist` 写的
  `valuableCommentStore`（`src/cache/valuable-comment-store.ts`）属主是 **automation**
  ——即「content 角色写 automation 属主表」，与岔口 C 的四条方向全反，台账里也找不到它。
  B1 把该角色改判 automation 后，这条反向边同样消失。

### 5.5.5 文字卡 OCR 整条子链在 segC 构造，且完全不在 12 条台账内

segC（3899–7787）内构造、但属主全是 content、automation 仓里全都没有的：
`OpenAiCompatVisionClient` ×2（6473 / 6486）、`createCoverFormSensor`（6479）、
`createTextCardTranscriber`（6493）、两个 provider/model 解析闭包（6460 / 6461），
另有 `new PersonaGenerator`（5290）、`new ReplyAiService`（4693）、`hasUserRejectionEvidence`（7506）。
**这些都要补进台账**——否则台账清零了，automation 仍然起不来。

### 5.5.6 「静默吞掉」不止 0.5a 那一处，同形共四层

1. `curated-note-evaluator.ts:145` / `:179` 的 `this.textCardTranscriber?.enabled()`（0.5a 本体）。
2. **`CuratedNoteSink` 的两个可选方法**`refreshReferenceImages?` / `getTextCardContext?`，
   调用点 `:153` / `:182` 都用 `?.`。岔口 C 一旦把这条 Sink 换成 content HTTP 客户端，
   **客户端少实现一个方法：编译通过、运行不报**。少 `getTextCardContext` → 缓存恒空 →
   每篇图文帖每次重跑视觉转写（**纯成本爆炸、零错误信号**）；少 `refreshReferenceImages` →
   多打一次 LLM 全量评估。
3. `CoverFormSensor.senseAt?` 可选，缺席时降级成 `{status:'error'}` →
   没有任何图被判为文字卡 → **转写产出空、不抛、不 warn**。
4. `ContentRoleOptions` 的 `soul?` / `getSoul?` 两者皆缺时**构造期不报**，
   第一次读才抛，而读它的位置在 fire-and-forget + try/catch 里 → **静默不纳入**。
   `llmTimeoutMs?` 缺席则静默回落共享天花板、per-role deadline 悄悄消失
   （且角色调度器的公共选项**本来就不传它**）。

**另一条必须记住的事实**：转写器在今天的单体里是**无条件构造、无条件注入**的
（`server.ts:6493` / `:6761`），旗标只作为回调传进去、在内部判。
所以 `server.ts:116` 那个条件展开的 false 分支**生产上从未走过**——
**「漏传」这个失败态只可能由本次拆仓引入**，现有测试不可能覆盖它。
新用例应作 `AC-TCT-3` 加进已有的 `test/acceptance/text-card-transcription-honesty.test.ts`。

### 5.5.7 四条运营指令：两条判错、一条通道其实不存在、一条已写好只差接线

- **「飞书调度启停」这条通道自始至终不存在。** `feishu/command-face.ts` 组装的动作全集是
  `status / pause / resume / bindChat / delegate / publish / comment`，**没有 dispatch**。
  那个 `:dispatch` 文案只服务**面板路由**与 dashboard 状态灯。
  台账那两条证据是同一条通道的两个证据，不是两条通道。
  **好消息**：一条 paired command 一次接线即同时点亮面板按钮与状态灯，飞书侧零改动。
- **委托卡片动作的处理器其实是 api 属主**（`src/feishu/` 整目录 15/15 归 api）。
  方向仍是 api→automation（缺的是服务端口注入），但**没有任何代码需要搬家**。
- **委托的跨进程通道已经写好了**：`aidcp-automation/src/transport/delegated-task-http.ts`
  同时有服务端注册与客户端、7 个路由方法齐全，文件头明写「不接线、不改默认注入」。
  cloud 全仓对这两个符号零消费。**这条离关闭只差一次接线。**
- **委托服务在 api 侧有三个消费者**（飞书入站 `8316`、面板 `8615`、客户端 API `9157`），
  后两个走 `DataGateway`。而 `DataGateway` 在 `8539-8563` 已经预留了 remote thunk 的位置。
  **paired command 与 DataGateway remote 是同一件事的两种做法，MUST 二选一**——
  两条都建会出现「飞书走一条、面板与客户端 API 走另一条」的分叉，而两者的鉴权、
  target 校验、错误归一都不同。
- **批 B 有一个前置改动**：`feishu/command-face.ts:27-35` 自带的那份 `PanelCommandActions`
  两个方法都是**必填**，而 `panel/types.ts:270/275` 那份是**可选**。api 因此被迫必须传一个函数——
  「诚实地不注入」在类型层做不到，只能在「抛错」与「撒谎」之间选。
  要先把前者改成可选（顺带消掉两份同名类型的漂移）。

### 5.5.8 岔口 A：**裁决成立，但 0.4 记的理由有一条是错的**

- **模型客户端本身干净**：`src/llm/qwen.ts` 548 行，SQL / 连接池 / 存储引用全部零命中，
  import 只有两条且都指 kernel。transport 准入（三家都可能调用 + 不含属主表 SQL）成立。
- **`AIDCP_SERVICE=automation` 今天已经在建它**：`gateway/service-mode.ts:71-84` 五种模式
  `segA: true` 无一例外。A1 不是新增需求。
- **⚠️ 0.4 写的「密钥各自从 env 读」与生产事实不符。** 真实做法是**库内优先、env 回退**
  （`server.ts:2295-2297` 与 `:2337-2341` 走 `credentialStore.getSecretForRuntime`），
  且 content 的手写 main **已经**改成经属主侧窄读口取（`aidcp-content/src/server.ts:421-428`）。
  **按 0.4 字面实施，后台「厂商密钥」页面对 automation 进程彻底失效，且无任何信号。**
  → **更正**：各服务照 content 手写 main 的做法，经属主侧窄读口取（库内优先、env 回退），
  **MUST NOT 复刻四层回落逻辑**（content 那份的注释原话：「复刻正是两侧悄悄不一致的来源」）。
  裁决的**实质不变**（模型出口进 transport、三家各自 new、热路径不加跳），变的只是取密钥的方式。
- **视觉客户端与模型客户端不可随意分家**：`src/llm/vision.ts:19-24` 从 `qwen.ts` 取
  **5 个错误族符号**。qwen 进包而 vision 留 content，两边就各持一份 `ProviderKeyMissingError`，
  跨副本 `instanceof` 会静默退化，把「密钥没配」报成「模型不可用」。
  → **落点**：`vision.ts` 的消费者**全是 content**（视觉分析 / 保真核验 / 封面形态 / 文字卡转写），
  所以 **vision 留 content**；把**错误族抬进 kernel**（`ProviderKeyMissingError` / `LlmErrorMeta` /
  `buildLlmHttpError` / `buildLlmApiError` / `buildLlmShapeError`，共 53 行）——
  四条准入正则**实跑全 CLEAN**，且 CLAUDE §8.4 明写 kernel 现有导出类全是错误类型，形态吻合。
  一份定义 ⇒ `instanceof` 跨进程仍然成立。
- **`src/llm/providers.ts` 进不了 kernel**：厂商 base URL 字面量当场命中
  「LLM 或供应商 HTTP 调用」那条正则（正则**只剥注释、不剥字符串字面量**）。它随 qwen 进 transport。
- **automation 对模型的真实需求面只有单方法 `complete`**（角色调度器只注入 `{ complete }`，
  automation 全仓零 `.chat(`）。

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
