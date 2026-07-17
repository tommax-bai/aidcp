# Why

这是视频号（WeChat Channels）评审的**残余批**。同批已有 4 个 change 在 `origin/main` 上（`wechat-edge-runtime-honesty` / `wechat-edge-auth-recoverable` / `wechat-store-and-circuit` / `wechat-customer-api-contract`），另有两个同名 change 已完成并部署（详见「已剔除的发现」）。本 change 收的是**没有被任何 change 覆盖的那批发现**，逐条已在 2026-07-17 的当前主干上重验为仍然成立。

八条发现共用一条主线：**系统在它其实不知道 / 其实没做到的地方，向客户与运营陈述了一个确定的结论**。

- **发送编排把「现在暂时投不出去」实现成「这个任务永远失败」**（H6）。边缘处在验证码硬暂停期时回复命令必然投递为 0，整批排队积压会被 30s 恢复循环烧成终态失败，人工审批过的稿子一并烧掉。刺眼的不对称就在同一个函数里：「边缘完全离线」这条分支不建尝试、留在排队态等自愈，「投递数为 0」这条却直接判死——两者成因同为暂时性。
- **失败后的重试在结构上不可能成功**（H9）。发送尝试的幂等键在库上无条件全局唯一且不含尝试序号，而模板渲染是确定性的，于是任何重试必然撞唯一约束，并被回一句「已有发送尝试在进行中」的假话——而此时可能一个活跃尝试都没有。私信渠道因 AI 润色默认关闭，重试是 100% 结构性阻断，运营只能陷入 409 死循环空转。同表的「任务+尝试序号」唯一约束、尝试序号递增逻辑、可重试标记三处设计共同预设了「一个任务可以有第 2、3 次尝试」，全局唯一把这个前提直接推翻。
- **一道安全吊销 fail-open**（H1）。撤销读写能力与撤销登录态两条更新语句，在主键之外多带了一个环境标识条件，而该列在库里可空、管理员配置开关那条路径从不写它。空值比较既不真也不假，更新命中 0 行；没有任何一处检查更新行数，于是系统写下解绑记录、写审计、向客户返回成功——而读写开关仍是开、登录态仍是「活跃」，后台面板把一个**已终止**的账号显示成「允许读取」。同样刺眼的不对称：**授权**那条更新只认账号主键、永远生效；**吊销**这条多带条件、于是条件生效。全文件其余写入者也都只认主键，吊销是唯一的例外。
- **H12 的修复自己开了一个新洞（本 change 接手）**。上游 `60acb89` 把「缺绑定即回滚」换成了「记清理墓碑 + 继续」，解掉了管理员的四方死锁——但那条新路径**完全不撤销任何能力**，且能力投影只看待处理解绑、对墓碑无感。等于拿死锁换了个 fail-open，还把 H1 的暴露面从「管理员配置过的账号」扩大到「**每一次**对未登录环境的吊销」。恢复路径本身已经存在（迟到的登录态把墓碑兑现成正式解绑），但没有测试钉住，也没有写进 spec。
- **能力投影凭空捏造绑定**（M11）。环境标识缺失时被回落成账号 id，于是作用域校验恒真——把「不确定是否绑定」洗成「作用域有效」，这是静默假成功的教科书形态。
- **定向同步编造平台时间戳**（H7）。客户对某个帖子 / 会话点「重新同步」时，边缘把**云端下发请求时的时钟**当成平台的更新时间上报。这个假值一路写进会话的「最后消息时间」，而云端的写法是取最大值——**永不回退、无法自愈**。后果不是显示错一次：该帖下每条评论会话被改写成点击时刻、全部跳到收件箱顶部显示「刚刚」，而真实最新评论可能是三天前的；该字段同时是收件箱的排序键与分页游标，排序和翻页一起坏掉，只能改库恢复。同一个错误在两个文件各写了一遍，说明这不是笔误，而是这条链路缺一条契约。
- **后台动作枚举漂移**（M12）。云端本批给风控动作全集加了私信回复动作，管理后台的手工镜像仍停在 8 个，于是安全限额页出现 3 行「动作」列空白、编辑弹窗标题显示 `undefined`——而私信回复配额默认是 0、放开它的唯一入口就是这一页，运营认不出该调哪三行。同类漂移在本仓已经把 `/roles` 整页打崩过一次，现有的崩溃防线只覆盖「对象值徽标映射」，标量文案映射仍是裸取、未知值静默渲染成空白（不崩，但更难发现）。
- **冷启动 clamp 不认平台白名单**（M10）。慢启动的平台准入判定只作用于对外投影，不作用于实际 clamp。全局旁路开关一开，视频号账号仍会被夹到小红书浏览曲线上——第 1~2 天评论上限为 0、入站评论回复被夹成 0——而对外投影同时宣称该账号「平台不支持慢启动」。界面说没在养号，配额却被一条从不属于它的曲线压着，无日志、无告警。
- **台账已无法用于对账**（M9）。视频号互动管理那份台账里 5 处提交号指向 rebase 掉的悬空提交，在任何新 clone 里都取不到；台账里「均已集成到各自默认分支」一句对其中一个可直接证伪。工作本身没丢（主干上有逐字同名的等价提交），但台账失去了它唯一的用途；另一份台账已经订正过同一批 sha，两份现在互相矛盾。同一 change 的冻结 spec 还把协议消息类型总数钉死为 89（两端代码与 `docs/protocol.md` 实测均为 91），归档会把这条 SHALL 级的过时计数烘焙进主 spec。

