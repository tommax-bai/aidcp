## 1. aidcp-cloud — 单一时序点改造
<!-- aidcp-cloud 7f59fbb 已实现并推送 master -->

- [x] 1.1 定位主页子链当前接线：确认「关注评估完成」事件、统一出口下发关注处、返回信息流角色的订阅（不关注分支 + 关注回执），以及返回命令构造（dwellMs/targetPage/上下文清理）所在 <!-- profile.done 处理器 role-dispatcher.ts:643；BackToFeed back-to-feed.ts；feed.entered 处理器算 dwell/targetPage -->
- [x] 1.2 在「主页关注评估完成」单一决策点改为顺序处理：当且仅当决定关注且风控放行时先下发关注命令，随后**无条件**发出一个「主页子链结束」单一信号 <!-- role-dispatcher.ts profile.done → sendCommand(follow) 后 emit profile.exit；新事件 types.ts ProfileExitPayload -->
- [x] 1.3 返回信息流角色改为只订阅该「主页子链结束」信号触发返回；**移除**其对「不关注分支」与「关注回执」的旧订阅（保留对质量否决/不互动/作者不值得访问等「未进主页就返回」来源的订阅不变） <!-- back-to-feed.ts 改订阅 profile.exit -->
- [x] 1.4 返回命令携带主页停留时长 `dwellMs` <!-- 经查：返回统一走 feed.entered 处理器算 dwell，与旧 follow-成功返回路径完全一致（handleReturn 先清当前笔记→dwell=undefined→边缘内置默认停留兜底）。本修未改 dwell 计算，仅去掉了回执往返的附带延迟；拟人停留靠边缘默认 floor，留 3.2 真机确认手感 -->
- [x] 1.5 确认关注回执仅用于配额扣减（仅真实新关注扣）与诚实成败记录，不再触发返回；不伪造回执、不改协议、不改边缘 <!-- 配额扣减仍在 action.completed{follow,ok,!already_followed}；本修不伪造回执、无协议/边缘改动；对抗性评审红线全过 -->

## 2. aidcp-cloud — 自动化测试（先 acceptance 再全量）
<!-- aidcp-cloud 7f59fbb -->

- [x] 2.1 新增/更新断言：关注被风控拦截（canInteract=false）时，主页子链仍下发一次返回信息流命令（覆盖 spec 场景「关注被风控拦截 → 仍返回信息流」） <!-- test/integration/follow-block-return-to-feed.test.ts -->
- [x] 2.2 断言时序：决定关注且放行时，关注命令在返回命令之前下发（同一决策点顺序）；返回触发器唯一、无重复返回（覆盖「FIFO 时序」「不重复返回」） <!-- 同上：iFollow<iBack、back 恰好一次 -->
- [x] 2.3 断言决定不关注分支仍返回信息流；断言关注回执仍按真实回执扣减配额且不触发返回 <!-- 不关注分支用例 + 既有「follow 配额按真实回执扣减」用例仍绿；back-to-feed 防回归用例锁契约 -->
- [x] 2.4 跑 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`；安全红线 AC-* 全过（尤其不伪造回执、不静默假成功） <!-- acceptance 26/26、full 640/640；typecheck 我的文件零错（唯一报错在他会话 WIP role-prompt-preview.ts，非本改动） -->
- [x] 2.5 提交前独立多视角对抗性评审（并发时序/事件接线/红线）：9 发现 0 真实 bug，仅修一处过时注释 + 补 design 软暂停自愈说明 <!-- workflow review-follow-block-fix -->

## 3. 真机回归（gated）

- [ ] 3.1 本机起边缘连 ECS 跑完整自动浏览，制造/等到一次关注被风控拦截，确认会话**干净回到信息流**、不再卡在作者主页（对照 2026-06-24 复现现象）
- [ ] 3.2 确认正常关注路径下「关注先点、返回后离开主页」时序成立（关注未落空），且关注后在主页有可见停留

## 4. 部署与收尾

- [x] 4.1 已上线 ECS 并验证生效 <!-- 2026-06-24 deployed: 并发会话(token-usage)把含本修 7f59fbb 的干净 master HEAD 部署并重启(ActiveEnter 20:28:39 > 文件 mtime 20:18，运行进程已加载新码)。本会话已独立验证: ECS 上 role-dispatcher/back-to-feed/event-bus-types 三文件与本地干净 HEAD 快照 md5 逐字节一致; healthcheck 全绿(active running / 8787 listening / 飞书长连接已建立 / PG select 1 / 启动日志无错)。本会话未自行 rsync(避免与并发部署竞态覆盖)，仅先做了全量备份 cloud.bak.20260624-2032.tar.gz + .env.bak.20260624。co-ship 范围: return-to-feed + safety-quota(0010) + prompt-viewer + token-usage(迁移0013由其属主已跑、healthcheck绿)。 -->
- [ ] 4.2 真机回归(task 3)后 `openspec validate return-to-feed-on-follow-block --strict` → 归档 <!-- task 3 真机回归未做，归档≠已验证(见 archived-unverified)，暂不归档 -->

> 现状：代码+测试+评审+部署已完成且线上验证生效；仅剩 **task 3 真机回归**（重起干净边端连 ECS、复现一次「关注被风控拦截」、确认会话干净回到信息流不再卡主页）。
