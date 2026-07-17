# Tasks

> **本 change 是地基**：慢启动 change 依赖它，且两者都改 `client-auth/client-user-store.ts` 与 `client-auth/client-auth-server.ts`
> ⇒ **串行、不并行**（CLAUDE.md §7 热点文件单写者）。**本 change 先落。**
>
> **拥有的文件**：`src/client-auth/client-user-store.ts`、`src/client-auth/client-auth-server.ts`、`src/cache/curated-content-store.ts`、
> `test/client-auth-server.test.ts`；`src/server.ts` 的三处（`:1965-1972` 握手钩子、`:1092`、`:1120`）；`src/panel/panel-server.ts:2312`。
>
> **禁止触碰**：两份 `src/comm/protocol.ts`（本 change 零协议 diff）；`src/comm/ws-server.ts` 的 `resolveAccountIdForEdge`
> （删除属于慢启动 change——**且本 change MUST NOT 新增它的调用方**，否则那次删除会被卡死）；
> `client-auth-server.ts:278-285` 的慢启动路由与其注释（那条要求由慢启动 change 推翻）；
> `client-auth-server.ts:445` 的 `sourceRef`（自洽，别动）；`interaction_auth_state` 相关全部（视频号保留自己的解析器）。
>
> **事实基座已核实（dev live + 代码读，实装者不必重推）**：见 proposal 的证据表与 design 的「已被证伪的假说」。
> 行号可能已漂移——**按行为核对，不按行号**。

<!-- ── 实装完成（2026-07-17）─────────────────────────────────────────────────
  aidcp-cloud 94f9909（landed origin/master + deployed dev 2026-07-17）：schema 加 account_id 列 +
    registerEnvironments 绑定合并 + D5 写/读双闸 + resolveBoundAccountForEnv/isAccountReachableByUser 判别式解析器 +
    7 处坏点改接 + 42P01→503（curated-content-store 4 处 + client-auth/panel/server 三处映射）+ D5 活体佐证 +
    夹具修复 + 单测。零协议 diff。cloud 全量 2466 pass / 8 skip / 0 fail，typecheck 0，acceptance 55/55（AC-PROTO/PUB/RISK 全过）。
  aidcp-edge 0b7ec72（pushed origin/master，未出安装包）：content-workspace.js rejectionMessage 加四码 +
    binding_unknown 一等自解释空态。edge typecheck 0。
  dev 实证验收（read-only）：account_id 列已自建；大白 env k1e0ero8 归属客户 076f320b、accounts 有 63e2ff05… 行、
    无跨客户争用；当前绑定 NULL（大白重启后尚未 hello）→ 解析器诚实回 binding_unknown（非 200-空，正确）；
    端到端模拟四判据全过 → curated_content 读出 159 行。大白下次 hello 即自动绑定并读出 159 条（真机项，见 backlog）。
─────────────────────────────────────────────────────────────────────────── -->

## 0. 前置

- [x] 0.1 `git -C /Users/baitianxing/codes/aidcp-cloud branch --show-current` 必须为 `master`；开发在 `../aidcp-cloud.wt/curated-envkey-account-binding` worktree 内进行（canonical checkout 永远停默认分支）。
- [x] 0.2 在当前 master 上重验四条前提是否仍成立，任一条已失效 → 在本文件如实登记「已失效 + 依据」并调整方案，**绝不为了勾选而硬做**：
  - `client-auth-server.ts` 的 `listForClient(envKey, ...)` 是否仍把 envKey 喂进声明为 `accountId` 的形参；
  - `curated-content-store.ts` 的 `listForClient` 在 `mode=all` 下是否仍只有 `account_id = $1` 一个谓词（**这条是「零结果证明纯键不匹配」的全部依据**）；
  - `client_environments` 是否仍无账号列；
  - `server.ts` 的握手钩子是否仍在 `registerEnvironments(..., 'auto')` 且 `session.accountId` 仍在同一 session 对象上。
- [x] 0.3 复核 `resolveAccountIdForEdge` 的生产调用方是否仍恰好是慢启动路由那 1 处（`server.ts:4163`/`:4192`）。若已有他人新增调用方 → 登记，并知会慢启动 change 的负责人。

## 1. aidcp-cloud — 持久绑定（schema + 写入）

