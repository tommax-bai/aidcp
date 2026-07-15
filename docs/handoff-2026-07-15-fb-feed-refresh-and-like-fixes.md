# Handoff — FB feed「一直刷新」+「读了不点赞」两大卡点根因修复（2026-07-15，真机驱动）

> 接手先读本文件 + backlog 簇 82（含更正块）+ 三条 memory：`fb-feed-dialog-guard-reload-churn`、`fb-feed-dialog-guard-reload-churn`（刷新）、`token-cost...`。本轮在 dev 真机（FB 号 Tianxing Bai `ads-k1ei3dbi`，独立受控核心 mode=on）把两个长期卡点根因定位并修复、部署，全程 CDP + 日志取证。

## 0. 一句话结论

**两个独立卡点都已根因定位 + 修复 + 部署：①「页面一直刷新」= edge `ensureFeed` 的 `!dialogOpen` 守卫遇 FB 首页瞬时良性弹层→每条 scroll 整页重载（已修 edge `fb8c5b3`，真机验证零重载）；②「读了从不点赞」= 先是人设太窄（已放宽人设，读+粗筛打通），再是 cloud FB 点赞闸的同步事件竞态（已修 cloud `56112be`，部署 dev）。** 截至交接，正在真机验证「第一个真点赞」是否落地。

## 1. 已 land 的三处修复

### 1a. edge — FB feed 刷新churn（`fb8c5b3`，master，已推）
- **根因**：`ensureFeed` onTarget 判据含 `&& !dialogOpen`。FB 首页常挂**瞬时良性** `[role=dialog]`（聊天/加载/通知浮层，来了又走）→ 每条 scroll 命令开头都 `Page.navigate` 整页重载（经 `fbsbx.com/maw_proxy_page` 重定向回首页）→ feed 被钉回顶部、永远下不去。取证：`timeOrigin` 每 ~8s 重置、window 标记被清、顶层 `frameNavigated` 无 script 发起标记=命令式导航。
- **修法**：`src/facebook/feed-reader.ts` 去掉 `!dialogOpen`（已在正确列表面 + feed 容器在场即为在目标）；`src/facebook/facebook-session.ts` 的 `scrollFeed` 到底判据改懒加载感知（`scrollHeight` 不再增长 + 接近底部 + 连续 2 轮确认才 `feed_exhausted`）；新增 `scrollMetrics()` + ensureFeed 导航诊断日志。
- **验证**：修复后 26s，timeOrigin 恒定、scrollY 3780→5066 一路下滚、scrollHeight 懒加载追加、整页导航仅启动 1 次、`feed_exhausted`=0。单测 3 新 + edge 全量 1342 过。
- **openspec change**：`facebook-feed-dialog-and-lazyload-refresh-fix`（已建 proposal+tasks+spec delta，`validate --strict` 过）。
- **⚠ 未上运营机**：这是 edge 客户端代码，运营机 GUI 跑的是旧打包版——生效要**重打客户端包**（按惯例默认不做，等显式发版）。本机独立核心跑 tsx 源码已带修复。

### 1b. 人设放宽（改 dev DB，热加载，未重启云端）
- **根因**：选卡角色（content_evaluator）忠实执行原人设「河内市餐厅/服务岗」→ 连工厂招工帖/河内省的都划过。
- **修法**：把人设放宽成「**任何越南招工帖通吃，不管省份、不管行业**」。用面板 `POST /api/auth/login` + `PUT /api/persona/61591753702668` 热加载（内部 `store.set()` 写库+刷缓存，**不重启云端、不影响小红书车队**）。脚本在 scratchpad：`push-persona.cjs` + `persona-broad.yaml`（现口径 = location/industry-agnostic）。
- **效果**：读 + 粗筛打通——view 快速涨、粗筛正确 pass 招工帖（Qisda/Autonics 工厂招工）、close 非招聘（外卖/卖花/垃圾处理）。
- **注**：人设改在 **dev 库**。原窄人设已备份在对话里（scratchpad `persona-k1ei3dbi.backup.yaml`）。

