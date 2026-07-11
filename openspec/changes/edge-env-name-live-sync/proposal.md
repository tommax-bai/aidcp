# Proposal: edge-env-name-live-sync

## Why

客户端（aidcp-edge Electron 壳层）左侧环境列表（fleet rail）的展示名，与「添加环境」面板里**同一个环境**的名字对不上。根因经端到端追踪 + 三路对抗验证确认：

1. **两套名字来源不同，且只有一套实时更新**：
   - 「添加环境」面板每次刷新都**实时**从 AdsPower `user/list` 拉回当前环境名（`ads-local-api.cjs:292`，`it.name || it.username`）。
   - 左侧列表的名字取自本机**运行花名册**的 `name`，经主进程 `syncEnvHandles → fleetSnapshot / status.envName` 投影到渲染层（`renderer.js:1180` railDisplayName）。该名字**只在「加入」那一刻写一次**，此后永不与实时名对齐。
2. **有三个入口会把花名册名字写空**：
   - **创建环境**（最常见、必现）：创建其实已给环境起了真名（`ads-create-flow.cjs:101`，`name || templateKey`），但创建返回体（`ads-create-flow.cjs:110-117` / `main.cjs:2223-2230`）**漏带 `name`**，渲染层拿不到，于是自动选中时以空名入册（`renderer.js:2085`，`selectProfile(r.userId, null, '', …)`）。
   - 手动「加入这个分身 ID」按钮（`renderer.js:1642`，`name:''`）。
   - 手工敲分身 id 加入（`renderer.js:1633/1499`，显式存空名）。
3. 空名时左侧列表回落显示「环境 …末4位」（登录后回落平台账号昵称），与面板显示的真实环境名不一致。

（次要：`self`「本机 Chrome」是写死常量、无对应 AdsPower 环境，本就不在面板列表里——非「不一致」，不在本 change 修复面。）

## What Changes

两段式修复（aidcp-edge，纯客户端；不改协议、不动云端、不动浏览器生命周期层）：

- **源头修（创建路径）**：创建流的返回体带回已起好的环境名，一路透传到渲染层；创建后自动选中时把真名写进花名册，不再写空串。此条**即时生效、不依赖任何刷新**，正对最常见的「新建即不一致」。
- **兜底修（拉列表时回填）**：每次**成功且完整**地拉到 AdsPower 环境列表时，用实时名回填/更新花名册里对应成员的 `name`（仅回填实时名非空者、仅覆盖列表中在场的成员，与既有剔孤儿同一套安全闸；名字为纯展示字段，无「人工标注优先」问题），落盘触发左栏重刷。此条兜底手动加入 / 手填 id / AdsPower 端改名三种情况。

红线沿用：拉取失败 / 截断 / 空列表时绝不回填（不因缺数据把在用环境名误清 / 误改），沿用 `pruneOrphanRoster` 的守卫（`r.ok && !r.truncated && live.size>0`）。

## Capabilities

### Modified Capabilities

- `adspower-desktop-env-picker`：新增需求——**环境展示名保真与实时同步**。写入运行花名册（并投影到左侧列表）的环境名 SHALL 忠于该环境的 AdsPower `user/list` 名字；创建路径 SHALL 把已起名字带回并写入花名册、MUST NOT 写空名；拉取环境列表成功且完整时 SHALL 用实时名回填花名册成员名，安全闸沿用剔孤儿守卫。

## Impact

- aidcp-edge 渲染层（`src/electron/renderer/renderer.js`）：创建成功后带名选中；`refreshEnvs` 拉列表成功且完整时回填花名册名。
- aidcp-edge 主进程（`src/electron/main.cjs`）：`ads:createEnv` 返回体带回 `name`（单建与 FB 单账号导入两路）。
- aidcp-edge 创建流（`src/electron/ads-create-flow.cjs`）：`createEnvironment` 返回体带回 `name`。
- 回归测试：`renderer-smoke.test.ts` 新增用例（创建带名入册 + 拉列表回填空名）；`ads-create-flow.test.ts` 断言返回体含 name。
- 无 openspec 协议改动、无云端改动、无 ECS 部署（edge-only；需运营机 pull master + 重建安装包后生效）。
