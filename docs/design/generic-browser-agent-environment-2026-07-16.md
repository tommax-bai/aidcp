<!--
设计草案，2026-07-16 落档。状态：讨论中 / 未开 openspec change / 未写代码。
来源：对话 + 两轮代码坐实（平台/环境生命周期）+ OpenCLI 一手源核实。
关联研究档：docs/research/opencli-generic-platform-feasibility-2026-07-16.md
（注意：研究档结论是「养号语境」，本工具是「非养号语境」，口径差见 §8。）
-->

# 通用浏览器 Agent 环境 — 设计草案（待讨论，未实装）

## 一句话

给 edge 桌面客户端新增一种「通用环境」类型：用户登录**自己的账号**（知乎 / B 站…），用**自然语言**下指令，一个内嵌 **OpenCLI** 的 **LLM Agent 侧车**驱动浏览器做**只读搜索 / 收集**；能做就做、不能就如实回不支持；与养号业务**物理隔离**。

---

## 1. 意图与边界

- **要做什么**：一个通用工具 / 通用环境，用 LLM Agent 完成用户的网站操作指令（当前聚焦搜索、信息收集）。best-effort：支持则做、不支持则如实说。
- **与养号的本质区别**：操作的是**用户自有真账号**、做**正当搜集**，不是养一批假号躲风控。因此养号那套（AdsPower 指纹隔离、云端风控、协议 v2 边云通信）**都不需要**，反而必须**绕开**。
- **核心原则**：独立侧车，物理隔离养号三样。

---

## 2. 关键决策（已达成）

| 决策点 | 结论 | 理由 |
|---|---|---|
| 引擎 | **用 OpenCLI**（jackwener/opencli，Apache-2.0） | 图它 **100+ 现成站即拿即用**（自建拿不到这个广度）；此场景正是它的设计原点（登录态 + 自然语言 + 能则做） |
| 落点 | **客户端新增一种「环境类型」** | 复用现有环境栏 + 每环境一套运行时的模型，最省 |
| 类型轴 | 走 **`kind` 轴**（加 `kind:'generic'`），**不加 `platform`** | `platform` 有全覆盖 typecheck 热点、会污染养号 registry；`kind` 只有零散判断、无穷举 |
| 隔离 | 独立侧车运行时，不继承养号 core | 见 §5 红线 |

**一个要记住的现实**：OpenCLI 对签名硬化的站会退化成人工维护的 DOM 适配器、偶尔失效——与「能做就做、不能就不支持」的定位合拍（失效就显示不支持），但不是「100+ 站永久零维护」。

---

## 3. 架构

- 新类型 = `kind:'generic'`（现有 `adspower` / `self` 之外）。
- 选中一个 generic 环境 → 起一个**新的独立侧车进程**（不是养号 core `dist/main.js`）：
  1. 驱动**用户自己登录的普通 Chrome**（`SelfChromeProvider` / 带 `--remote-debugging-port` 起、用户登录，或接管已开的）；显式 `AIDCP_STEALTH=off`。
  2. 内嵌 **OpenCLI**（CDP 模式接那个 Chrome，`OPENCLI_CDP_ENDPOINT`，**免装浏览器扩展**）当浏览器操作引擎。
  3. 一个 **LLM Agent 循环**：NL 指令 → 选 OpenCLI 站点 adapter（支持则做）/ 通用原语 / 回「不支持」→ 如实回报。
  4. **绝不**：连协议 v2 :8787、写风控、走 AdsPower。

---

## 4. 落地改点（按环境生命周期，全在 `aidcp-edge`）

> A–D 打通「一个 non-adspower 环境能建、能显示、能选中」；E 是纯新增主体。

**A. 建模（先补缺口，否则 generic 与 adspower 无法混排）**
- roster 成员（落盘 `userData/settings.json`）加 `kind` 字段：`electron/fleet.cjs:24-40` + 渲染层镜像 `electron/renderer/renderer.js:323-340`。
- `syncEnvHandles` 改读成员 `kind`（现在一律派生 `adspower`）：`electron/main.cjs:1029-1036`。
- `makeEnvHandle` 允许新 kind、generic status 用中性默认：`electron/main.cjs:958-1003`。
- 渲染层接收快照里的 `kind`（现被丢弃）：`renderer.js:2018-2029`（快照已带 kind：`main.cjs:1101-1108`）。

**B. 新建（绕开整条 AdsPower 建号链）**
- 新建面板加「环境类型」选择：`electron/renderer/index.html:404-446`。
- 新 IPC `generic:createEnv`：自造 id（`gen-<uuid>`）直接入册，不经 `ads:createEnv`（`main.cjs:4193-4287`）与 `ads-create-*.cjs`；入册复用 `selectProfile`/`persistRoster`（`renderer.js:2856-2903`）→ `settings:save`（`main.cjs:3952-3994`）。preload 暴露新方法。

