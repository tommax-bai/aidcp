> **架构纠正提案**:初版把「读昵称+诚实闸判定」放 edge=违铁律,且真机证明 feed 页无昵称、初版永不采集。改为**云端角色 `nickname_enricher` 驱动一次本人主页访问采集,edge 纯执行**。经 §3 workflow + 3 路对抗评审(0 BLOCKER / 7 MAJOR 全收敛)。
> **协议计数恒 56**:删 `HelloPayload.nickname` + 加 `ProfileOpenPayload.direct?` 均字段增删、无新 MessageType;`self.profile.capture` 是云端内部事件、不入协议。
> **已部署现状**:edge 28ba097(待 revert)/ cloud 4c7fea2(hello 摄取待 revert;列+setNickname+panel-store 保留=已部署)/ console b8484ce(保留=已部署)。
> **并发纪律**:cloud 满并发(session-auto-resume/prompt-preview 近期已部署进 master)——精确 git add、提交后核 commit diff 只含自己改动、部署用干净 origin/master worktree。
>
> **实装提交(2026-06-27)**:edge `30d746e`(origin/master)/ cloud `53bd333`(origin/master)。在 Windows 工作区实装,精确 git add(并发会话同时在改 cloud/edge/umbrella 的 docs 与 pg-anchor-cache/pg-risk-store,均未裹挟)。

## 0. KEEP(已部署/复用,不动)

- [x] 0.1 `accounts.nickname` 列 + 自愈 ALTER + 迁移 0021 + `AccountStore.setNickname`(单写拒空)+ 其测试 <!-- cloud 4c7fea2 已部署 -->
- [x] 0.2 panel-store nickname 暴露 + 发布历史折叠;console `accountDisplayName` helper <!-- cloud 4c7fea2 / console b8484ce 已部署 -->
- [x] 0.3 `ProfileDetailPayload.nickname`(interaction-feed-enrichment 既有,角色消费,**勿动**);`dev-run.sh` 去强制 default(身份引导,仅删过时昵称注释) <!-- 既有 -->

## 1. REVERT 初版错放(edge 决策 + cloud hello 摄取)

- [x] 1.1 cloud + edge `src/comm/protocol.ts`:删 `HelloPayload.nickname`(两份逐字一致) <!-- edge 30d746e / cloud 53bd333 -->
- [x] 1.2 cloud `src/comm/handler.ts`:删 onHello nickname 摄取 + `HandlerDeps.recordAccountNickname` + 3 个 handler 昵称测试;`src/server.ts`:删 `recordAccountNickname` 接线 <!-- cloud 53bd333；实测 onHello 块 330-338 / 接口 93-97 / server 694-697 / 测试 70-116 -->
- [x] 1.3 edge `src/client/edge-client.ts`:revert nickname 透传 + `setNickname`(保留 setAccountId);`src/main.ts`:revert nickname var + 两处诚实闸 + setNickname 调用 <!-- edge 30d746e -->
- [x] 1.4 edge `src/cdp/self-identity.ts`:in-place 路径 `displayName=null`/`redId=null`(**不**恢复无作用域 `readDisplay`)+ IN_PLACE_SCAN_JS 去自作用域昵称读 + 撤对应 self-identity.test.ts 用例 <!-- edge 30d746e；偏离:handoff 提到的「displayName 日志装饰」经核 28ba097 diff 并不存在(main.ts:142 `const display` 是先于 28ba097 的既有行,予以保留) -->
- [x] 1.5 edge `scripts/dev-run.sh`:删过时的昵称闸注释(实测 39-40 两行,保留「去强制 default」行为与文件本身) <!-- edge 30d746e -->

## 2. aidcp-edge — 通用纯执行能力(direct 直navi + 昵称读解耦数字门)

- [x] 2.1 `src/comm/protocol.ts`:加 `ProfileOpenPayload.direct?: boolean`(与 cloud 逐字一致)+ 注释 <!-- edge 30d746e -->
- [x] 2.2 `src/browse/browse-session.ts` `openAuthorProfile(authorId, direct)`:`direct&&authorId` → 直接 `Page.navigate` 到 `/user/profile/<authorId>`;缺省/false 维持 scrape 路径逻辑不变(DRY:共用 navigate 后续);edge **不带** isSelf 标志;调用点透传 `payload.direct` <!-- edge 30d746e -->
- [x] 2.3 `src/browse/browse-session.ts`:昵称读与数字门解耦——注入 JS 加 `document.title`(「<名> - 小红书」去尾)兜底;`lastName` 累积器使 `extracted===false` 超时路径仍带回 nickname;openAuthorProfile else 分支改为带 nickname/url 上报(extracted:false) <!-- edge 30d746e -->
- [x] 2.4 测试:by-id direct open 导航到 `/user/profile/<id>`、不跑 scrape 探针;昵称在 counts 缺失(extracted:false)时仍被带回 <!-- edge 30d746e test/browse/browse-session.test.ts -->

## 3. aidcp-cloud — nickname_enricher 角色 + 隔离 + 时序

