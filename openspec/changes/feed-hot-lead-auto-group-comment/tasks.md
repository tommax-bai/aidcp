# Tasks — feed-hot-lead-auto-group-comment

> 纯 cloud;默认关(`group_comment_enabled=false`)→ 零回归。edge/console 不动。
> 主体＝把群评日上限对浏览触发补成真生效(评审 blocker)。热点 `role-dispatcher.ts`/`server.ts` 串行单写。

## 1. aidcp-cloud — 受闸群评触发 helper（防漂移，两源共用）

- [ ] 1.1 新增 `triggerGatedGroupComment({accountId, source, target?, snapshot?, triggerFn})`:闸序 `group_comment_enabled?(浏览)` → `canDo('comment')` 状态闸 → `countGroupAttemptsToday<cap` → `triggerFn()` → **回执 ok 才** `recordGroupCommentAttempt(accountId,{noteId,source,velocity,ageHours})`;任一不过不触发不记账
- [ ] 1.2 **排期路径重构调 helper**(server.ts:2340-2358 triggerGroupComment):行为不变(回归确认排期群评闸序/记账时机一致)
- [ ] 1.3 单测:回执 ok→记一次;非 ok(单飞/离线/缺码)→不记;cap=N 触发 N+1 次第 N+1 被拦

## 2. aidcp-cloud — 尝试台账加审计列 + 记账修复（blocker①）

- [ ] 2.1 `config/content-schedule-store.ts`:`group_comment_attempts` 自愈 `ALTER ADD COLUMN IF NOT EXISTS note_id TEXT / source TEXT / velocity DOUBLE PRECISION / age_hours DOUBLE PRECISION`(可空);`recordGroupCommentAttempt` 接受可选快照写入;`countGroupAttemptsToday` 不变
- [ ] 2.2 共码数查询:某 `group_chat_info` 被几个账号配用(供卡面标注)
- [ ] 2.3 删除 proposal/design/spec 之外代码注释里若有「triggerTargeted 自带记账」的误导(实际以本 change 为准)

## 3. aidcp-cloud — detector 经 helper 自动触发

- [ ] 3.1 `hot-lead/hot-lead-detector.ts`:命中不入队,改经 `triggerGatedGroupComment(source='hot_lead', target={noteId,title}, snapshot={velocity,ageHours}, triggerFn=()=>triggerTargeted(...injectGroup))`
- [ ] 3.2 去重:`hasInteracted` + **短时 per-account「本 note 已尝试(任意终态)」内存 TTL 标记**(防人审拒/超时后重刷反复推审) + 单飞
- [ ] 3.3 砍每会话计数;移除对 `hotLeadQueue` 依赖
- [ ] 3.4 依赖缺失安全退化:未接 helper → 命中仅 log、不触发
- [ ] 3.5 单测:全闸过→经 helper 触发一次;账号未开→不触发;canDo 拒/日上限满→不触发;已评过/近期已尝试→不触发;quality.reject→不触发

## 4. aidcp-cloud — 发出前复检 + 审批卡标注（评审 major）

- [ ] 4.1 `comment-agent/compose-approve.ts`(或审批卡构造/发出处):**post 前**复检 `canDo('comment') + countGroupAttemptsToday<cap`,不过→honest-fail 不发
- [ ] 4.2 群评审批卡加标注:「今日 x/cap(排期+浏览合计) + 风控态 + 本群码被 N 账号共用」
- [ ] 4.3 单测:触发时过闸、发出时已满→post 前复检拦

## 5. aidcp-cloud — 接线 + 去队列

- [ ] 5.1 `role-dispatcher.ts`/`server.ts`:detector 注入改为 helper + `group_comment_enabled` 判定 + `hasInteracted`;移除 `hotLeadQueue` 构造/init/注入
- [ ] 5.2 移除 `hot-lead/hot-lead-queue.ts`(+测试);`hot_lead_queue` 表停用(不强删)
- [ ] 5.3 `panel/panel-server.ts` 删 `/api/hot-leads*`;`panel/types.ts` 删 `PanelHotLeads/HotLeadQueueItem/HotLeadCommentResult` + deps `hotLeads`;`server.ts` 删 `hotLeads` 接线
- [ ] 5.4 保留:`hot-lead-config-*`/`/api/hot-lead-config`/安全页卡片/`heat-velocity.ts`/detector 订阅——不动

## 6. 回归

- [ ] 6.1 cloud:`test:acceptance` → `test` → `typecheck` 全过(AC-PUB/AC-RISK 红线不破)
- [ ] 6.2 关键断言:账号未开→命中不发(零回归);cap 对浏览触发真生效(N+1 被拦);发出前复检拦超额;人审拒后短时不重触发;排期群评行为不变

## 7. 文档 + backlog

- [ ] 7.1 归档 spec delta 合并:过滤闸 MODIFIED;helper/自动触发/真生效安全闸/卡面+发出复检/去重+审计 ADDED;队列/人审逐条/永不自动红线 REMOVED
- [ ] 7.2 `docs/real-machine-acceptance-backlog.md` 簇 16 更新:自动触发验收——账号开关、日上限触发+发出双检真生效、卡面频率/共码标注、缺码 fail-closed、note_not_found 率(D8 灰度指标)、放开红线后无越闸自动发

## 8. 部署

- [ ] 8.1 cloud dev 安全序列(备份→rsync→restart→healthcheck);edge/console 不动
- [ ] 8.2 灰度:tom 分组测试账号(工程师大白/Tmax)开 `group_comment_enabled` + cap≤2 + 配码,真机看命中→审批卡(频率/共码标注)→发出、日上限双检、note_not_found 率
- [ ] 8.3 回写 sha + `<!-- deployed -->`,`openspec validate --strict` → archive
