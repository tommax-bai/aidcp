## Context

云端有**两个标识空间**，dev 实测**可证不交**：

| 空间 | 来源 | 形状 | 谁写它 |
| --- | --- | --- | --- |
| `envKey` | AdsPower 分身 id | 8 字符（`k1e0ero8`） | 客户端**唯一**能提交的东西；`client_environments` / `client_env_scope` 的键 |
| `accountId` | 登录态页面读出的平台 id | 24-hex（XHS）/ 14 位（FB） | `curated_content` / `publish_log` / `delegated_tasks` / `accounts` 的键 |

`client-auth-server.ts` 是这两个空间的**接缝**：它按 `envKey` 鉴权（正确——那是管理员授予的归属，fail-closed），然后**把 `envKey` 原样当作 `accountId` 去查库**（错误）。今天云端**没有任何持久事实**能把它们连起来。

现有的三个「谁在这个环境上」解析器，没有一个能承担这件事：

| 解析器 | 方向 | 依赖 | 能否用于本 bug |
| --- | --- | --- | --- |
| `resolveEdgeIdForAccount`（`ws-server.ts:290-306`） | account→edge | 活会话 | ❌ 方向反了 |
| `resolveAccountIdForEdge`（`ws-server.ts:316-333`） | edge→account | 活会话 | ❌ **要求边缘在线**——违反 D1 |
| `withAuthorizedInteractionScope`（`client-user-store.ts:783-795`） | env→account | `interaction_auth_state` | ❌ 只有视频号有行（那里 `account_id == env_key` 是构造恒等式） |

## Goals / Non-Goals

**Goals**
- 读灵感库 / 成稿数 / 委托任务列表**不需要边缘在线**（D1）。
- 每一处不可解析都**响亮**：`403` / `409` / `503`，**永不 200-空**。
- 持久化自报身份**不放大**既有暴露面（D5）。
- 让慢启动 change 能干净地删掉 `resolveAccountIdForEdge`。

**Non-Goals**
- 不治握手无鉴权（根问题，D5 只封住放大路径）。
- 不回填（见 proposal Non-Goals：`interaction_auth_state` 回填是个会把 accountStore 静默降级成内存态的雷）。
- 不收敛视频号解析器。

## Decisions

### D-1 绑定写在已经存在的握手钩子上（不新开写入点）

`server.ts:1965-1972` **今天就已经**在每次 hello 上 fire-and-forget 调：

```
clientUserStore.registerEnvironments(
  [{ envKey: eid.slice('ads-'.length), label: session.accountNickname ?? null, platform: session.platform ?? null }],
  'auto',
).catch(...)
```

`session.accountId` **就在同一行的同一个 session 对象里**。

**这个位置按构造是安全的**：`ws-server.ts:352-358` 只在 `env.type==='hello' && reply.type==='welcome'` 时（**握手已成功、welcome 已先行回发之后**）触发 `onEdgeRegisteredCb`，且包在一个「记日志 + 吞掉」的 try/catch 里。⇒ **在这里加一个字段，结构上不可能拒掉一次握手。**

### D-2 重绑语义：最后一次握手为准，`COALESCE(EXCLUDED.x, current)`

`env_key` 已是 PK ⇒ **每环境至多一个账号** ⇒ 结构上不存在「多个候选里挑一个」的猜测。

沿用 `registerEnvironments` 现有的合并形状（`client-user-store.ts`）：

```sql
ON CONFLICT (env_key) DO UPDATE
  SET account_id = COALESCE(EXCLUDED.account_id, client_environments.account_id),
      ...
```

**读法**：「来了新值才覆盖」。

**MUST NOT 写成**「当前为空才写」（`SET account_id = COALESCE(client_environments.account_id, EXCLUDED.account_id)`）——那是 2026-07-12 修掉的 **FB 昵称回归的形状**，会把环境**永远钉死在它的第一个登录账号**上，而换号登录恰恰是运营的日常动作。

**退役账号守卫**：`accountId === 'default'`（`account-store.ts:25` `RETIRED_ACCOUNT_ID`）在调用侧归一为 `null` ⇒ 在 COALESCE 下等价于「没有新值到达」⇒ **不写成绑定，也不擦掉既有绑定**。（`account-store.ts:278-279` 已经在拒绝登记这个保留 id，绑定层与它保持一致。）

