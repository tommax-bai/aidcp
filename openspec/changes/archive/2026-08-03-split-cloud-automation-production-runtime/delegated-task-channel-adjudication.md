# 1.4d 裁定调研 · 委托任务通道选哪一条（含 1.3 / 1.5 落地方案）

> 调研日期 2026-07-29～30。**所有行号 pin 在 `aidcp-cloud@1b36b74`（分支 `codex/split-cloud-automation-production-runtime` 当时的 HEAD）**，
> 用 `git show HEAD:src/server.ts` 取的稳定快照。
> **实测期间有另一路并行 session 正在改同一个 worktree 的 `src/server.ts`**（工作区可见 ` M src/server.ts`），
> 工作树行号已经在漂——凡引用请按符号名定位，别按行号。
> 本轮**没有改任何 `src/` 文件**，也没有 `git add` / `commit`。

---

## 0. 结论摘要

**一句话：不是「二选一」，而是「一套口径、一个注入点、两半方法面」。**

- **传输口径**只留一套 = 4a 的信封形态（版本 + 服务端注入的执行目标 + Bearer + 具名失败码）。
  既有那 7 条委托路由**必须升上来**，不是可选项。
- **注入点**只留一个 = 面板与客户端 API 今天已经在用的那个取数聚合口。飞书那两处今天**绕开它**、
  直接握着本地实例，MUST 改指同一个口。**改完之后，一处切换即三个消费者同时切换。**
- **方法面**是互补的两半，不是两条互斥通道：既有 7 条是「委托任务读写窄面」，
  本 change 新落的运营指令通道补的是第 8 个方法（自由文本入口）+ 另外三条与委托无关的指令。
  实测**方法集零重叠**，kernel 自己也把它们声明成一个交集接口（`DelegatedTaskCommandPort`
  = 7 方法端口 ∪ 文本入口端口，`src/kernel/operator-command-port.ts` 尾段）。
  所以**两个文件都留，都不是重复实现**；重复的只有传输纪律，而那正是要收口的那件事。

**本轮最重要的一条实测事实（tasks.md 没记，且它反过来影响 1.7② 的完成度）：**

> 既有那 7 条路由**今天连业务拒绝都跨不过去**。
> 内部 HTTP 的线格式对一个「带 `code` 的抛出物」只保 `code` + `message`
> （`src/transport/internal-http.ts` 的 `encodeHandlerError`，:63-73），
> **`name` 与 `status` 两个字段在这一跳被丢掉**；客户端收到后重建的是传输层自己的错误对象，
> 它的 `name` 是传输层的名字（同文件 :20-29）。
> 而刚落地的结构化守卫判的正是 `name === 'DelegatedTaskServiceError'`
> （`src/kernel/operator-command-port.ts` 的 `isDelegatedTaskServiceError`）。
> ⇒ **那六处刚从 `instanceof` 迁过来的调用点，一旦真的跨进程，仍然恒 false。**
> 迁移本身没错（它治的是「原型链没了」），但它只治了一半：线格式还得把 `name` / `status` 带过去。

---

## 1. 坐实现状

### 1.1 委托服务在 api 侧的接线点是 **四个**，不是三个；其中一个绕开了取数聚合口

| # | 消费者 | 拿到实例的位置（`src/server.ts@1b36b74`） | 经取数聚合口？ | 用到的方法 |
| --- | --- | --- | --- | --- |
| ① | 飞书 · 自由文本委托 | `:8097` `delegate: async (text, context) => …`，直接读闭包里的本地实例 `:8101` | **否** | `createFromText`（**不在端口面上**）、`pause` / `resume` / `cancel` / `get` |
| ② | 飞书 · 委托卡片按钮 | `:8369` `...(delegatedTaskService ? { delegatedTasks: delegatedTaskService } : {})`，喂给 `:8313` 的入站启动 | **否** | 经 `src/feishu/api-owner-composition.ts:63,186-187` 转给 `src/feishu/delegated-task-card.ts` 的卡片动作处理器：`confirm` / `cancel` / `pause` / `resume` / `get` |
| ③ | 面板 | `:8668` `delegatedTasks: dataGateway.delegatedTaskService` | **是** | `src/panel/panel-server.ts:689` 起的 `/api/delegated-tasks*` 全套；`:3066` / `:3116` 的精选行级动作用 `createDraft` |
| ④ | 客户端 API | `:9210` `delegatedTasks: dataGateway.delegatedTaskService` | **是** | `src/client-auth/client-auth-server.ts` 的 `createDraft`(:2186/:2638) / `get` / `cancel` / `confirm` / `pause` / `resume` / `list` |
| ④′ | 客户端 API · 发布队列视图 | `:9267` `if (!delegatedTaskService) return null;` + `:9278` `delegatedTaskService.list({…})` | **否（同一个 deps 字面量里的绕过）** | `list` |

**④′ 是 tasks.md 完全没记的一处**：它和 ④ 在同一个 deps 对象字面量里，
上面一行走聚合口、下面几十行直接握本地实例。切 remote 时它不会跟着切——
拆完之后 api 进程里那个本地实例根本不存在，这个分支会走 `return null`，
即「该账号没有发布队列」，**而真相是「问不到」**。这就是红线形态。

**另外两条与 tasks.md 记载不同的事实：**

