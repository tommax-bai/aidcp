# fb-search-livelock-recovery

## Why

2026-08-09 dev FB 车队实诊(账号 61579018622326 等多台):浏览闭环的发现式搜索在 Native 引擎里是退役路径(无 container 即 `permission_gated` 拒绝、`not_submitted`),云端却仍会发起——且在**下发那一刻**就把会话页型标成 `search`、失败后无任何回滚。此后空闲看门狗每 240s 重发一条注定失败的搜索面滚动,边缘诚实拒绝(`surface_mismatch_observed_reels`)但该回执云端零消费,失败回执又刷新看门狗活跃度,1h idle-end 兜底失效;冷待机判定看到「配额未满+续场未拦」给 `no_wait`,浏览器槽位 20+ 分钟不让出,44 台账号排队不动。搜索失败不记账,评估器永远认为「还没搜过」,失败无限重发。这不是偶发:**每一台走 Native 引擎的 FB 账号,只要触发发现搜索,100% 进入此死循环**。

## What Changes

- **FB 停发发现式搜索(止血)**:云端搜索下发口加平台准入闸,Facebook 账号不再发起发现式(无 container)搜索;评估器判了也拦下并记具名跳过。定向评论搜索(带 container,`/comment` 链路)不受影响。FB 发现搜索的业务流程由用户另行设计后再立 change 实装。
- **云端消费搜索失败与面错位失败**:搜索失败回执到达 → 回滚 `sourcePageType`(标回 `feed`);`surface_mismatch_observed_*` 滚动失败回执不再零消费,按回执携带的观测面纠正云端面认知并走统一失败处置。
- **搜索额度与概念词按「发起」记账**(**BREAKING**——翻转两条现行 spec 要求):账号 `search` 额度消耗与概念词「已搜」标记改在命令发起(真正下发)时记,失败同样占用 1 次额度;平台事实流仍保留三态诚实终态(`results_ready`/`no_results`/`failed_after_submit`/`not_submitted`)用于审计,但额度预闸/饱和判断/候选词排除一律以发起为准。方向偏保守(把没碰页面的失败也算进额度),换来「失败不免费」——防止失败搜索无限重发。
- **导航类失败默认兜底改为 redrive 回主浏览入口**:`recover_after_<action>_failed` 的「在云端以为的当前面上原地滚动」改为复用现有 `resume_redrive` 语义回本场钉住的主浏览入口(Reels 账号回 Reels 入口、Feed 账号回首页),redrive 同时把页型标回 `feed`;带同因连败上限,连败到顶诚实结束会话,不再制造新的无限循环。互动类失败(like/comment 等)保持既有各自重试逻辑不变。

## Capabilities

### New Capabilities

(无——四项全部落在既有能力的要求修订上)

### Modified Capabilities

- `platform-search-activity`:①新增「发现式搜索平台准入」要求(FB 当前不支持发现式搜索,MUST NOT 下发,具名跳过);②「仅下发命令不计搜索事实」要求翻转为「额度按发起消耗、事实流保留三态终态」。
- `concept-pool-search`:「actuated=true 后才 markSearched / 计搜索事实」翻转为「发起即标已搜、即占额度」,失败词当天不再进候选集;终态回执仍如实落审计流。
- `browse-loop-resilience`:①新增「导航类动作失败的默认恢复 = 有界 redrive 回主浏览入口(含页型回滚)」要求;②新增「`surface_mismatch_observed_*` 回执必须被消费(面认知重同步),MUST NOT 落入零处置」要求;③新增「搜索失败必须回滚搜索行程页型」要求。

## Impact

- **代码**:全部落 `aidcp-automation`(云端编排层)——搜索下发三道闸处(role-dispatcher 搜索下发链)、`action.completed` 失败处置分支、`currentScrollSurface()`/`sourcePageType` 生命周期、通用失败兜底 `recover_after_*`、搜索记账点(handler 的 search 终态处理 + concept 标记)。**边缘/引擎零改动**(边缘行为本就符合红线)。
- **协议**:零改动(复用既有 `resume_redrive` reason 与既有回执字段)。
- **风险面**:额度按发起记会使 FB 以外平台(XHS)的搜索计数略偏保守(失败也计),属安全方向;`platform-search-activity` 与 `concept-pool-search` 两处现行 MUST NOT 被显式翻转,须在 spec delta 中写明取代关系。
- **部署**:仅 aidcp-automation 服务,默认 target=dev。