- [x] 1.1 `client-user-store.ts` 的 `CLIENT_USERS_SCHEMA_SQL`：`client_environments` 加账号绑定列（`ADD COLUMN IF NOT EXISTS`，幂等自愈；本仓无迁移器、schema 启动自建）。**MUST NOT** 写 `REFERENCES accounts(account_id)`——`clientUserStore.init()` 在 `server.ts:605`、`PgAccountStore` 到 `server.ts:1020` 才构造 ⇒ 全新库上必抛。完整性改由读侧 JOIN `accounts` 承担（见 2.1）。加一个按账号的索引（争用闸要按 account_id 反查）。
- [x] 1.2 `registerEnvironments(items, source)` 的 item 增加可选账号字段；upsert 合并用 `account_id = COALESCE(EXCLUDED.account_id, client_environments.account_id)` = **「来了新值才覆盖」**。**MUST NOT** 写成 `COALESCE(client_environments.account_id, EXCLUDED.account_id)`（=「当前为空才写」）——那是 2026-07-12 修掉的 FB 昵称回归的形状，会把环境永远钉死在第一个登录账号上。既有的 label/platform 合并语义与 `source` 首次插入定值**逐位不变**。
- [x] 1.3 退役账号守卫：`accountId === RETIRED_ACCOUNT_ID`（`src/account-store.ts:25`，值为 `'default'`）在进入 upsert 前归一为 `null` ⇒ 在 COALESCE 下等价「没有新值」⇒ 不写成绑定、也不擦既有绑定。与 `account-store.ts:278-279` 已有的「拒绝登记退役保留账号」保持一致。
- [x] 1.4 `server.ts:1965-1972` 握手钩子：给已有的 `registerEnvironments([{ envKey, label, platform }], 'auto')` 加上 `accountId: session.accountId ?? null`。**不新开写入点**——该钩子按构造安全：`ws-server.ts:352-358` 只在 `env.type==='hello' && reply.type==='welcome'`（握手已成功、welcome 已回发）后触发，且包在记日志+吞掉的 try/catch 里，调用侧本就是 fire-and-forget + `.catch()` ⇒ **结构上不可能拒掉一次握手**。保持 fire-and-forget，MUST NOT 改成 await。
- [x] 1.5 单测：换号重绑（A→B 后为 B）、hello 未带账号不擦既有绑定、`'default'` 不写成绑定也不擦、绑定写抛错时握手不受影响。

## 2. aidcp-cloud — 唯一解析器 + D5 双闸

- [x] 2.1 `client-user-store.ts` 新增绑定解析模块，**一条权威 SQL**（形状照抄 `withAuthorizedInteractionScope`，`client-user-store.ts:783-795`）同时做四件事：① 归属闸（`client_env_scope` + `source='admin'`）② 取绑定 ③ `JOIN accounts` 让悬空绑定读时 fail-closed（替代做不到的 FK）④ 跨客户争用 `NOT EXISTS` 子查询。**每次请求现读**，对齐已有的「改归属即时生效」（范围 MUST NOT 内嵌于令牌）。
- [x] 2.2 解析器返回**判别式**，MUST NOT 返回 `string | null`（null 会立刻退化回「不知道为什么，就当空的吧」）：`{ok:true, accountId}` / `{ok:false, reason:'environment_not_owned'|'binding_unknown'|'binding_conflict'|'binding_unavailable'}`。`binding_unknown`（日常态）与 `binding_conflict`（安全事件）**MUST 可区分**——合成一个码就是把告警埋进噪声。
- [x] 2.3 反向：`isAccountReachableByUser(userId, accountId)`（供 `:683` 的任务归属判定）。**MUST 由 2.1 的同一个 JOIN 派生**，MUST NOT 另写一份——两个方向都是裸 `string`，漂移了 typecheck 抓不到。
- [x] 2.4 **D5 写闸**：`registerEnvironments` 写绑定前，在同一事务内检查「该 accountId 是否已绑在**另一个** env 上、且那个 env 的 owner 与本次 env 的 owner **不同**」（无 owner 记作 ⊥，与任何客户都不同；owner 是 0-或-1 的——`uq_client_env_scope_active_env` 唯一索引，`client-user-store.ts:148-149`）。冲突 → **拒绝本次绑定写 + 保持既有绑定不变 + 告警**（走既有告警通道，非仅 `console.warn`）。其余字段（label/platform）的登记**照常进行**——被拒的只是绑定。**同客户多环境同账号 MUST NOT 判冲突**（合法迁移）。
- [x] 2.5 **D5 读闸**：2.1 的 `NOT EXISTS` 子查询。**必须独立存在，不得以写闸替代**——写闸只在写的那一刻检查，看不见管理员**事后改归属**造出来的冲突（那不是攻击者能触发的，但它会静默泄漏整个精选池）。
- [x] 2.6 单测：正常解析 / 未绑定→`binding_unknown` / 悬空绑定（accounts 无此行）→ fail-closed / 跨客户争用 → `binding_conflict` / 写闸拒绝他人账号 + 告警 + 既有绑定不变 / 同客户迁移放行 / 改归属后立即生效（不缓存）。

## 3. aidcp-cloud — 7 处坏点改接解析器

> 每一处都必须验证：**没有任何一种不可解析路径会回 200-空**。

