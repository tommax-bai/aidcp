## Context

aidcp 自动浏览是边-云协作的事件驱动闭环：edge `BrowseSession` 上报 `page.cards`/`note.detail`，cloud `RoleDispatcher` + 多 Agent 评估后回发 `open_note`/`scroll`/`interaction.*`/`navigation.back` 等命令。2026-06-17 真机验收发现：单篇深读链路正常，但 `back_to_feed` 返回后整循环死锁——这是已知「空扫→死锁」修复（`0a78363` 初始路径、`3bffc50` 仅 `navigateBack` 的 `targetPage==='feed'` 分支）的**未覆盖孪生路径**。约束：cloud 只在 ECS `121.89.85.150` 运行、改动须走部署安全序列且绝不碰同机 isales；不改 `protocol.ts` 报文形状；正文选择器收紧是 `f8712f5` 为修「标题…刚刚」假阳性引入的，拓宽时不能让该假阳性回归。

## Goals / Non-Goals

**Goals:**
- 破除 `back_to_feed` 后的边-云互等死锁，使浏览循环能连续跑多篇笔记。
- 让 cloud orchestration 具备不依赖 edge 善意、且不依赖外部 SIGTERM 的自愈能力（back 续刷 + idle 看门狗）。
- 文本笔记正文跨布局变体可抽到、抽取失败如实记录；点赞数 feed/detail 口径一致。
- 补回归测试覆盖生产实际路径（无 `targetPage` 的 back、无 `#detail-desc` 的正文布局）。

**Non-Goals:**
- 不改协议报文形状或新增报文类型（`targetPage` 语义保持向后兼容：缺省即按 feed）。
- 不重构 RoleDispatcher 的事件总线架构；只在现有订阅上增量加 handler/timer。
- 不调拟人化时序参数（command-pacing 另有 spec）。
- 不解决小红书主页作品数不公开（postsCount=0=未知，已是既定结论）。

## Decisions

- **决策 1：edge 把 `targetPage===undefined` 路由到 `'feed'` 分支（load-bearing）。** 在 `navigateBack` 把 `if (targetPage === 'feed')` 扩为 `if (targetPage === 'feed' || targetPage === undefined)`（或参数默认 `'feed'`），复用已有 `waitForVisibleCards(8000)` + `Page.navigate` 兜底。
  - 备选：让 cloud 在 `role-dispatcher.ts:352` 补 `params.targetPage='feed'`。否决为唯一手段——cloud 改动要重新部署 ECS，而 edge 单点修复零部署成本即可破死锁；cloud 侧作为纵深一并加（决策 3），双保险。
- **决策 2：`reportVisibleCards` 空扫不静默。** 0 卡时重轮询一次，仍空则显式发 `page.cards{cards:[]}`。
  - 取舍：显式空报有「cloud 对空 cards[] 是否会误判 session.end」的风险（见风险 + 未决问题）。因此把 **cloud 的 back 续扫（决策 3）设为主兜底**，edge 显式空报为次兜底；实装前先核对 `ContentEvaluator`/`FeedScroller` 对空 `cards[]` 的处理，若不安全则只走「重轮询 + cloud 续扫」、不发空报。
- **决策 3：cloud 在 `action.completed{back, ok:true}` 加续扫。** 新增/扩展 handler 发 `scroll{reason:'rescan_after_back'}`，使 back 自驱动。注意避开与 `follow`/`browse_images`/`scroll_comments` 的 `noRecoverScroll` 冲突（那些有各自推进路径）。
- **决策 4：cloud idle 看门狗用真 wall-clock 定时器。** 现状 orchestration 内无任何 `setInterval/setTimeout`（grep 为空），`SessionMonitor` 的 elapsed 检查是事件驱动的——循环一静默就再不触发。新增一个 `setInterval`：刷新「最后活动时间戳」于每次 edge 上报/命令；超 N 秒发 `scroll` nudge、超 M 秒发 `session.should_end`。会话结束/销毁时 `clearInterval`，避免泄漏与误触已结束会话。
- **决策 5：正文选择器抽成单一共享列表，门与抽取器复用。** 拓宽候选为 `['#detail-desc', '.note-detail-mask .desc', '.desc', '#detail-desc .note-text', '.note-scroller .note-text', '[class*="note-content"] .note-text']`，仍排除裸 `.note-content`/`[class*=content]`。门超时 3500→~5500ms。超时日志按「modal 内是否还有任何文本节点」区分两类。
- **决策 6：点赞数选择器收紧。** `feed-scroller` 去掉末位 `[class*=count]`（或约束到 `like-wrapper` 内）；`note-extractor.countNear` 先 `like-wrapper` 精确再退 `like` 子串。

## Risks / Trade-offs

- **[显式空报触发 cloud 误判 session.end] → 缓解**：实装前核对 `ContentEvaluator.evaluate` 对空 `cards[]` 的行为；若会提前结束会话，则不发空报、改以「重轮询 + cloud back 续扫 + 看门狗」兜底（决策 3/4 已能独立破死锁）。
- **[正文选择器拓宽导致「标题…刚刚」假阳性回归] → 缓解**：变体候选一律 scope 到 `.note-text`/`.desc` 末级文本节点，不引入裸 `.note-content`；补一条断言「正文不含 title 前缀/『刚刚』时间串」的测试。
- **[看门狗误结束仍健康的慢会话] → 缓解**：idle 阈值取足够宽（nudge 与 end 阈值分层，M 远大于单次拟人停留上限），且任何 edge 活动都刷新时间戳；先 nudge 再 end，给恢复机会。
- **[cloud back 续扫与 edge 自身重报 page.cards 重复驱动] → 缓解**：续扫是 `scroll`（edge 执行后才重报 cards），与 edge 返回路径的一次 `reportVisibleCards` 在时序上串行、不会双开笔记；必要时按 `reason` 去重。

## Migration Plan

1. edge 改动本地实装：`npm run typecheck` + `npm test`（含新增回归）+ `npm run test:acceptance` 通过。
2. cloud 改动本地代码级验证（`typecheck` + `test`），**不本地起 cloud**。
3. cloud 部署走安全序列：ECS 先备份 `/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak`；`rsync`（排除 .env/node_modules/.git）；`systemctl restart aidcp-cloud.service`；healthcheck（active + 8787 监听 + 飞书长连 + PG `select 1`）；失败即回滚备份。绝不触碰同机 isales。
4. 重跑 5 分钟带时间戳真机验收（edge 连 ECS），按 proposal 的验收判据确认。
5. 全 task 完成 → `openspec validate fix-browse-loop-resilience --strict` → archive（delta 合并进 `openspec/specs/`）。

## Open Questions

- cloud `ContentEvaluator`/`FeedScroller` 对空 `page.cards{cards:[]}` 的确切处理——是安全 no-op/触发 scroll，还是会判 session.end？（决定决策 2 是否发空报）
- idle 看门狗 N/M 阈值具体取值（需结合单篇深读最长耗时 + 拟人停留上限定标，避免误杀慢会话）。
- back 续扫的 `scroll` 与「返回后 feed 已有卡片正常重报」是否需要按 `reason`/时间窗去重，避免偶发双滚。