### D-3 D5 双闸：写时防攻击者，读时防管理员脚下的雷

**归属是 0-或-1 的**：`uq_client_env_scope_active_env`（`client-user-store.ts:148-149`）是 `client_env_scope (env_key)` 上的唯一索引 ⇒ 每个环境至多一个 owner。

**写闸**（D5 本体）：绑定写入前，若存在**另一个** env 已绑定同一 accountId 且其 owner 与本次 env 的 owner **不同**（无 owner 记作 ⊥，与任何客户都不同）→ **拒绝本次绑定写**、既有绑定不变、告警。

- 无主环境本来就读不到任何东西（全部 client-auth 读都先过 `listEnvScope` 归属闸），所以对它 fail-closed **不花费任何东西**。
- 合法迁移仍然通得过：同一客户的两个环境跑同一账号 → owner 相同 → 放行（无边界被跨）。
- 被拒的环境在**管理员把它分给同一个客户之后的下一次 hello** 自愈。

**读闸**（写闸结构上看不见的那个洞）：写闸只在写的那一刻检查。管理员**事后**把环境 B（已绑 X）分配给客户 D，而环境 A（也绑 X）属于客户 C ⇒ D 读到 C 的池。**这不是攻击者能触发的**（攻击者无法分配归属），是**管理员脚下的雷**——但它会静默泄漏一整个精选池，正是本项目红线最恨的形状，而代价只是解析查询里多一个谓词。

解析器因此**一条 SQL 同时做四件事**（形状照抄 `withAuthorizedInteractionScope` `client-user-store.ts:783-795`）：

```sql
SELECT e.account_id
FROM client_env_scope s
JOIN client_environments e ON e.env_key = s.env_key
JOIN accounts acc ON acc.account_id = e.account_id          -- 悬空绑定读时 fail-closed（替代做不到的 FK）
WHERE s.user_id = $1 AND s.env_key = $2 AND s.source = 'admin'
  AND e.account_id IS NOT NULL
  AND NOT EXISTS (                                           -- 跨客户争用 → 不解析
    SELECT 1 FROM client_environments e2
    JOIN client_env_scope s2 ON s2.env_key = e2.env_key AND s2.source = 'admin'
    WHERE e2.account_id = e.account_id AND s2.user_id <> s.user_id
  )
```

= 归属闸 + 绑定 + accounts 存在性 + 争用闸。**每次请求现读**，对齐已有的「改归属即时生效」（`client-customer-auth:53`：范围 MUST NOT 内嵌于令牌）。

### D-4 解析器有两个方向，但只有一个权威 JOIN

`:683` 的方向是反的：`task.accountId`（真 accountId）→ 这个客户拥有它吗？

⇒ 解析模块暴露两个函数：`resolveBoundAccountForEnv(userId, envKey)` 与 `isAccountReachableByUser(userId, accountId)`。**两者 MUST 由同一个绑定+归属 JOIN 派生**，MUST NOT 各写一遍——否则两个方向会漂移，而 typecheck 抓不到（又是裸 `string`）。

返回**判别式结果**而非 `string | null`（`null` 会立刻退化回「不知道为什么，就当空的吧」）：

```
{ ok: true, accountId }
| { ok: false, reason: 'environment_not_owned' }   → 403
| { ok: false, reason: 'binding_unknown' }         → 409（该环境从未上报过登录账号）
| { ok: false, reason: 'binding_conflict' }        → 409（跨客户争用，fail-closed）
| { ok: false, reason: 'binding_unavailable' }     → 503（注册表读不到）
```

`binding_unknown` 与 `binding_conflict` **在协议上必须可区分**：前者是「等这个环境连一次就好了」的日常态（部署当天 ~16/18 个环境都是它），后者是**安全事件**。把它们合成一个码，就是把一次告警埋进日常噪声里。

### D-5 ESSENTIAL / INCIDENTAL：读离线可用，不可逆写要活体佐证