**C. 列表渲染 + 选中切工作区（有先例）**
- rail / 工作区透传 `kind`：`syncInteractionWorkspace`（`renderer.js:205-214`）。
- 参照视频号先例（`isWechat = platform==='wechat_channels'`：`electron/renderer/interaction-workspace.js:739-765`）加第三分支 `kind==='generic'` → 新「通用 Agent 工作区」面板（DOM 参照 `index.html:325`）。

**D. 选中 → 起运行时（核心改点）**
- `spawnEdgeChild` 已有 kind 分叉（`main.cjs:2533`）。加 `else if kind==='generic'`：`edgeEntry` 按 kind 选（generic → 新侧车入口，非写死的 `dist/main.js`，`main.cjs:2528`）；spawnEnv 不含养号变量（跳过 `buildEnvSpawnEnv` `fleet.cjs:127-128` / `buildAdsProviderEnv` `main.cjs:825-834` / 身份闸 `:2534-2561` / 云端注入 `:2571-2576`）。
- 消化散落的 `handle.kind==='adspower'` 判断点：`main.cjs:652,861,967,1033,1073,2728,2822,2846,2883,3176,3593,3720`。

**E. 新侧车运行时（纯新增，本工程主体）**
- 新入口（如 `src/generic-agent/main.ts`），骨架参照 `src/wechat-channels/browser-sidecar.ts`（独立 CDP、不写风控、不走协议——但连云那段**不要抄**）。
- 组成：① Chrome 起停 + 用户登录门（参照 `src/main.ts:266-338` 扫码等待）；② OpenCLI 子进程封装（CDP 模式）；③ LLM Agent 循环（NL→动作→观测→回报）。
- **LLM 调用**：复用与云端同一模型出口形态（`aidcp-cloud/src/llm/qwen.ts`，DashScope OpenAI 兼容），侧车内薄客户端直连、显式传 model（不进 role-catalog、零养号回归）。
- **打包红线**：打包 Electron 内 spawn 时 cwd 须复刻 asar 规则 `appRoot.endsWith('.asar')?path.dirname(appRoot):appRoot`（`electron/main.cjs:2528-2531`），否则 `ENOTDIR`。

---

## 5. 隔离红线（must NOT）

1. 不实例化 `EdgeClient` / 不连 `ws://…:8787`（协议 v2）。
2. 不发 `risk.canDo` / `risk.record` / 不经 `comm/handler`（风控单写）。
3. 不走 `AdsPowerProvider` / 不需要 `AIDCP_ADS_USER_ID`。
4. generic 环境不进 `platform` 枚举、不碰 `registry.ts` 全覆盖表。

---

## 6. v1 范围（YAGNI）

- 只读 / 收集（搜索 + 抽取），best-effort + 诚实门控（绝不假成功）。
- 首发 1–2 站（知乎 + B 站，用 OpenCLI 现成 adapter）。
- 暂不做：写操作、跨环境编排、定时、与养号数据打通。

---

## 7. 待讨论（开放问题，下次继续）

1. **写操作要不要开**：v1 定只读；若要「按指令发帖 / 互动」，风险与授权模型另议（仍是用户自有账号，但性质变重）。
2. **OpenCLI 的装包 / 分发**：它带守护进程 + CLI，桌面客户端如何随包分发 / 版本管理 / 更新？（联动已知的 OSS 分发受阻问题。）
3. **登录态持久化**：用户登录的普通 Chrome 用哪个 `--user-data-dir`？跨会话保持登录、与养号 profile 目录如何隔离。
4. **LLM 放侧车还是云端**：侧车直连模型（自包含、简单）vs 走云端 panel（统一计量 / 配模型）。
5. **adapter 破裂的维护责任**：签名硬化站失效后谁修、多快修，还是就长期「不支持」。
6. **安全边界**：用户自有 cookie 落在本机侧车，权限 / 清理 / 多用户隔离。
7. **console 是否也要入口**：目前定客户端;后台要不要只读查看这些通用任务。
8. **成本 / 计量**：这条 LLM 用量是否进现有用量台账。

---

## 8. 与研究档的口径差（重要，避免被误读）

`docs/research/opencli-generic-platform-feasibility-2026-07-16.md` 把「复用已登录真 Chrome」列为 **foot-gun**——那是**养号语境**（怕业务养号号被暴露进抓取）。**本工具语境不同**：用户操作的是**自己的账号**、正当搜集、**非养号**，所以「复用登录态」从 foot-gun **变成正需特性**。两者**架构隔离结论一致**（独立旁路、绕开养号三样），但用户 / 资产性质不同，勿用研究档的养号红线误伤本工具。

---

## 关联

- 研究档：`docs/research/opencli-generic-platform-feasibility-2026-07-16.md`
- 隔离先例：`aidcp-edge/src/wechat-channels/browser-sidecar.ts`
- 计划文件（本次对话）：`~/.claude/plans/gleaming-floating-backus.md`