- ① 用的 `createFromText` **不在** `DelegatedTaskServicePort` 上（该端口只有 7 个方法，
  `src/kernel/delegated-task-types.ts:211-229`），所以它不可能经任何一个「满足该端口的客户端」跨过去。
  kernel 已经把这条记在 `operator-command-port.ts` 的 `DelegatedTaskTextCommandPort` 注释里。
- ① 与 ② 都在飞书侧，但它们是**两条独立接线**（一条是命令面闭包，一条是入站 deps），
  不是「飞书一条」。改指聚合口要改两处。

### 1.2 那个「已预留的 remote 位置」到底预留成什么样

文件 `src/gateway/data-gateway.ts`（属主 **api**，实测 `boundaries/module-ownership.json`）：

- `DataGatewayRemote`（:48-54）是**五个可选的构造闭包**，其中 `delegatedTaskService?: () => DelegatedTaskServicePort`。
- 选择逻辑 `selectPort`（:34-37）：`mode === 'http' && remote` 才调闭包，否则回本地实例。
- 该文件**只 import kernel**，注释（:9-18）写明理由：网关在 api 层，直接 import 传输层会新增一条需豁免的跨层边；
  所以闭包**由组装根注入**，组装根可以合法 import 传输层。

组装根侧（`src/server.ts:8592-8617`）：

- `:8594` `delegatedTaskLocal: delegatedTaskService`；
- `:8610-8616` 的 `remote: { … }` 里**只有两条**：精选库读与发布状态读，
  **委托任务与收件箱刻意留空**，注释（:8605-8608）写明「属 automation 域、由 core 本地拥有，一律保持 local，
  绝不指向 content」。
- 且 `remote` 整块只在 `gatewayMode === 'http' && gatewayBaseUrl` 时才给。

**所以「预留」的准确含义是：类型位置留好了、注入通路留好了，值一直没给过，
并且当前那个 base URL 是「content 那一跳」的 base URL，不是 automation 的。**
接 automation 方向要用的是另一个客户端与另一个令牌（`AIDCP_AUTOMATION_URL` /
`AIDCP_AUTOMATION_INTERNAL_TOKEN`，`src/server.ts:7944-7957` 已经建好了一个指向 automation 的内部客户端）。

**还有一条容易踩的**：本地实例是在**共享段**里构造的（`src/server.ts:2969` / `:2983`，
位于 `segAApiFoundation`，:1986 起），而共享段在**五种运行模式下全部执行**
（`src/gateway/service-mode.ts` 的 `segmentsForMode`，五个分支 `segA: true` 无一例外）。
在 cloud 单仓的 `api` 模式下，它照样会被构造出来——**所以「切到 http 模式」在单仓里测不出真问题**。
派生仓那边才是真的：`aidcp-api/src/` 里**没有 `delegated-task/` 目录**（实测），
`src/delegated-task/**` 十个文件全判 automation 属主。⇒ **api 进程物理上造不出这个实例，只能走端口。**

### 1.3 两条通道逐项对比（鉴权 / 版本与目标校验 / 错误编码）

| 项 | 既有 7 条（`src/transport/delegated-task-http.ts`） | 新的运营指令通道（`src/transport/operator-command-http.ts`） |
| --- | --- | --- |
| 路由数 | 7（`DELEGATED_TASK_ROUTES`，:28-36） | 5（四组：文本委托 1 / 手动发帖 1 / 手动评论 1 / 调度启停 2） |
| 注册方式 | `server.register(...)`，**无鉴权** | `server.registerBearer(route, callerToken, …)`，**逐条 Bearer** |
| 调用方式 | `this.http.call(...)`，**裸参数** | `callApiDirectWrite` / `callApiDirectRead`，**信封** |
| 契约版本 | **无** | 信封带版本，接收方不符即 `api_direct_version_unsupported` |
| 执行目标校验 | **无** | 客户端由构造参数注入、接收方逐字比对，不符即 `api_direct_target_mismatch`；**调用方无从选择** |
| 传输失败归一 | 无——传输层原始错误直接冒泡 | 超时 / 连不上 / 形状不符统一译成带具名 `code` 的错误，写路径 code = 「结果未知」 |
| 业务拒绝 | **跨不过去**（见 §0，`name`/`status` 在线上丢失） | 带内回执 `outcome:'rejected'` + 三字段齐全的拒绝对象，客户端侧可原样重建成本仓既有的业务错误 |
| 「未送达」与「未知」 | 不区分 | 严格分开：`not_delivered` 是接收方答出来的带内结论，走回执；「未知」走抛 |
| 幂等 | 无 | `commandId` + `applied` / `duplicate` / `collision` |
| 形状校验 | 无（`call<T>` 直接断言类型） | 逐字段守卫，缺字段判形状不符（:187-189 的 `hasAllKeys` 明写「缺席 MUST NOT 放行成 undefined」） |
| 现有消费者 | **零**（全仓只有它自己的测试 `test/transport/delegated-task-http.test.ts`） | **零** |

**两者都在共享传输包名单里**（控制仓 `scripts/sync-split-repos` 的 `TRANSPORT_MEMBERS`，
`delegated-task-http.ts` 在 :87、`operator-command-http.ts` 在 :121），
所以 api 派生仓能拿到它们——虽然 `src/transport/` 整目录判 automation 属主、api 仓里没有这个目录。

### 1.4 重叠面实测：**方法集零重叠**

