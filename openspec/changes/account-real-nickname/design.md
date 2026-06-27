## Context

后台「账号」列显示的是占位/运营字符串（实测单租户下就是 `default`），而不是登录账号的小红书真实昵称（如「工程师大白」）。坐实代码：

- `accounts` 表（`../aidcp-cloud/src/account-store.ts`）无 nickname 列；seed `('default','default')`，`label` 是 `account_id` 副本（`ensureAccount`/`setPaused` 也按 `label = account_id` 兜底，故 `label` 对新账号**非 NULL**）。
- `accountId` 现在来自**登录态读出的真实稳定 userid**（24 位 hex，`account-identity-from-login` 已落：`../aidcp-edge/src/cdp/self-identity.ts:44-46`、`main.ts:133`），`AIDCP_ACCOUNT_ID` 降级为可选覆盖。06-23 提案里「accountId = AIDCP_ACCOUNT_ID 运营字符串」的说法**已过时**。
- 协议 `author`/`authorId`（`note.detail` / `profile.detail`）描述的是**被浏览**对象，不是登录账号本身。

所以要让后台显真名，必须新增「**登录账号自身昵称** → 上报 → 持久化 → 展示」这条链路，落点跨 edge / cloud / console 三仓。

**本设计经一道多 agent 对抗评审（CLAUDE.md §3）打磨**，相对 06-23 初稿有重大纠偏，见末尾「Drift corrections」。其中一条是 **BLOCKER 级红线修复**。

## Goals / Non-Goals

**Goals:**
- 边缘 DOM-first 读取**当前登录账号自身**昵称，**且读到的名字可证明属于自己**（不是被浏览作者），诚实失败（读不到不伪造）。
- 把昵称随**已有的握手消息**带回云端（不新增消息类型）。
- cloud 自愈式持久化到账号行（可空、additive、不回填假值），单写、不阻塞握手。
- console 各「账号名」展示面统一走真名→运营名→ID 的诚实回落链。

**Non-Goals（YAGNI）:**
- 不做改名实时推送（无重连即改名的传播）；靠下次重连/重确立身份自愈，诚实记录其陈旧窗口。
- 不做昵称历史版本表 / 改名审计（Type-1 覆盖即可）。
- 不做 avatar / bio 等其他资料富化（留可空列扩展缝，不现做）。
- 不改 `account_id` 作为 PK，不动已 keyed 子表，不引入 cloud→edge 新命令。

## Decisions

### D1 — 采集：复用握手身份读，但昵称**必须自作用域**（红线修复）

边缘在确立身份时（握手 + 重确立身份）**已经**读到登录账号信息（`readSelfIdentity`），复用这一刻，**不**另起一条「逛到自己主页再抽一次 DOM」。

**但 06-23「直接复用 `displayName`」的写法不安全（BLOCKER，已在代码确认）**：
- `readSelfIdentity` 就地路径里，**账号 ID** 取自你自己头像祖先锚点的 href（`self-identity.ts:115-118`，作用域限定在导航容器 `NAV_SCOPE_SELECTOR`，可靠属己）；
- 但 `displayName` 来自**另一段无作用域的全局查询** `READ_DISPLAY_JS`（`self-identity.ts:133` `document.querySelector('.user-name,[class*="nickname"]…')`），且它在**握手时当前停留页（推荐流 feed）**上执行（`:225-226`）；
- feed 上铺满**别人**的笔记，名字元素同样命中那组通配类名 → 返回的第一个**极可能是被浏览作者的昵称** → 与自己的 accountId 配对存库 = **把别人的名字挂到你的账号行**，违背「绝不伪造 / 绝不错配身份」红线。
- `IN_PLACE_SCAN_JS` 本身把 `nickname` 写死 `null`（`:125`）；昵称完全依赖那段全局查询。navigate 兜底路径（`:254-255`）因为在自己主页上跑 `readDisplay` 才安全，但它**只在就地读 ID 失败时**才触发，是少数路径。

**修复（必做，非 contingent）**：把昵称读改为**限定在自己头像所在的导航容器作用域内**读取（与可靠读出自己 ID 用的是同一作用域），使名字**可证明属己**。具体在 `IN_PLACE_SCAN_JS` 里于 `navScope`/头像锚点上下文内取昵称文本；保留 navigate 路径在自己主页上的读取作为兜底。

