## Context

后台账号列要显登录账号真实昵称。**初版(已部分实装+部署)把「读昵称+判定发不发」放在 edge,违背铁律(edge 只执行、决策收口云端角色)**;且真机坐实昵称只在**本人主页**DOM 才有(feed 页没有),初版「就地读 ID 一次成功→不再走进主页」导致实际永不采集。

本设计经 §3 多 agent workflow(5 路坐实现状 → 综合 → 3 路对抗评审 → 定稿),**0 BLOCKER / 7 MAJOR 全收敛**。核心:**云端角色驱动一次本人主页访问采昵称,edge 纯执行,且把本人彻底挡在社交管线之外。**

坐实的现成链路:`ProfileOpener`/role-dispatcher emit `profile_open{authorId}`(role-dispatcher.ts:918-919)→ `command-bridge`(:46-47)→ edge `browse-session.ts:636` 打开 `/user/profile/<id>`、抽 `nickname`(诚实空,~:1607)、报 `profile.detail`。账号 ID == userid == 主页 id。

## Goals / Non-Goals

**Goals**:edge 全程纯执行;云端角色编排一次本人主页访问、读 `profile.detail.nickname`、单写持久化;本人**绝不**进 AuthorEvaluator/关注/互动流/去重;只在库内昵称空时采一次(幂等、无放大);风控/预算/节奏中性;有界回 feed、绝不困死会话。

**Non-Goals(YAGNI)**:不做改名实时推送(下次连接 NULL 门自然再采);不做昵称历史/审计;不做 avatar/bio;不引入新协议消息类型;edge 不带「这是自己」标志。

## Decisions

### D1 — 触发(握手同步算、会话开始同步触发,消除异步窗口)
- 握手建连接运行时时(handler 已有 `session.accountId`)**同步算一次** `pendingNicknameCapture = (accountId 非 'default') && (AccountStore.getNickname(accountId) IS NULL)`,存为 `SessionContext` 上的**布尔**(不是会话开始时再 await PG——否则 `feed.entered{session_start}` 是同步 emit(role-dispatcher.ts:686-690/627-631),await 期间在途 `page.cards` 会驱动 `open_note` 插进绕路中,R3-MAJOR)。
- `nickname_enricher` 订阅 `feed.entered`,仅 `trigger==='session_start'`:若 `pendingNicknameCapture && !selfCaptureInFlight` → **同一 tick**:`browseSuspended=true`、`selfCaptureInFlight=true`、武装 ~20s 超时、emit `self.profile.capture{accountId}`。否则 no-op(已采过的会话零扰动)。

### D2 — 开本人主页(新增**通用纯执行**能力 `direct`,不是「自己」语义)
- 新增 `self.profile.capture` **云端内部事件** → `setupCommandTranslation` 新翻译:`sendCommand({action:'profile_open', params:{authorId:accountId, direct:true, thinkMs:thinkNow()}})`。**不复用** `profile.entered`(它会顺带 seed `ProfileBrowser.pending`,profile-browser.ts:47,把自己拖进浏览管线,R2-MAJOR)。
- edge `ProfileOpenPayload.direct?: boolean`(两份 protocol.ts 逐字一致):`direct===true && authorId` → 在 `openAuthorProfile` 顶部直接 `Page.navigate` 到 `/user/profile/<authorId>`(而非 scrape 当前页第一个作者链);下游 `waitForProfile`/抽取/上报不变;`direct` 缺省/false → 已部署 scrape 路径**逐字不变**(关注链路零回归)。**edge 不知道这是不是自己**——云端独知,这只是「精确打开这个 id」的通用操作。

### D3 — 昵称读与「数字渲染门」解耦(否则永远采不到、永远重绕)
- 现状 `extractAuthorProfile` 只在 `extracted===true`(粉丝/作品/获赞在 8s 内渲染)分支带 nickname(browse-session.ts ~1696),fallback 不带 → `setNickname` 拒空 → 库恒 NULL → **每会话都全程绕路**(R3-MAJOR)。
- 修:by-id 自访问路径上,即便 `extracted===false` 也报 `.user-name`/`.user-nickname` + `document.title`(「<名> - 小红书」去尾)兜底,使昵称独立于数字渲染被采到。

