# Tasks — publish-select-mode-layout-robust

> 纯 aidcp-edge 侧稳健性修复；协议 / 云端不改。回写格式 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。
> 协调：`publish-command-handlers.ts` 是活跃 change `publish-trigger-and-apply` 的热点文件；集成前 `git fetch` + rebase 到最新 edge master、`runSelectMode` 段若被并发方动过手工并轨。

## 1. aidcp-edge — 稳健 runSelectMode

- [x] 1.1 `src/flows/publish-command-handlers.ts` `runSelectMode()`：点「上传图文」tab 时**只取可见候选**（可见性判据复用消费端 `offsetParent!==null || getClientRects().length>0`，兼容窄布局 `position:fixed`），躲开隐藏副本；优先 `creator-tab` / `tab` class + 精确文本，其次窄布局兜底（文本含「图文」而非「视频/长文/播客」的最小 tab 形态）。验证：单测「双布局取可见（隐藏副本在前）」通过 <!-- aidcp-edge 130acd7：CLICK_TAB 先 vis=all.filter(IS_VISIBLE) 再三级精确匹配 + 窄布局 best-effort（短文本含图文非其它频道）；单测「下发点击 JS 含 offsetParent||getClientRects」静态坐实取可见 -->
- [x] 1.2 幂等早退：点击前先判「当前激活 tab 是图文」（保守信号：某可见 tab 带 active/selected/aria-selected 且文本含「图文」不含「视频」），已在图文模式直接 `ok:true`；该早退 MUST 保守——仍是视频模式不得谎报（不静默假成功）。验证：单测「已在图文模式 → 幂等 ok，不点击」通过 <!-- aidcp-edge 130acd7：MODE_STATE 返回 'image'|'video'|''，pre-click 只认 'image'（inImageMode(false) 短路不碰 IMG）；单测幂等早退 clickEvalCount=0 -->
- [x] 1.3 统一有界重试：把「找+点+确认模式激活」并进一个约 20s 的重试环（**严格 < 云端 30s 单指令超时**），点后留 grace（~1.5s）再重点，容忍冷加载晚渲染；模式激活后置校验保留原「文件输入 accept 变图片类 / 出现『上传图片·文字配图』」信号并小幅加固（多文件输入 some、加 `image/`）。验证：单测「tab 冷加载晚渲染 → 有界重试点中」通过 <!-- aidcp-edge 130acd7：deadline=clock+20000，RECLICK_GRACE_MS=1500，poll 400ms；IMG_MODE_ACTIVE 多输入 some + image/ 前缀 -->
- [x] 1.4 诚实失败分类：始终无可见 tab 且未在图文模式 → `no_target`；点了但模式始终未激活 → `post_validate_failed`；绝不假成功。验证：单测两条失败路径分别断言 error 值 + 「不假成功」红线反例 <!-- aidcp-edge 130acd7：everClicked ? post_validate_failed : no_target；**评审硬化**：MODE_STATE==='video' 否决辅助 IMG 信号（防残留图片信号在视频模式假成功），+2 硬化单测 -->

## 2. aidcp-edge — 单测

- [x] 2.1 `test/flows/publish-command-handlers.test.ts` 加 `select_mode` 用例：取可见 / 幂等已在模式 / 冷加载后现 / no_target / post_validate_failed / 不假成功；复用既有 `FakeCdp`（按 `Runtime.evaluate` expression 分派）harness。验证：`npm test` 新用例全过 <!-- aidcp-edge 130acd7：新增 SelectModeFakeCdp（按 /*MARKER*/ 分派）+ 10 条 select_mode 单测（含 2 条对抗性硬化：video 否决 + pre-click 不盲信残留 IMG） -->

## 3. aidcp-edge — 文档

- [x] 3.1 `docs/xhs-layout-states.md` 补「创作发布页（creator.xiaohongshu.com）双布局」一节：重复两套 tab、取可见选择、模式激活判据、窄布局形态待真机标定。验证：文档含该节、与代码选择器一致 <!-- aidcp-edge 130acd7：新增 §2.7，含默认视频模式/重复 tab/取可见/幂等保守/有界重试/权威 MODE_STATE + 辅助信号 video 否决/诚实失败/窄布局待标定入口 -->

## 4. 回归

- [x] 4.1 edge：`cd ../aidcp-edge && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿 <!-- aidcp-edge 130acd7：acceptance 12 绿 + 全量 587 绿（+2 硬化）+ typecheck 净 -->
- [x] 4.2 中控：`openspec validate publish-select-mode-layout-robust --strict` 通过 <!-- 2026-07-04 strict 通过 -->

## 5. 真机标定（AdsPower 大白 k1e0ero8，2026-07-04 已做）

- [x] 5.1 宽/窄两窗口各探一次创作发布页 tab 的可见元素/文案/class，据此收紧候选。<!-- aidcp-edge f51ae9c：真机 CDP 只读 dump（scripts/calibrate-select-mode-layout.ts）。**关键发现**：①「上传图文」隐藏副本不是 display:none，而是**移到屏幕外** rect≈{x:-9758,y:-9934}（offsetParent 非空、getClientRects 非空）→ 消费端 offsetParent 判据误判其可见、且在文档序更靠前 → 旧「取首个」正点了它；②600×900 窄视口 tab 栏形态与 1904 完全一样、克隆仍在 -9758 → **不是宽/窄响应式差异，是持久屏幕外克隆、与视口无关**。**修**：IS_VISIBLE 由 offsetParent 判据改为「与视口相交」(getBoundingClientRect 非零盒 + right>0&&bottom>0&&left<innerWidth&&top<innerHeight)，排除屏幕外克隆、兼容 fixed。窄布局 best-effort 候选保留但实测未触发（无独立窄形态）。 -->
- [x] 5.2 `select_mode` 端到端真机验（驱动真实 dispatcher）。<!-- aidcp-edge f51ae9c：scripts/verify-select-mode-live.ts 跑真实 PublishCommandDispatcher 一条 select_mode——BEFORE mode=video/accept 视频类 → ok:true 531ms（点屏内 369,81、未误点屏外克隆、无重试）→ AFTER mode=image/accept=.jpg,.jpeg,.png,.webp（模式真切换）。窄视口 dump 亦取屏内可见 tab。 -->
- [x] 5.3 接发布链路簇 3 **整条** `/publish` 端到端（会真发一条帖：审批→填写→提交→落地）——`select_mode` 步已单独验，剩全链路。留待簇 3 一并跑。<!-- 2026-07-10 transferred to publish-trigger-and-apply task 11.4 as chain-wide /publish validation; not a blocker for this select_mode robustness change. -->
