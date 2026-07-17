## Why

**客户端拿着「环境编号」去问「这个账号收集了什么」，云端拿着环境编号当账号去查库——两个键空间，实测零交集。**

| 键 | 是什么 | 大白的值 | 谁在用 |
| --- | --- | --- | --- |
| `envKey` | AdsPower 分身 id，8 字符 | `k1e0ero8` | 客户端**唯一知道**并提交的东西 |
| `accountId` | 登录态页面上读出的真实平台 id | `63e2ff0500000000260049ce`（24-hex） | 全部写入方**唯一写入**的东西 |

dev 实测（本 change 的事实基座，实装者不必重跑）：

```
select count(*) from curated_content where account_id='k1e0ero8'                  → 0
select count(*) from curated_content where account_id='63e2ff0500000000260049ce'  → 158   (最新 updated_at 2026-07-17 15:53)
select count(*) from curated_content where length(account_id) <> 24               → 0     ← 没有任何写入方写过 profileId
JOIN client_env_scope.env_key = curated_content.account_id                        → 0 行
```

`client-auth-server.ts:374` 把 `envKey` 传进一个声明为 `accountId: string` 的形参（`curated-content-store.ts:1002-1005`）。该 SQL 在 `mode=all` 下**只有一个谓词**（`curated-content-store.ts:1008-1013`：`const conds = ['account_id = $1']`）——所以「全部」标签页返回零条，**结构上证明了这是纯键不匹配**，不可能是形态/状态/契合度筛选的结果。

**两端都诚实，合起来在撒谎。** 云端如实回 `200 {items:[],total:0}`；客户端如实画出「精选池还是空的 / 系统发现适合当前账号的内容后，会出现在这里」（`content-workspace.js:377`）。客户端**完全无辜**：它每一种失败都是一张独立可见的错误卡 + 「重新加载」按钮（`content-workspace.js:438-443` 三态闸），所以**一个和善的空态本身就证明了云端回的是 200-空**。这正是本项目「MUST NOT 静默假成功」红线的**镜像**——不是把失败谎报成成功，而是把**失败谎报成「你没有数据」**。

### 波及面：client-auth 里每一处吃 accountId 的地方都是坏的

（早期「委托任务是一座自洽的 envKey 孤岛」的说法**已被推翻**，且被 live 实测证实推翻：`delegated_tasks` 30 行，`account_id` 长度只有 14（facebook）与 24（xiaohongshu）两种，**零条 8 字符行**。）

| 位置 | 现在的行为 | 性质 |
| --- | --- | --- |
| `:364` `referenceDraftCountForAccount(envKey)` → `publish_log WHERE account_id=$1`；写入方用真 accountId（`publish-executor.ts:262-302` ← `executors.ts:330 triggerDelegated(task.accountId)`） | 恒为 0 | **静默** |
| `:374` `listForClient(envKey)` | `200 {items:[],total:0}` | **静默**（头号 bug） |
| `:419` / `:498` `getOneForAccount(id, envKey)` | 恒 null → `404 not_found` | 响亮但**误导** |
| `:623` `delegatedTasks.list({accountId: envKey})` | `200 {tasks:[]}` | **静默** |
| `:648` `createDraft({accountId: envKey})` | `service.ts:280-282` resolveAccount 抛 `account_not_found` 404 | 结构上不可能成功：`delegated_tasks.account_id TEXT NOT NULL REFERENCES accounts(account_id)`（`delegated-task/store.ts:27`） |
| `:683` `scope.some(item => item.envKey === task.accountId)` | 恒不匹配 → 对**正当所有者**回 `403 environment_not_owned` | 响亮但**诬告** |
| `:438` curated create-post | **当前是死代码**（`:419` 的 404 先开火） | 不是自洽孤岛 |

**为什么 typecheck 抓不到**：两个形参都是裸 `string`。
**为什么测试抓不到——夹具把错误的契约固化了**：`test/client-auth-server.test.ts:566-572` 断言 `assert.deepEqual(reads[0], { kind:'list', accountId:'p1', ... })`，而 `'p1'` **就是请求里的 envKey**（`:551` `/curated-contents?envKey=p1`）；`:572` 断言 `draftCountReads === ['p1']`；`:383`/`:642` 把 `listAccounts` 伪造成 `[{accountId:'p1'}]`——**账号注册表本身被造进了 envKey 空间**，于是 resolveAccount 命中、外键永远跑不到。**这些夹具必须先改，否则它们会与修复正面冲突。**