# What Changes

## 云端 — 发送失败语义（H6 / H9）

- **投递前先查边缘暂停态**：复用发布链已有的实现（`publish-dispatcher.ts` 的验证码硬暂停闸 + `ws-server.ts` 的 `isEdgePaused`）。暂停期零副作用：不建尝试、不烧稿、任务留在 `queued`，等暂停解除后由既有 30s 恢复循环自动重投。
- **投递数为 0 时不置任务终态**：与同函数中「边缘完全离线」分支的语义对齐——两者成因同为暂时性，必须走同一条自愈岔路，而不是一条自愈、一条终局。
- **`sent > 1` 与下发抛异常两条分支的 `ambiguous` 语义保持不变**：那两条是「无法证明命令未离开进程」，保守留不确定态是对的，**MUST NOT** 一并放开——重复评论的代价高于人工核查。
- **幂等键全局唯一降级为「仅活跃状态」的部分唯一索引**（同表兄弟索引 `uq_interaction_send_attempts_active_job` / `_active_account` 已经是这个写法），令一个任务的第 2、3 次尝试在结构上成为可能。需新增 migration `0046`（接手时主干已占用 `0045_wechat_store_and_circuit.sql`，故顺延一号）。
- **拆分错误映射**：键冲突不得再冒充「已有发送尝试在进行中」。真的有活跃尝试才这么说；否则如实报键冲突。
- **清理 `retryable` 这个全仓无消费者的谎言标记**：接线成恢复循环的真实判据，或删除。二选一，不得留着让读者误以为重试语义已实现。

## 云端 — 吊销作用域（H1 / H12 遗留缺口 / M11）

- 删除两条吊销语句里多余且危险的环境标识条件（主键已是「平台+账号」），并**检查更新行数**：预期要撤销却命中 0 行，是结构性异常，MUST 报错回滚，MUST NOT 向客户回报成功。
- **清理墓碑在同一事务里一并撤销读写能力与登录态**；墓碑的恢复路径（迟到的登录态把墓碑兑现成正式解绑）已存在，本 change 将其显式写进 spec 并补测。
- 能力投影不得凭空捏造绑定：环境标识缺失时 MUST 把全部能力投影为关闭，MUST NOT 用账号 id 顶替出一个「看起来合法」的作用域；未了结的清理墓碑 MUST 与待处理解绑一样构成能力屏障。
- **不改 schema**，因此无 migration。理由见下。

