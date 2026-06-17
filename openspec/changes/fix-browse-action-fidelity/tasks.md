# Tasks — fix-browse-action-fidelity

> 承 fix-browse-loop-resilience（已归档）。本 change 修部署后真机暴露的 3 个动作保真/决策正确问题。
> 进度回写：完成标 `[x]` + 行尾 HTML 注释 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。

## 1. aidcp-edge — 评论滚动真执行（deep-read-fidelity）

- [ ] 1.1 `src/browse/browse-session.ts` `scrollNoteComments`：单次 Runtime.evaluate 内按 overflow 能力上溯定位真正可滚动容器（评论节点祖先中首个 `scrollHeight>clientHeight && overflowY∈auto/scroll`），记录 `before` scrollTop → `scrollBy({top:360})`（去 smooth）→ 返回 `{before,after}`
- [ ] 1.2 按实测位移如实回报：累计 `after>before` 的次数；有位移→`ok:true reason=scrolled=N/total`；全程无位移→`ok:false reason='no_scroll'`（区别 no_target）；logger 打真实次数
- [ ] 1.3 滚动间隔由 `cardGapTiming` 改为 `TIMING_PRESETS.scroll`（保留入口 thinkBefore）
- [ ] 1.4 CDP 真机现场核对评论区真正可滚动祖先（实测 scrollHeight/overflowY），校准上溯起点选择器
- [ ] 1.5 测试：更新 mock 返回带 before/after scrollTop 的 JSON；新增「真实位移→scrolled=N」「命中不可滚→no_scroll」用例，去掉仅靠 includes 即 found 的夹具

## 2. 关注决策只用真实信号（follow-decision，both）

- [ ] 2.0 比对 ECS 上 follow-agent.ts 是否已是 9e23bc9（确认是否还需清理 prompt 软化残留）
- [ ] 2.1 aidcp-cloud `src/agents/follow-agent.ts`：prompt **移除"作品数"信号行**，改以 粉丝数 + 获赞与收藏 + 内容/作者相关性判定；不再以"作品数未知"为由 skip
- [ ] 2.2 aidcp-edge `src/browse/browse-session.ts` `extractAuthorProfile`（主页统计抽取）：新增抽取"获赞与收藏"（`.user-interactions` 内 `shows==='获赞与收藏'` 对应 `.count`）
- [ ] 2.3 协议两侧同步加可选字段 `likesCollects`：edge `src/comm/protocol.ts` `ProfileDetailPayload` + cloud `src/comm/protocol.ts` + cloud `src/event-bus/types.ts` `ProfileDetailData`/`ProfileBrowsedPayload`；ProfileBrowser 透传到 follow-agent 输入
- [ ] 2.4 测试：edge profile 抽取夹具断言 likesCollects 被解析；cloud follow-agent 在 postsCount 未知但粉丝/获赞健康 + 相关 → verdict=visit/follow（不再 skip）

## 3. aidcp — back 按页型返回 + 404 健壮（browse-loop-resilience 增量，both）

- [ ] 3.1 aidcp-cloud `src/orchestrator/role-dispatcher.ts`：`feed.entered(back_to_feed)` 把 `payload.pageType` 透传为 `params.targetPage`
- [ ] 3.2 aidcp-edge `src/browse/browse-session.ts` `navigateBack`：`search` 分支补 URL 校验 + 兜底（失配则重新发起搜索或回 explore，不再裸 history.back+sleep）
- [ ] 3.3 aidcp-edge 新增 404/坏页探测（"笔记不见了/当前笔记暂时无法浏览"等标记 + 0 卡）：命中即 `Page.navigate(exploreUrl)` + `waitForVisibleCards` 健康校验后再 `reportVisibleCards`；倾向 search 来源或回退目标带 token 时直接 Page.navigate 跳过 history.back
- [ ] 3.4 测试：cloud 断言 `feed.entered{pageType:'search'}` → `navigation.back{targetPage:'search'}`（pageType:'feed'→'feed'）；edge 断言坏页/0 卡→兜底导航而非静默

## 4. aidcp-edge / aidcp-cloud — 校验

- [ ] 4.1 edge `npm run typecheck` + `npm test` 通过
- [ ] 4.2 cloud `npm run typecheck` + `npm test` 通过（本地仅代码级验证，不起 cloud）

## 5. aidcp-cloud — 部署（安全序列，仅 cloud 改动后执行）

- [ ] 5.1 ECS 备份 `/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`
- [ ] 5.2 rsync src → `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 + 飞书长连 + PG）；**绝不碰 isales**
- [ ] 5.3 失败即回滚

## 6. 真机验收复跑（edge 重启到最新构建后）

- [ ] 6.1 edge 本地重启到最新构建（含 fix-browse-loop-resilience + 本 change）
- [ ] 6.2 验证：评论真滚动（scrollTop 变 / 日志 scrolled=N/total 真实）、健康创作者被关注、搜索会话返回搜索结果、无 404 滞留、循环连续多篇
- [ ] 6.3 验收结果回写本 tasks.md

## 7. 收尾

- [ ] 7.1 `openspec validate fix-browse-action-fidelity --strict` 通过
- [ ] 7.2 archive
