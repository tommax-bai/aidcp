> **架构纠正提案**:初版把「读昵称+诚实闸判定」放 edge=违铁律,且真机证明 feed 页无昵称、初版永不采集。改为**云端角色 `nickname_enricher` 驱动一次本人主页访问采集,edge 纯执行**。经 §3 workflow + 3 路对抗评审(0 BLOCKER / 7 MAJOR 全收敛)。
> **协议计数恒 56**:删 `HelloPayload.nickname` + 加 `ProfileOpenPayload.direct?` 均字段增删、无新 MessageType;`self.profile.capture` 是云端内部事件、不入协议。
> **已部署现状**:edge 28ba097(待 revert)/ cloud 4c7fea2(hello 摄取待 revert;列+setNickname+panel-store 保留=已部署)/ console b8484ce(保留=已部署)。
> **并发纪律**:cloud 满并发(session-auto-resume/prompt-preview 近期已部署进 master)——精确 git add、提交后核 commit diff 只含自己改动、部署用干净 origin/master worktree。

## 0. KEEP(已部署/复用,不动)

- [x] 0.1 `accounts.nickname` 列 + 自愈 ALTER + 迁移 0021 + `AccountStore.setNickname`(单写拒空)+ 其测试 <!-- cloud 4c7fea2 已部署 -->
- [x] 0.2 panel-store nickname 暴露 + 发布历史折叠;console `accountDisplayName` helper <!-- cloud 4c7fea2 / console b8484ce 已部署 -->
- [x] 0.3 `ProfileDetailPayload.nickname`(interaction-feed-enrichment 既有,角色消费,**勿动**);`dev-run.sh` 去强制 default(身份引导,仅删过时昵称注释) <!-- 既有 -->

## 1. REVERT 初版错放(edge 决策 + cloud hello 摄取)

- [ ] 1.1 cloud + edge `src/comm/protocol.ts`:删 `HelloPayload.nickname`(两份逐字一致)
- [ ] 1.2 cloud `src/comm/handler.ts`:删 onHello nickname 摄取(~:330-337)+ `HandlerDeps.recordAccountNickname`(~:94-97)+ 3 个 handler 昵称测试;`src/server.ts`:删 `recordAccountNickname` 接线(~:695-696)
- [ ] 1.3 edge `src/client/edge-client.ts`:revert nickname 透传 + `setNickname`;`src/main.ts`:revert nickname var + 诚实闸
- [ ] 1.4 edge `src/cdp/self-identity.ts`:in-place 路径 `displayName=null`/`redId=null`(**不**恢复无作用域 `readDisplay`,避免复活 feed-author-as-self 错配)+ 撤 displayName 日志装饰 + 撤对应 self-identity.test.ts 用例
- [ ] 1.5 edge `scripts/dev-run.sh`:删过时的昵称闸注释(~:39-41,保留文件本身)

## 2. aidcp-edge — 通用纯执行能力(direct 直navi + 昵称读解耦数字门)

- [ ] 2.1 `src/comm/protocol.ts`:加 `ProfileOpenPayload.direct?: boolean`(与 cloud 逐字一致)+ 注释「云端指定时直接 Page.navigate 到该主页 id、不 scrape 当前页」
- [ ] 2.2 `src/browse/browse-session.ts` `openAuthorProfile`(~:1577):`direct===true && authorId` → 直接 `Page.navigate` 到 `https://www.xiaohongshu.com/user/profile/<authorId>`;缺省/false 维持 scrape 路径**逐字不变**;edge **不带** isSelf 标志
- [ ] 2.3 `src/browse/browse-session.ts`(~:1696):昵称读与数字门解耦——`extracted===false` 也报 `.user-name`/`.user-nickname` + `document.title`(「<名> - 小红书」去尾)兜底
- [ ] 2.4 测试:by-id open 导航到 `/user/profile/<id>`、不 scrape;昵称在 counts 缺失时仍被带回

## 3. aidcp-cloud — nickname_enricher 角色 + 隔离 + 时序