**Schema 判断：只改查询，不动表结构。** 三条理由：① 该列可空是**正确**的——管理员可以在环境绑定之前先把开关配好，「已配置、尚未绑定」是真实且合法的状态，加 NOT NULL 等于要么发明哨兵值、要么禁掉预配置，是远超 bugfix 的行为变更；② 把它并进主键是**错的**——运行控制行的身份是账号，边缘上报时用的是「按账号主键 upsert、顺带覆盖环境标识」，可见该列是**可变属性**而非身份，并进主键会让一个账号累积出多行控制记录，把 fail-open 换成 fail-multiple；③ 缺陷不在可空，而在**全文件唯一一条**语句拿可变属性当键，最小且正确的修法是把这个异类拉回一致。对活跃库做一次零收益的 migration 只增加风险。

## 边缘 + 云端 — 同步时间戳诚实（H7）

- 定向（scoped）同步路径**不再合成时间戳**：边缘内部类型 `WechatPost.updatedAt` / `WechatDmSession.updatedAt` 放宽为 `number | null`，定向路径传 `null`，表达「平台更新时间未知」而不是编一个。
- 评论侧：线程时间戳退回**平台事实**——`post.updatedAt` 为 `null` 时直接取根评论的 `createdAt`（平台值，恒存在），不再和一个假值取最大值。
- 私信侧：线程时间戳取本页消息 `createdAt` 的最大值；**若本页无消息且无平台更新时间，则不发出该线程行**，让字段缺失而不是填假值。
- 云端加一道可执行的防御：拒绝**未来时间戳**的线程行（超出观测时刻 + 时钟偏移容差即 422 拒整批）。理由是取最大值合并下一个未来值会永久粘住，必须在入口拦，**MUST NOT** 静默裁剪——裁剪会把「边缘在编值」这个上游缺陷藏起来。
- **不做**存量数据批量修复（理由见下），改为登记真机 backlog。

**存量数据为何不修**：视频号读取默认关闭（`commentsReadEnabled` / `dmReadEnabled` 均为 `false`），污染最多停在 dev、未触达生产客户。且修复本身有歧义——「最后消息时间」理论上可从消息的平台创建时间最大值反推，但全局同步路径下平台给的会话更新时间**合法地**可以领先于已翻页到的最新消息，一刀切回填会把这些正确值改错。故只在 backlog 留一条「用诊断查询列出可疑线程、由运营按真机数据判定」，不写自动回填。

## 后台 — 动作镜像与未知值回落（M12）

- **动作镜像补齐私信回复动作**：镜像数组、中文文案映射、徽标色映射、以及 `api.ts` 里那份手写的配额动作联合类型，四处同补；既有的镜像自洽测试与 live 对拍哨兵随之覆盖新动作。
- **未知动作值优雅回落，绝不空白、绝不崩页**：按线上值取中文文案的地方，未知值 SHALL 回落为可见的原值标签。落地手段沿用现有的容错取值入口范式，并把守卫测试的扫描面从「对象值映射裸取」扩到「标量文案映射裸取」。不引入代码生成 / 共享包（YAGNI：本仓只有一处消费方、live 对拍哨兵已能探测漂移，结构性根治的收益不抵引入构建期跨仓依赖的代价）。

## 云端 — 冷启动 clamp 尊重慢启动平台白名单（M10）

- 让 clamp 与投影共用同一道平台准入闸：投影说不适用，clamp 就 MUST NOT 生效。副产品是视频号私信回复的那处逐窗口特判成为死代码，一并删除。**MUST NOT** 改为「再补一个评论豁免」——补豁免会把「白名单说不支持」和「clamp 照夹」的矛盾固化下来，且下一个新增动作会再次默认落入被夹集合。

