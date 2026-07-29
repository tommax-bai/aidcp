> **基线（2026-07-29 真机实测，Xu Nu / `k1f4kcsv` 越南语首页）**：`div[role="feed"]`=0；`[role="article"]`=2（均为 286px 空壳）；
> `[aria-posinset]`=11；退役 TS 回落路 → **5 张真卡**（作者 + 正文均正确）；页面滚动正常（高度 2010→9407）。
> **可上报卡：冷启动 + 纯程序化滚动（零指针事件）复测 = 0 张。** 首轮曾测得 2 张，后查明是调查中我自己悬停点亮的，
> 属测量被自身干扰污染，已作废。**本 change 的收益是「发现 0 → 5 张真卡 + 物理卡证据由假转真」，可上报卡仍为 0。**
>
> **落地**：edge `2a4752a`（rebase 到 `90e093c` 后 ff 合入 master）。

## 1. aidcp-edge — 对照与落点确认

- [x] 1.1 逐行读退役实现的 `fbFeedFallbackCards` / `fbFeedMergeCards` / `fbFeedTopCards`，把判据抄成清单 <!-- aidcp-edge 2a4752a 只作对照，未改动任何 TS 文件 -->
- [x] 1.2 逐处判断 9 处消费方放宽候选集是否安全 <!-- aidcp-edge 2a4752a 全部按 permalink 精确匹配 + 唯一命中，放宽安全；合并去重保证同帖不双份 -->
- [x] 1.3 确认注入脚本拼接顺序与作用域 <!-- aidcp-edge 2a4752a 新 helper 只用了 00-shared.js 内的 all/visible，未引用后续文件常量 -->

## 2. aidcp-edge — 补回回落找卡路径（design D1 / D2）

- [x] 2.1 加 `storyMessageSelector` / `authorLinkSelector` 两个具名常量，逐字对齐退役实现 <!-- aidcp-edge 2a4752a -->
- [x] 2.2 实现 `fallbackArticles()`：正文标记为种子 → 上溯至含作者链接的祖先；跳过语义 feed 内种子；无作者证据即不成卡 <!-- aidcp-edge 2a4752a 红线守住：走到 body/documentElement 一律放弃，绝不回落整页 -->
- [x] 2.3 实现 `mergeArticles()` 并让 `topArticles()` 返回合并结果 <!-- aidcp-edge 2a4752a -->
- [x] 2.4 语义化版式零回归 <!-- aidcp-edge 2a4752a 由 facebook-feed-like-parity.test.ts 的语义夹具（8 用例）与 client.test.ts（13 用例）守住，全过 -->
- [x] 2.5 **（实装新增，非原计划）** 文档顺序比较改用字面量 `4` 而非 `Node.DOCUMENT_POSITION_FOLLOWING` <!-- aidcp-edge 2a4752a 首版用 Node.* 直接炸了 3 个既有用例（jsdom 求值环境无 Node 全局，ReferenceError 会把整条找卡打断）。这是本次唯一一处自造缺陷，已修 -->

## 3. aidcp-edge — 补回水合过滤（design D3）

- [x] 3.1 加 `hydratedCard()`：含作者链接**或**正文标记即算水合 <!-- aidcp-edge 2a4752a 取或不取与 -->
- [x] 3.2 `articleCount` 改为只数已水合的卡；`topArticles()` 不加水合过滤 <!-- aidcp-edge 2a4752a 发现宽、计数严 -->
- [x] 3.3 `listState` 的 `present_unreportable` 依据与 `articleCount` 同源 <!-- aidcp-edge 2a4752a 两处都走 hydratedCards() -->

## 4. aidcp-edge — 真机比对验证（design D4）

> 方法教训（务必照做）：**任何取值测量必须在重载后、用纯程序化滚动（`window.scrollBy`，不产生任何指针事件）复测**。
> 本次首轮测量正是被调查过程自身的悬停污染，得出了偏乐观的结论。