| | 读（`:364` `:374` `:419` `:498` `:623`） | 不可逆写（`:438` create-post、`:648` 建委托） |
| --- | --- | --- |
| 陈旧绑定的代价 | 读到上一个账号的语料——**幂等、非破坏、可回头** | **发布出去了**——不可回头 |
| 边缘离线时能兑现吗 | **能**（数据在库里） | **不能**（发布结构上就需要活浏览器） |
| 结论 | 活体前置是 **INCIDENTAL** ⇒ **MUST NOT 加**（加了就是重造本 bug） | 活体前置是 **ESSENTIAL** ⇒ **MUST 加**，且不花费本 change 想要的任何东西 |

**佐证判据刻意选用 `resolveEdgeIdForAccount`（幸存者），而非 `resolveAccountIdForEdge`（将被删者）**：

```
resolveEdgeIdForAccount(boundAccountId) === 'ads-' + envKey
```

- 语义正好是要问的那句：「我解析出的这个账号，此刻真的活在这个环境上吗」。
- **不给 `resolveAccountIdForEdge` 新增调用方** ⇒ 它的生产调用方仍恰好是 1 个（慢启动路由 `server.ts:4163`/`:4192`）⇒ **慢启动 change 仍能干净地删掉它**。反过来（用 `resolveAccountIdForEdge` 做佐证）会把那次删除卡死，制造一次本可避免的跨 change 纠缠。
- 多连接时 `resolveEdgeIdForAccount` 取最早登记者（`ws-server.ts:301-304`）⇒ 可能误拒。**误拒可接受**（fail-closed + 有日志），误放不可接受。

**诚实的代价（必须写下来，不许假装没有）**：给一个当前停着的环境**排一篇定时发布**会被拒。这是本 change 有意识付的价，不是遗漏；要放宽的话是另一个 change 的事（那时需要的是「兑现时刻校验绑定」，而不是「创建时刻不校验」）。

### D-6 42P01 → 503，而不是空

`curated-content-store.ts` 有 **4 处只读方法**把「表不存在」翻译成「没有数据」：`listForPanel:986-987`、`listForClient:1037-1038`、`facetsForPanel:1089-1090`、`getOneForAccount:1114-1115`。

改为抛 typed `CuratedContentUnavailableError`，由调用方映射：

| 调用方 | 今天 | 改后 |
| --- | --- | --- |
| `client-auth-server.ts:374` | `200 {items:[],total:0}` | `503 curated_content_unavailable` |
| `client-auth-server.ts:419` / `:498` | `404 not_found`（谎：行可能在） | `503 curated_content_unavailable` |
| `panel-server.ts:2312` | `404`/空 | `503 curated_unavailable`（面板**已有**的第三态） |
| `server.ts:1092` / `:1120` | 抛出会逃逸 | 映射为诚实的非成功码，**MUST NOT** 复用 `curated_target_unavailable`（那句是「这行不存在」= 谎） |

**为什么这动了 spec**：`panel-curated-content:77` 现文明写「当底层表尚不存在时，只读接口 MUST 回落为空结果而非 500」，scenario 叫「表不存在回空而非报错」。本 change 推翻**这半条**——它就是红线本身，只是穿了「优雅降级」的外衣。「MUST NOT 500 / 不崩闭环」的本意**原样保留**：503 不是 500，且同一条要求**已经**要求前端「加载中 / 暂无数据 / 服务不可用」三态可区分——缺表只是终于落进了它自己的第三态。

**blast radius 提醒**：`getOneForAccount` 是**共享**的（client-auth `:419`/`:498` + `panel-server.ts:2312` + `server.ts:1092`/`:1120`）。改它的降级行为**必须同时**处理这 5 个调用点，否则 `server.ts` 那两处会把 typed error 变成一次未捕获抛出。

## Risks / Trade-offs