- 既有 7 条 = `createDraft` / `confirm` / `pause` / `resume` / `cancel` / `get` / `list`。
- 运营指令四组 = `createFromText`（委托）+ `triggerManualPublish` + `triggerManualComment`
  + `setDispatch` / `readDispatchActivity`（与委托无关）。
- kernel 的机械普查表 `OPERATOR_COMMAND_PORT_INVENTORY` 里，`delegatedTaskFull` 一项就是
  **8 = 7 + 1**；接口 `DelegatedTaskCommandPort extends DelegatedTaskServicePort, DelegatedTaskTextCommandPort`
  已经把这层关系写成类型。

⇒ **「二选一」在方法层面是个伪命题。真正重复、必须收口的是传输纪律与注入点。**

---

## 2. 裁定建议

### 2.1 裁定

1. **传输纪律统一到信封形态。** 既有 7 条路由整体升级：`registerBearer` + 信封（版本 + 目标）
   + 业务错误跨线可还原。**方法签名一个不动**（这是代价有界的关键，见 §2.5）。
2. **注入点统一到取数聚合口。** ①②④′ 三处改指它；类型从「7 方法端口」放宽到 kernel 已有的
   `DelegatedTaskCommandPort`（7+1）。本地分支与 HTTP 分支注入的是**同一个接口**。
3. **接收方只写一个。** automation 侧写一个「委托任务指令接收方」，
   它同时是：(a) 单进程形态下组装根注入给聚合口的本地实现；(b) HTTP 路由挂上去的处理器。
   **一份实现服务两条路径**——这样幂等语义、拒绝翻译、目标校验不可能在两条路径上长歪。
4. **两个传输文件都保留，职责写清楚**：
   - `delegated-task-http.ts` = 委托任务**读写窄面**（7 方法）的传输实现；
   - `operator-command-http.ts` = **四条运营指令**（含委托的自由文本入口）的传输实现。
   两者共用同一套信封 helper（`api-direct-http-common.ts`），共用同一个内部 HTTP 客户端与令牌。
   **不合并成一个文件**：粒度不同（一个是端口面、一个是指令面），合并会让路由表失去
   `satisfies Record<keyof Port, string>` 那道「端口加方法而路由没跟上就编译红」的保护。

### 2.2 判据（为什么不是别的走法）

| 判据 | 推出什么 |
| --- | --- |
| **红线：传输失败＝结果未知** | 既有 7 条把传输层原始错误直接冒泡，调用方（面板 / 客户端 API / 飞书卡片）今天都是 `catch → 500 / 一条 toast`。跨进程后「超时」与「版本冲突」在调用方眼里长得一模一样。⇒ 必须归一到带具名码的失败，且「未知」必须有自己的码。这一条**只有信封形态给得出**。 |
| **不许两套机制并存** | 但机制的粒度是「传输纪律 + 注入点」，不是「文件数」。删掉一个文件、把 7 条重写进另一个，机制数不变、工作量凭空多一份。⇒ 收口纪律，不搬文件。 |
| **YAGNI** | 既有 7 条的**接口形状是对的**（客户端 `implements` 同一个 kernel 端口，本地实例可原样注入）——这正是本仓裁定过的既有范式（design §3.0）。把它改成回执型会连带毁掉「本地实例可直接注入」这条性质，逼出一层适配器 × 2。⇒ 只补它缺的三样（鉴权 / 信封 / 错误可还原），不动签名。 |
| **归属事实源** | `src/feishu/` 整目录归 api，`src/delegated-task/**` 归 automation，`src/gateway/` 归 api，`src/transport/` 归 automation。⇒ 飞书那两处**没有代码要搬家**，缺的只是把端口注入进去；聚合口留在 api 是对的；两个传输文件留在传输目录也是对的。 |
| **DEV/OL 共库** | 既有 7 条无目标校验。dev 的 api 进程配错 URL 指到 ol 的 automation，**没有任何东西会拦**，而委托任务是真副作用（发帖 / 评论）。⇒ 目标校验不是锦上添花。 |

### 2.3 另一条怎么处置

**都不删。** 具体：

- `delegated-task-http.ts`：**保留 + 改造**。它的三件套（路由常量 / 服务端注册 / 类型化客户端）
  是本仓其他两个传输文件明写「范式逐字照它」的样板
  （`curated-content-http.ts:3`、`interaction-store-reader-http.ts:3`）。删它等于删样板。
  改造后把它的文件头注释从「证明性接线（behavior-zero）、不接线不改默认注入」改成「委托任务读写窄面的正式传输实现」。
- `operator-command-http.ts` 的 `OPERATOR_COMMAND_WIRING_DEBT` 第①条（:610）措辞要跟着改：
  现在写的是「MUST 与本文件的 create-from-text 统一到信封形态」，方向对；但要补上真实理由
  ——不只是「两套鉴权口径」，而是「不升级，那 6 处刚迁好的结构化守卫在真线路上仍然恒 false」。

### 2.4 三个消费者是否都改指同一条？——**四个接线点全改，一个不留**

