## Why

客户端启动时若选中的分身已被**同一 AdsPower 账号在别处**（另一台机 / 另一并行实例 / AdsPower 桌面端窗口）打开，AdsPower 本地 API 对 `browser/start` 返回 `code=-1 msg=[<profile>] is being used by [<account>] and is not allowed to open`。核心据此诚实抛错并以退出码 1 退出（正确：绝不回落 self）。

问题在外壳看护层：它把这个退出**当成普通崩溃**喂进「有界重起」。默认 1 次初始 + 5 次重起、退避 `1+2+4+8+16s`，共 6 次重发 `browser/start`、约 45–60s，全部注定被同样拒绝——因为「被别处占用」这类冲突**重起一万次也不会自愈**。期间操作者看到状态在「启动失败 ↔ 稍后重试」间来回（其感知的「浏览器关闭又被拉起」），最终落到通用「本机引擎已停止」+ 生英文原文详情，既慢又不说人话。

经读码 + 多 agent 对抗验证（锚点在 edge master `1e7e6d9` 仍在）：整条启动 / 退出 / 重起路径**没有**把该冲突归类为「不可重起终局」，唯一的原因特判是缺内核（`SunBrowser <N> is not ready`）。另外，现状代码在该失败路径上天然不碰浏览器（拒绝发生在拿到浏览器句柄之前，无任何 teardown 触达该分身），但缺一条**显式不变量**守住「绝不去关那个别处正被使用的浏览器」，值得在本变更里坐实。

## What Changes

- 边缘看护层 SHALL 把「AdsPower 同账号并发占用拒启（`browser/start` 被拒、拒因指明该分身正被使用 / 不允许并发打开）」识别为**不可重起终局**：MUST 立即诚实停止该环境、MUST NOT 消耗有界重起预算做无谓退避重试。该识别 SHALL 独立于普通崩溃与缺内核可恢复态。
- 该终局处置 MUST NOT 触发任何对该分身浏览器的停止 / 强制终止 / 调试附着——绝不干扰同账号在别处的活跃会话（红线：不动别人的浏览器）。
- 伴随窗 SHALL 把该终局以**可识别的「环境被其它端占用」原因**呈现（含占用账号，若可从拒启信息解析），而非通用「引擎已停止」+ 无谓「稍后自动重启」倒计时；该原因 MUST 源自真实拒启信息、MUST NOT 编造。
- 提供 env 护栏（默认开，`AIDCP_EDGE_ENV_IN_USE_TERMINAL`）便于一键回退到旧的「按崩溃重起」行为，用于识别误伤时的应急。
- 补一个纯函数单测：识别真实拒启 msg 判终局并解析账号；对普通崩溃 / 缺内核行判否（防误判）。

## Capabilities

### New Capabilities
<!-- 无新增能力：本变更强化两个既有能力的现有需求。 -->

### Modified Capabilities
- `edge-node-supervised-recycle`: 在「有界重起 + 连续失败诚实放弃」之上收紧——**不可重起终局（同账号并发占用拒启）MUST 即刻诚实停止、不进重起预算**，且该处置 MUST NOT 关闭 / 强杀 / 附着别处正在用的同分身浏览器。
- `edge-companion-ui`: 收紧「异常退出详情持久可见」——同账号并发占用这一具体终局 MUST 以可识别的「环境被其它端占用」原因呈现（而非仅生技术行 / 通用文案），原因须源自真实拒启信息。

## Impact

- 代码（edge，`../aidcp-edge`，edge-only，不动云端 / 协议 / 风控 / 发布）：
  - `src/electron/fleet.cjs`（新增纯函数 `classifyAdsInUse(line)`：识别拒启签名 + 解析占用账号；与 `decideRespawn` 同一纯逻辑模块，`node:test` 单测）
  - `src/electron/main.cjs`（`handleEdgeLogLine` 置 `envInUseThisRun` 标志；`child.on('close')` 退出处理据标志覆盖重起决策为 `stop`、换友好 `edgeFailure.summary`、补一次性通知、复位标志；`startEdge` spawn 处清零标志；env 护栏）
- 测试：`test/electron/fleet.test.ts` 补 `classifyAdsInUse` 用例；改动后按回归纪律 `npm run test:acceptance` → `npm test` → `npm run typecheck`。
- 无协议 v2 改动、无风控 / 发布链 / ECS 改动（edge-only；真机生效需运营机 pull edge master + 安装包重建）。
- 真机验收（登记 backlog）：在运营机制造「分身已在别处打开」再启动，确认不再空转 6 次、直接停 + 中文「环境被其它端占用」提示、且别处浏览器不被关。
