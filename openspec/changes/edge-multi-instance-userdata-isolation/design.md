## Context

edge 监督者是 Electron 主进程（`aidcp-edge/src/electron/main.cjs`），一台机上托管 N 个 AdsPower 环境子进程（核心），全部继承该监督者的单一 `AIDCP_CLOUD_URL`。当前设计意图是「一台机一个监督者」，由 `requestSingleInstanceLock()`（main.cjs:2284）强制：拿不到锁即弹「已在运行」并 `app.quit()`（main.cjs:2294）。

对抗性代码核查（15 agent workflow）确认的现状约束：

- 单实例锁**按 userData 目录**划分（bare call，无 additionalData）；`AIDCP_CLOUD_URL` 不参与 userData / 锁的推导，故 dev / ol 选择在外壳层零隔离，第二个 GUI 直接被拦。
- 全部 userData 派生路径均为**懒调用**（在函数体内，跑在 `whenReady` 之后）：日志 `main.cjs:65`、设置 `:116`、界面状态 `:468`、运行时落地 `:1420`、内核 `:1464`。模块加载期在顶层执行的、会碰 userData 的唯一动作是 `:2284` 的锁。
- 代码里**无任何** `app.setPath('userData')` / `app.setName()` / argv 解析 / `--user-data-dir` 接线；userData 恒为默认（按 app 名派生）。
- AdsPower 本机守护进程（默认端口 50325）与分身库是**机器全局**（`~/.adspowerCli`），两个监督者天然共享；第二个探测到已在跑的守护进程会**复用而非重起**。
- 边缘身份 `ads-<分身id>`（`src/client/edge-id.ts:44`）与图片上传临时目录（`src/flows/image-uploader.ts`，按 edgeId 前缀）都按分身划分。

## Goals / Non-Goals

**Goals:**
- 同机可并行两个监督者（GUI）实例，一个连 dev、一个连 ol，各自独立的锁 / 设置 / 名册 / 界面状态 / 日志 / 运行时落地。
- 未设新开关时**零行为变更**（现有单实例 dev GUI 完全不受影响）。
- 改动面最小：单文件、顶部一处，不碰锁逻辑、协议、云端、风控。

**Non-Goals:**
- **不做跨实例分身占用租约**。两实例必须使用**不重叠**的 AdsPower 分身，靠运营纪律保证；因分身 / edgeId / 图片临时目录都按分身划分，分身不重叠时它们天然全分开，无需新增锁。
- **不改单实例锁逻辑**。不同 userData 天然是两把独立锁，锁代码保持原样。
- **不解决同分身双驱动**。一个分身 = 一个浏览器窗口 = 一个 CDP 端点；两套决策循环无法同时驱动同一浏览器，这是浏览器 / CDP 物理约束，非软件可解。
- 不新增云端选择逻辑（沿用既有 `AIDCP_CLOUD_URL`）。
- 不做 userData 之外的机器全局资源隔离（50325 守护进程 / 分身库本就该共享）。

## Decisions

### D1：用环境变量 `AIDCP_USER_DATA_DIR` + `app.setPath('userData', …)` 覆盖，而非 `--user-data-dir` / 多包变体

- **选择**：监督者启动顶部读 `process.env.AIDCP_USER_DATA_DIR`，非空则 `app.setPath('userData', <该目录>)`。
- **理由**：显式、可单测、不依赖平台参数解析行为；落点在 require 之后、锁与任何 userData 读取之前即满足全部顺序约束（因所有 userData 读取都是懒调用）。
- **备选**：
  - `electron . --user-data-dir=<path>`（Chromium 原生开关）——零代码，但本仓未接线 / 未测，行为纯靠平台；保留为「先验可行性」的手段，不作为固化方案。
  - 出第二个包变体（不同 appId / productName → 各自 userData）——需要额外构建产线，重，非必需。

### D2：落点在 main.cjs 顶部（require 之后、`requestSingleInstanceLock()` 之前）

- **理由**：`setPath('userData')` 必须早于锁（锁文件落在 userData）与任何派生路径读取。核查确认这些读取全为懒调用，故顶部即安全。放在 require 块之后、模块其余顶层语句之前，远离并发方正在改的运行时逻辑（~1400-1550），把热点文件冲突面压到最小。

### D3：未设变量 = 严格旧行为

- **理由**：以 `if (process.env.AIDCP_USER_DATA_DIR)` 守卫，缺省不调用 `setPath`，路径解析与今日逐字一致，保证对现役单实例 GUI 零回归。

### D4：并存约束写进 spec（运营前置，非代码强制）

- 两实例分身不重叠；先起一个、待 50325 守护进程稳定后再起第二个（避免冷启动抢杀守护进程）；保持默认 AdsPower 模式（self 模式会撞固定 9222）。这些是文档化的运营前置，spec 以「说明性要求」记录，不落代码闸（YAGNI；真需要强制时再引入租约，见 Non-Goals）。

## Risks / Trade-offs

- [同分身被两实例误配置 → 两套操纵系上同一浏览器，且因连不同云不触发互踢、错误不外显] → spec 明文要求分身不重叠；运营纪律 + 真机验收核对；后续若需硬保障再评估跨进程分身租约（本 change 不含）。
- [两实例同时冷启动 → CLI `ads start` 互相 SIGKILL 守护进程] → spec 要求错峰启动（先起一个、稳定后再起第二个），第二个复用已在跑的守护进程。
- [每实例在各自 userData 各落一份内置运行时 → 磁盘开销（~数百 MB/实例）] → 记为已知开销；守护进程 / 内核 / 分身库仍机器全局共享；后续可将多实例运行时指向同一目录优化，非本 change 范围。
- [热点文件 main.cjs 与并发 change（self-contained-ads 等）同期改动] → 落点置于文件顶部 require 区、与运行时逻辑物理隔开；经独立 worktree 开发、集成前 rebase 到最新 master 再 ff；若并发方整文件重写，需在集成时逐位保留本段（集成纪律）。

## Migration Plan

- 纯增量：合入后默认不生效（需显式设 `AIDCP_USER_DATA_DIR`）。
- 回滚：移除顶部那段守卫即恢复；或运行时不设该变量即等同旧行为。
- edge-only，不涉及 ECS 部署；生效需本机重建 / 重跑客户端。