| 接线点 | 改法 | 不改的后果 |
| --- | --- | --- |
| ① 飞书自由文本 | 改读聚合口的委托端口（类型放宽到 7+1），文本入口用运营指令通道那条路由 | 派生 api 仓里根本没有本地实例，这条命令整条不可用；且它是四条运营指令里唯一一条今天**用到了不在端口面上的方法**的 |
| ② 飞书卡片动作 | 入站 deps 的 `delegatedTasks` 改读聚合口 | 同上；且卡片上的版本冲突分流会失效（见 §2.5） |
| ③ 面板 | **已经在聚合口上，零改动** | — |
| ④ 客户端 API | **已经在聚合口上，零改动** | — |
| ④′ 客户端 API 发布队列视图 | 改读聚合口（同一个 deps 对象里就有） | 拆完之后「问不到」被渲染成「这个账号没有发布队列」，静默假成功 |

**没有一个该保留直连。** 唯一看起来像例外的是①的 `createFromText`——它不在 7 方法端口上，
但 kernel 已经给了 7+1 的合并接口，把聚合口的返回类型放宽到它即可，**不需要第二个 getter、
不需要第二条 remote 闭包**。

### 2.5 核对 tasks.md 1.7① 的判断：**成立，但理由记轻了，且代价与不做的代价都要重估**

原文：「`delegated-task-http.ts` 既有 7 条路由不带信封（无版本 / 无 target 校验、无 Bearer），
MUST 与新的 `create-from-text` 统一到信封形态，否则同一个域会有两套鉴权口径。」

**核对结论：MUST 成立。但「两套鉴权口径」只是第三重要的那条。**

**不统一的代价（按严重性排序）：**

1. **业务拒绝跨不过去 → 刚做完的 1.7② 在真线路上无效。**
   服务端把带 `code` 的抛出物编码成 `{code, message}`，丢 `name` 与 `status`；
   客户端重建的是传输层错误对象。结构化守卫判 `name`，故恒 false。
   具体后果与 kernel 注释里写的一字不差：飞书卡片的版本冲突退化成普通错误提示且不再回刷新卡；
   客户端 API 的 409 / 422 一律塌成 500；后台控制台发起的委托任务同样塌成泛化 500。
   **这三条今天已经被当成「已修复」记在 tasks.md 里了。**
2. **无执行目标校验 → DEV/OL 共库下可以把真副作用投到另一台机器上，无人拦。**
3. **两套鉴权口径**——7 条完全无鉴权，与同进程里逐条 Bearer 的路由并存。

**统一的代价（实测，有界）：**

- 服务端：7 个 `server.register` → `registerBearer` + 信封解包 + 一层错误包装（把业务错误的
  `name` / `status` 塞进传输错误的 `details`——线格式对传输层自己的错误**是保 `details` 的**，
  见 `internal-http.ts:63-66` 与客户端解码 :266-268）。
- 客户端：7 个方法各多一层信封 + 一个「收到传输错误时按 `details` 还原业务错误」的出口。
  **方法签名不变**，所以 `implements DelegatedTaskServicePort` 与「本地实例可原样注入」两条性质都保住。
- 构造参数：客户端多两个（令牌、执行目标），与运营指令通道那四个客户端一模一样。
- 既有测试 `test/transport/delegated-task-http.test.ts`（186 行）要跟着改：加令牌、加信封。
- **不需要**新错误类、**不需要**改 kernel 端口、**不需要**改任何调用点的签名。

**一条现成但没被用起来的判据**：kernel 已经写好了
`OPERATOR_COMMAND_TRANSPORT_ERROR_CODES` + `isOperatorCommandTransportErrorCode`——
「线上错误码若**不在**本表内，它就是处理器给的业务原因码」的**补集**判据，
并明写了为什么不用白名单。它今天**零消费**。还原业务错误的那一步就该用它，
不要再造一张「业务码白名单」。
但补集判据只回答「是不是业务错误」，回答不了 `status` 是多少——
**`status` 必须由服务端随 `details` 带过来，MUST NOT 在客户端补默认 400**
（补 400 会把 409 / 422 一并压平，kernel 注释已经点名这条）。

### 2.6 幂等台账（1.7③）：落在哪一侧、用哪张表、跨重启靠什么

**先纠正一条范围：1.7③ 写的「四条写指令」实际是三条。**

| 指令 | 要不要持久台账 | 判据 |
| --- | --- | --- |
| 自由文本委托 | **要** | 有真副作用（落一条委托任务并可能自动入队） |
| 手动发帖 | **要** | 真副作用（整条发帖编排 + 发审批卡） |
| 手动评论 | **要** | 真副作用（评论任务） |
| **调度启停** | **不要——保持进程内** | 它改的状态本身就是**进程内的一个布尔**（`src/server.ts:5324` 的 `let dispatchActive`，写在 `:7724-7740` 的闭包里）。给它一个跨重启的台账，会让「重启后运营再点一次启动」被判成 duplicate 并**回放一条陈旧的「是否真翻转」**——那是编造事实，正是红线形态。4a 的既有判例逐字支持这条：`src/comm/edge-resume-command-receiver.ts:36-40` 明写「回执缓存刻意是进程内的，因为它管的状态也是进程内的，本适配器 MUST NOT 暗示持久的恰好一次」。**同一条推理对启停成立。** 这条 MUST 写进契约注释，否则将来一定有人为了「四条一致」把它补上。 |

**为什么不能只靠既有的领域级判重（这是我原本以为可以省掉的那一步，实测被推翻）：**

委托任务表上已经有一条持久唯一索引
`idx_delegated_tasks_target_active_dedupe (execution_target, dedupe_key) WHERE status IN (…)`
（`src/delegated-task/store.ts:92-94`），`createDraft` 命中即返回 `created:false`——
看起来天然就是「跨重启的持久判重 + 原样回放首次结果」。