## 控制仓 — 台账与冻结计数订正（M9）

- `wechat-channels-interaction-management/tasks.md` 的 5 处悬空提交号改为主干上真实可达的等价提交号，被证伪的那句「均已集成到各自默认分支」按事实改写，并消除与另一份台账（真机 backlog，已于 2026-07-17 订正过同一批 sha）的矛盾。判据统一为 `git merge-base --is-ancestor <sha> origin/<默认分支>`。
- **附带一条（同属该 change 的可验证性欠账，故同批处理）**：冻结 spec 的消息类型总数 89 → 91，在其归档前落地，避免过时计数被烘焙进主 spec。

# 已剔除的发现（上游同名 change 已完成并部署，绝不重复实装）

| 发现 | 处置 | 依据 |
| --- | --- | --- |
| **M1**（请求是否离开进程的诚实位） | 剔除 | 已由 `origin/main` 上的 `wechat-send-failure-semantics`（6/6，edge `6afa18f` / `29ef51b`）做完：`WechatChannelsApiClient` 拆开请求错误与响应解析错误，解析错误提升为「已发出」证据；`WechatReplySender.isDefinitiveFailure` 以可信的「未发出」证据为首要判据。「确定没离开进程 → failed，其余 → ambiguous」的红线在边缘侧已守住。该位不跨协议，云端拿不到它——**不要为它加协议字段**。 |
| **H12**（缺绑定即回滚，四方死锁） | 剔除 | 已由 `origin/main` 上的 `wechat-env-ownership-revocation`（12/12）做完，cloud `60acb89` / console `643aad5`，已部署 dev。两处 `ROLLBACK + offboard_binding_missing` 已换成「记清理墓碑 + 继续」。**但它遗留的能力撤销缺口由本 change 接手**（见上）。 |
| **M10**（冷启动配额豁免） | **收进来** | 主评审人推测该缺口已随账号级慢启动改造作废。**2026-07-17 在 `aidcp-cloud` 主干现场复核：仍然成立**，详见下节。 |

> **同名不同物的坑**：`openspec/changes/` 下现有的 `wechat-send-failure-semantics` / `wechat-env-ownership-revocation` / `wechat-console-enum-and-ledger` / `wechat-sync-timestamp-honesty` 四个 change，与本批评审草稿**重名但内容不同**——它们是各自独立完成的上游 change。核对上游是否已覆盖某条发现时，**MUST 按内容核对，MUST NOT 凭 change 名判断**。

# 核实记录（2026-07-17 主干实测；接手时请按 tasks §0 重验）

基线：`aidcp` `origin/main` = `2cff970`，`aidcp-cloud` `origin/master` = `6122083`，`aidcp-edge` `origin/master` = `0d38116`，`aidcp-console` `origin/master` = `643aad5`。

