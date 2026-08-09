# fb-search-livelock-recovery — tasks

> 全部代码落 `aidcp-automation`(边缘/引擎/协议零改动)。按 CLAUDE.md §7 在 `../aidcp-automation.wt/fb-search-livelock-recovery` worktree 开发。

## 1. aidcp-automation — FB 停发发现式搜索(止血)

- [ ] 1.1 `search.needed` 消费入口加平台准入闸:Facebook 账号直接记具名跳过(`platform_unsupported`)并 emit `search.skipped`,不调用 SearchEvaluator 的 LLM 判定;定向(container)搜索链路不受影响
- [ ] 1.2 搜索下发口(三道闸处)加同名断言式拦截作防绕过网:Facebook 账号的发现式搜索到达下发口即拦下、具名记录、不进下行通道
- [ ] 1.3 测试:FB 账号触发 `search.needed` → 零 LLM 调用、零下发、`search.skipped` 续滚;XHS 账号不受影响;FB 定向评论搜索照常下发

## 2. aidcp-automation — 记账翻转为发起制

- [ ] 2.1 下发点(`sent=true`)完成全部记账:扣 `budget.searches`(现状保持)+ `recordSearch`(现状保持)+ `markSearched`(从终态处理移到下发点)+ 记 1 次账号 `search` 风险事实(幂等键 `activityId`,从 handler 的 actuated 分支移到下发点)
- [ ] 2.2 终态回执处理只补 outcome 审计(`search.occurred` 三态照旧发、重复 activityId 去重照旧),删除其记额度/标已搜的职责;旧 Edge 兼容分支(`legacy` 标记)收敛到统一发起制
- [ ] 2.3 更新既有断言旧行为的测试(platform-search-activity / concept-pool-search 相关):额度随发起增长、失败不回滚、终态只审计不计数、三态终态不放松
- [ ] 2.4 核对客户端今日进展投影(搜索格)读的是同一发起制账本,无第二套计数

## 3. aidcp-automation — 失败消费与页型回滚

- [ ] 3.1 搜索失败终态(`action=search, ok=false`)处理:`sourcePageType` 回滚 `feed` + 清搜索行程计数(searchCardsBrowsed / scrolls),先于任何兜底处置执行
- [ ] 3.2 `action=scroll, ok=false, reason=surface_mismatch_observed_*` 原因级消费分支(插在 noRecoverScroll 名单判定之前):按回执重同步 `lastFacebookListKind`,`sourcePageType='search'` 时回滚 `feed`,随后进统一失败恢复
- [ ] 3.3 测试:搜索失败 → 页型回滚、后续恢复滚动声明正确的面;`surface_mismatch_observed_reels` → 面认知纠正为 reels、不再重复同一错位

## 4. aidcp-automation — 默认失败兜底改有界 redrive

- [ ] 4.1 `recover_after_<action>_failed` 兜底从「原地滚动」改为 `redriveBrowse()`(Reels 主入口账号重驱 Reels,其余 feed redrive),redrive 前统一 `sourcePageType='feed'`;互动类 noRecoverScroll 名单保持不变
- [ ] 4.2 统一恢复预算 `failureRedriveAttempts`:失败→redrive 消耗 1,任何成功动作回执清零,达 3 次 `endSession('recovery_exhausted')` 诚实结束;与既有 Reels 专用重驱共享同一预算,防交替空转
- [ ] 4.3 测试:导航类失败 → redrive 命令(非原地滚);连续 3 次失败恢复无成功 → 会话以 `recovery_exhausted` 结束;成功回执重置预算;互动类失败不走 redrive
- [ ] 4.4 端到端回归本次事故链:模拟「FB Reels 会话搜索失败」→ 页型回滚 → redrive 回 Reels → 无 `facebook.search.scroll` 重发、无活锁

## 5. 验证与部署

- [ ] 5.1 `npm run test:acceptance` + `npm test` + `npm run typecheck` 全绿(aidcp-automation)
- [ ] 5.2 部署 dev(安全序列:备份→rsync→restart→healthcheck),观察:FB 账号零 `action=search` 下发;存量卡死账号一个 nudge 周期内恢复;搜索计数随发起增长
- [ ] 5.3 tasks.md 回写 commit sha;真机长时观察项(多账号槽位轮转恢复)如需解耦登记 `docs/real-machine-acceptance-backlog.md`