### 1c. cloud — FB 点赞闸同步事件竞态（`354d6a6`+`56112be`，master，已推，已部署 dev）
- **根因**：`interaction_appraiser` 恒 `skip fb_quality_not_passed`、系统性挡掉全部点赞。`[fb-gate]` 诊断日志取证：**eligibility 检查 `passed=false` 紧接着才打 `quality_passed add`**——顺序反了。`quality.pass` 有两个同级订阅者（gate 的 add + deep_reader）；角色 subscribe 在 setupCommandTranslation 之前（role-dispatcher :1290-1291），deep_reader 先跑，且 FB（不看图/不滚评论）下它在自己的 quality.pass 处理器里**同步**一路驱动到 reading.done→点赞资格检查，早于同级的 gate add → 检查时集合恒空。**不是 noteId 形态漂移**（两处 key 实测一致）。
- **修法**：`facebookNaturalInteractionEligibility` **不再硬闸 `quality_passed` 集合**——`interaction_appraiser` 由 `reading.done` 触发，而 reading.done 只可能在 curator quality.pass 驱动深读链后发出，**能走到点赞判定本身就证明 curator 已放行**。改为只闸 `content_selected`。另加 `facebookPostKey()` 把 noteId 归一到帖数字 id（防将来形态漂移，防御性）+ `[fb-gate]` 诊断日志。
- **测试**：`facebookPostKey` 6 新单测过、acceptance 50 过、typecheck 净。
- **openspec change**：**尚未建**（commit 里引用了名字 `facebook-natural-interaction-gate-key`，但 change 目录未建）——**接手补建 + 归档**。
- **⚠ 诊断日志还在**：`[fb-gate]` 三处 `console.log` 是这轮加的取证日志，验证完点赞后可考虑降噪/移除（现很有用，先留）。

## 2. 当前状态 / 接手第一步

- **独立核心还在跑**：`ads-k1ei3dbi` mode=on 连 dev（`ws://121.89.85.150:8787`），tsx 源码含 edge 修复。日志 `scratchpad/fb-standalone.log`。**它占着 AdsPower 分身 k1ei3dbi**——用户已在客户端关掉该号移出车队（所以能独立跑不撞车，见 memory `fb-feed-scan-onecard-livelock`）。接手若要停：`pkill -f "tsx src/main.ts"`（会留浏览器进程，AdsPower 不自动关）。
- **正在验证**：cloud 修复部署后，点赞是否真落地。**接手先看**：`ssh dev "journalctl -u aidcp-cloud.service --since '5 min ago' | grep -E 'fb-gate\] eligibility|action=like|role=browse:interaction_appraiser'"`——若 eligibility 后**不再** `fb_quality_not_passed`、出现 `role=browse:interaction_appraiser` 的 LLM 判定 + `action=like` + 边缘 `fb-like` + like 计数>0 = **点赞打通**。
- **RETRIABLE 未处理**：backlog 82.4 硬前置「真开前把 FB like 从 `RETRIABLE_INTERACTION_REASONS` 移除」（避免对已赞帖二次 toggle 撤销）——**点赞一旦跑起来，这个要尽快做**（edge `role-dispatcher` 里那个集合，或 cloud 侧，见 backlog）。

## 3. 剩余待办（接手清单）

1. **确认第一个真点赞落地**（若交接时还没看到）。看到后核：`isReactedState` 认「从…移除赞」串、MUST NOT 对已赞帖二次 toggle。
2. **补建 cloud openspec change** `facebook-natural-interaction-gate-key`（proposal+tasks+spec delta，delta 落 `facebook-feed-browse` 或新 capability）+ 归档 edge 的 `facebook-feed-dialog-and-lazyload-refresh-fix`。
3. **`[fb-gate]` 诊断日志降噪**（验证稳定后）。
4. **RETRIABLE 移除 FB like**（见 §2）。
5. **重打客户端包**让运营机拿到 edge 刷新修复（显式发版才做）。
6. **存 memory**：FB 点赞闸同步事件竞态这条根因（很值得记：quality.pass 同级订阅者顺序 + deep_reader 同步驱动链）。

## 4. 观测速查（durable）
- **CDP 只读取证脚本**（scratchpad）：`fb-dom-behavior.cjs`（scrollHeight/timeOrigin/window标记判真导航 vs SPA）、`fb-nav-events.cjs`（Page 导航事件）、`fb-dialogs.cjs`（列 `[role=dialog]`）、`fb-feed-probe.cjs`（扫卡口径对照）。取端口：`curl -s "http://local.adspower.net:50325/api/v1/browser/active?user_id=k1ei3dbi"` → debug_port → `curl -s http://127.0.0.1:<PORT>/json` 找 facebook page 的 webSocketDebuggerUrl。
- **人设 PUT 脚本**：`push-persona.cjs`（scp 到 ECS，`set -a; . /opt/aidcp/cloud/.env; node /tmp/push-persona.cjs /tmp/persona-broad.yaml 61591753702668`，服务端不泄密）。
- **dev journal**：`ssh -i ~/codes/isales-4.pem root@121.89.85.150 "journalctl -u aidcp-cloud.service ..."`（macOS 无 timeout，用 ssh 的 ConnectTimeout；绝不碰同机 isales）。
- **角色判定日志不带账号号**：FB 的判定看越南语内容辨别（XHS 是中文-AI）；`[content_evaluator]`/`[content_curator]`/`[fb-gate]` 的 `LLM 判定`/决策都在 journal。