### D4 — 隔离(红线:自己绝不进社交管线;判据 `detail.authorId === 连接 accountId`)
判据用 `detail.authorId===evt.accountId`(**不是**在途标记——标记受同总线分发顺序竞态,重叠会把别人昵称写到自己,R3-MAJOR;而 by-id 自访问的 authorId 由 edge 从导航 URL 派生,`authorId===accountId` race-free,且门(a)已排除 'default')。四处守卫,**均必需、各自独立测试**:
1. **ProfileBrowser 本人早退**(profile-browser.ts:34 透 `p.accountId`,onDetailArrived 若 `detail.authorId===accountId` 早退、**不** emit `profile.browsed`)——从根上断掉自关注链,连 FollowAgent LLM 都不空跑。
2. **profile.done 关注自跳过**(role-dispatcher.ts ~973,`payload.authorId===accountId` 跳过)——自路径正常不会走到 profile.done(ProfileBrowser 已早退),此为非标记可达消费者的兜底网。
3. **`server.ts:583` 全局观测 upsertMeta 自跳过**(tee 带 `evt.accountId`,`if(d.authorId===evt.accountId) return`)——防自己进 interaction_feed meta。
4. note-scoped 链(note.detail author-meta server.ts:579 / AuthorEvaluator / ProfileOpener / skip-if-followed)对**直驱**自访问天然不触发。
- 在途标记 `selfCaptureInFlight` **只**用于 chokepoint 放行 + 超时,**绝不**用于持久化/隔离判定。

### D5 — 浏览闭环时序 + 有界回 feed(绝不困死)
- chokepoint(role-dispatcher.ts:357-364)**仅**为自访问 open 放行(不是 blanket 关掉 suspension,R2/R3-MAJOR):`if (browseSuspended && action!=='session.end' && !isExcursionCommand(action) && !(selfCaptureInFlight && action==='profile_open')) return false`。`open_note/like/scroll` 在绕路中照样被丢(下次 page.cards 无害重来)。
- **回 feed**:收到本人 `profile.detail.arrived` 时**严格顺序**:`setNickname`(非空) → 取消超时 → 清 `selfCaptureInFlight` → `browseSuspended=false` → emit `feed.entered{back_to_feed}`(汇聚到既有唯一返回处理 role-dispatcher.ts:985)。`back` 命令此时 `browseSuspended` 已清,放行。
- **超时兜底**:emit 自捕获时武装 ~20s unref'd 定时器;到期清标记+恢复+emit back_to_feed;收到本人 detail 即取消。最坏滞留从 1h(idle_end)降到 ~20s。自路径完全在关注链之外(无 profile.browsed→无 profile.done→无 profile.exit),角色自管返回,无双返回竞态。
- **采空兜底**:nickname 空 → 每连接尝试计数(K=3)递增、仍回 feed;genuinely 抽不到的主页退避而非永绕。

### D6 — 幂等 / 风控 / 持久化
- 幂等:门即「实时 DB-NULL 决策(握手缓存)」;一旦非空写入,下次连接 `getNickname` 非空 → `pendingNicknameCapture=false` 永久。无持久 once-flag、无写放大。
- 风控/预算/节奏:`profile_open` 翻译处**无** `canInteract`/cooldown/`consumeBudget`,非 RiskAction,不发 `interaction.occurred`/`action.completed` → 采集对风控/预算/节奏**中性**。重连重评 NULL 门可能重绕,但中性 + 超时 + K=3 封顶,MVP 接受。
- 持久化:复用已部署 `setNickname`(trim 拒空、单写 ON CONFLICT),诚实空绝不覆盖好名;依赖经 `buildDispatcher` 注入(server.ts 已有 accountStore 作用域),**不**走被 revert 的 handler hello 路径。

## KEEP vs REVERT(精确清单)