**但它对命令重放不成立**：去重键由账号 / 动作 / 来源 / 来源引用 / **截止时间** / 两组约束派生
（`src/delegated-task/service.ts` 的 `createDraft` 里那段 `delegatedTaskDedupeKey({…})`），
而截止时间是解析器按**当前时刻**从散文算出来的绝对时间（`parseDelegatedText(text, { now: this.now(), … })`）。
同一条飞书消息被重投，`now()` 变了 ⇒ 截止时间变了 ⇒ 去重键变了 ⇒ **建出第二条任务**。
所以领域级判重挡得住「同一秒内两次点击」，挡不住「几分钟后的重投」。⇒ 仍然需要按命令键的台账。

**落哪一侧：automation（接收方）。** api 侧记账只能记「我发出去了」，那不是幂等——
判重必须发生在产生副作用的那一侧，且与副作用同库才能同事务。

**用哪张表：新建一张 `operator_command_receipt`，形状照 `migrations/0079_risk_command_outcome.sql` 的判例。**
那条迁移的头部注释就是现成的设计论证（「异步之后提交那一刻不可能知道结果，
不落结果就只能在『编一个乐观的已生效』和『永远显示处理中』之间二选一，两者都不可接受」）。

建议列（**最小面，不镀金**）：

| 列 | 说明 |
| --- | --- |
| `execution_target` | DEV/OL 共库隔离（CLAUDE §2）。与 `command_id` 组成主键——命令键本身不含目标 |
| `command_id` | 运营侧那一次意图的稳定键，已带 kind 前缀 ⇒ 面板与飞书落同一把键空间、互相判得出重复 |
| `kind` / `scope` | 从命令键反解（`parseOperatorCommandId` 已有）。`scope` 用于冲突检测：同键不同 scope ⇒ 回 `collision` |
| `state` | `in_flight` / `applied` / `rejected` 三态，`CHECK` 约束钉死 |
| `receipt` | JSONB。`applied` 存首次回执原文（**原样回放靠它**）；`rejected` 存拒绝三字段 |
| `created_at` / `decided_at` | 审计与剪裁 |

**跨进程重启仍成立靠三件事：**

1. 记录在 automation 属主库，不在内存；
2. 首写用 `INSERT … ON CONFLICT DO NOTHING` 抢 `in_flight`，抢不到就读既有行——
   抢占本身就是判重，不需要额外的锁；
3. **崩在 `in_flight` 上的那一格是唯一需要显式裁的**：重放读到 `in_flight` 时
   **MUST NOT 回 `duplicate`**（那是在断言首次成功了），也 **MUST NOT 直接重跑**（可能双发）。
   MUST 回「结果未知」——即抛，且用**传输码表里那个未知码**，好让客户端侧的补集判据
   把它认成传输失败而不是业务原因。这与语义 C 严丝合缝。

**耦合单元提醒**（design §5 陷阱 5，别只加迁移）：新迁移 + `src/schema/schema-contract.ts`
的两个常量（`REQUIRED_SCHEMA_VERSION` :35 / `KNOWN_MAX_SCHEMA_VERSION` :147）
+ `boundaries/table-ownership.json` 里给这张表登记 owner=automation，
**是一个耦合单元，同一批做完**。

**一条必须如实说的行为变化**：接收方是本地分支与 HTTP 分支共用的，
所以台账一上线，**单进程现网路径也会开始按命令键判重**。
今天飞书那条链路是没有这层的——SDK 只对短时重复帧按事件 id 幂等，
「处理器久不回帧导致重投」挡不住（`src/feishu/ws-receiver.ts:8` 的注释自己写了这一条），
而手动发帖恰恰是长耗时同步操作。
所以这不是回归，是**补上一个今天真实存在的重复触发缺口**——但它是行为变化，
5.x 的部署验证要专门看一眼，1.5 要有用例钉住。

---

## 3. 1.3 落地步骤（谁先谁后 · 每步的验收信号）

> 前置：`src/server.ts` 是并行热点。**第 5 步之前的所有步骤都不碰它**，可与其他两路并行；
> 第 5 步必须等热点让出来再做。

### 步骤 0 · 先修两个当场就该修的位置（不在热点清单里，代价极小）

- **0-a｜命令键与飞书批命令的分隔符撞车（真缺陷，做 1.3 之前必须先解决，否则整条路走不通）**
  分号批命令给每条子命令编的消息 id 是 `${messageId}:command:${index+1}`
  （`src/feishu/commands.ts:365-366`），而命令键的分段分隔符正是冒号，
  且合法性检查明确拒绝含分隔符或空白的分段
  （`src/kernel/operator-command-port.ts` 的 `isCleanIdPart` / `operatorCommandId`）。
  ⇒ 用它当稳定键，`operatorCommandId()` 返回 `null`，而契约要求「拿到 `null` MUST 当场判成参数错误并拒绝下发」。
  **后果是每一条分号批里的委托 / 发帖 / 评论命令都会被拒发**，而且拒得「有道理」，最难查。
  修法二选一，**建议前者**：把那个子命令 id 的分隔符换成不与命令键冲突的字符；
  或在调用点做一次显式归一并**在归一函数里保证单射**（顺手 `replace` 会把两个不同 id 归成同一个）。
