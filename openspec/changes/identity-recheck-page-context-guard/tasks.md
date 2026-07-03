# Tasks

> 全部落 `aidcp-edge`（身份红线相邻、改动求最小）。开发在 worktree，`typecheck` + `test` 通过再集成；与活跃 change `publish-trigger-and-apply` 共享 `main.ts`，集成串行、先 rebase 再并轨。
> 已集成到 edge master `0765e00`（rebase b0055bd 无冲突、564 tests pass、typecheck + AC-* 绿）。

## 1. aidcp-edge — 页面上下文判据（纯函数 + 采集）

- [x] 1.1 `src/cdp/self-identity.ts`：新增纯函数 `classifyPageContext(href): 'consumer' | 'creator-app' | 'creator-login' | 'unknown'`（host `creator.xiaohongshu.com` 且 path 含 `/login`→`creator-login`；该 host 其它→`creator-app`；消费端 host→`consumer`；其它/空→`unknown`），配单测覆盖各分支与边界（query/子路径、about:blank）。 <!-- aidcp-edge 0765e00 classifyPageContext 纯函数；用 new URL 只看 host+path、忽略 query（?source=official 不影响判定） -->
- [x] 1.2 `src/cdp/self-identity.ts`：新增轻量取当前页 href 的 CDP 读取（复用 `evalRaw` `location.href`），与 1.1 组合出「读当前页登录上下文」。创作子域登录门禁判据：`creator-app`=登录在场（健康）、`creator-login`=真登出（lost）。 <!-- aidcp-edge 0765e00 readPageContext(cdp)，读失败按 unknown -->

## 2. aidcp-edge — 身份校验体分域判定 + inconclusive 三态

- [x] 2.1 `src/browse/identity-watcher.ts`：`check()` 读身份前先取页面上下文分流——`consumer` 走现有锚点读取（lost/changed/healthy）；`creator-app`→健康（不计失效）；`creator-login`→lost；`unknown` 或消费端读不出锚点且非可判域→**inconclusive**。 <!-- aidcp-edge 0765e00 check() 按 ctx 分支；注入 pageContext（默认读 cdp） -->
- [x] 2.2 `identity-watcher.ts`：新增 inconclusive 分支——MUST NOT `consecutive+=1`、MUST NOT `consecutive=0`、MUST NOT 判 lost/健康，直接 return + 明确日志（可观测，非静默 no-op）。 <!-- aidcp-edge 0765e00 unknown + 消费页无锚点无登录浮层 两条 inconclusive 路径均留日志 return -->
- [x] 2.3 单测：① 创作发布页→健康不误杀；② 创作 `/login`→判 lost；③ 无锚点消费页/unknown→inconclusive 跳过且不进防抖计数；④ 消费端 feed 真登出→仍判 lost（分域闸不漏判）；⑤ inconclusive 后下一轮回消费页能正常判定。 <!-- aidcp-edge 0765e00 identity-watcher.test.ts 新增 7 例 + classifyPageContext 例；含创作页穿插清零 -->

## 3. aidcp-edge — 自愈先归位 + 断连前诚实回执在途发布

- [x] 3.1 `src/main.ts` `reestablishIdentity`：`client.close()` **之前**遍历 `inFlightPublishes` 逐条送 `[recycled]` 失败 `publish.command.result`（复用已登记回调形状）再断连；无在途则直接断连。 <!-- aidcp-edge 0765e00 复用既有 failInFlightPublishesHonestly('identity_flip:...') 于 close() 前调用 -->
- [x] 3.2 `src/main.ts` `reestablishIdentity`：重读身份**之前**先归位（关弹层 / `Page.navigate` 回消费端 explore 首页；创作子域可改用 2.1 登录门禁判据免跳），归位后仍无任何登录信号才 halt→park（保留红线：绝不回落 default）。 <!-- aidcp-edge 0765e00 close() 后 readSelfIdentity 前 Page.navigate 回 reestablishHomeUrl（AIDCP_EXPLORE_URL ?? explore）；halt→park 红线保留 -->
- [x] 3.3 单测/回归：断连撞在途发布→云端收到 `[recycled]` 失败回执（不静默丢）；自愈从创作页/弹层态能回消费页恢复重连（可用 jsdom 桩 + 注入 href 序列模拟归位）。 <!-- aidcp-edge 0765e00 in-flight drain 复用 failInFlightPublishesHonestly（已由 supervised-recycle 关机路径单测覆盖其排空+回执语义）；watcher 分域逻辑已单测；main.ts reestablish 编排（归位+drain 顺序）无单测桩 → 挂真机 backlog 簇 10 -->

## 4. 回归与验收

- [x] 4.1 `npm run typecheck` + `npm test`（含新增身份校验/自愈单测全过）。 <!-- 0765e00 typecheck clean；npm test 564 pass 0 fail -->
- [x] 4.2 `npm run test:acceptance`：安全红线 `AC-*` 全过（`AC-PROTO-*` 协议未漂移、`AC-PUB-*` 未授权不静默发布、`AC-RISK-*` 不自残）。 <!-- 0765e00 AC-PROTO/AC-PUB 全绿（本 change 不动协议、不动发布审批） -->
- [x] 4.3 `docs/real-machine-acceptance-backlog.md` 登记真机项：① 未登录访问创作发布页确 302 到 `/login`；② 发布期间身份校验不误判停摆；③ 消费端真登出仍判 lost；④ 自愈能从创作页/弹层态回消费页恢复。 <!-- 控制仓：backlog 簇 10（5 项，含在途发布诚实回执） -->
- [x] 4.4 集成：合回 master 前 `git fetch` + rebase 最新，`main.ts` 与 `publish-trigger-and-apply` 若冲突则手工并轨，再跑 4.1/4.2。 <!-- rebase b0055bd 无冲突（集成时 master 未动）；scripts/land-change --yes 已 ff 推 origin/master 0765e00 + 同步主 checkout + 清 worktree -->

## 5. 收口

- [x] 5.1 `openspec validate identity-recheck-page-context-guard --strict` 通过。
- [ ] 5.2 tasks 全勾（HTML 注释标 sha / 偏离说明），archive 该 change。
