# Handoff — FB feed 就地读+赞 真机灰度：跑出 82.1 扫卡缺陷（2026-07-15）

> **⚠️ 本文档诊断已被后续取证推翻（2026-07-15 同日二跑）——保留作过程记录，勿据本文的「扫卡缺陷」结论行动。**
> 真根因**不是**扫卡/settleCards，而是 `ensureFeed` 的 `&& !dialogOpen` 守卫遇 FB 首页瞬时良性 `[role=dialog]` → **每条 scroll 命令都整页 `Page.navigate` 重载**（＝「一直刷新、下不去」）。**已修**：edge `fb8c5b3`（change `facebook-feed-dialog-and-lazyload-refresh-fix`，去 dialog 守卫 + feed_exhausted 改懒加载感知），真机 CDP 验证达标。点赞仍 0 是**独立**问题（content_curator 相关性粗筛拒了越南语招工帖）。权威结论见 backlog 簇 82「✅ 二跑更正」块 + memory `fb-feed-dialog-guard-reload-churn`。

> 接手先读本文件 + `docs/real-machine-acceptance-backlog.md` 簇 82（含本次「⚠ 首跑真机结论」块）。
> 本次 session 把 backlog 簇 82 的「FB feed 就地读+赞灰度」在 dev 真机跑了第一轮，**跑出一条确凿的真机缺陷**并根因定位到边缘代码，未落 change。已提交/推送安全。

## 0. 一句话结论

**FB feed 就地读+赞在真机上「只刷不点」活锁——根因是 feed 扫卡每轮只提取到 1 张合格卡、达不到「连续两轮稳定」，每次走 degraded 兜底，云端拿不到可互动的卡→无限 `scroll`。就地读/点赞机制本身没坏（就地读成功过 1 次）。同客户端的小红书号闭环完全正常，故是 FB 扫卡专属缺陷。** 下一步＝对正在跑的 FB 浏览器做**只读 CDP DOM 取证**，区分「feed 真稀疏」vs「scanCards 选择器漏配」，再决定开 edge change 修哪层。

## 1. 本次怎么跑的 / 为什么这么跑

- 目标：backlog 簇 82「FB feed 就地读+赞灰度」，原计划「先 shadow 后 on」。
- **发现 1：shadow 档从客户端 GUI 够不着。** `aidcp-edge/src/electron/fleet.cjs:88`（来自已归档 change `facebook-dev-autobrowse-enable`，commit `5e23261`）把「平台=facebook ∧ 云端=dev」的分身**硬编码返回 `'on'`**；`src/electron/main.cjs:2335` 无条件覆盖子进程 env（防外壳残留 shadow/on 泄漏）。所以 GUI 起 dev-FB 分身**一上来就是真点赞 `on`**，`shadow` 只有绕过 GUI、直接给核心进程注入 `AIDCP_FB_BROWSE_AUTO=shadow` 才生效。
- **发现 2：独立起核心跑 shadow 会与正在跑的 GUI 抢同一分身。** 本次实测：`npm start` 起核心拿到 AdsPower debug 端口 49277、正常读身份+扫首屏卡，但约 1 分钟后 GUI 车队（在册同分身）把该分身**重启到新端口 50395**，核心连的 49277 掉 → CDP 不可恢复 → 诚实下线退出（正确行为）。**两个 FB 号（`k1ei3dbi` Tianxing Bai、`k1ej3o8f` Dennis Scott）都在 GUI 花名册里**（`settings.json`），所以任何独立进程都可能撞车。
- **改用「观测正在跑的 GUI 车队」**（零扰动）：GUI 本就在 mode=on 驱动 FB 号，直接读它的日志 + 云端 journal 就拿到真机信号。这一步立刻跑出了缺陷。

## 2. 缺陷证据（硬数据）

观测账号：dev、FB 号 **Tianxing Bai `ads-k1ei3dbi`**（GUI 车队，mode=on）。两个观测窗：

### 边缘侧（客户端 GUI 车队日志）
`~/Library/Application Support/aidcp-edge/logs/edge.log`（**这是观测 GUI 车队边缘细节的唯一窗口**，car 日志按 `[ads-<profileId>]` 前缀分账号交织）。约 14h 断续活跃窗口内，`ads-k1ei3dbi`：

| 指标 | FB (k1ei3dbi) | 对照 小红书 (k1e0ero8) |
|---|---|---|
| 每次 `page.cards` 上报卡数 | **恒 1 张**（`上报 1 张`×3） | 10–11 张 |
| `scroll settle degraded`（扫卡未稳定，卡为真抽） | **3 次** | 0 |
| `[fb-inline] ✓ 就地读全文` | **1 次**（越南语群帖 👍0、正文 1408 字） | 大量 note.open |
| 点赞执行器 `[fb-like]` 调用 | **0 次** | — |
| `like` 计数 / `view` | like=0 / view=1 | 正常 |

