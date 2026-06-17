## Context

承 fix-browse-loop-resilience（已修 back_to_feed 死锁 + 部署）。部署后真机又暴露 3 个"动作保真 / 决策正确"缺陷（详见 proposal）。三仓铁律不变：cloud 只在 ECS、改动走部署安全序列、不碰 isales；不破坏协议报文形状（新字段一律可选、两侧同步加）。诊断均经代码 + live CDP 实证（小红书主页只有 关注/粉丝/获赞与收藏，无作品数；评论容器选择器从未校准；back 丢 sourcePageType）。

## Goals / Non-Goals

**Goals:**
- 评论滚动真实发生并按实测位移如实回报（消除"假成功"）。
- 关注决策不再依赖平台不提供的作品数；改用粉丝 + 获赞收藏 + 相关性；获赞收藏被抽取串达。
- back 按来源页型返回正确列表；返回路径对 404/过期笔记健壮、健康校验后再上报。

**Non-Goals:**
- 不改协议报文形状（targetPage 复用既有可选字段；likesCollects 新增可选字段两侧同步）。
- 不重构深读多角色编排；只在现有动作/角色上增量修。
- 不解决"小红书是否某处另有作品数"——已实证主页不提供，按不可得处理。
- 暂不做搜索结果页的完整 SPA 状态保持（recover 以重新发起搜索或回 explore 兜底为先）。

## Decisions

- **决策 1（评论滚动）：运行时按 overflow 能力定位可滚动容器，不靠硬编码 class。** 单次 `Runtime.evaluate` 内：从评论节点（`.note-text`/`[class*="comment"]`/`.comment-item`）上溯首个 `scrollHeight>clientHeight && overflowY∈{auto,scroll}` 的祖先；记录 `before=scrollTop`，`scrollBy({top:360})`（**去 smooth** 以便同步读），返回 `{before, after}`。按 `after>before` 累计真实位移次数，`ok` 与 `reason=scrolled=N/total` 据此；全程无位移→`ok:false no_scroll`。间隔改用 `TIMING_PRESETS.scroll`。
  - 备选：继续硬编码 class——否决（未校准、真机易失配，正是本 bug 根因）。
- **决策 2（关注决策）：prompt 去作品数 + 抽取获赞收藏。** follow-agent prompt 删除"作品数"信号行，明确以 粉丝 + 获赞与收藏 + 相关性判定。edge `extractAuthorProfile` 新增 match `获赞|收藏`（取 `.user-interactions` 内 `shows==='获赞与收藏'` 对应 `.count`），经 `ProfileDetailPayload.likesCollects?`（两侧协议同步加）→ ProfileBrowser → follow-agent 输入。`postsCount` 字段保留线协议但不进 prompt（向后兼容、最小改动）。
  - 备选：用加载出的笔记网格数量当作品数代理——否决（是"已加载格子数"非总作品数，不可靠）。
- **决策 3（back 页型 + 404 健壮）：cloud 透传 targetPage + edge 双分支硬化。**
  - cloud `role-dispatcher` 的 `feed.entered(back_to_feed)` 把 `payload.pageType` 透传为 `params.targetPage`。
  - edge `navigateBack`：(a) `search` 分支补 URL 校验 + 兜底（不再裸 `history.back()+sleep`，失配则重新发起搜索或回 explore）；(b) 新增 404/坏页探测（"笔记不见了"等标记 + 0 卡），命中即 `Page.navigate(exploreUrl)` 并 `waitForVisibleCards` 健康校验后再 `reportVisibleCards`；(c) 倾向"来源为 search 或回退目标是带 token 的 /explore/<id> 时直接 `Page.navigate` 目标列表页，跳过会落到过期笔记的 `history.back()`"，消除瞬态 404。
  - **edge 硬化与 cloud 透传必须同发**：否则 targetPage='search' 把会话导入当前无 recover 的 search 分支，反而更糟。

## Risks / Trade-offs

- **[评论真可滚动容器仍需真机核对] → 缓解**：用运行时 overflow 能力定位而非固定 class，天然适配；并以 scrollTop delta 兜底验证；先在 live 页 `Runtime.evaluate` 实测候选祖先再定。
- **[评论极少的笔记本就不可滚 → no_scroll 不应判失败] → 缓解**：`no_scroll` 与 `no_target` 区分；cloud 对 `no_scroll` 视为"已读完/无需滚"而非错误，不触发兜底。
- **[likesCollects 单侧加导致静默丢值] → 缓解**：edge protocol + cloud protocol/types/ProfileBrowsedPayload 同步加，补两侧测试（与上轮 counts 同类教训）。
- **[targetPage='search' 进入未 recover 的 search 分支更糟] → 缓解**：edge search 分支硬化与 cloud 透传同一批次上线，绝不分批。
- **[直接 Page.navigate 丢 SPA feed 状态、整页重载更重/更易检测] → 缓解**：仅作 recover 兜底，非搜索的正常 feed 仍优先 history.back()。
- **[deploy 9e23bc9 是否真落 ECS 存疑] → 缓解**：实装前比对 ECS 上 follow-agent.ts，再决定是否仅靠本次硬改。

## Migration Plan

1. edge + cloud 改动本地实装；各自 `typecheck` + `npm test`（含新增回归：评论 scrollTop 位移、follow 不因作品数 skip、back targetPage 透传）。本地不起 cloud。
2. cloud 走部署安全序列（备份 → rsync src → restart → healthcheck → 失败回滚），不碰 isales。
3. edge 本地重启到最新构建（让 back 死锁/404-recover/抽取/评论修复全部生效）。
4. 重跑真机验收：评论真滚动（scrollTop 变）、健康创作者被关注、搜索会话返回搜索结果、无 404 滞留、循环连续多篇。
5. 全 task 完成 → `validate --strict` → archive。

## Open Questions

- 真机评论区真正可滚动祖先的稳定特征（overflow 容器是 `.note-scroller` / `.interaction-container` / 其它？）——实装时 CDP 现场实测确定。
- 搜索结果页 recover 的最稳方式：重新 `executeSearch(keyword)` vs 直接 `Page.navigate(/search_result?keyword=)` vs 回退 explore——按真机表现定。
- ECS 上 follow-agent 是否已是 9e23bc9（决定本次是否还需带 prompt 软化的清理）。