| 风险 | 应对 |
| --- | --- |
| **陈旧绑定授权了不可逆写** | D-5：`:438`/`:648` 要活体佐证。**注意**：风险登记表 MUST NOT 只拿 `slow_start_since`（幂等可回滚）来推理——那两处是**修好后第一次变得可达**的、且不可逆。 |
| **绑定不追溯** ⇒ 部署当天 ~16/18 环境是 `binding_unknown` | 这是**诚实**取代了**谎言**，不是回归。UI 必须把它画成一等可见态；hello 一次即自愈。已列入运营预期。 |
| `binding_unknown` 在 UI 上退化成通用错误卡 | edge 侧一行人话化映射（`content-workspace.js` 的 `rejectionMessage` 词典，遵循「只翻译已知码、未知码原样透传」）。**在 edge 发版到达之前也不是红线违反**——通用错误卡是响亮且可见的，不是伪装的空态。 |
| **无 FK ⇒ 悬空绑定** | 每次读 JOIN `accounts`（`withAuthorizedInteractionScope:789-791` 的既有形状）⇒ 读时 fail-closed。这是真实取舍，已在 proposal Non-Goals 里诚实陈述。 |
| 争用闸误伤同客户多环境同账号 | 判据是 **owner 不同**，不是「账号已绑过」⇒ 同客户合法迁移不受影响。 |
| 与慢启动 change 抢 `client-user-store.ts` / `client-auth-server.ts` | **串行**（CLAUDE.md §7 热点文件单写者）。本 change 先落。 |

## 解析器终局清点（必须交代）

**本 change 之后 = 4 个**：

| # | 解析器 | 存活理由 |
| --- | --- | --- |
| 1 | `resolveEdgeIdForAccount`（`ws-server.ts:290-306`） | **永久存活**。account→edge，命令路由用。把命令路由给一个断连的边缘**在结构上就做不到** ⇒ 这里的活体依赖是 ESSENTIAL。本 change 额外把它用作 D-5 的活体佐证判据。 |
| 2 | `resolveAccountIdForEdge`（`ws-server.ts:316-333`） | **仅在本 change 内存活**。唯一生产调用方是慢启动路由（`server.ts:4163`/`:4192`）。本 change 刻意**不**新增其调用方 ⇒ 慢启动 change 落地时其调用方归零 → **由那个 change 删除**（留着就是在邀请别人复用这个反模式）。 |
| 3 | `withAuthorizedInteractionScope`（`client-user-store.ts:783-795`） | **永久存活**。视频号互动面的授权根（持 `FOR SHARE OF s,e,a,acc`）。那里 `account_id == env_key` 是**构造恒等式**（live `accounts` 表：`k1eooed5`/`k1eoujd8`，platform `wechat_channels`）⇒ 两个键空间**永不可能不一致** ⇒ 收敛它 = 零行为差的搅动。 |
| 4 | **新增**：绑定解析器（`client_environments.account_id`） | 本 change 的主体。唯一不要求边缘在线的 env→account 事实源。 |

**慢启动 change 之后 = 3 个**（#2 消失）。

## 已被证伪的假说（别再发现一遍）

- **「委托任务是一座自洽的 envKey 孤岛」——已推翻。** live `delegated_tasks` 30 行，`account_id` 长度只有 14 与 24 两种，**零条 8 字符行**；且 `delegated-task/store.ts:27` 的 `REFERENCES accounts(account_id)` 让 envKey 行**结构上不可能存在**。
- **「`:445` 的 `sourceRef` 也得改」——不必。** `edge:curated:${envKey}:${id}:create-post` 是不透明诊断字符串，从不被当键解析 ⇒ **自洽，别动它**。
- **「客户端画错了空态」——客户端无辜。** `content-workspace.js:438-443` 是三态成功闸，每种失败都是独立可见的错误卡 + 重新加载；`main.cjs` 的 `delegatedTaskRequest` 每条失败出口都回 `ok:false`。⇒ **一个和善的空态本身就证明了云端回的是 200-空。**
- **「视频号那个 503 是 bug」——不是，它是不可达的死代码。** `interaction-customer-api.ts:319`「平台登录状态尚不可用」**读起来和症状一模一样，一定会被重新发现并「修」一遍而毫无行为变化**。两条独立的理由：(a) 浏览器关闭时**没有任何东西**清 `interaction_auth_state`（只有 offboard/purge 会：`interaction-store.ts:1583` DELETE、`:1521` status='disabled'）；(b) `withAuthorizedInteractionScope`（`client-user-store.ts:783-795`）**已经** JOIN 了 `interaction_auth_state` 并持 `FOR SHARE OF s,e,a,acc`（`:793`）覆盖整个操作 ⇒ `getAuth` 不可能回 null。它只在测试里「开火」，因为 `customer-api.test.ts:53` 把 scope 打了桩。**那是 Defect 3，属于另一个 change，且根因在边缘渲染层，与本 change 零共享代码。**