### 为什么是持久绑定，而不是活会话解析

用户已定案（D1）：**读灵感库绝不能要求边缘在线**。云端此刻**没有任何**环境↔账号的持久事实——`client_environments` 今天只有 `env_key`(PK) / `label` / `platform` / `source` / `created_at` / `updated_at`。

## What Changes

- **新增持久的 环境→账号 绑定**：`client_environments` 加一列账号绑定，**写在已经存在的握手钩子上**（`server.ts:1965-1972`，每次 hello 都会 fire-and-forget 调 `registerEnvironments(..., 'auto')`，accountId 就在同一个 session 对象里）。重绑语义 = **最后一次握手为准**、每环境至多一行（`env_key` 已是 PK ⇒ 结构上不存在「多个里挑一个」）。合并用 `COALESCE(EXCLUDED.x, current)` = **「来了新值才覆盖」**，**绝不是**「当前为空才写」——后者正是 2026-07-12 修掉的 FB 昵称回归的形状，会把环境永远钉死在它的第一个登录账号上。`accountId === 'default'`（`account-store.ts:25` `RETIRED_ACCOUNT_ID`）归一为「没有新值」：不写成绑定，也不擦掉既有绑定。
- **D5 跨客户冲突闸（fail-closed + 告警）**：绑定写入时，若该 accountId 已绑在**另一个属于不同客户的环境**上，**拒绝写入**并告警，既有绑定保持不变。**读侧再补一道**：解析器在绑定被跨客户争用时拒绝解析（写闸结构上看不见「事后改归属」造出来的冲突——那是管理员脚下的雷，不是攻击者的入口）。
- **一个解析器供全部 7 处坏点用**（`:364` `:374` `:419` `:498` `:623` `:648` `:683`），带**诚实的 `binding_unknown` 契约**：未绑定 → `409 binding_unknown`，**永不 200-空**。区分 `403 environment_not_owned` / `409 binding_unknown` / `409 binding_conflict` / `503 curated_content_unavailable`；`200 {items:[],total:0}` **只**在「绑定解析成功、该账号确实零行」时出现。
- **修 42P01 → 和善空态的降级**（`curated-content-store.ts:1038` 等 4 处只读方法）：缺表/改名今天仍然浮现为 `200 {items:[],total:0}`——**正是本 change 要杀的那个红线字符串**。改为诚实的 503 `curated_content_unavailable`。
- **不可逆写加活体前置（ESSENTIAL/INCIDENTAL 判别）**：`:438` create-post 与 `:648` 建委托任务在修好后**首次变得可达**，且它们**不可逆**（不同于 `slow_start_since` 那种幂等可回滚的写）。发布在结构上就**做不到**没有活浏览器还能兑现 ⇒ 在**那里**加活体前置是 **ESSENTIAL** 的，且不花费本 change 想要的任何东西（读仍然离线可用）。**MUST NOT** 把这道前置抄到读路由上——那就是在重造本 bug。
- **修夹具**（`test/client-auth-server.test.ts:383` `:523-525` `:566-572` `:642`）。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `client-customer-auth`: **ADDED** 四条——① 环境→账号持久绑定由握手事实供给（重绑语义、退役账号守卫、握手绝不因此被拒）；② 跨客户绑定冲突 fail-closed（D5，含读侧争用闸）；③ 客户端账号态读 MUST 经绑定解析，未解析 MUST NOT 伪装成空结果；④ 不可逆写 MUST 由活会话佐证绑定。**不动** `:314` 的慢启动要求（那条明文禁用绑定表，由串行的后继 change 推翻——见下）。
- `curated-inspiration-corpus`: **MODIFIED**「账号隔离」——补上今天缺失的那半句：账号维度**只有一个键空间**（登录态读出的平台 id）；任何面向客户的读 MUST 先把环境标识翻译成它，MUST NOT 把环境标识当账号 id 直接查。
- `panel-curated-content`: **MODIFIED**「精选存储缺失时优雅降级，不崩闭环」——现文明写「当底层表尚不存在时，只读接口 MUST 回落为空结果」，scenario 叫「表不存在回空而非报错」。**本 change 推翻这半条**：缺表 MUST 回 503（服务不可用），MUST NOT 伪装成空结果。「MUST NOT 500 / 不崩闭环」的**本意原样保留**——503 不是 500，且面板前端**本来就已经有**「加载中 / 暂无数据 / 服务不可用」三态可区分的要求，本改动只是让缺表落进它已有的第三态。
- `edge-companion-ui`: **ADDED** 一条——灵感库空态 MUST 区分「真的空」与「还不知道这个环境上是谁」（对齐已有的「互动空态必须区分未开启与确实无消息」`:1019`）。