**KEEP(已部署/复用,均云端或展示层)**:`accounts.nickname` 列 + 自愈 ALTER(account-store.ts:33,38)+ 迁移 0021 文档物;`AccountStore.setNickname`(:145-153)+ 其测试;panel-store nickname 暴露 + 发布历史折叠;console `accountDisplayName` helper;`ProfileDetailPayload.nickname`(既有,角色消费,勿动);`dev-run.sh` 去强制 default(仅删过时昵称注释);session-monitor 在 `profile.detail.arrived` 刷新(绕路中喂看门狗)。

**REVERT(初版错放)**:两份 `HelloPayload.nickname`;cloud `handler.onHello` 摄取(:330-337)+ `HandlerDeps.recordAccountNickname`(:94-97)+ `server.ts` 接线(~695-696)+ 3 个 handler 昵称测试;edge `edge-client.ts` 昵称透传/`setNickname`、`main.ts` 诚实闸、`self-identity.ts` 自作用域读 → in-place `displayName=null`/`redId=null`(**不**恢复 readDisplay)+ 撤日志装饰 + 撤对应测试用例。

## 协议(计数恒 56)
- 两份 protocol.ts:删 `HelloPayload.nickname`、加 `ProfileOpenPayload.direct?: boolean`(逐字一致)。字段增删、无新 MessageType → `AC-PROTO-02` 计数 56 不变。
- `self.profile.capture` 云端内部事件,**不入 protocol**,无四处同步。
- `command-bridge`:`profile_open` 已映射,`params` 原样透传 `direct`,无改。
- docs/protocol.md:hello 去 nickname、profile.open 加 direct,头部计数仍 56。

## Risks / Trade-offs(对抗评审残留)
- by-id `Page.navigate` 到自己主页**渲染 `.user-name`/`document.title` 是否与点击进入一致**未验(self-identity 经点击进入)→ 部署前真机确认;已加 `document.title` 兜底缓解。
- 假设 `account_id == 主页 userid`('default' 被门排除 + authorId===accountId 判据双保险)→ 确认部署无其他非-userid 账号 id。
- genuinely 抽不到的主页不采 → K=3 退避,最坏有界非永绕。
- flapping 重连重评 NULL 门可能短暂重绕 → 中性 + 超时 + K=3 封顶。
- `self.profile.capture` 须**仅**云端内部(RoleEventMap),勿误暴露为协议消息。

## Migration Plan
1. 协议:两份 protocol.ts 删 hello.nickname / 加 profile.open.direct(逐字)→ docs 同步(计数 56)→ 两仓 typecheck。
2. edge:revert 初版传输/决策(in-place 置 null)→ 加 direct 直navi 分支 → 昵称读解耦数字门 → 测试。
3. cloud:revert hello 摄取 → 加 `getNickname` + 注入 → `SessionContext`(pending/marker/计数/超时)+ chokepoint 限定放行 → 新 `nickname_enricher` 角色(RoleName/RoleEventMap/setup 注册/session_start 钩子/翻译/超时/detail 消费持久化+回 feed)→ 四隔离守卫 → 测试。
4. 回归:两仓 `test:acceptance`(AC-PROTO 计数 56 / AC-RISK / AC-PUB)+ `test` + `typecheck`;新增:角色门控/幂等/非空才写、ProfileBrowser 自跳过回归(合法他访问仍 emit profile.browsed,与注册序无关)、server 自 meta 跳过、无自关注命令、chokepoint 丢 open_note 放自 profile_open、超时恢复。
5. 部署(显式):干净 origin/master worktree + 内容级 dry-run + 备份 + 重启 + healthcheck + **真机验**(本人主页直navi 采到真名 → 库 nickname 落值 → console 显示;采空不伪造;自己不进关注/互动流);绝不碰 isales。

## Open Questions
- by-id 直navi 自己主页的 DOM 与点击进入是否一致(真机定;有 title 兜底)。
- 部署是否确认无非-userid 账号 id(门 + 判据已双保险)。