复现 grep：
```bash
LOG=~/Library/Application\ Support/aidcp-edge/logs/edge.log
grep -aE "ads-k1ei3dbi" "$LOG" | grep -aoE "上报 [0-9]+ 张" | sort | uniq -c   # → 3 上报 1 张
grep -aE "ads-k1ei3dbi" "$LOG" | grep -acE "scroll settle degraded"            # → 3
grep -aE "ads-k1ei3dbi" "$LOG" | grep -aiE "fb-like|移除赞|reaction"           # → 0（只有 dailyUsage 里 like:0）
```

### 云端侧（dev journal）
```bash
# 注意：macOS 无 timeout 命令；用 ssh 自带超时选项，勿用 `timeout N ssh ...`
ssh -i ~/codes/isales-4.pem -o StrictHostKeyChecking=no -o ConnectTimeout=12 -o ServerAliveInterval=5 root@121.89.85.150 \
  "journalctl -u aidcp-cloud.service --since '15 min ago' --no-pager | grep 61591753702668 | tail -60"
```
结果：15+ 分钟**每一条命令都是 `sendCommand ... action=scroll sent=1`**（中间只夹 `content_evaluator`/`search_evaluator` 的 `[llm] ok=true`、一次 `action=refresh`），**零 `note.open`、零 `like`**。即 memory `note-open-miss-livelock` 的「只刷不点」活锁在 FB 上真机复现。

## 3. 根因定位（已到代码行）

- `settleCards`（`aidcp-edge/src/facebook/feed-reader.ts:348-376`）：稳定判据＝「连续两轮 `scanCards` 的 noteId 集合完全相等 ∧ 无 loading 信号 ∧ ≥minCards(默认1) 真卡」才返回 `degraded:false`；否则耗尽 wall-clock 后，`lastCards.length>=1` 就返回 `{cards:lastCards, degraded:true}`（`:373`，即日志里的「卡为真抽」）。
- `scanCards`（`:289`）+ `FEED_SCAN_JS`（`:151`）：scope=`div[role="feed"]`，卡=`[role="article"]`；**只收 `hydrated===true`（有 author link `h2/h3/h4 a` 类）∧ 有 permalink 的卡**（`:300-304`，无 permalink / 未水合即跳过，诚实不臆造）。
- **机理**：FB 此 feed 每轮 `scanCards` 只提取到 **1 张合格卡、且轮与轮之间还在变** → 永远达不到「连续两轮相等」→ 每次 degraded 1 张 → 云端每轮只有 1 张低价值卡可评 → 判定 scroll → 活锁，点赞执行器从不被触发。

**未定谳的关键问题**：是「该账号 feed 真的只有 ~1 张合格卡」（群组页 / 越南语 / 冷号、feed 真稀疏），还是「`scanCards` 的 `[role="article"]`+hydrated+permalink 组合在此 feed 布局上漏掉了大多数顶层卡」（选择器 bug）？**只有连实时 DOM 比对才能区分。**

## 4. 下一步（接手从这里开始）——只读 CDP DOM 取证

**目的**：对正在跑的 `ads-k1ei3dbi` 浏览器（**当前 debug 端口 50395**，会变，取值见下）做一次**只读** `Runtime.evaluate`，数：
1. `document.querySelectorAll('div[role="feed"] [role="article"]').length` — 页面上顶层 article 总数；
2. 其中有 `h2 a,h3 a,h4 a`（hydrated）的数量；
3. 其中能提取到 permalink（`a[href]` 命 `/posts/`、`/groups/xxx/permalink|multi_permalinks`、`/story.php` 等）的数量；
4. 对照 `scanCards` 会收几张。

**若「页面有 N≥5 张 article 但 scanCards 只收 1 张」→ 选择器/permalink 提取漏配（scanCards bug）；若「页面本身就 ~1 张 article」→ feed 环境稀疏（换热号 / 换 home feed 再验）。**

取端口 + page target：
```bash
curl -s "http://local.adspower.net:50325/api/v1/browser/active?user_id=k1ei3dbi"   # data.debug_port=<PORT>, data.ws.puppeteer
curl -s "http://127.0.0.1:<PORT>/json" | python3 -m json.tool | grep -iE 'facebook|webSocketDebuggerUrl|url'   # 找 facebook.com 那个 page target
```
然后用 `aidcp-edge/node_modules` 里的 `ws` 写个 ~40 行一次性 node 脚本连 page 的 `webSocketDebuggerUrl` 发 `Runtime.evaluate`（**纯读、不点不导航**，多 CDP 客户端并存安全）。选择器口径抄 `FEED_SCAN_JS`（feed-reader.ts:151）。取证脚本建议写在 scratchpad。

