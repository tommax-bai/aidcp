## 1. aidcp-cloud — Capability words + wired consumers

- [x] 1.1 Add `follow` / `profile_visit` / `patrol` / `notification` to the `capabilities` Record in `src/platform/registry.ts` (same shape as C1a), with XHS supported and Facebook `{false,reason}`. <!-- cloud 19b2e13: OrchestrationCapability 扩 4 词；XHS 全 supported:true / FB 全 {false, reason}（no_follow_actuator / no_profile_actuator / no_notification_patrol / no_notification_surface）。exhaustive Record ⇒ typecheck 逼两 entry 补齐。 -->
- [x] 1.2 Gate `RoleDispatcher.setup()` role registration: patrol/notification capability decides whether the 12 patrol roles register; follow/profile_visit decides whether AuthorEvaluator/FollowAgent register. <!-- cloud 19b2e13 **偏离（提案前提有误，实装期坐实并修正）**：AuthorEvaluator/FollowAgent **不是** inert——AuthorEvaluator 是「评论结算→返回 feed」的桥（emit profile.skipped 触发 BackToFeed），FollowAgent 的 profile.done 是主页子链返回信号。裸砍其注册会让 FB 每条评论后 loop 停摆到看门狗杀会话。故：①patrol&&notification→canPatrol() 关断原子 12 角色巡视子系统（唯一入口 NotificationGatekeeper，FB 从不 emit notification.detected）；②profile_visit→关断 ProfileOpener 注册（只订 worth_visiting，本人采集不经它）+ 注入 canVisitProfile 到 AuthorEvaluator（不支持时只产 profile.skipped、绝不 worth_visiting ⇒ 主页子链结构不触发，桥保留）；③follow→注入 canFollow 到 FollowAgent（跳过关注动作、仍产 profile.done 保返回链）。AuthorEvaluator/ProfileBrowser/FollowAgent 恒注册。不变量：follow⇒profile_visit⇒browse。 -->
- [x] 1.3 Gate is fail-open: only an explicit `supported===false` skips registration; a missing entry or exception registers as today (never silently drop XHS patrol on a lookup failure). <!-- cloud 19b2e13: canPatrol/canVisitProfile/canFollow 皆 `!accountPlatform || isOrchestrationCapabilitySupported(...)`；后者 try/catch 查表失败回 true。 -->

## 2. Verification

- [x] 2.1 Cloud unit tests: XHS registration snapshot asserts all 12 patrol roles + AuthorEvaluator/FollowAgent still register; Facebook `patrol.supported===false` ⇒ patrol roles not registered; lookup miss/exception ⇒ registers as today. <!-- cloud 19b2e13: 新 test/platform-orchestration-capability-gates.test.ts（XHS 全注册 / FB 12 巡视+ProfileOpener 不注册、其余仍注册 / fail-open 无平台全注册 / 12 角色原子）+ author-evaluator.test（canVisitProfile=false→只 profile.skipped 桥保留、不调 LLM；缺省零回归）+ follow-agent.test（canFollow=false→只 profile.done 返回保留、不调 LLM）。 -->
- [x] 2.2 `npm run test:acceptance` → `npm test` → `npm run typecheck`. <!-- cloud 19b2e13: acceptance 50/50 + full 2030/2030 + typecheck 净。 -->
- [x] 2.3 Rebase (serialize on `role-dispatcher.ts` after other FB changes settle), integrate, push cloud to `master`, deploy dev. <!-- cloud 19b2e13: 串行接在 C2 开关（c04051e）之后；ff-merge c04051e..19b2e13 pushed；dev 部署（backup cloud.bak.c4gates-20260714-230316.tar.gz，healthcheck active/NRestarts=0/8787/PG select 1/飞书长连接/FB 四词已入 registry）。 --> <!-- 2026-07-14 dev deployed -->

## 3. Change Record

- [x] 3.1 Update this task record with commits and validation; `openspec validate platform-orchestration-capability-gates --strict`. <!-- 台账已回写（cloud 19b2e13 + dev 部署）。openspec validate --strict 待归档批次前跑。 -->

### 三路对抗评审（landing 前，全 SAFE / severity none）

- **fb-loop-no-stall**：FB 评论后闭环 comment.done→AuthorEvaluator(canVisitProfile=false→profile.skipped)→BackToFeed(恒注册)→feed.entered→续；被关断的 12 巡视角色触发事件（excursion.requested/browse.suspended/notification.detected）对 FB 无外部产者 ⇒ 无孤儿事件、无阻塞等待。
- **xhs-zero-regression**：XHS 四词全 supported ⇒ canPatrol/canVisitProfile/canFollow 皆 true ⇒ 全角色注册、guard 缺省放行；逐位等今天。
- **self-capture-and-failopen**：本人昵称采集走永久接线的 NicknameEnricher（非 ProfileBrowser，后者对本人 early-return），与被关断的 ProfileOpener 不相干；FollowAgent canFollow=false→profile.done→dispatcher profile.exit→BackToFeed，返回链完整；fail-open 确认。

**Landing status（2026-07-14）**：cloud master `19b2e13` LANDED + DEPLOYED dev。change 可归档（下批 triage）。