- [x] 3.1 `src/comm/protocol.ts`:加 `ProfileOpenPayload.direct?`(与 edge 逐字);`command-bridge` 确认 `params` 原样透传 `direct`(无新映射,已核 :46-47) <!-- cloud 53bd333 -->
- [x] 3.2 `src/account-store.ts`:加**同步** `getNickname(accountId): string|null`(读 init 预热 + setNickname 更新的进程内缓存);setNickname 写后更新缓存 <!-- cloud 53bd333；同步缓存而非 await PG,以满足握手同步算门 -->
- [x] 3.3 `src/server.ts`/`buildDispatcher`:注入 `getNickname`(同步)+`setNickname` 进 dispatcher(非 hello 路径);握手同步算 `pendingNicknameCapture` 在 `RoleDispatcher.setCurrentAccountId`(connection-runtime onHandshake:131 调,先于 setup) <!-- cloud 53bd333；偏离:握手编排在 connection-runtime.ts,非 server.ts;SessionContext 在 dispatcher 构造期建 -->
- [x] 3.4 `SessionContext`:加 `pendingNicknameCapture`(同步布尔)、`selfCaptureInFlight` 标记、`selfCaptureAttempts`(K=3)、`SELF_CAPTURE_TIMEOUT_MS`(20s)+ timer 句柄;reset() 只清瞬时态(marker+timer),**不**清 per-connection 决策(pending/attempts) <!-- cloud 53bd333 -->
- [x] 3.5 `src/event-bus/types.ts`:`RoleName` 加 `nickname_enricher`;`RoleEventMap` 加云端内部事件 `self.profile.capture{accountId}`(**不**入 protocol) <!-- cloud 53bd333 -->
- [x] 3.6 新 `src/agents/nickname-enricher.ts`:订阅 `feed.entered{session_start}`(同步:pending&&!inFlight&&attempts<K → suspend+marker+武装超时+emit self.profile.capture);订阅 `profile.detail.arrived`(`detail.authorId===accountId` → 严格顺序 setNickname(非空)→清超时→清 marker→resume→emit feed.entered{back_to_feed};空则 attempts++仍回 feed);在 setup() roles[] 注册 <!-- cloud 53bd333 -->
- [x] 3.7 `src/orchestrator/role-dispatcher.ts`:`setupCommandTranslation` 加 `self.profile.capture` → `profile_open{authorId, direct:true, thinkMs}`(**不**复用 profile.entered);chokepoint 限定放行 `selfCaptureInFlight && action==='profile_open'`(非 blanket) <!-- cloud 53bd333 -->
- [x] 3.8 隔离守卫(均必需):`profile-browser.ts` 本人(detail.authorId===accountId,经事件 p.accountId)早退、不 emit profile.browsed;profile.done 关注自跳过(仍 emit 恰好一次 profile.exit);`server.ts` upsertMeta 自跳过(`d.authorId===evt.accountId` return) <!-- cloud 53bd333；note-scoped 链对直驱自访问天然不触发,无需改 -->
- [x] 3.9 测试:门控/幂等/非空才写/采空 K 退避/超时回 feed/他人 detail 忽略(nickname-enricher.test.ts 9 例);ProfileBrowser 自跳过 + 合法他访问仍 emit 回归(profile-browser.test.ts) <!-- cloud 53bd333 -->

## 4. docs — 协议同步(计数 56)

- [x] 4.1 `docs/protocol.md`:hello payload 去 `nickname`、profile.open payload 加 `direct`;头部 v2 计数**保持 56**(无新 MessageType) <!-- umbrella(本 change 提交) -->

## 5. 验证(红线 + 回归)

