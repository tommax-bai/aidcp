> **基线（2026-07-29 真机实测，Xu Nu / `k1f4kcsv` 越南语首页）**：`div[role="feed"]`=0；`[role="article"]`=2（均为 286px 空壳）；
> `[aria-posinset]`=11；退役 TS 回落路 → **5 张真卡**（作者 + 正文均正确），其中 **2 张**已带可接受 permalink；
> 页面滚动正常（高度 2010→9407）。**预期收益是「可上报卡 0 → 2」，不是 0 → 5**（另 3 张的 permalink 是悬停才出现的诱饵，属另一 change）。
>
> **热点文件**：`00-shared.js` 与 `20-feed.js` 与 change `restore-native-facebook-feed-scroll-continuation`（已合 master，edge `a7f9edc`）
> 及 `restore-native-facebook-residual-parity`（在途）同属 Facebook 注入脚本区。集成前 rebase 到最新 master。

## 1. aidcp-edge — 对照与落点确认

- [ ] 1.1 逐行读退役实现 `src/facebook/post-identity.ts` 的 `fbFeedFallbackCards`（`:87-106`）、`fbFeedMergeCards`（`:126-134`）、`fbFeedTopCards`（`:135-150`），把判据抄成清单（只作对照，**不复活** TS 代码）
- [ ] 1.2 确认 `00-shared.js` 的 `topArticles()` 现状与 9 处消费方（`10-feed-like.js:39`、`20-feed.js:23/43/228`、`30-reels.js:23`、`90-dispatch.js:39/190`、`00-shared.js:469`），逐处判断放宽候选集是否安全（判据：是否按 permalink 精确匹配 + 唯一命中）
- [ ] 1.3 确认注入脚本的拼接顺序与作用域（同一函数体、按文件名序），据此确定新 helper 只能用 `00-shared.js` 内已定义的工具（`all` / `visible` / `text`），不得引用后续文件的常量

## 2. aidcp-edge — 补回回落找卡路径（design D1 / D2）

- [ ] 2.1 在 `00-shared.js` 加两个具名选择器常量：帖子正文标记（`[data-ad-comet-preview="message"],[data-ad-preview="message"],[data-ad-rendering-role="story_message"]`）与作者链接（`h2 a[href],h3 a[href],h4 a[href]`），逐字对齐退役实现
- [ ] 2.2 实现回落发现：以正文标记为种子；跳过已在 `div[role="feed"]` 内的种子；从种子向上走到「自身之外且内部含作者链接」的祖先为卡边界；走到 body / documentElement 仍未命中 ⇒ **不成卡**（红线：绝不回落到 body / `[role="main"]`）
- [ ] 2.3 实现合并去重：语义路结果与回落路结果按互不包含去重（外层胜），按文档顺序排序；`topArticles()` 返回合并结果
- [ ] 2.4 确认语义化版式零回归：存在 `div[role="feed"]` 且有水合语义卡时，合并结果逐位等于今天的语义路结果

## 3. aidcp-edge — 补回水合过滤（design D3）

- [ ] 3.1 在 `00-shared.js` 加水合判据：卡含作者链接**或**正文标记即算水合（两者取或，不取与）
- [ ] 3.2 `20-feed.js:228` 的 `articleCount` 改为只数已水合的卡；`topArticles()` 本身**不**加水合过滤（发现宽、计数严）
- [ ] 3.3 复核 `20-feed.js:43` 的 `listState` 推导：`present_unreportable` 的依据须与 `articleCount` 同源，不得一处严一处宽

## 4. aidcp-edge — 真机比对验证（design D4）

> 本机有已登录 Xu Nu 的 AdsPower 浏览器在跑（本次调查启动，未关闭）。注入脚本无 JS 层单测夹具，故以真机比对为主要证据。

- [ ] 4.1 把改后的发现逻辑注入实页，断言：合并后卡数 ≥5
- [ ] 4.2 逐张核对卡边界：每张有作者名与正文，且与本次基线的 5 张一一对应（**不能只看数量对**）
- [ ] 4.3 断言带可接受 permalink 的卡 ≥2（对应预期收益 0 → 2）
- [ ] 4.4 断言同一 permalink 不会同时命中语义卡与回落卡（合并去重生效）
- [ ] 4.5 断言 `articleCount` 不再把那 2 个空壳计入（水合过滤生效）
- [ ] 4.6 在一个**语义化**版式上复核零回归（可用另一环境或群组 / 搜索页；若本机无可用样本，转 7.x 真机项并写明未验）

## 5. aidcp-edge — 回归与集成

- [ ] 5.1 `cargo test`（Native 引擎）全过
- [ ] 5.2 `npm run typecheck` 全过
- [ ] 5.3 `npm run test:acceptance` 再 `npm test` 全过（顺序按 CLAUDE.md §4）
- [ ] 5.4 `scripts/land-change aidcp-edge restore-native-facebook-feed-card-discovery`（rebase 到最新 master 后 ff）
- [ ] 5.5 回写本文件：完成项标 `[x]` 并附 `<!-- aidcp-edge <sha> 备注 -->`，sha 取自**已推送**提交

## 6. 部署

- [ ] 6.1 记录：本 change 改的是编入 Rust 二进制的注入脚本，**仅 push 不生效**，须重打边缘客户端包；按 CLAUDE.md §6 打包属用户显式触发，不进自动收尾
- [ ] 6.2 云端零改动确认（无需部署）

## 7. 真机验收 backlog 登记

- [ ] 7.1 登记「回落找卡在其余版式（群组页 / 搜索页 / 语义化首页 / Reels）上不误抓容器」的跨版式复核
- [ ] 7.2 登记「水合过滤是否会在慢网下把真卡误判成空壳」的观察
- [ ] 7.3 登记「合并后候选集变大是否影响点赞定位的唯一命中率」

## 8. 明确未做（登记，不留错觉）

- [ ] 8.1 **视频路（退役实现三路中的第 ②）未搬**。理由：准入依赖 `08-reaction-semantics.js` 的点赞 / 评论控件语义，跨文件取用引入隐式加载顺序耦合；实测该页 `[data-video-id]` 仅 1 个且其所属卡已被回落路覆盖。后续若在别的版式上观察到「有视频卡但回落路抓不到」，再单独立项
- [ ] 8.2 **时间戳诱饵链接未处理**。实测该版式时间戳 href 平时指向站点根路径，真实悬停后才换成 `/<主页>/posts/pfbid…` 或 `/permalink.php?story_fbid=…`（视口内 7/7 复现；视口外悬停无效）。退役实现同样没有，属**新能力**而非回归，另起 change
- [ ] 8.3 记录：`Nancy Terry` / `k1enonmg` 环境的 Facebook 标签页实测为 Chrome 错误页（整页未加载），与本 change 无关，疑代理，另查
