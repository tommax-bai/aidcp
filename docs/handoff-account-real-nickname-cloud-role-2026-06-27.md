# Handoff — account-real-nickname：改为「云端角色驱动」(edge 纯执行)

> 日期：2026-06-27 ｜ 写给：下一个 session ｜ 状态：**提案已定稿+校验+推送,未实装**(openspec `account-real-nickname` active, 3/30, 那 3 个 [x] 是已部署的 KEEP 项)。
> 权威设计在 `openspec/changes/account-real-nickname/{proposal,design,tasks}.md` + `specs/accounts-master-data/spec.md`(本文件是导读,设计以那 4 份为准)。

## 0. 一句话

后台账号列要显登录账号的小红书真实昵称(如「工程师大白」)。初版让 **edge 读昵称+判定** = 违背铁律,且真机证明**昵称只在本人主页 DOM、feed 页没有**,初版实际永不采集。已 revise 提案为:**新增云端角色 `nickname_enricher`,在「真实账号 + 库内昵称空」时开局指挥 edge 访问一次本人主页、读回昵称、存上、回 feed;edge 全程纯执行。** 经 §3 workflow + 3 路对抗评审(0 BLOCKER / 7 MAJOR 全收敛)。下一步 = 实装。

## 1. 铁律(本次纠正的根因,务必内化)

**edge 只执行原子操作、绝不做任何决策;一切决策/编排/数据判定收口云端、由云端角色(RoleDispatcher)驱动。**「做」(点击/滚动/打开页面/原样报 DOM)→edge;「定」(挑选/判定/何时做/做不做)→cloud 角色。enrichment 采集(昵称)= 云端角色下命令、edge 纯执行报 DOM、云端解析+持久化。见记忆 `edge-execute-only-cloud-roles-decide` + CLAUDE.md §2。

## 2. 现在 ECS / 各仓的真实状态(接手先认清)

**仓库 HEAD(2026-06-27)**:control `4c2b07e`(本提案)/ edge `28ba097`(初版昵称码,**待 revert**)/ cloud `472a2f8`(tip,含我的 `4c7fea2`/`95f3db6` 在历史)/ console `0d4308a`(并发,含我的 `b8484ce` 在历史)。

**已部署 ECS(`121.89.85.150`)**:
- cloud(我 06-27 部署 `4c7fea2` 的 6 文件 + 当时 master):`accounts.nickname` 列已加(自愈 ALTER)、`setNickname`、panel-store 暴露、**以及待 revert 的 `handler.onHello` 从 `hello.nickname` 摄取**。当前**无害但惰性**——edge 在 feed 上自作用域读昵称为 null→不发→handler no-op,所以线上没真错,只是没用。session-auto-resume(`472a2f8`)/prompt-preview 已由并发会话部署归档。
- console(我部署的 `index--UkkCngi.js`):账号列已按 `nickname→label→accountId` 显示。
- **DB**:`accounts` 有两行——`default`(nickname NULL)+ **真实 `63e2ff0500000000260049ce`**(=工程师大白 userid,identity-from-login 已 fire 过,nickname NULL)。
- edge 在本地跑(不在 ECS);初版 edge 昵称码已 push 但实际采不到。

**结论**:实装本提案 = revert 那段惰性的 hello 摄取 + edge 决策码,加云端角色;KEEP 的列/setNickname/console **不用重做**(已上线)。

## 3. approved 设计(摘要;细节看 design.md)

新云端角色 **`nickname_enricher`**(按连接):
1. **触发(握手同步算)**:连接建立时同步算 `pendingNicknameCapture = (accountId≠'default') && (getNickname(accountId) IS NULL)`,存 `SessionContext` 布尔(**不能**在会话开始时再 await PG——那会留时间窗让在途 page.cards 插 open_note 进绕路)。
2. **会话开始**(`feed.entered{trigger:'session_start'}`):若 pending && !inFlight → 同一 tick:`browseSuspended=true` + `selfCaptureInFlight=true` + 武装 ~20s 超时 + emit **云端内部事件** `self.profile.capture{accountId}`。
3. **翻译**:`setupCommandTranslation` 新增 `self.profile.capture` → `sendCommand({action:'profile_open', params:{authorId:accountId, direct:true, thinkMs}})`。**不复用** `profile.entered`(它会 seed ProfileBrowser.pending 把自己拖进浏览管线)。
4. **edge 纯执行**:`ProfileOpenPayload.direct===true` → 直接 `Page.navigate` 到 `/user/profile/<authorId>`(不 scrape 当前页);报 `profile.detail{nickname}`(诚实空)。
5. **持久化 + 回 feed**:收到本人 `profile.detail.arrived`(判据 `detail.authorId===evt.accountId`)→ **严格顺序**:`setNickname`(非空)→ 取消超时 → 清 marker → `browseSuspended=false` → emit `feed.entered{back_to_feed}`(汇聚既有返回处理)。空→尝试计数(K=3)仍回 feed。
6. **幂等**:门即实时 DB-NULL;采到后此后 getNickname 非空→不再绕。无持久 flag、无放大。
7. **风控中性**:`profile_open` 翻译处无配额/预算/cooldown,非 RiskAction,不发 interaction.occurred → 采集不碰风控/预算/节奏。