- **0-b｜手动发帖 / 手动评论拿不到稳定键**
  自由文本委托那条把上下文（含消息 id）透传到了动作
  （`src/feishu/commands.ts:427-429` 的 `runDelegated`），
  但发帖那条只传了来源会话 id、**丢掉了消息 id**（`:456` `runPublish(cmd, sourceChatId)` → `:464`），
  评论那条同形。⇒ 要么把消息 id 一并透传，要么按契约要求「由指令内容决定的确定性串」构造，
  **MUST NOT 顺手用随机数或当前时刻**。
  反面样板已经在派生仓里长出来了：`aidcp-api/src/server.ts:1175` 的
  `commandId: \`api-feishu-resume:${accountId}:${randomUUID()}\``——每次重试新随机一个，幂等键形同虚设。
  **别照抄它。**

**验收信号**：一条包含两个子命令的分号批消息，两条都能算出合法命令键，且两条互不相同。

### 步骤 1 · automation 侧写「委托任务指令接收方」（新文件，不碰热点）

- 落点：`src/delegated-task/` 下新增一个接收方文件（属主 automation，目录默认判定即可，
  **不需要动归属规则表**）。
- 它 `implements` 三样：7 方法端口（直接转调现有服务）+ 文本入口端口 + 台账。
- 三件必须在这里做完、别推给传输层的事：
  1. 把服务类抛出的业务错误 catch 成带内拒绝（三字段原样，**`status` 取服务给的那个，不补默认**）；
  2. 把 `{kind:'control', request}` 的形状转成契约的 `{kind:'control', action, taskId}`
     （kernel 刻意只留了 api 侧真正消费的两段）；
  3. 台账三态与 `collision` 判定（见 §2.6）。
- **调度启停的接收方不带台账**，注释里写明理由（§2.6 那条）。

**验收信号**：新接收方的单测——同一命令键连发两次拿到 `applied` 然后 `duplicate`，
且第二次的回执与第一次**逐字段相同**（不是重算的）；换 scope 同键拿到 `collision`；
业务拒绝拿到 `rejected` 且 `status` 是服务给的 409 / 422 而不是 400。

### 步骤 2 · 升级既有 7 条路由到信封形态（`src/transport/delegated-task-http.ts`，不碰热点）

- 服务端：`register` → `registerBearer`；每条包一层信封解析（版本 + 目标）；
  加一层错误包装，把业务错误的 `name` / `status` 塞进传输错误的 `details`。
- 客户端：构造多两个参数（令牌、执行目标）；每个方法走信封；
  加一个统一出口——收到传输错误时先用**补集判据**判是不是业务原因码，是则按 `details` 还原成业务错误抛出。
- **7 个方法签名一个不动。**
- 同批更新文件头注释（从「证明性接线、不接线」改成正式实现）。

**验收信号**：
① 回环测试里，服务端抛版本冲突 → 客户端侧结构化守卫**返回 true** 且 `status === 409`（这条今天是红的）；
② 不带令牌调用 → 401；
③ 目标不符 → 目标不匹配码；
④ 既有那 186 行测试改完全绿。

### 步骤 3 · 补运营指令通道的服务端注册与客户端（`src/transport/operator-command-http.ts` 已就绪，本步只用不改）

四组注册函数与四个客户端类都已经写好了，本步只是把它们接到接收方与内部客户端上。

### 步骤 4 · 放宽取数聚合口的委托端口类型（`src/gateway/data-gateway.ts`，属 api，不在热点清单）

- 本地字段与 getter 的类型从 7 方法端口放宽到 kernel 的 7+1 合并接口；
- `DataGatewayRemote` 那条闭包同步放宽。
- **不新增第二个 getter、不新增第二条闭包。**

**验收信号**：`npm run typecheck` 零错；聚合口的默认（本地）分支行为逐位不变——
默认模式下 getter 返回的仍是注入进去的那个对象本身。

### 步骤 5 · 组装根接线（`src/server.ts`，**热点，必须串行**）

顺序（每一小步都能单独编译过）：

1. automation 内部 API 注册块（`startAutomationInternalApi`，`@1b36b74` 的 `:1729`，
   照 `:1779-1801` 那三组 `if (…) { register… } else { console.warn(…) }` 的形状）
   挂上：委托 7 条 + 四组运营指令。**每组独立注册、缺依赖走具名 warn，不连带关闭其它组。**
2. 共享段构造本地接收方（包住既有服务实例）。
3. 聚合口构造处（`:8592`）：本地字段改喂接收方；
   `remote` 块新增委托闭包，用**指向 automation 的那个内部客户端与令牌**
   （`:7944-7957` 已有），**不要复用 content 那个 base URL**。
4. 四个接线点改指聚合口：飞书自由文本（`:8097`）、飞书入站 deps（`:8369`）、
   客户端 API 发布队列视图（`:9267` / `:9278`）；面板与客户端 API 主接线已在聚合口上、零改动。
5. 飞书自由文本那段按回执形状重写渲染分支：
   - `rejected` → 还原成业务错误后走既有的「需要补充信息」提示（行为逐位不变）；
   - `not_delivered` → **明说「这台机器上没有接这条指令的处理器」**，
     MUST NOT 表述成已受理 / 已排队；
   - 传输失败（抛）→ **明说结果未知**。
     ⚠️ 今天 `src/feishu/commands.ts:427-437` 的 `runDelegated` 把**所有**异常
     统一渲染成「委托任务需要补充信息」的黄色提示——传输超时会被画成「你的话没说清楚」。
     这一步必须一并改，否则「结果未知」这条语义在运营眼里根本不存在。

