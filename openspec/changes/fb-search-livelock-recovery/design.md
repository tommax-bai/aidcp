# fb-search-livelock-recovery — design

## Context

事故链五环(全部已用 dev 日志+代码坐实,详见 proposal):

1. FB 发现式搜索(无 container)在 Native 引擎是退役路径:页面路由脚本 `if(!p.container) return fail('search','permission_gated')`,`searchOutcome=not_submitted`,同秒失败。
2. 云端在搜索**下发那一刻** `setSourcePageType('search')`(role-dispatcher ~:4499),失败零回滚;唯一退出=搜索结果页攒 20 张卡(~:4687-4708),页面不在搜索页则永远走不到。
3. 搜索失败触发通用兜底 `recover_after_search_failed`(~:5194-5197),滚动面从被污染的 `sourcePageType` 解析(`currentScrollSurface()` ~:2507)→ 声明 search 面;边缘观测 Reels → 诚实拒绝 `surface_mismatch_observed_reels`。
4. 该失败原因云端零消费(scroll 失败只认抢占原因 + 3 个 reels 终局原因);空闲看门狗 240s(`DEFAULT_IDLE_NUDGE_MS`)每次轻推又发同样的搜索面滚动;失败回执照样进 `action.completed` 刷新 `lastActivityAt`(SessionMonitorRole 不分 ok)→ 1h idle-end 永不触发。
5. 冷待机判定(`browser-standby.ts`)只认「被挡住且等待 ≥5min」,配额未满+续场未拦 → `no_wait` 永不让位。

用户裁定(2026-08-09):① FB 先关发现搜索(业务流程另行设计);② 云端要消费搜索失败;③ 额度按发起记,失败同样占额度;④ 失败默认处置=回主路径重新开始(redrive),带上限。

## Goals / Non-Goals

**Goals:**

- Facebook 账号不再发起发现式搜索(定向评论搜索不受影响)。
- 搜索失败与 `surface_mismatch_observed_*` 回执有明确消费路径,页面面认知可自愈。
- 搜索额度与概念词记账翻转为「发起制」,失败不免费。
- 导航类失败的默认兜底从「原地滚」改为「有界 redrive 回主浏览入口」,同因连败到顶诚实结束会话。

**Non-Goals:**

- 不实装 FB 发现搜索(引擎侧导航到搜索结果页)——等用户设计完业务流程另立 change。
- 不改边缘/引擎任何代码——边缘行为符合红线,面声明闸保持原样。
- 不改冷待机让位判据——僵局解除后会话能推进或诚实结束,槽位自然轮转。
- 不改看门狗 nudge 机制与「失败回执刷新活跃度」语义——恢复上限已由 redrive 预算承担,不叠第二道闸(加闸准入:概率低×后果可恢复=不加闸)。
- 不改协议(复用既有 `resume_redrive` reason 与既有回执字段,零新消息)。

## Decisions

### D1 FB 平台闸落点:评估器入口拦 + 下发口断言

闸放在 `search.needed` 的消费入口(SearchEvaluator 判定之前):平台为 facebook → 直接 emit `search.skipped`(具名原因 `platform_unsupported`),**不烧 LLM 调用**。下发口(三道闸处)再加同名断言式拦截作防绕过网(未来若有别的触发路径直达下发口,同样拦下并具名记录)。

- 为什么不做成 env 开关:重新放开 FB 搜索的前提是引擎实装真搜索(那是新 change 的交付物),不是拨开关;开关只会制造「拨开了但引擎还是拒绝」的新错位。
- `search.skipped` 复用既有事件与 SearchScroller 的续滚路径,浏览闭环不断流。

### D2 记账翻转:发起制,幂等键不变

- **额度**:命令真正下发(`sent=true`)即写账号 `search` 风险事实(占额度),幂等键仍用 `activityId`(下发点生成,一次下发恰一条事实)。终态回执到达时**只补写 outcome 审计**(`search.occurred` 携带三态终态照旧),不再二次占额度。
- **概念词**:下发即 `markSearched`(来源标记 `dispatch`)。永久标记——失败的词被烧掉不再重选。取舍:概念池持续产新候选,烧词代价低;换来的是「同词不会因失败被反复选中」的确定性。
- **会话预算**(`budget.searches`)与 `SearchFrequencyLimiter` 本就发起制,不动。
- **旧 Edge 兼容分支收敛**:无 `search_activity_receipt_v1` 能力的旧 Edge 原本就是「下发即标记」,翻转后两类 Edge 统一为发起制,兼容分支简化而非增多。
- 现行 spec 两条 MUST NOT(`platform-search-activity`「仅下发不计事实」/ `concept-pool-search`「actuated 前不 markSearched」)在 spec delta 中显式翻转,并写明动机:失败不记账 ⇒ 评估器永远认为「还没搜过」⇒ 失败无限重发,是本次死循环的燃料环。

