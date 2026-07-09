## 1. aidcp-edge — 未连云中立态 + 换会话清 stale

<!-- edge e4f8bfa：renderer 未连云中立态「待启动」+ main.cjs startEdge 清 handle.status.personaBound；切环境泄漏由既有 resetPersonaDraft 处理；typecheck 干净、全量 788 绿。纯 edge、cloud/协议不动。 -->

- [x] 1.1 `renderer.js` `updatePersonaGate`：已绑判定仅在 `personaReady`（已登录+已连云）时权威；未连云 → 徽标中立「待启动」（不谎称「未设置」）；权威未绑 → 「未设置」+ 启用向导；「待确认」草稿态不被覆盖
- [x] 1.2 `renderer.js`：断连（`cloud !== 'connected'`）时清 `personaLocallyBound`（换会话待新权威信号重建）；hint 未连云文案改中立（「连上云端后会显示该账号是否已设置人设」）
- [x] 1.3 `main.cjs` `startEdge`：core 重启时清 `status.personaBound`（云端只在为真时下发，stale-true 会跨环境泄漏）
- [x] 1.4 edge 回归：`npm run typecheck` + `node --check` renderer/main.cjs；全量 `npm test`

## 2. 真机 backlog

- [x] 2.1 `docs/real-machine-acceptance-backlog.md` 登记：设置页选/切环境未启动时徽标显示「待启动」（非「未设置」）；切到另一环境不残留旧账号「已设置」；连云后据 personaBound 正确翻已设置/未设置