**验收信号**：单体形态下部署 dev，飞书 `/delegate`、`/publish`、`/comment`、
面板启停与状态灯、面板与客户端 API 的委托任务全套，**行为逐位不变**；
重启后错误行数 0；具名的「未接线」告警一条不响（dev 上全都接着线，本来就不该响）。

### 步骤 6 · 派生对账

按既有顺序：先 `--apply --prune`（源码）+ `--apply --tests`（测试）**全部落完**，
再按 kernel → transport → 三个业务仓抬 pin。
（这条顺序是 5.4 那条注释里用真事故换来的，别倒过来。）

---

## 4. 1.5 契约测试清单（每条都写「它红的时候在说什么」）

落点建议：既有的 `test/transport/delegated-task-http.test.ts` 扩写 + 新增
`test/transport/operator-command-http.test.ts`（形状照 `test/transport/paired-command-http.test.ts`）。

| # | 用例 | 红的时候在说什么 |
| --- | --- | --- |
| 1 | 不带令牌调用任一条委托路由 → 401 | 有一条路由漏了鉴权 |
| 2 | 信封版本不符 → 版本不支持码 | 契约版本漂了却没人拦 |
| 3 | 信封目标与接收方不符 → 目标不匹配码 | DEV/OL 隔离失效 |
| 4 | **客户端无法自选目标**（构造参数注入，方法入参里没有目标位） | 有人把目标做成了请求字段 |
| 5 | 服务端抛版本冲突 → 客户端侧结构化守卫为真、`code==='version_conflict'`、`status===409` | 业务错误跨不过那一跳（**今天这条是红的**） |
| 6 | 服务端抛平台不支持（422）→ 客户端侧 `status===422` | 有人在客户端补了默认 400 |
| 7 | 服务端返回缺字段的任务对象 → 客户端判形状不符并抛，**不放行成属性为 undefined 的对象** | 缺席被压成空值 |
| 8 | 同命令键连发两次 → `applied` 然后 `duplicate`，且回执逐字段相同 | 回放是现算的，不是记下来的 |
| 9 | 同命令键不同 scope → `collision` | 键空间串了 |
| 10 | 台账停在进行中态时重放 → **抛「结果未知」**，既不回 `duplicate` 也不重跑 | 崩溃窗口被推断成成功或被双发 |
| 11 | 接收方进程重启后重放（用同一张表、新建接收方实例）→ 仍判 `duplicate` | 台账其实只活在内存里 |
| 12 | **调度启停重启后重放 → 重新执行，不判 duplicate** | 有人给它加了持久台账，重启后一次真实启动被吃掉 |
| 13 | 处理器未注入 → `not_delivered` + 具名原因，且**不是**异常 | 「没接线」与「答不上来」合流了 |
| 14 | 客户端连不上 / 超时 → 抛，码为「结果未知」，**领域结局不被改写** | 传输失败被推断成失败或成功 |
| 15 | 状态灯读不到 → 抛，调用方渲染成「读不到」而**不是** `active:false` | 「云端答不上来」被画成「调度引擎正常停着」 |
| 16 | 端口加一个方法而路由表没跟上 → **typecheck 红** | `satisfies` 那道闸被拆了 |
| 17 | 注册函数漏挂一条路由 → 用例红（typecheck 抓不到） | 变异实测过的那条：`satisfies` 保证表全，保证不了都挂上 |
| 18 | 分号批的两个子命令各自算出**合法且互异**的命令键 | 步骤 0-a 的回归 |
| 19 | 手动发帖 / 手动评论的命令键**跨重试稳定**（同一条运营消息两次投递得到同一个键） | 有人用了随机数或当前时刻 |

**不在本轮验收范围**（如实分层，design §7）：三进程真跑。回环测试只证明路由与客户端；
dev 单体部署只证明现网零回归。

---

## 5. 与 tasks.md 第 1 节记载不符的事实（这一节最重要）

