# Tasks — feed-hot-lead-auto-group-comment

> 纯 cloud;默认关(`contactCommentEnabled=false`)→ 零回归。已 land origin/master `1bb0406` + dev 部署。
> 实装范围＝**浏览路径**(命中→过共用评论安全闸→triggerTargeted(injectContact)→飞书人审;helper 触发 ok 显式 record('comment') 消费共用配额)。
> **三项 fast-follow 未做**(见组 4 / 1.2-1.3 / backlog)——单独另案,勿丢。
> 注:代码库已被 generalize-contact-info 改名 群评→联系评论(`contact_*`/`injectContact`);spec 保留概念口径,代码用 contact_*。

## 1. aidcp-cloud — 受闸自动评论触发 helper

- [x] 1.1 `src/comment-agent/gated-auto-comment.ts` `triggerGatedAutoComment`:闸序 `canDo('comment')`(共用配额,时/日) → 子上限 `countContactAttemptsToday<cap` → `triggerFn()` → **回执 ok 才** `record('comment')`(消费共用) + `recordContactCommentAttempt({noteId,source,velocity,ageHours})`(子上限+审计);任一不过不触发不记账 <!-- cloud 1bb0406 -->
- [ ] 1.2 **排期评论/排期群评重构为调 helper**(令其也 record 消费共用配额)——**DEFERRED**(改线上现行为、风险高,单独灰度另案)
- [ ] 1.3 (原稿"改 skipRiskRecord 语义")——**未采用**:改为 helper 在浏览路径**显式 record('comment')** 达成共用配额消费,未动 takeover 跳过语义 <!-- 方案改：Option B -->
- [x] 1.4 单测:全闸过→触发+record+attempt;单场预算耗尽→session_budget;canDo 拒→risk_blocked;子上限满→daily_cap;回执非 ok→不记(6 测) <!-- cloud 1bb0406 test/gated-auto-comment.test.ts -->

## 2. aidcp-cloud — 尝试台账加审计列

- [x] 2.1 `contact_comment_attempts` 自愈 `ALTER ADD COLUMN IF NOT EXISTS note_id/source/velocity/age_hours`(可空);`recordContactCommentAttempt` 接受可选快照(ECS 已自建确认) <!-- cloud 1bb0406 -->
- [ ] 2.2 共码数查询(供卡面标注)——**DEFERRED**(随组 4 卡面)

## 3. aidcp-cloud — detector 经 helper 自动触发

- [x] 3.1 `hot-lead/hot-lead-detector.ts`:命中不入队,经注入的 `fireAutoContactComment`(内部 helper + triggerTargeted(injectContact));账号 `contactCommentEnabled` gate <!-- cloud 1bb0406 -->
- [x] 3.2 去重:`hasCommented`(risk_interactions) + 短时 per-account「本 note 已尝试(任意终态)」内存 TTL 标记 + triggerTargeted 单飞 <!-- cloud 1bb0406 -->
- [x] 3.3 场次:单场评论预算 gate + 触发成功扣减;砍每会话计数;移除 `hotLeadQueue` 依赖 <!-- cloud 1bb0406 -->
- [x] 3.4 依赖缺失安全退化:未接 fireAutoContactComment/未开 → 命中仅 log、不发 <!-- cloud 1bb0406 -->
- [x] 3.5 单测:全闸过触发+扣预算;未开不发;reject 不触发;已评过/短时已尝试不触发;裸日期超窗不触发;缓存 miss 跳过(8 测) <!-- cloud 1bb0406 test/hot-lead-detector.test.ts -->

## 4. aidcp-cloud — 发出前复检 + 审批卡标注 —— **DEFERRED（fast-follow）**

- [ ] 4.1 post 前复检 `canDo + countContactAttemptsToday<cap`(TOCTOU 收紧)——未做
- [ ] 4.2 审批卡标注「今日 x/cap + 风控态 + 本联系方式被 N 账号共用」——未做
- [ ] 4.3 相应单测——未做

## 5. aidcp-cloud — 接线 + 去队列

- [x] 5.1 `role-dispatcher.ts`/`server.ts`:detector 注入 `fireAutoContactComment`(helper+triggerTargeted injectContact) + `isAutoContactEnabled` + `hasCommentedForLead` + 单场预算取值口;移除 `hotLeadQueue` 构造/init/注入 <!-- cloud 1bb0406 -->
- [x] 5.2 移除 `hot-lead/hot-lead-queue.ts`(+测试);`hot_lead_queue` 表停用 <!-- cloud 1bb0406 -->
- [x] 5.3 `panel-server.ts` 删 `/api/hot-leads*`;`panel/types.ts` 删 `PanelHotLeads/HotLeadQueueItem/HotLeadCommentResult`+deps `hotLeads`;`server.ts` 删 `hotLeads` 接线 <!-- cloud 1bb0406 -->
- [x] 5.4 保留:`hot-lead-config-*`/`/api/hot-lead-config`/安全页卡片/`heat-velocity.ts`/detector 订阅——未动 <!-- cloud 1bb0406 -->

## 6. 回归

- [x] 6.1 cloud 全量 `npm test` **1678 pass / 0 fail**(含 AC-PUB/AC-RISK);`typecheck` 净(仅 base 预存 text-card) <!-- cloud 1bb0406 -->
- [x] 6.2 关键断言:账号未开→不发(零回归);子上限 N+1 被拦;单场预算耗尽拦;短时不重触发;canDo 拒拦(helper+detector 单测覆盖) <!-- cloud 1bb0406 -->

## 7. 文档 + backlog

- [x] 7.1 归档 spec delta:过滤闸 MODIFIED;helper/命中自动触发/浏览共用安全上限/去重+审计 ADDED;队列/人审逐条/永不自动红线 REMOVED(card+发出复检需求已从本 change 移出→follow-up)
- [x] 7.2 backlog 簇 16 更新:自动触发验收 + fast-follow(排期纳统一账本 / 卡面标注 / 发出复检)

## 8. 部署

- [x] 8.1 cloud dev 安全序列(备份 `cloud.bak`+`.env.bak`→rsync 净 master→restart→healthcheck:active/8787/8090/PG select 1/`contact_comment_attempts` 审计列自建/无错;未碰 isales) <!-- 2026-07-09 deployed dev -->
- [ ] 8.2 灰度启用:tom 分组测试账号(工程师大白/Tmax)配联系方式 + 开 `contactCommentEnabled` + cap≤2,真机看命中→审批卡→发出、子上限、note_not_found 率(→ backlog 簇 16)