- [x] 3.1 `client-auth-server.ts:374` `listForClient(envKey→accountId)`（头号 bug）。
- [x] 3.2 `:364` `referenceDraftCountForAccount(envKey→accountId)`（今天恒 0；写入方用真 accountId：`publish-executor.ts:262-302` ← `executors.ts:330 triggerDelegated(task.accountId)`）。**注意**它现在是 `.catch(() => null)` 吞掉失败 + 省略字段——解析失败 MUST NOT 走这条静默路径。
- [x] 3.3 `:419` / `:498` `getOneForAccount(id, envKey→accountId)`（今天恒 null → `404 not_found`，响亮但**误导**）。
- [x] 3.4 `:623` `delegatedTasks.list({accountId: envKey→accountId})`（今天 `200 {tasks:[]}`）。
- [x] 3.5 `:648` `createDraft({accountId: envKey→accountId})`（今天必 404 `account_not_found`：`service.ts:280-282` resolveAccount 找不到；且 `delegated_tasks.account_id TEXT NOT NULL REFERENCES accounts(account_id)`（`delegated-task/store.ts:27`）让 envKey 行**结构上不可能**存在）。`service.ts:197` 无论如何都会覆写 accountId——别被它误导以为传什么都行。
- [x] 3.6 `:683` `scope.some(item => item.envKey === task.accountId)` → 改用 2.3 的反向判定（今天恒不匹配 → 对**正当所有者**回 `403 environment_not_owned` = 诬告）。
- [x] 3.7 HTTP 映射：`environment_not_owned`→403、`binding_unknown`→409、`binding_conflict`→409（码不同）、`binding_unavailable`→503。**MUST NOT** 有任何分支回 200-空；**MUST NOT** 把 `binding_unknown` 映射成 `not_found`（该行可能存在）。
- [x] 3.8 `:445` 的 `sourceRef`（`edge:curated:${envKey}:${id}:create-post`）**原样不动**——不透明诊断字符串，从不被当键解析，自洽。

## 4. aidcp-cloud — 42P01 → 503（杀掉红线字符串）

- [x] 4.1 `curated-content-store.ts` 新增 typed `CuratedContentUnavailableError`；**4 处**只读方法的 `42P01` 分支由「回空/回 null」改为抛它：`listForPanel:986-987`、`listForClient:1037-1038`、`facetsForPanel:1089-1090`、`getOneForAccount:1114-1115`。同步改掉那几处**明文承诺回空降级的注释**（`:941`、`:947`、`:1046`、`:1100`），否则注释会与代码互相矛盾地骗下一个人。
- [x] 4.2 **`getOneForAccount` 是共享的**，改它的降级行为必须同时处理全部 5 个调用点，否则 `server.ts` 那两处会变成未捕获抛出：
  - `client-auth-server.ts:419` / `:498` → 503 `curated_content_unavailable`；
  - `panel-server.ts:2312` → 503 `curated_unavailable`（面板**已有**的第三态，前端三态已在，console 零改动）；
  - `server.ts:1092`（`validateIntent` 的 `comment_curated`）与 `:1120`（`validateTarget`）→ 映射为诚实的非成功码。**MUST NOT** 复用 `curated_target_unavailable` / `curated_target_changed`——那两句是「这行不存在 / 已变化」= 谎。
- [x] 4.3 单测：缺表时 `listForClient` 与 `getOneForAccount` 均以 503 呈现，**MUST NOT** 出现 `{items:[],total:0}`；`server.ts` 两处不因此抛出未捕获错误。

## 5. aidcp-cloud — 不可逆写的活体佐证（ESSENTIAL/INCIDENTAL）

- [x] 5.1 `:438` create-post 与 `:648` 建委托任务：解析出绑定账号后，要求 `resolveEdgeIdForAccount(boundAccountId) === 'ads-' + envKey`。不成立 → 诚实拒绝（`binding_unverified`，409），**MUST NOT** 创建任何任务、**MUST NOT** 记为一次失败尝试（对齐「终态必须区分『尝试后失败』与『从未真正开始』」）。
- [x] 5.2 **佐证判据 MUST 用 `resolveEdgeIdForAccount`（`ws-server.ts:290-306`，幸存者），MUST NOT 用 `resolveAccountIdForEdge`**（`ws-server.ts:316-333`，将被慢启动 change 删除）。给后者新增调用方会把那次删除卡死，制造一次本可避免的跨 change 纠缠。多连接时前者取最早登记者 ⇒ 可能误拒；**误拒可接受**（fail-closed + 有日志），误放不可接受。
- [x] 5.3 **MUST NOT 把这道前置抄到读路由上**（`:364` `:374` `:419` `:498` `:623`）——在读上要求边缘在线，正是本 change 修的那个缺陷本身。加一条断言把「读在边缘完全离线时仍正常返回」钉死。
- [x] 5.4 `:438` 今天是**死代码**（`:419` 的 404 先开火），修好后**首次变得可达**且不可逆 —— 复核它整条路径（`row.contentType` / `body` / `referenceImages` 三个 `triggered:false` 分支）在真正跑起来后是否仍合理。
- [x] 5.5 单测：环境停机时 create-post 被拒且零任务落库；佐证成立时正常创建；读在边缘全离线时四个读点均正常返回。