| # | tasks.md 的记载 | 实测 | 影响 |
| --- | --- | --- | --- |
| **A** | 1.7② 记「两处 `instanceof` MUST 迁到结构化守卫」，注释更正为「3 个文件 / 6 个调用点，**已做**」 | 迁移确实做了（面板 :289、客户鉴权 :547、飞书卡片 :146 均已用守卫），**但它在真线路上仍然恒 false**：线格式只保 `code` + `message`，`name` 与 `status` 在这一跳被丢弃（`internal-http.ts:63-73`），而守卫判的是 `name` | **1.7② 只完成了一半**，且另一半（线格式带 `name`/`status`）没有任何地方登记。它必须与 1.7① 同批做，否则 1.7② 是纸面完成 |
| **B** | 1.4d 记「三个消费者（飞书 `8316`、面板 `8615`、客户端 API `9157`），后两个走取数聚合口」 | 是**四个接线点**：飞书有**两条独立接线**（命令面闭包 `:8097` + 入站 deps `:8369`），且客户端 API 里还有**第五处直连**（`:9267` / `:9278` 的发布队列视图，与走聚合口的 `:9210` 在同一个 deps 字面量里） | 只改「三个」会漏掉两处；漏掉 `:9267` 那处的后果是「问不到」被渲染成「没有队列」——静默假成功 |
| **C** | 1.7③ 记「**四条**写指令的接收方 MUST 建持久幂等台账」 | 应是**三条**。调度启停改的是进程内布尔（`:5324` / `:7724-7740`），给它持久台账会让重启后一次真实启动被判 duplicate 并回放陈旧的「是否真翻转」——编造事实。4a 的既有判例（`edge-resume-command-receiver.ts:36-40`）逐字支持「状态是进程内的，台账就该是进程内的」 | 照字面做会新造一条红线违规 |
| **D** | 1.4a 的 ⚠️ 注释：「组装根仍在往下传两个占位桩（约 `src/server.ts:8219-8229`），桩还在，行为逐位未变」 | **已过时**。`@1b36b74` 的 `:8250-8258` 明写「调度启停两条句柄直接透传，不补占位桩」，两个占位桩已删（由 0.6g 的第二条注释记录）。两份同名动作面也已收成一份（`src/feishu/command-face.ts:35` 的 `PanelCommandActions`，理由注释 :23-34），面板那份改为从飞书侧导入 | 1.4a 实际已完全兑现，可以勾掉 ⚠️；照旧注释去找桩会白找 |
| **E** | 1.4d 记「`DataGateway` 在 `8539-8563` 已预留 remote thunk 的位置」 | 位置在 `@1b36b74` 的 `:8592-8617`；且**预留的只是类型位与注入通路**，`remote` 块里实际只给了精选库与发布状态两条，委托与收件箱是**刻意留空**并写了理由（`:8605-8608`）；那个 base URL 是指向 content 的，**不是** automation 的 | 接线时要新建一条指向 automation 的闭包，用 `:7944-7957` 已有的客户端与令牌，别复用 content 那条 |
| **F** | 1.4c 记「`delegated-task-http.ts` 服务端注册 + 客户端 + 7 个路由方法齐全……这条离关闭只差一次接线」 | 齐全属实、零消费属实，**但「只差一次接线」不成立**：它无鉴权、无版本、无目标校验，且业务拒绝跨不过去。直接接上去等于把三个已知缺口一起接进生产 | 1.4c 的「只差接线」措辞要改成「差一次升级 + 一次接线」 |
| **G** | 1.7① 记「否则同一个域会有两套鉴权口径」 | 成立，但这是三条后果里最轻的一条。更重的两条：① 业务拒绝跨不过去（见 A）；② 无目标校验，DEV/OL 共库下真副作用可能投到另一台机器 | 理由要补写，否则将来评估优先级会低估它 |
| **H** | 无记载 | **命令键与飞书分号批命令的分隔符撞车**：批命令给子命令编的 id 是 `${messageId}:command:${n}`（`src/feishu/commands.ts:365-366`），冒号正是命令键的分段分隔符，合法性检查明确拒绝含它的分段 ⇒ 用它当稳定键会算出 `null`，而契约要求拿到 `null` 就拒发 | **每一条分号批里的委托 / 发帖 / 评论都会被拒发**。必须在 1.3 之前先解决 |
| **I** | 无记载 | **手动发帖 / 手动评论拿不到稳定键**：消息 id 只透传给了自由文本委托那条（`runDelegated`），发帖 / 评论只拿到来源会话 id（`:456` / `:464`） | 幂等台账对这两条无从落地，除非先补透传 |
| **J** | 无记载 | **`runDelegated` 把所有异常统一渲染成「委托任务需要补充信息」的黄色提示**（`src/feishu/commands.ts:427-437`）⇒ 传输超时会被画成「你的话没说清楚」 | 「结果未知」这条语义在运营侧目前无处可见，1.3 步骤 5 必须一并改 |
| **K** | 无记载 | **派生 api 仓的手写 main 里有两处已经写下的不诚实**：`aidcp-api/src/server.ts:1197` 的 `dispatchActive: () => false`（把「不知道」答成「停着」，而 1.4a 刚把这个字段改成可选就是为了让它可以诚实缺席）；`:1175` 的命令键里塞了随机数（幂等键形同虚设） | 都还没上生产（三进程未部署），但 1.3 接线时若照抄就会把它们带进生产。**建议：`dispatchActive` 直接省略不传**（现在类型上允许了），命令键改用稳定来源 |
| **L** | 无记载 | **既有领域级判重挡不住命令重放**：委托任务表上那条唯一索引（`store.ts:92-94`）的去重键含**由当前时刻算出的截止时间**（`service.ts` 的 `createDraft` 那段），重投时会变 ⇒ 建出第二条任务 | 不能用「已经有唯一索引」当理由省掉命令台账（我原本以为可以，实测被推翻） |
| **M** | 无记载（属工作方式） | **本 change 的 cloud worktree 正被多路并行 session 同时写**（调研期间 `src/server.ts` 与 `src/cache/curated-content-store.ts` 都处于已修改未提交状态，`src/server.ts` mtime 在调研过程中前进） | tasks.md 里所有 `src/server.ts` 行号都会持续漂。后续注释建议**只写符号名**，行号只作导航并标 sha |

---

## 6. 一句话给接手的人

**先修分隔符撞车（H）与稳定键透传（I），再写 automation 侧那个唯一的接收方，
再把既有 7 条升到信封（顺带把 A 那半条补完），最后一次性在组装根把四个接线点全部改指同一个取数口。
台账三条不是四条（C），启停那条保持进程内并把理由写进注释——否则下一个人一定会「顺手补齐」。**