- [x] 4.1 注入实页断言合并后卡数 <!-- aidcp-edge 2a4752a 冷启动零指针：semantic=2 / fallback=4 / merged=6 / hydrated=4；先前一次滚够的样本为 fallback=5 -->
- [x] 4.2 逐张核对卡边界 <!-- aidcp-edge 2a4752a 每张均有作者名与正文（Hoa hậu Nguyễn Cao Kỳ Du / Kenh14.vn / BusyCat / Adam Phillips 等），边界高度合理，与基线一一对应 -->
- [x] 4.3 ~~断言带可接受 permalink 的卡 ≥2~~ **实测为 0，原指标作废** <!-- aidcp-edge 2a4752a 原「0→2」来自被悬停污染的首轮测量；冷启动零指针复测恒为 0。该版式所有时间戳 href 均为诱饵，取身份须可信悬停（见 8.2） -->
- [x] 4.4 断言无重复身份 <!-- aidcp-edge 2a4752a duplicateIds=[] -->
- [x] 4.5 断言空壳不再计入物理卡 <!-- aidcp-edge 2a4752a merged=6 中 hydrated=4，两个 286px 空壳被正确排除 -->
- [ ] 4.6 **（未做，转真机）** 在真实语义化版式上复核零回归——本机当前无该版式样本；已由语义夹具单测覆盖，但非真机。见 7.1

## 5. aidcp-edge — 回归与集成

- [x] 5.1 `cargo test` 全过 <!-- aidcp-edge 2a4752a 106+1+2+37+1 -->
- [x] 5.2 `npm run typecheck` 全过 <!-- aidcp-edge 2a4752a 本 change 零 TS 改动 -->
- [x] 5.3 `test:acceptance`（30/30）+ `npm test`（2561 pass / 0 fail / 1 skipped） <!-- aidcp-edge 2a4752a 首跑曾 3 fail，全部由 2.5 那个 Node 全局引用引起，修后全绿 -->
- [x] 5.4 `land-change --yes` <!-- aidcp-edge 2a4752a rebase 到 90e093c 后 ff 推送，worktree/分支已清理 -->
- [x] 5.5 回写本文件 <!-- aidcp-edge 2a4752a -->

## 6. 部署

- [x] 6.1 记录：改的是编入 Rust 二进制的注入脚本，**仅 push 不生效**，须重打边缘客户端包 <!-- aidcp-edge 2a4752a 未出包，按 CLAUDE.md §6 待用户显式触发 -->
- [x] 6.2 云端零改动确认 <!-- 无需部署 -->

## 7. 真机验收 backlog 登记

- [x] 7.1 跨版式复核（群组 / 搜索 / 语义化首页 / Reels）不误抓容器，含 4.6 的语义化零回归真机复核 <!-- aidcp docs/real-machine-acceptance-backlog.md 簇 119.1 / 119.2 -->
- [x] 7.2 水合过滤在慢网下是否误判 <!-- 簇 119.3 -->
- [x] 7.3 候选集变大是否影响点赞定位唯一命中率 <!-- 簇 119.4 -->

## 8. 明确未做（登记，不留错觉）

- [x] 8.1 **视频路（三路中的第 ②）未搬**。准入依赖 `08-reaction-semantics.js` 的控件语义，跨文件取用引入隐式加载顺序耦合；实测该页 `[data-video-id]` 仅 1 个且其卡已被回落路覆盖 <!-- 后续若观察到「有视频卡但回落路抓不到」再立项 -->
- [x] 8.2 **时间戳诱饵链接未处理 —— 这是首页恢复可读的必经一步，且比原估计更重**。实测两条硬事实：① 时间戳 href 平时是站点根路径，**可信**悬停后才换成 `/<主页>/posts/pfbid…` 或 `/permalink.php?story_fbid=…`（视口内 7/7，视口外无效）；② **页面内合成的 `pointerover`/`mouseover`/`mouseenter`/`mousemove`/`focus` 一律无效**，四张卡路径仍为 `/`。⇒ 取身份**不能**留在注入脚本内（它只有一次求值、发不出可信输入），必须改成「探测 → Rust 侧下发可信指针移动 → 复探」的多步编排，并考虑节奏与可检测性。另起 change
- [x] 8.3 记录：`Nancy Terry` / `k1enonmg` 环境的 Facebook 标签页实测为 Chrome 错误页（整页未加载），与本 change 无关，疑代理，另查