**诚实闸**：
- 读到（自作用域、非空）→ 携 nickname；
- 读不到 / 非自作用域 / 形态可疑 → **省略该字段（发 `undefined`，JSON 自然丢弃）**，绝不用 accountId/label/占位伪造。

### D2 — 传输：在**已有的握手消息**上加可选 `nickname` 字段（不新增消息类型）

`HelloPayload`（`protocol.ts:100`）已是 `PayloadMap` 的键、本就携带 `accountId`（昵称要挂的那个 PK）。给它加一个可选 `nickname?: string`：

- **零消息计数变化**：不新增 `MessageType` 成员 → 计数**保持 56**、无 `PayloadMap` 新条目、无 `AC-PROTO-02` 改动、无 `command-bridge`、无 `onMessage` 白名单改动。
- 握手消息在**身份可变的两个时刻自动重发**：首次握手 + 重确立身份后（`main.ts:323-334`：`client.close()` → `setAccountId()` → `await connect()`，`connect()` 重发 hello，`edge-client.ts`）。免费拿到「改名/换号即刷新」。
- 诚实空：用「可选字段是否在场」表达，沿用 hello 既有 `accountId?`/`machineLabel?` 的惯例，**不需要**额外 `extracted` 布尔。

（否决：新增 `account.identity` 消息 = 多处协议同步 + 计数 +1，仅换来「不重连也能带外重报」这一 YAGNI 收益；cloud→edge 主动拉取 = 同步点最多 + 撞 onMessage 静默丢弃坑 + 多一次往返。）

### D3 — 落库：自愈式幂等 DDL（**本仓无迁移执行器**），迁移号 0021

- **关键事实**：cloud **没有迁移执行器、没有 `schema_migrations` 跟踪表**（`package.json` 无 migrate 脚本、无处 readdir `migrations/`）；`.sql` 文件只是文档伴随物。真正生效的是各 store `init()` 里的**幂等内联 DDL**。
- `account-store.ts` 今天**没有任何 ALTER**（`ACCOUNTS_SCHEMA_SQL` 只有 `CREATE TABLE IF NOT EXISTS` + seed），而 `CREATE TABLE IF NOT EXISTS` **不会**给 ECS 上已存在的表加列。故必须：
  1. 在 `CREATE TABLE` 加 `nickname TEXT`（新库直接有列）；
  2. **追加幂等** `ALTER TABLE accounts ADD COLUMN IF NOT EXISTS nickname TEXT;` 到 init() DDL（已存在表自愈加列；照火山方舟 model-config 0018 先例）；ALTER 须在任何引用该列的 SELECT 之前执行。
- `nickname` 可空、无 DEFAULT、不回填 → default 行保持 NULL = 零回归。
- 迁移号用 **0021**（不用 0012——低于当前最大号的空号会被误读为「已应用」；**0020 已被并发 change session-auto-resume 的 `0020_resume_config` 占用**，故取下一空号 0021）；该 `.sql` 仅文档伴随、不被执行。落地前再核 0021 仍空（并发 WIP 可能继续抢号）。

### D4 — 写入：单写、按已认证连接账号、不阻塞握手、自愈 upsert

- 在握手处理里持久化，**按这条连接已认证的 `session.accountId` 写**（防伪造/多租户安全；对齐 `handler.ts:224/231/280`），**不**按 `payload.accountId`。
- **绝不阻塞握手**：包 try/catch（或 fire-and-forget），失败只告警、仍返回 welcome（照 `server.ts:834-836` 的「ensureAccount 失败不阻塞握手」先例；welcome 在 `handler.ts:326-329`）。
- 写法用 `INSERT … ON CONFLICT (account_id) DO UPDATE SET nickname=$2`：`ensureAccount` 是 best-effort（可能静默失败），行不绝对保证在 → upsert 自愈，不会因 0 行 UPDATE 静默丢名。
- **只在非空时写**（`typeof === 'string' && trim() !== ''`）：miss/omit 是 no-op，**绝不用空值覆盖已有好名字**。

### D5 — 诚实身份闸：仅在名字可证明属己时发