- [ ] 3.1 `src/comm/protocol.ts`:加 `ProfileOpenPayload.direct?`(与 edge 逐字);`command-bridge` 确认 `params` 原样透传 `direct`(无新映射)
- [ ] 3.2 `src/account-store.ts`:加 `getNickname(accountId)` 读 API
- [ ] 3.3 `src/server.ts` / `buildDispatcher`:握手同步算 `pendingNicknameCapture`(非 'default' && getNickname IS NULL),存 `SessionContext`;注入 `getNickname`+`setNickname` 进 dispatcher(非 hello 路径)
- [ ] 3.4 `SessionContext`:加 `pendingNicknameCapture`(同步布尔)、`selfCaptureInFlight` 标记(reset() 清)、每连接尝试计数(K=3)、~20s 超时句柄
- [ ] 3.5 `src/event-bus/types.ts`:`RoleName` 加 `nickname_enricher`;`RoleEventMap` 加云端内部事件 `self.profile.capture{accountId}`(**不**入 protocol)
- [ ] 3.6 新 `src/agents/nickname-enricher.ts`:订阅 `feed.entered{session_start}`(同步:若 pending && !inFlight → suspend+marker+武装超时+emit self.profile.capture);订阅 `profile.detail.arrived`(`detail.authorId===evt.accountId` 时:取消超时 → `setNickname`(非空)→ 清 marker → resume → emit `feed.entered{back_to_feed}`;空则尝试计数++仍回 feed);在 `setup()` roles[] 注册
- [ ] 3.7 `src/orchestrator/role-dispatcher.ts`:`setupCommandTranslation` 加 `self.profile.capture` → `sendCommand({action:'profile_open', params:{authorId, direct:true, thinkMs}})`(**不**复用 profile.entered);chokepoint(~:357-364)限定放行 `selfCaptureInFlight && action==='profile_open'`(非 blanket)
- [ ] 3.8 隔离守卫(均必需):`profile-browser.ts`(:34 透 accountId,本人 `detail.authorId===accountId` 早退、不 emit profile.browsed);profile.done 关注自跳过(~:973);`server.ts:583` upsertMeta 自跳过(`d.authorId===evt.accountId` return)
- [ ] 3.9 测试:门控(非 default & NULL 才采)/幂等(非空不再绕)/非空才写;ProfileBrowser 自跳过回归(合法他访问仍 emit profile.browsed,与角色注册序无关);server 自 meta 跳过;无自关注命令;chokepoint 丢 open_note 但放自 profile_open;超时恢复回 feed

## 4. docs — 协议同步(计数 56)

- [ ] 4.1 `docs/protocol.md`:hello payload 去 `nickname`、profile.open payload 加 `direct`;头部 v2 计数**保持 56**(无新 MessageType)

## 5. 验证(红线 + 回归)

- [ ] 5.1 两仓 `npm run typecheck`(protocol 不漂移、计数 56);console 不动
- [ ] 5.2 两仓 `npm run test:acceptance`:`AC-PROTO-*`(计数 56、两端一致)/ `AC-RISK-*` / `AC-PUB-*` 必过
- [ ] 5.3 两仓 `npm test` 全量绿(隔离跑本 change 相关:角色/隔离/chokepoint/超时/edge direct/昵称解耦);并发 WIP 阻塞全量时用干净 worktree 验
- [ ] 5.4 真机 E2E(gated):本人主页 direct 采到真名 → 库 `accounts.nickname` 落值 → console 显示;采空不伪造;**自己绝不进关注/互动流/去重**;采过不再绕路;edge 静默 ~20s 超时回 feed

## 6. 收尾与部署

- [ ] 6.1 按 sub-repo 分节回写进度(`<!-- <repo> <sha> -->`)
- [ ] 6.2 `openspec validate account-real-nickname --strict` 通过
- [ ] 6.3 部署 ECS(显式):干净 origin/master worktree + 内容级 dry-run + 备份 + 重启 + healthcheck(计数 56 / 角色就绪 / 列在)+ 真机验;绝不碰 isales
- [ ] 6.4 `/opsx:archive` 归档(delta 并入 `openspec/specs/accounts-master-data`)