- **H6**：成立。`send-orchestrator.ts` 的 `dispatchQueued` 投递前无任何暂停态检查；`sent === 0` 分支调 `markDispatchFailed` 判终态；同函数 `!edgeId` 分支反而不建尝试、留 `queued`（即那条不对称仍在）。
- **H9**：成立。`migrations/0039_interaction_inbox.sql` 的 `idempotency_key` 仍是无条件 `TEXT NOT NULL UNIQUE`；`createAttempt` 的 23505 catch 仍一律映射成「已有发送尝试在进行中」。`interaction_send_attempts.retryable` 列仍**无任何消费者**（全仓其余 `retryable` 命中均为 `InteractionError.retryable`，是另一回事）。
- **H1**：成立。`enqueueOffboard` 的两条撤销 UPDATE 的 WHERE 仍带 `env_key=$2`，且两处均无 `rowCount` 检查。
- **H12 遗留缺口**：成立。`enqueueCleanupHold` 只 `INSERT INTO client_env_revocation_holds`，**不撤销任何能力**。恢复路径 `reconcileRevocationHolds` 已存在（迟到登录态 → 兑现 offboard → 删墓碑）。
- **M11**：成立。`projectRuntimeControls` 仍有 `const envKey = controls.envKey?.trim() || accountId`，`scopeValid` 因此恒真；`hasPendingOffboard` 仍只读 `interaction_offboards`、对墓碑无感。
- **H7**：成立。`dm-sync.ts:35` / `comment-sync.ts:36` 的定向分支仍用 `request.requestedAt` 合成占位对象的 `updatedAt`；`types.ts` 的两个 `updatedAt` 仍是非空 `number`；`interaction-store.ts:450` 仍是 `last_message_at=GREATEST(...)`（即假值仍不可回退）。协议 `InteractionSyncThread.updatedAt` 仍是非空 `number`。
- **M12**：成立。云端 `RISK_ACTIONS` 9 项含 `dm_reply`；后台 `RISK_ACTIONS` / `RISK_ACTION_LABEL` / `RISK_ACTION_COLOR` 均为 8 项。`QuotasPage.tsx` 的动作列渲染与编辑弹窗标题两处均为裸取，未知值得到 `undefined`；排序用的 `ACTION_ORDER` 对未知值给出 `NaN`。**新发现（素材未记）**：`src/types/api.ts` 的 `QuotaAction` 是**另一份手写的 8 项联合类型**，与 `aidcp-enums.ts` 的镜像各写一遍——补齐时必须同改，否则 wire 类型仍在撒谎。
- **M10**：**核心成立**（原报告的具体形态部分作废）。账号级慢启动改造确实把视频号排除在 `SLOW_START_PLATFORMS`（`['facebook','xiaohongshu']`）之外，但该白名单**只被 `slowStartView()` 引用，`applyColdStartClamp()` 自己不查**。clamp 只判「平台是否可确认」，可确认即取曲线（`coldStartDailyCap` 里 `platform === 'facebook' ? FB 曲线 : 小红书曲线`）——视频号落小红书曲线。故全局旁路开关一开，视频号号仍被夹。原报告所指的「只豁免私信回复、漏了评论」这一具体形态仍然在代码里（`applyColdStartClamp` 里对 `wechat_channels` 的 `dm_reply` 逐窗口特判），只是正确修法不是补评论豁免，而是补平台准入闸。**另有一层加重**：env 旁路场景下 `slowStartView()` 在 `anchor.source !== 'account'` 时直接返回 `state:'off', eligible:true`——即投影连「不适用」都不说，直接说「没开」，而 clamp 正在夹。
- **M9**：成立。5 处悬空 sha 逐个用 `merge-base --is-ancestor` 复验，全部**不可达**（对象仍在本地存在，`git cat-file` 照常回 `commit`——**不能用它判可达性**）；4 条主干等价提交逐个复验**可达**且 subject 逐字相同。台账中「the control contract `a678003` … are all integrated on their default branches」一句被 `a678003` 不可达直接证伪。真机 backlog 已于 2026-07-17 把 `a678003` 订正为 `3aa51de`，两份台账现互相矛盾。冻结 spec 写「使目标 `MessageType` 总数为 89」，两端 `protocol.ts` 联合类型成员实测各 91。

# Capabilities

## Modified Capabilities

- `wechat-channels-interaction`：规定回复发送的失败语义——哪些失败可重试、什么把任务从不可发状态拨回来、诚实位必须有消费者；以及定向同步不得编造平台时间戳，取不到就让字段缺失。
- `inbound-interaction-management`：线程时间戳必须来自平台，未来值必须在入口被拒。
- `client-customer-auth`：客户环境的能力吊销必须真正命中并被验证；未绑定环境的墓碑必须同时撤销能力并声明恢复路径；能力投影不得捏造绑定。
- `console-panel-api`：风控动作镜像补齐私信回复动作；按线上值取中文文案的未知值 SHALL 优雅回落为可见原值标签，绝不空白或抛错。
- `interaction-risk-gating`：冷启动 clamp SHALL 与对外投影共用同一道慢启动平台准入闸；平台不在白名单内 MUST NOT 叠加任何曲线 clamp。

