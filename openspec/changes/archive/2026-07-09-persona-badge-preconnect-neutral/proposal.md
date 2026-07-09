## Why

建号人设向导修复（change `persona-wizard-onboarding-fixes`）上线后真机反馈：在设置页选 / 切换环境时，**已绑人设的账号仍先显示「未设置」，启动连云后才翻「已设置」**。

根因是已知边界（上一 change 设计里记为残留限制、按 YAGNI 未补）：「该账号是否已绑人设」是**云端权威、按真实账号 id 存**的状态；而边缘在**启动 + 扫码登录 + 连云之前**，既不知道选中环境（AdsPower profile）对应哪个真实账号、也没连云拿不到 `personaBound` 信号。上一 change 在未连云时让徽标显示本地默认「未设置」——这是**对未知状态的错误断言**，误导用户以为已配好的号没人设。

本变更做**诚实中立态**（Option A）：未连云时不谎称「未设置」，改显示中立「待启动」；连云后再给权威判定。纯 edge 渲染层，不动云端、不动协议。

## What Changes

- **未连云时徽标显示中立态**：`updatePersonaGate` 在「已登录 + 已连云」（`personaReady`）之前，徽标显示中立「待启动」而非「未设置」（守「宁缺毋假」——不知道就不断言）；hint 明确「连上云端后会显示该账号是否已设置人设」。连云后：`personaBound=true`（或本会话确认）→「已设置」跳过向导；权威未绑 →「未设置」+ 启用向导。
- **换会话清除 stale 已绑态**：`personaBound` 云端只在为真时下发（从不发 false），故 stale-true 会跨环境泄漏。边缘 MUST 在换会话清零：core 重启时清 `ui.snapshot` 派生的 `status.personaBound`（`main.cjs` startEdge）、断连时清本会话确认标记 `personaLocallyBound`（renderer）。避免切到另一个（可能未绑的）环境后旧账号「已设置」误染。
- **已绑判定仅在已连云时权威**：renderer 只在 `personaReady` 时把 `personaBound`/`personaLocallyBound` 当权威已绑，之前一律中立。

## Capabilities

### New Capabilities
<!-- 无。 -->

### Modified Capabilities
- `persona-keyword-generation`: 修改「云端下发已绑人设信号，边缘按 onboarding 三态渲染」要求——未连云时徽标中立（不谎称未设置）+ 换会话清 stale 已绑态 + 已绑判定仅在已连云时权威。

## Impact

- **aidcp-edge**：`src/electron/renderer/renderer.js`（`updatePersonaGate`：未连云中立态 + 断连清 `personaLocallyBound` + 已绑仅在 `personaReady` 权威 + hint 中立文案）、`src/electron/main.cjs`（`startEdge` 清 `status.personaBound`，换会话不泄漏）。
- **不涉及**：cloud、协议（`personaBound` 字段已在，不改）、后台。纯 edge 渲染层 + 壳状态清零。edge 是客户端，需本地重建安装包 + 真人扫码验（真机项）。