> 注意：**别再独立起核心/新浏览器**（会与 GUI 抢分身，见 §1 发现 2）。只读 attach 到 GUI 已开的浏览器不启新进程、不撞车。若非要跑受控独立会话，得先停 GUI（扰动全车队）或把 FB 号临时移出花名册。

取证定谳后：
- 若 scanCards 漏配 → 开 **edge change** 修 `scanCards`/`settleCards` 鲁棒性（放宽 permalink 提取 / 兼容此 feed 布局 / 或放宽稳定判据允许「稳定的 1 张也算」但要防误报）。交叉 memory `fb-feed-never-scrolls-down`（簇 72，settle 判稳 fix 已 land 但此 feed 未达成稳定多卡）。
- 若环境稀疏 → 换热度更高的 FB 号 / 确认落在 home feed（非群组页）再复验，同时评估「degraded 1 张时也该让云端能互动」的产品决策。

## 5. 被推后的事（先解 82.1 再谈）

- **shadow 档 toggle**（要做纯影子见证 82.3 才需要）：给 `facebookBrowseModeFor`（fleet.cjs:85）加「dev-FB 显式降档 shadow/off」——读 `process.env.AIDCP_FB_BROWSE_AUTO` 作 `requested`，dev-FB 时 honor `shadow`/`off`、否则默认 `on`；**非 dev-FB 仍在读 requested 前就 return `off`（保 anti-leak）**；main.cjs:2335 传 `requested: process.env.AIDCP_FB_BROWSE_AUTO`。测试加在 `test/electron/fleet.test.ts`（现有 `facebookBrowseModeFor` 用例在 :47）。**但 feed 都出不来多卡，影子见证无从谈起，故此项排在 82.1 之后。**
- 82.2 / 82.3 / 82.4 / 82.6 全部被 82.1 阻塞，未验。

## 6. 环境 / 命令速查（durable）

- **AdsPower 本地 API**：`http://local.adspower.net:50325`。列分身 `/api/v1/user/list?page_size=100`（`remark` 是 JSON、`plat` 字段辨平台，memory `adspower-env-platform-label`）；占用态 `/api/v1/browser/active?user_id=<id>`（Active 时带 debug_port + ws）。
- **FB 测试号**：`k1ei3dbi`=Tianxing Bai（本次跑的，已登录 FB id 61591753702668）、`k1ej3o8f`=Dennis Scott（Inactive、在花名册）。**小红书对照号** `k1e0ero8`=工程师大白（闭环正常，用它证明「非通用回归」）。
- **GUI 花名册**（`~/Library/Application Support/aidcp-edge/settings.json`）：8 环境＝6 小红书 + 2 FB（两 FB 号都在册）。GUI 主进程 `npm run electron:dev`（pid 每次不同），核心子进程从 `dist/main.js` 起（**已今日新构建、含 shadow 逻辑**，改 `src/facebook/*.ts` 要 `npm run build:dist` 才进 dist；改 `src/electron/*.cjs` 直接生效不用 build）。
- **dev 云端**：`ws://121.89.85.150:8787`（TCP 可达）；journal `journalctl -u aidcp-cloud.service`（key `~/codes/isales-4.pem`，**绝不碰同机 isales**）。
- **本次独立跑命令（仅存档，别再跑——会撞 GUI）**：`AIDCP_FB_BROWSE_AUTO=shadow AIDCP_BROWSER_PROVIDER=adspower AIDCP_ADS_USER_ID=<id> AIDCP_PLATFORM=facebook AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm start`（from `../aidcp-edge`）。

## 7. 收尾状态（干净）

- 控制仓 `main` == `origin/main`；本次结论提交 `4e5c4e2`（backlog 簇 82「⚠ 首跑真机结论」块）**已在 origin/main、安全**。HEAD 现为并发 session 的 `c6a2285`（叠在我上面，正常）。
- **canonical `aidcp-edge` 干净 on `master`**（本次全程未改 edge 代码，只读日志/源码）。未建任何 worktree（`aidcp-edge.wt/*` 是其他并发 session 的）。
- 我的独立影子核心（pid 98109）**已自行退出**，无残留进程。GUI 车队仍在用户自己手上跑（未动）。
- **未落 change**：82.1 扫卡缺陷的 edge fix、shadow toggle——都留给下一 session。