# 跨仓与跨 change 协调

**本 change 跨 4 个仓**：`aidcp-cloud` 为主战场（H6 / H9 / H1 / H12 遗留 / M11 / M10 + H7 的入口防御），`aidcp-edge`（H7 的定向同步侧），`aidcp-console`（M12），控制仓 `aidcp`（M9）。四段互不依赖，可分头做；但 §3（M9）改的是另一个仍活跃的 change 的文件，见下。

必须协调的具体点：

1. **`src/interactions/interaction-store.ts` 可能与 `wechat-store-and-circuit` 撞车**。H9 的错误映射修正、`retryable` 处置与 H7 的入口未来值校验都落在这个文件（本 change 在云端的主战场其实是 `send-orchestrator.ts`）。改动务必 surgical、只动本 change 点名的函数（`createAttempt` 的 23505 映射、`markDispatchFailed`、`applyReplyResult` 的 `retryable` 赋值、同步批次入口校验），集成时按 rebase 顺序解冲突。
2. **`src/server.ts` 要接两行 dep 注入**（H6 的 `isEdgePaused`、M11 的墓碑查询）。`server.ts` 是共享文件：**合回前先 rebase 到最新 master 再改，勿做无关重排**。`isEdgePaused` 在 `server.ts` 已被其它三处消费，照抄注入方式即可。
3. **`src/risk/risk-controller.ts`（M10）不是热点清单成员，但改动频率高**。动手前先 `git log -3 -- src/risk/risk-controller.ts` 确认无并发改动在飞；有则先与该 change 协调串行。（热点是 `risk-state-machine.ts`，本 change 不碰。）
4. **§3 改的是 `openspec/changes/wechat-channels-interaction-management/` 下的文件**（另一个仍活跃的 change）。只订正可验证性，**MUST NOT** 改动其 task 的完成判定或勾选状态。
5. **`console-panel-api` capability 同时被 `wechat-console-enum-and-ledger` / `wechat-store-and-circuit` / `wechat-channels-real-runtime-closure` / `wechat-channels-interaction-management` 的 delta 触碰**；本 change 对它只 ADD 一条新 requirement + MODIFY 那条既有的 enum 哨兵 requirement，已复核与上述四者**无同名 requirement 冲突**。

# 并行安全与热点文件

本 change **不触碰** CLAUDE.md 列的四个热点文件（两份 `protocol.ts`、command-bridge 动作映射、`RoleName` + role-catalog、`risk-state-machine.ts`），故与本批其余 change 可全并行开发；集成仍串行（合回前 rebase + `test:acceptance` + `typecheck`）。

**H7 的设计约束（务必保留）**：方案**刻意**让 `InteractionSyncThread.updatedAt` 保持 `number` 非空，靠「取平台值 / 不发这一行」两条路避开协议改动。若为了表达「未知」而把它改成可空，就要动两份 `protocol.ts`——那会碰热点文件、破坏本批并行安全。**不要走那条路。**

# 归档序

`wechat-channels-interaction` 与 `inbound-interaction-management` 两个 capability 目前**只存在于活跃 change `wechat-channels-interaction-management` 的 delta 里，尚未并入 `openspec/specs/`**（`openspec list --specs` 实测两者均不在列）。**本 change 必须在它之后归档**，否则 spec-merge 会找不到基线 capability。这也是这两份 delta 用 `## ADDED Requirements` 而非 `MODIFIED` 的原因——基线 capability 尚不存在，没有可 MODIFY 的对象。

`console-panel-api` 与 `interaction-risk-gating` 已在 `openspec/specs/` 里，故那两条既有 requirement 用 `MODIFIED`（requirement 标题已逐字复核存在）；两份 delta 中的新增部分仍用 `ADDED`。
