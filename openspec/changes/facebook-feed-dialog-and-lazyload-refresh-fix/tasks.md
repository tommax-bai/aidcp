# Tasks

## 1. aidcp-edge — ensureFeed 良性 dialog 不整页重载

- [x] 1.1 `ensureFeed` onTarget 去掉 `!dialogOpen`；已在列表面且 feed 在场即为在目标；保留 `dialogOpen` 字段仅供探测/日志观测 <!-- aidcp-edge fb8c5b3 feed-reader.ts -->
- [x] 1.2 保证不导航放行路径仍跑 consent 预清理 + `blockingReason` 登录/验证码 fail-closed 复检（原有，未动）<!-- aidcp-edge fb8c5b3 -->
- [x] 1.3 新增 `ensureFeed 判非目标→整页导航` 诊断日志（打 want/surface/hasFeed/dialog/href），导航决策可观测 <!-- aidcp-edge fb8c5b3 feed-reader.ts -->
- [x] 1.4 单测：已在首页有 feed + 挂瞬时 dialog → 仍不导航（`navs` 为空）<!-- aidcp-edge fb8c5b3 test/facebook/feed-reader.test.ts -->

## 2. aidcp-edge — scrollFeed 懒加载感知到底判据

- [x] 2.1 新增 `FacebookFeedReader.scrollMetrics()`（scrollY/scrollHeight/innerHeight；探测异常回全 0）<!-- aidcp-edge fb8c5b3 feed-reader.ts -->
- [x] 2.2 `scrollFeed` 重写：本轮 0 新卡时，「高度不再增长 + 接近底部 + 连续 2 轮确认」才 `feed_exhausted`；否则继续下滚；有界 `FEED_SCROLL_MAX_ROUNDS=8`；从没扫到卡=`no_target`（区分没内容 vs 没新内容）<!-- aidcp-edge fb8c5b3 facebook-session.ts -->
- [x] 2.3 单测：懒加载还在长/未到底 → 续滚到出新卡才上报、不提前 `feed_exhausted`；高度稳定+接近底部+连续无新卡 → 诚实 `feed_exhausted` <!-- aidcp-edge fb8c5b3 test/facebook/facebook-session.test.ts -->

## 3. 回归 + 真机验证

- [x] 3.1 `npm run typecheck` 干净；edge 全量 `npm test` = 1342 pass / 0 fail（含安全红线 AC-*）<!-- aidcp-edge fb8c5b3 -->
- [x] 3.2 真机验证（dev, ads-k1ei3dbi）：修复后 26s timeOrigin 恒定/零重载、scrollY 持续下滚、scrollHeight 懒加载追加、ensureFeed 整页导航仅启动 1 次、feed_exhausted=0 <!-- 2026-07-15 CDP 只读取证 -->

## 4. 收尾

- [x] 4.1 提交推送 edge master <!-- aidcp-edge fb8c5b3 pushed -->
- [ ] 4.2 `openspec validate facebook-feed-dialog-and-lazyload-refresh-fix --strict` 通过后归档；delta 并入 `facebook-feed-continuity`
- [ ] 4.3 客户端重打包生效（按惯例默认不做，等显式发版）——真机复验「运营肉眼看浏览器不再刷新」登记 backlog 簇 82
