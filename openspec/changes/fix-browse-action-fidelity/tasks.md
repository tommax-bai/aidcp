# Tasks — fix-browse-action-fidelity

> 承 fix-browse-loop-resilience（已归档）。本 change 修部署后真机暴露的 3 个动作保真/决策正确问题。
> 进度回写：完成标 `[x]` + 行尾 HTML 注释 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。

## 1. aidcp-edge — 评论滚动真执行（deep-read-fidelity）

- [x] 1.1 `scrollNoteComments`：单次 eval 内 overflow 上溯定位真可滚动容器 + 记录 before → scrollBy(去 smooth) → 返回 {before,after} <!-- aidcp-edge fd01b7f -->
- [x] 1.2 按实测位移如实回报：scrolled=N/total（有位移）/ no_scroll（命中不可滚）/ no_target（无容器）；logger 打真实次数 <!-- aidcp-edge fd01b7f -->
- [x] 1.3 滚动间隔 cardGapTiming → TIMING_PRESETS.scroll <!-- aidcp-edge fd01b7f -->
- [x] 1.4 运行时按 overflow 能力定位（无硬编码 class 需校准）；真容器最终核对并入 6.x 真机验收 <!-- aidcp-edge fd01b7f overflow-walk 取代硬编码，真机确认放 6.2 -->
- [x] 1.5 测试：mock 返回 before/after scrollTop；新增 真实位移→scrolled / 命中不可滚→no_scroll 用例 <!-- aidcp-edge fd01b7f -->

## 2. 关注决策只用真实信号（follow-decision，both）

- [x] 2.0 ECS follow-agent 状态核对 <!-- 部署版 d1d8a9b 含 9e23bc9 软化措辞，但 LLM 仍以"作品数未知"skip → 软化不够，本次彻底移除作品数 -->
- [x] 2.1 aidcp-cloud `follow-agent.ts`：prompt **彻底移除"作品数"**（连负向措辞也不提，避免再 anchor），改以 粉丝数 + 获赞与收藏 + 相关性判定 <!-- aidcp-cloud 3e9b1be -->
- [x] 2.2 aidcp-edge `extractAuthorProfile`：新增抽取"获赞与收藏"（label match /获赞|收藏/ 取 .count） <!-- aidcp-edge fd01b7f -->
- [x] 2.3 协议两侧同步加可选 `likesCollects`：edge protocol + cloud protocol/types(ProfileDetailData/ProfileBrowsedPayload)；ProfileBrowser 透传 <!-- aidcp-edge fd01b7f / aidcp-cloud 3e9b1be -->
- [x] 2.4 测试：edge profile 抽取断言 likesCollects；cloud follow prompt 不含作品数 + postsCount=0 但粉丝/获赞健康→follow <!-- aidcp-edge fd01b7f / aidcp-cloud 3e9b1be -->

## 3. aidcp — back 按页型返回 + 404 健壮（browse-loop-resilience 增量，both）

- [x] 3.1 aidcp-cloud `role-dispatcher.ts`：`feed.entered(back_to_feed)` 把 `payload.pageType` 透传为 `params.targetPage` <!-- aidcp-cloud 3e9b1be -->
- [x] 3.2 + 3.3 aidcp-edge `navigateBack` 统一硬化：在作者主页时跳过 history.back 直接整页导航（消除经过期笔记 404 闪现）；按"目标列表 URL + 有可见卡片"健康校验，不健康即 Page.navigate(exploreUrl) 兜底；search 不可达回退 explore（不卡死） <!-- aidcp-edge fd01b7f 用 URL+卡片健康校验取代单独的"笔记不见了"文本探测 -->
- [x] 3.4 测试：cloud 断言 feed.entered{pageType:'search'}→navigation.back{targetPage:'search'}（feed→feed）；edge navigation.back 无 targetPage/水合路径回归（含上轮） <!-- aidcp-cloud 3e9b1be / aidcp-edge -->

## 4. aidcp-edge / aidcp-cloud — 校验

- [x] 4.1 edge `npm run typecheck` + `npm test` 通过 <!-- aidcp-edge fd01b7f 216→217 -->
- [x] 4.2 cloud `npm run typecheck` + `npm test` 通过 <!-- aidcp-cloud 3e9b1be 167→169 -->

## 5. aidcp-cloud — 部署（安全序列，仅 cloud 改动后执行）

- [x] 5.1 ECS 备份 <!-- /opt/aidcp/cloud.bak.20260617-211609.tar.gz + .env.bak.20260617-211609 -->
- [x] 5.2 rsync src(5 文件) → restart → healthcheck 全绿 <!-- aidcp-cloud 3e9b1be deployed 2026-06-17 21:16：active(MainPID 1393245,NRestarts 0)+8787+飞书长连接已建立+PG 锚点缓存就绪+RoleDispatcher 无报错；获赞与收藏 grep 0→4、targetPage 0→1；isales 未触碰 -->
- [x] 5.3 失败回滚预案：备份在手，healthcheck 通过未触发 <!-- 回滚：tar -xzf cloud.bak.20260617-211609.tar.gz -C /opt/aidcp && systemctl restart aidcp-cloud.service -->

## 6. 真机验收复跑（edge 重启到最新构建后）

- [ ] 6.1 edge 本地重启到最新构建（含 fix-browse-loop-resilience + 本 change）
- [ ] 6.2 验证：评论真滚动（scrollTop 变 / 日志 scrolled=N/total 真实）、健康创作者被关注、搜索会话返回搜索结果、无 404 滞留、循环连续多篇
- [ ] 6.3 验收结果回写本 tasks.md

## 7. 收尾

- [ ] 7.1 `openspec validate fix-browse-action-fidelity --strict` 通过
- [ ] 7.2 archive
