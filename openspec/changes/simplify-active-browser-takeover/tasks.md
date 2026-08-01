## 1. Active Takeover and Proxy Preparation

- [x] 1.1 Add a race-safe Active-only startup path that bypasses Cloud authority, GOST, and preflight while refusing to fresh-start if Active disappears
- [x] 1.2 Remove expected/browser public-egress plumbing and make the AdsPower provider attach directly to every Active profile
- [x] 1.3 Reduce Facebook proxy preflight to bounded target reachability for Inactive fresh starts while preserving authority revision, cache, `no_proxy`, and double-hop behavior

## 2. Observation and UI

- [x] 2.1 Replace public-egress runtime observation with generation-scoped receive-traffic aggregation
- [x] 2.2 Remove browser/direct public-egress fields and verification conclusions from the Facebook proxy status UI
- [x] 2.3 Remove the obsolete Active-proxy takeover error classifier, terminal lifecycle branch, and associated status copy

## 3. Regression Coverage

- [x] 3.1 Update provider, preflight, Electron lifecycle, and startup-order tests for direct Active takeover and race-safe fresh-start protection
- [x] 3.2 Update traffic aggregation and renderer tests to prove no public-egress probing or display remains

## 4. Validation and Delivery

- [x] 4.1 Run focused Edge tests, full Edge tests, typecheck, and diff checks
- [x] 4.2 Run strict OpenSpec validation and record Edge commit, validation results, release boundary, and deviations

<!--
Implementation: aidcp-edge@0fda134, pushed to origin/master.
Validation: 94 focused tests passed; full Edge suite passed 2850 with 0 failures and 1 gated skip; typecheck, CJS syntax checks, diff checks, and strict OpenSpec validation passed.
Delivery: source only; no installer was built and no installed client was changed.
Deviation: an Active-takeover core refuses cold standby so a later Inactive relaunch cannot bypass the normal proxy preparation path.
-->

<!--
归档顺序约束（2026-08-01 归档前逐条对读 delta 时发现并处置）：

本 change 的 delta 与另外两条同批待归档 change 撞在同一批 requirement 上，且**三处的底稿都是当前主 spec**——
写它的那一轮看不到另外两条尚未归档的修改。后果分两类，处置不同：

① **有意取代，只需定归档顺序**：`edge-fleet-console` 的「Facebook 运行页顶栏区分代理配置与运行证据」与
   `facebook-proxy-preflight` 的「预检状态 SHALL 与浏览器出口证据分离」，与
   `invalidate-stale-proxy-runtime-evidence` 相撞。本 change 是 BREAKING、明写移除浏览器出口探测与展示，
   确属有意取代。**必须 `invalidate-stale-proxy-runtime-evidence` 先归档、本 change 后归档**；
   反过来会让主 spec 停在「要求分别展示浏览器出口与本机出口」的旧文本上，而那个界面已经不存在了。

② **不是取代，是底稿旧了**：`facebook-proxy-preflight` 的「启动与唤醒 SHALL 复用短时预检结果」与
   `refresh-proxy-preflight-on-manual-start` 相撞。本 change 的范围里**根本没有**「手动启动是否重检」这件事
   （见 proposal 的 What Changes），但它的 MODIFIED 全文按主 spec 写，于是会把那条 change 的
   「单环境显式点击启动 SHALL 作废旧结果并重检」整段连同 4 条 scenario 静默删掉。
   **已就地修复**：本 change 的该条 requirement 已改写为「以 `refresh-` 的版本为底稿 + 叠加本 change 的
   Active 接管改动」，两者语义不冲突（Active 走接管不做预检 / Inactive 显式点击重检，分属不同分支）。
   归档顺序同样是 **`refresh-proxy-preflight-on-manual-start` 先、本 change 后**。

**这三处 `openspec validate --strict` 一条都抓不到**（它只校验 delta 内部结构，不做跨 change 冲突检测）。
判据是「同一能力被多条待归档 change 同时改」——攒批归档前应机械扫一次。
-->