## 4. KEEP vs REVERT(精确,照着做)

**KEEP(已部署/复用,别动)**:`accounts.nickname` 列+自愈 ALTER(`account-store.ts:33,38`)+迁移 0021;`AccountStore.setNickname`(`account-store.ts:145-153`)+其测试;panel-store nickname+发布历史折叠;console `accountDisplayName` helper(b8484ce);`ProfileDetailPayload.nickname`(既有,角色消费);`dev-run.sh` 去强制 default(仅删过时昵称注释)。

**REVERT(初版错放)**:
- 两份 `HelloPayload.nickname`(protocol.ts ~113-114)。
- cloud `handler.onHello` 摄取(~:330-337)+ `HandlerDeps.recordAccountNickname`(~:94-97)+ `server.ts` 接线(~:695-696)+ 3 个 handler 昵称测试。
- edge `edge-client.ts` 昵称透传/`setNickname`、`main.ts` nickname var+诚实闸、`self-identity.ts` 自作用域读 → **in-place `displayName=null`/`redId=null`(切勿恢复无作用域 `readDisplay`,会复活 feed-author-as-self 错配 bug)** + 撤 displayName 日志装饰 + 撤对应 self-identity.test.ts 用例。

## 5. edge 改动(净缩但非零,全部纯执行)

(A) revert 上面 edge 项。(B) 加 `ProfileOpenPayload.direct?: boolean`(两份 protocol.ts 逐字一致)+ `browse-session.ts` `openAuthorProfile`(~:1577)顶部:`direct&&authorId`→`Page.navigate` 到 `/user/profile/<authorId>`,缺省/false 维持 scrape **逐字不变**;edge 不带 isSelf 标志。(C) `browse-session.ts`(~:1696)昵称读解耦数字门:`extracted===false` 也报 `.user-name`/`.user-nickname` + `document.title`(「<名> - 小红书」去尾)兜底。

## 6. 隔离(红线:自己绝不进社交管线;判据 `detail.authorId===连接accountId`)

四守卫**均必需、各自独立测试**:(1) `profile-browser.ts:34` 透 accountId,本人 `detail.authorId===accountId` **早退不 emit `profile.browsed`**(断自关注链根)。(2) profile.done 关注自跳过(`role-dispatcher.ts ~973`)。(3) `server.ts:583` upsertMeta 自跳过(`d.authorId===evt.accountId` return;tee 带 `evt.accountId` 在 handler.ts:236)。(4) note-scoped 链对直驱自访问天然不触发。**marker 只用于 chokepoint 放行+超时,绝不用于持久化/隔离。**

chokepoint(`role-dispatcher.ts:357-364`)**限定**放行:`!(selfCaptureInFlight && action==='profile_open')`(非 blanket;open_note/like/scroll 绕路中照丢)。

## 7. 真机已坐实的事实(别重复踩)

- feed 页 DOM **无**自己昵称(头像是跳转链、文字只「我」);**只有本人主页**有(`document.title`「工程师大白 - 小红书」;`.user-name`/`.user-nickname`=「工程师大白」)。
- 本机 chrome profile `~/.aidcp-chrome-profile` 已登录工程师大白(real id `63e2ff0500000000260049ce`)。跑只读探针:独立起 Chrome `--remote-debugging-port=9222 --user-data-dir=~/.aidcp-chrome-profile`,再 attach(杀 edge 会连带关其 Chrome,故独立起)。
- **残留待真机验**:`Page.navigate` 直接按 id 进自己主页,渲染的 `.user-name`/`document.title` 是否与「点击进入」一致(self-identity 走点击)。已加 title 兜底缓解;部署前真机核。

## 8. 对抗评审揪出的 7 个 MAJOR(实装时别重新引入)