边缘仅当 **(a)** 昵称是自作用域读出的非空值，**且 (b)** 握手身份是真实 id 的 `use`、无 override mismatch（`self-identity.ts:73-77`）时，才带 nickname；override 与真实登录 id 不一致、或 `use-override-after-read-fail` 时**省略**。

- 为何：override 值与真实登录 id 不符时，`displayName` 属于**另一个**账号，配对即「把一个账号的真名挂到另一运营行」——红线禁止的静默错配。
- 实现为单条正向规则：`decision.kind === 'use' && !mismatch && 自作用域 nickname 非空` 才发。

### D6 — console：单一真相源 + 一个纯诚实回落 helper

- `PanelAccount` 增 `nickname`（cloud `ACCOUNT_SELECT` 加 `a.nickname`，**不新增 join**）；console `types/api.ts` 镜像。
- 建一个纯函数 `accountDisplayName(nickname, label, accountId) => nickname || label || accountId`（用 `||` 连空串也兜底，绝不造假），**所有显示账号名处统一走它**，防回落链漂移、统一守红线。
- 总表（`AccountTotalsTable`）：`AccountTotals` 仅 `{accountId, totals}`，**不**加宽其 GROUP-BY 查询（`panel-store.ts:213-232` 函数依赖坑）；改为**客户端 join**——用已在线上的 `DashboardSummary.accounts` 建 `accountId→displayName` 映射，渲染 `nickname ?? accountId`。
- 发布历史列/抽屉由云端算的 `PanelPublish.accountLabel` 驱动：在 `panel-store.ts:306` 把 `r.account_label ?? r.account_id` 改为 `r.nickname ?? r.account_label ?? r.account_id`（该 join 加 `a.nickname`），一处改动覆盖列+抽屉、console 零改。

## 协议同步清单（add-to-hello → 4 处中仅 2 处实改）

1. `../aidcp-edge/src/comm/protocol.ts`：`HelloPayload` 加 `nickname?: string`（remoteAddr 之后）+ 注释「当前登录账号自身平台昵称（诚实失败省略，绝不用 accountId/label 伪造）」。**非** MessageType 变化。
2. `../aidcp-cloud/src/comm/protocol.ts`：同字段、与 edge **逐字一致**（含注释）。`Record<MessageType,true>` 穷举不受影响（无 union 成员变化）；字段级逐字一致仍是人工纪律。
3. `../aidcp-cloud/src/comm/command-bridge.ts`：**无改动**——只映射 cloud→edge 动作 verb，hello 是 edge→cloud 握手、不过它。tasks 显式记「无改动」。
4. `docs/protocol.md`：在 §3 hello payload 定义加 `nickname` 字段说明；**头部计数保持 56 不变**（无新 MessageType）。`AC-PROTO-02`（两仓断言 `ALL_TYPES.length === 56`）**无需改**。
5. 附（不触发）：`../aidcp-edge/src/client/edge-client.ts` `onMessage` 白名单——仅 cloud→edge 主动控制命令用，本 change 不涉及。

## Drift corrections（相对 06-23 初稿）

1. **采集**：删掉「另起一条逛主页 DOM 抽取（D1）」；改为复用握手身份读。
2. **红线修复（BLOCKER）**：昵称读**必须自作用域**——原「直接复用 `displayName`」在 feed 上会抓成被浏览作者的名字配自己的 ID（`self-identity.ts:133` 无作用域全局查询 + `:225-226` 在当前页跑）。诚实闸新增「名字须可证明属己」一条，不止 override mismatch。
3. **传输**：新消息 + 计数 56→57 → 改为**已有 hello 加可选字段**，计数**不变 56**。「MessageMap」是 `PayloadMap` 笔误，且 add-to-hello 下无新键。
4. **迁移**：0012（低于当前最大号的空号）→ **0021**；本仓**无迁移执行器**，靠 init() 幂等 ALTER 自愈（`account-store.ts` 今天无 ALTER，必须新增）。
5. **写入**：按 `session.accountId`（非 payload）、**不阻塞握手**（try/catch）、`ON CONFLICT` 自愈 upsert、空值 no-op。
6. **accountId 语义**：已是登录态 24-hex userid（非 AIDCP_ACCOUNT_ID）。
7. **console 范围**：D4 低估面——除账号表/总表外还有发布页(列+抽屉+筛选)、通知联系人选择器、人设页、监控/配额/用量等；总表走客户端 join 非服务端 GROUP-BY join。统一用 `accountDisplayName` helper（`||`）。
8. **删除 tasks.md 的「5 流并发协调」整块**（06-23 并行快照已过期：迁移 0009/0010/0011 已落、stream D 已归档、chokepoint 文件已被多次追加），改为单 change 说明，并对所有引用行号按当前 HEAD 重核。
9. `label` 对新账号非 NULL（= account_id），故回落链无昵称时经 label 显示 account_id——仍诚实、非假名。