## Impact

- **aidcp-cloud（主仓）**：`client-auth/client-user-store.ts`（schema 加列 + `registerEnvironments` + 新解析器 + D5 闸）、`client-auth/client-auth-server.ts`（7 处坏点改接解析器、新错误码）、`cache/curated-content-store.ts`（4 处 42P01）、`panel/panel-server.ts`（`:2312` 映射 503）、`server.ts`（`:1965-1972` 握手钩子加字段；`:1092`/`:1120` 处理新的 typed error）、`test/client-auth-server.test.ts`（夹具）。
- **aidcp-edge**：只加一条人话化映射 + 空态区分（`content-workspace.js` 的 `rejectionMessage` 词典与 `renderListMessage`）。**不动协议**。
- **aidcp-console**：零改动（面板只多一个 503 分支，前端三态已在）。
- **协议五处同步点：一处不碰**。两份 `protocol.ts` 零 diff ⇒ **不是热点单写者改动**。
- **DB**：`client_environments` 加一列（`ADD COLUMN IF NOT EXISTS`，schema 启动自建、无迁移器）。**无回填**（见 Non-Goals）。
- **部署**：纯云端 + 一个可延后的 edge 文案改动；dev 当天可部署，**不需要出安装包**（edge 那半可随下一次发版走；在它到达之前，409 会落进已有的通用错误卡——**响亮且可见**，只是不够自解释，这不是红线违反）。
- **真机验收**：挂 backlog（大白 `k1e0ero8`：重启该环境一次让它 hello → 绑定落库 → 灵感库出现 158 条；另找一个从未连过云端的环境 → 看到 `binding_unknown` 的自解释态而**不是**「精选池还是空的」）。

### 运营预期（必须提前打招呼，否则会被当 bug 报回来）

**绑定不追溯。** 部署当天 18 个环境里约 16 个是未绑的——它们会从「精选池还是空的」变成「还不知道这个环境上登录的是哪个账号」。**这是本 change 的目的，不是回归**：前者是谎，后者是真话。每个环境**连上云端一次**（hello）绑定即自愈，无需任何人工操作、无需回填脚本。

### 与慢启动 change 的关系：**串行，不是并行**（CLAUDE.md §7 热点文件单写者）

- 两者都改 `client-auth/client-user-store.ts` 与 `client-auth/client-auth-server.ts`。
- 且存在**真实依赖**：`client-customer-auth` 现行 `:314` 要求明文写着「**MUST NOT 依赖持久化的环境↔账号绑定表**——持久绑定会陈旧……只是把「现在自称是谁」冻成「曾经自称是谁」」。**本 change 建的正是那张表**。本 change **不推翻该要求**（它只约束慢启动路由，本 change 不碰那条路由）；推翻它是慢启动 change 的职责，且**必须在本 change 之后**——否则它没有可依赖的绑定。
- **本 change 先落，慢启动 change 后落。** archive 时按此依赖序合并 spec delta（两个 change 都动 `client-customer-auth`）。

### 那条要求的反对意见必须被正面回答（不能装作它不存在）

`:314` 反对持久绑定的两条理由都成立，本 change 逐条应答而非无视：