1. 角色发的是**事件**、dispatcher 才翻译命令——必须走新内部事件 `self.profile.capture` + 新翻译,**不能**直接复用 `profile.entered`(会 seed ProfileBrowser.pending)。
2. chokepoint 放行要**限定到自 profile_open**,不能 blanket 关 suspension。
3. 自我判据用 `detail.authorId===accountId`,**不用 in-flight marker**(marker 受同总线分发顺序竞态,重叠会把别人昵称写到自己)。
4. 「需采集」判定要**握手同步缓存**,不能会话开始再 await PG(异步窗口→page.cards 插 open_note)。
5. 必须有 **~20s 兜底超时**:edge 静默/CDP 崩会让 suspension+marker 卡住,只剩 1h idle_end 恢复=最长 1h 死会话。
6. 昵称抽取**与数字渲染门解耦**(+title 兜底),否则 fallback 不带昵称→setNickname 拒空→库恒 NULL→**每会话全程重绕**。+ K=3 尝试上限退避。
7. revert 时 in-place **置 null 而非恢复 readDisplay**(后者复活错配 bug)。

## 9. 纪律 / 坑(本会话血泪)

- **并发会话**:cloud/control/console 常有他人未提交 WIP。**精确 `git add <file>`、绝不 `-A`;提交后必 `git diff <parent> <sha> -- <file>` 核只含自己改动**(本会话 `git add server.ts` 裹挟了 session-auto-resume 的 WIP→master server.ts 引用缺失文件→**部署后 prod down ~1min**;回滚+修 master+干净 worktree typecheck 才查清)。见 `precise-git-add-concurrent-sessions`。
- **部署**:cloud 只在 ECS、本地永不起 cloud;**用干净 origin/master worktree** rsync(绝不带本地 WIP)+ 内容级 `--checksum` dry-run surface scope + 备份 + 重启 + healthcheck + **grep 实测新码在 ECS**(非仅信 rsync 回执)。console 是单一 bundle、没法外科手术,**从自己的 commit 建** bundle 来排除并发 gated 改动。绝不碰 isales。见 `ecs-deploy-scope-full-master` / `deploy-verify-content-after-rsync`。
- 协议:计数恒 **56**(删 hello.nickname + 加 profile.open.direct 均字段增删、无新 MessageType);两份 protocol.ts 字段逐字一致;`self.profile.capture` 仅云端内部事件、**不入协议**、无四处同步。
- 验证:cloud 全量 typecheck/test 常被并发 WIP 污染——**用干净 master worktree 跑**(symlink node_modules)才是真绿;或隔离跑本 change 相关测试(`npx tsx --test test/<file>`)。

## 10. 指针

- **openspec change**:`openspec/changes/account-real-nickname/`(proposal/design/tasks/spec)。`openspec validate account-real-nickname --strict` 通过。
- **设计 workflow 全量产出**(10 agent,0 BLOCKER/7 MAJOR):transcript dir `~/.claude/projects/-Users-baitianxing-aidcp/<session>/subagents/workflows/wf_6e35aa1a-c22/`(若仍在);设计已落 design.md,以 design.md 为准。
- **关键 commit**:edge `28ba097`(待 revert) / cloud `95f3db6`→`4c7fea2`(KEEP 部分已部署) / console `b8484ce`(已部署) / control 提案 `4c2b07e`。
- **记忆**:`account-real-nickname-implemented` / `edge-execute-only-cloud-roles-decide` / `precise-git-add-concurrent-sessions` / `ecs-deploy-scope-full-master` / `deploy-verify-content-after-rsync`。
- **ECS 部署规程**:`aidcp-cloud/docs/deployment-ecs.md`(systemd `aidcp-cloud.service`,`/opt/aidcp/cloud`,8787,`npx tsx src/server.ts`,无 build/无迁移执行器=靠 init() 幂等 DDL)。SSH `ssh -i ~/codes/isales-4.pem root@121.89.85.150`。

## 11. 下一步(实装顺序)

1. revert 初版(§4 REVERT,精确 git add)。2. edge:`direct` 直navi + 昵称读解耦(§5)。3. cloud:`getNickname` + 注入 + SessionContext(pending/marker/计数/超时)+ chokepoint 限定放行 + 新 `nickname_enricher` 角色 + 四隔离守卫(§3/§6)。4. 测试(§8 那 7 点各有回归)。5. 部署(干净 worktree)+ 真机验(本人主页直navi采名 + 自己不进社交管线 + 采过不再绕 + 静默~20s恢复)。6. 归档。