## Risks / Trade-offs

- **命中率（MAJOR）**：若小红书网页左栏头像旁不暴露自己昵称文本，自作用域就地读会落空，只能靠 navigate 路径（少触发）→ 可能上线却常显 ID。缓解：实装前用只读探针 `scripts/self-identity-probe.ts` 真机量左栏 DOM；命中则就地零跳转读，否则诚实在验收标准写明「仅 navigate/重确立时填充」。**归档前以真机命中率为闸**，不让其成为「测试绿但真机显 hex」的空壳。
- 改名陈旧窗口：无重连不传播，持续到下次重连/重启——诚实记录，YAGNI 不做实时推送。
- emoji/特殊字形：`TEXT` UTF-8 直存、React 直渲；cloud `setNickname` 可加防御性长度上限 + 拒空白。
- 协议字段逐字一致靠人工：两份 `HelloPayload` 加完全相同字段+注释；勿顺手改无关的既有 drift（如 isVideo）。
- 部署裹挟：ECS rsync 会连带 master 累积 WIP（并发 publish-multi-image 等）→ 用干净 origin/master 工作树 + 内容级 dry-run（期望 0 意外 diff）+ 排除 .env/node_modules/.git + 先备份 + 重启 + healthcheck + 绝不碰 isales。

## Migration Plan

1. 协议：edge + cloud 两份 `HelloPayload` 同步加 `nickname?`（逐字一致）→ `docs/protocol.md` §3 加字段（计数不变）→ 两仓 `npm run typecheck`。
2. edge：`self-identity.ts` 自作用域昵称读（先真机探针核左栏 DOM）→ `edge-client.ts` 透传 + `setNickname` setter → `main.ts` 握手 + 重确立身份按诚实闸传入。
3. cloud：`account-store.ts` CREATE 加列 + 幂等 ALTER + `setNickname`（按 session.accountId、ON CONFLICT、拒空白）→ `handler.ts` onHello 非阻塞持久化 → `panel-store.ts` `PanelAccount.nickname` + 发布历史 accountLabel 折叠 → `panel/types.ts` 镜像 → `migrations/0021` 文档伴随。
4. console：`accountDisplayName` helper → 账号表/总表（客户端 join）+ 发布筛选 + 通知联系人选择器（人设页 Tier2-可选；监控/配额/用量 Tier3 DEFER）。
5. 回归：两仓 `npm run test:acceptance`（`AC-PROTO-*`/`AC-PUB-*`/`AC-RISK-*`）→ `npm test` → `npm run typecheck`。新增覆盖：自作用域读、诚实省略不写、空值 no-op、override mismatch 不发、回落链。
6. 部署：cloud 按 §5 安全序列上 ECS（healthcheck 确认 nickname 列已加 + default 行 nickname 为 NULL）；edge 本地运行。回滚：列可空 additive，回退代码即可。

## Open Questions

- **真机 DOM**：小红书网页左栏/顶部账号区，头像旁是否暴露登录用户**昵称文本**（决定就地零跳转读 vs 仅 navigate 兜底读）。先跑只读探针确认。
- console MVP 范围：Tier1（账号表+总表）必做；Tier2（发布筛选/通知选择器/发布历史折叠）几乎零成本一起做；人设页 DTO 加宽与 Tier3（监控/配额/用量）DEFER。本设计取 Tier1+Tier2（人设页可选）。
- 落地时确认 0021 仍为下一空号（并发 WIP 可能抢号），抢了则取当时下一空号、不硬编码。