| 反对 | 应答 |
| --- | --- |
| 「持久绑定会陈旧」 | 对**读**：陈旧的代价是读到「这个环境上一次登录的那个账号」的语料——幂等、非破坏，且被 D5 读侧争用闸兜住。对**写**：不接受陈旧——不可逆写 MUST 由活会话佐证（见上）。**读写用不同的强度，因为它们的代价不同**。 |
| 「其账号身份同样源自无凭据握手，只是把『现在自称是谁』冻成『曾经自称是谁』」 | **完全成立，且正是 D5 存在的理由**（见下）。本 change 不假装解决了握手无鉴权；它只保证**持久化这件事不把既有暴露面放大成跨客户资产窃取**。 |

### D5 要回答的安全问题（明说，别绕）

边缘 WS 握手**全文无鉴权**，accountId 是**边缘自报的字符串**（`client-auth-server.ts:281-283` 已白纸黑字写明）；edgeId 由客户端自选（`aidcp-edge/src/client/edge-id.ts:41-42`）；`ensureAccount`（`connection-runtime.ts:136`）接受任何 hello 声明的 accountId。**把这个自报身份持久化、并用它授权读，会把既有暴露面升级**：

- **今天**：恶意边缘可以把自己拥有的环境绑到受害者的 accountId 上，去改受害者的慢启动——**内存态、瞬时**。
- **持久绑定之后**：同一个动作可以读到**受害者的整个精选池**、并操控其**具备发布能力**的委托任务——**持久、新资产、新的行为主体**。

**D5 的闸**：绑定写入时若该 accountId 已绑在**属于另一个客户**的环境上 → **拒绝写入 + 告警**。Fail closed。

## Non-Goals

- **绝不做 `interaction_auth_state` 回填**。把它放进 `accountStore.init()`（`server.ts:1027`）会读一张**283 行之后**才由 `interactionStore.init()`（`server.ts:1310`）建出来的表；本仓**没有迁移器**、schema 在启动时自建 ⇒ 全新库上必 `42P01` ⇒ `store.init()` 抛 ⇒ **accountStore 静默降级为内存态**（账号 / 昵称 / 慢启动 / 平台全部不再持久化），而日志会**谎称是「PG 不可用」**。它的全部收益是那 **2 行 `wechat_channels`**——**唯一对本 bug 免疫的平台**（那里 `account_id == env_key` 是构造出来的恒等式），且它们在下一次 hello 就自愈。
- **不给绑定列加外键到 `accounts`**。`clientUserStore.init()` 在 `server.ts:605` 跑，`PgAccountStore` 到 `server.ts:1020` 才构造 ⇒ 在 `CLIENT_USERS_SCHEMA_SQL` 里写 `REFERENCES accounts(account_id)` 会在全新库上直接抛。改为**每次读都 JOIN `accounts`**（与 `withAuthorizedInteractionScope` 在 `client-user-store.ts:789-791` 已经在做的一字不差），于是悬空绑定在**读时 fail-closed**。**注意**：这是一个真实的取舍（少了写时完整性），**不是**「初始化顺序禁止加列」——后者是假论据，别照抄。若日后要加 FK，必须诚实陈述真实取舍。
- **不碰 `:445` 的 `sourceRef`**（`edge:curated:${envKey}:${id}:create-post`）：它是**自洽**的——一个不透明的诊断字符串，从不被当键解析。
- **不收敛 `interaction_auth_state`**（视频号保留自己的解析器）：那里 `account_id == env_key` 是构造恒等式，两者**永不可能不一致**；收敛 = 零行为差的搅动。
- **不在本 change 删 `resolveAccountIdForEdge`**（`ws-server.ts:316-333`）：它最后一个调用方是慢启动路由（`server.ts:4163`/`:4192`），删除属于慢启动 change。**本 change 刻意不新增它的调用方**（活体佐证改用幸存的 `resolveEdgeIdForAccount`——见 design），好让那次删除仍然干净。
- **不治「边缘握手无鉴权」这个根问题**。D5 只防止本 change 把它放大。
- **不做视频号互动开关的离线可调**（Defect 3）：与本 change **零共享代码**，是纯边缘渲染层修复，可当天独立发版，**MUST NOT** 被压在本 schema 改动或安全决策后面。