- [x] 5.1 两仓 `npm run typecheck` 全绿(protocol 不漂移、计数 56);console 不动 <!-- edge/cloud typecheck exit 0 -->
- [x] 5.2 两仓 acceptance:`AC-PROTO-*`(计数 56、两端一致)全过;`AC-RISK-*` 过;`AC-PUB-*` edge 6/6 过、cloud 2/3(**唯一 fail = AC-PUB-01 在 Windows 上 path.join 出 `\tmp\` ≠ `/tmp/` 的平台差异,与本 change 无关,Linux/ECS 上为 `/tmp/` 通过**) <!-- 平台性 fail,非回归 -->
- [x] 5.3 隔离跑本 change 相关测试全绿:角色/隔离/chokepoint/超时/edge direct/昵称解耦/protocol-contract/handler/连接运行时/事件总线 <!-- 详见提交说明 -->
- [x] 5.4 真机 E2E(gated)——**2026-06-27 通过 ✅(经两轮集成 bug 修复:cloud `115912e` + `de0d094`)**:本人主页 direct 采到真名「工程师大白」→ 库 `accounts.nickname` 落值;采过不再绕(复跑 sess-2 直接正常浏览、无采集);自己不进社交流(profile.open→navigation.back,无 follow/like);edge 静默 ~20s 超时回 feed(首轮已验)。<!-- 真机闭环坐实:edge `[browse] profile.open: ... 昵称「工程师大白」`→cloud `本人昵称采集成功...已持久化`→DB `63e2ff05...|工程师大白`→重连 sess-2 无 `需采登录账号昵称`。亦坐实 handoff §7 残留:by-id Page.navigate 进本人主页能渲染 .user-name、采到真名（这次 extracted:true 含数字+昵称）。 -->
      <!-- 真机暴露的三层集成 bug(隔离单测+对抗评审全过仍漏):①profile_open sent=0(命令在 hello 同步窗口发、早于 ws-server edges.set)→延后;②通知巡视与采集争用边缘→巡视让位 selfCaptureInFlight;③命令在边缘初始扫 feed(命令循环未起)时到达被丢→改在首个 page.cards.arrived(边缘就绪)再发。教训:真机验是集成时序 bug 的唯一照妖镜。 -->
      <!-- 修复+重部(cloud 115912e, 2026-06-27):BUG#1 采集命令延后到边缘登记后再发(emitCapture/setTimeoutFn 0);BUG#2 通知巡视在 selfCaptureInFlight 时让位。clean-worktree typecheck 通过、单测 nickname-enricher 10/10 + notification-gatekeeper 5/5、ECS grep 实测修复在位、重启 healthcheck 全绿(备份 cloud.bak.20260627-180841)。复测当时被「本机已安装版 Google Chrome(PID 3208)正占用 ~/.aidcp-chrome-profile」挡住(edge 的 chrome-win64 启动握手到既有实例即退出)——未动用户 Chrome;复测交用户:关掉占用该 profile 的 Chrome 后重跑 edge,或用户自己的 AdsPower/edge 连入即可,云端已就绪。 -->
      <!-- 真机首跑结果(edge edge-win-realtest 连 ECS,account=63e2ff05...):edge 身份确立 OK、nickname_enricher 触发 OK、~20s 超时兜底恢复 OK、浏览继续、DB 保持 NULL(无假数据)。但采集**未成功**——根因 BUG#1:`profile_open sent=0`。ws-server.ts onConnection:`this.edges.set`(注册可推送)在 `await routeMessage`(同步跑完 hello→onHandshake→edge.hello→restartSession→startSession→feed.entered{session_start}→nickname_enricher→profile_open→pushToEdges)**之后**,故采集命令在 hello 窗口内发出时边缘尚未登记→sent=0。普通浏览闭环不受影响(其首命令是对**后续** page.cards 的反应,那时已登记)。BUG#2(次要):有未读通知时 notification 巡视在会话开始约 2s 后也触发,与采集争用边缘。修法见下。 -->
      <!-- 拟修:BUG#1 = nickname_enricher 同步置 suspend/marker/超时,但把 emit('self.profile.capture') 推到下一 macrotask(注入的 setTimeoutFn(…,0)),使命令在 edges.set 之后发出(sent=1);R3 窗口不受影响(suspend 仍同步、首个 open_note 需 LLM 秒级)。BUG#2 = 采集在途时 notification 准入应让位/延后(协调 selfCaptureInFlight)。 -->——用已登录工程师大白的 Chrome 跑 edge 连 `ws://121.89.85.150:8787`,观察:本人主页 direct 采到真名 → 库 `accounts.nickname` 落值 → console 显示;采空不伪造;**自己绝不进关注/互动流/去重**;采过不再绕路;edge 静默 ~20s 超时回 feed。<!-- 涉及在真实账号上跑真浏览(真互动),且已登录的 Chrome 在 Mac;不宜无人监督自动跑,交接用户 -->
      <!-- 真机验步骤:`cd aidcp-edge && AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm start`(确保 Chrome 已登录工程师大白);看云端日志 `journalctl -u aidcp-cloud -f` 应见 self.profile.capture→profile_open{direct}→profile.detail→setNickname;核 `select nickname from accounts where account_id='63e2ff0500000000260049ce'` 落值;console 账号列显真名 -->

## 6. 收尾与部署

- [x] 6.1 按 sub-repo 分节回写进度(`<!-- <repo> <sha> -->`) <!-- 本文件 -->
- [x] 6.2 `openspec validate account-real-nickname --strict` 通过 <!-- validate exit 0, 2026-06-27 -->
- [x] 6.3 部署 ECS:干净 origin/master worktree(`5900bd4`,先 clean-worktree typecheck 把关——**正是它揪出并修了一个 tsx 漏过的测试类型错**)经 git-archive-over-ssh 覆盖 `/opt/aidcp/cloud`(备份 `cloud.bak.20260627-154229.tar.gz` + `.env.bak.20260627-154229`);grep 实测新码在 ECS(nickname-enricher.ts / self.profile.capture / 同步 getNickname / ProfileOpenPayload.direct@560 / guard3,旧 hello 摄取已撤);重启 healthcheck 全绿(active / 监听 :8787 / 飞书长连接已建立 / psql select 1 / AccountStore 已就绪 / 自重启 0 error);DB 现有 `63e2ff0500000000260049ce`(工程师大白)nickname=NULL → 下次会话将触发采集;**未碰 isales** <!-- cloud 5900bd4 deployed 2026-06-27;Windows 无 rsync 改用 git archive over ssh -->
- [ ] 6.4 `/opsx:archive` 归档(delta 并入 `openspec/specs/accounts-master-data`) <!-- 待部署+真机验后 -->