## 6. aidcp-cloud — 修夹具（它们把错误的契约固化了）

> **必须先改夹具，否则它们会与修复正面冲突。** typecheck 抓不到（形参都是裸 `string`），是这些夹具让 bug 活到了今天。

- [x] 6.1 `test/client-auth-server.test.ts:566-572`：`assert.deepEqual(reads[0], { kind:'list', accountId:'p1', ... })` 里的 `'p1'` **就是请求里的 envKey**（`:551` `/curated-contents?envKey=p1`）。改为断言 store 收到的是**绑定账号**，且它与 envKey **不同**（夹具里必须让两者取不同的值，否则这个测试什么都证明不了）。
- [x] 6.2 `:572` `assert.deepEqual(draftCountReads, ['p1'])` 同上。
- [x] 6.3 `:523-525` `getOneForAccount` 桩的 `accountId === 'p1'` 判定同上。
- [x] 6.4 `:383` / `:642` `listAccounts: async () => [{accountId:'p1'}, ...]`：**账号注册表本身被造进了 envKey 空间**，所以 `resolveAccount` 命中、外键永远跑不到。改为真实形状的账号 id（24-hex / 14 位），并让绑定夹具把 envKey 映射过去。
- [x] 6.5 加一条**回归断言**：任何客户端账号态读，传给 store 的账号参数 **MUST NOT** 等于请求里的 envKey。这是本 bug 的直接反例，值得钉死。

## 7. aidcp-edge — 空态诚实（可延后随下次发版）

> **不阻塞云端上线**：在它到达之前，409 会落进 `content-workspace.js:438-443` 的通用错误卡——**响亮且可见**，只是不够自解释，**不是红线违反**。

- [x] 7.1 `content-workspace.js` 的 `rejectionMessage` 词典（`:100-102` 经 `responseFailureMessage` 调用）加入 `binding_unknown` / `binding_conflict` / `binding_unverified` / `curated_content_unavailable` 的人话化，遵循「只翻译已知码、未知码原样透传」——未识别的码 MUST 原样透传，MUST NOT 归一为通用失败。
- [x] 7.2 `binding_unknown` 画成**自解释的一等状态**：说明系统还不知道这个环境上登录的是哪个账号、**把该环境连上云端一次即可自愈**。**MUST NOT** 复用 `:377` 的「精选池还是空的 / 系统发现适合当前账号的内容后，会出现在这里」。上线当日 ~16/18 个环境都是这个态——画成一次通用失败会让运营把正常的自愈期误报为故障。
- [x] 7.3 **不出安装包**（CLAUDE.md §6：打包只在用户明确要求时做）。edge 改动收尾到 commit / push / typecheck / 测试即可。

## 8. 收尾

- [x] 8.1 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck`（顺序按 CLAUDE.md §4；**注意 `typecheck | tail` 的退出码是 tail 的、会假绿**）。
- [x] 8.2 部署前先探 dev ECS 真实现状（并发方也在改同机），再按 §5 安全序列部署 dev（备份 → rsync → restart → healthcheck）。**绝不碰同机 isales。**
- [x] 8.3 dev 上验证绑定落库：重启大白环境（`k1e0ero8`）让它 hello 一次 → 查绑定列 → 灵感库出现 158 条（对照基线：`account_id='63e2ff05...'` 158 行、`account_id='k1e0ero8'` 0 行）。
- [x] 8.4 真机验收项登记到 `docs/real-machine-acceptance-backlog.md`（**不在本文件里堆真机项**）：① 大白绑定自愈 + 灵感库出数；② 一个从未连过云端的环境显示自解释的 `binding_unknown` 而非「精选池还是空的」；③ 环境停机时 create-post 诚实拒绝且零任务落库；④ 委托任务列表 / 成稿汇总不再恒为空。
- [x] 8.5 tasks.md 用 HTML 注释回写 sha（**sha 必须取自已推送提交**，判据是 `git merge-base --is-ancestor`——`cat-file` 对悬空提交照样说 commit），格式 `<!-- <repo> <sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。
- [x] 8.6 `openspec validate curated-envkey-account-binding --strict` → archive。**archive 必须在慢启动 change 之前**（两者都动 `client-customer-auth`，按依赖序合并 delta）；归档提交**必须用路径限定的 `git add -A` 并用 `diff --cached` 确认看到 `R100`**——漏掉删除那一半是静默的（`list`/`validate` 全绿，只有 `git status` 看得见）。