### D3 失败消费:两个入口,一条处置

- **搜索失败**(`action=search, ok=false`):`sourcePageType` 回滚为 `feed` + 清搜索行程计数(searchCardsBrowsed / scrolls),再进 D4 统一失败处置。回滚放在失败回执处理最前,保证后续任何恢复滚动解析到正确的面。
- **面错位失败**(`action=scroll, ok=false, reason` 以 `surface_mismatch_observed_` 开头):按回执名重同步面认知——`observed_reels` → `lastFacebookListKind='reels'`;`observed_list` → `'feed'`;若 `sourcePageType==='search'` 一并标回 `feed`(观测已证明不在搜索页)。随后进 D4 统一失败处置。此前 scroll 在 `noRecoverScroll` 名单里失败即零处置,本分支是新增的原因级消费,插在名单判定之前(与既有抢占原因短路同构)。

### D4 默认失败处置:有界 redrive 回主浏览入口

- 导航类失败(现 `recover_after_<action>_failed` 覆盖的动作集:search / open_note / back / refresh / profile_open 等,即 `noRecoverScroll` 名单之外的)与 D3 的面错位失败,统一改走 `redriveBrowse()`:FB 主入口 Reels → Reels 入口重驱;其余 → feed redrive(`resume_redrive`)。引擎对 `resume_redrive` 的既有语义就是「回本场主浏览面重新锚定」(Reels 入口导航 / active_list_url 重置为首页),零协议改动。
- **redrive 前统一把 `sourcePageType` 标回 `feed`**——回主路径与页型账本必须同步翻,否则新到的卡片被记错类(本次事故第 2 环的对偶)。
- **恢复预算**:新增单一计数器 `failureRedriveAttempts`,凡「失败→redrive」消耗 1,任何成功动作回执清零;达上限(3)→ `endSession('recovery_exhausted')` 诚实结束。恢复预算 MUST 只由失败消费(不因准备动作扣减);结束是诚实终局,不是静默假失败——会话结束后续场闸/排程正常接管,槽位随会话结束轮转。
- 互动类失败(like / comment / collect / follow / join_group / comment_like / browse_images / scroll_comments)保持既有原地重试逻辑,不走 redrive(它们失败不改变页面位置认知)。
- Reels 既有专用重驱(`reelsRedrivePending` 及其原因集)保持原语义,新计数器与其并存:专用路径处理「Reels 内容到不到位」,新路径处理「面认知错位/导航失败」;二者都算失败恢复,共享同一恢复预算上限,防止交替空转。

## Risks / Trade-offs

- [额度翻转波及 XHS] XHS 发现搜索是真实装路径,翻转后其失败(偶发)也占额度 → 方向保守(计多不计少),平台账面安全;spec delta 写明适用两平台。
- [失败词永久烧掉] XHS 偶发失败会永久损失一个概念词 → 概念池持续补新,代价可接受;若未来成为痛点,可在新 change 里加「not_submitted 不烧词」细分,不在本次做(YAGNI)。
- [redrive 自身失败] Reels 入口进不去/首页打不开 → 恢复预算上限 3 兜住,到顶诚实结束会话;绝不无限重驱。
- [现有验收测试断言旧记账行为] `platform-search-activity`/`concept-pool-search` 的既有测试会红 → 属预期(变异可见),随实装同步改断言,并保留三态终态审计断言不放松。
- [多账号同时卡死的存量恢复] 部署后已卡死的会话:下一次看门狗 nudge 的滚动失败会走 D3 面错位消费 → redrive → 恢复;无需手工干预。

## Migration Plan

1. aidcp-automation 实装 + 单测/验收测试更新 → `npm run test:acceptance` + `npm test` + `npm run typecheck`。
2. 部署 dev(默认 target;安全序列照常:备份→rsync→restart→healthcheck)。
3. dev 观察:①FB 账号不再出现 `action=search` 下发;②存量卡死账号在一个 nudge 周期内 redrive 恢复;③搜索额度计数随发起增长。
4. 回滚 = 恢复上一版构建(无 schema 变更、无协议变更、无 env 新旗标)。

## Open Questions

(无——四项裁定已由用户 2026-08-09 当面定案;FB 搜索业务流程属后续独立 change。)
