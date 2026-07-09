## Context

发布卡「上次发布」历史态的现状数据流（均在 `aidcp-edge/src/electron/main.cjs`）：

- 存储：主进程单例 `status.lastPublish` + `userData/ui-state.json`（`uiStateFile/loadUiState/saveUiState`，247-269 行），文件仅 `{ lastPublish: { title, at } }`，无归属键。
- 写入点仅两处（`handleEdgeLogLine` 内）：本地发布成功（964-965 行）与云端快照回填（968-975 行，要求非空 title 才覆盖）。落盘由 `updateStatus` 的 `if (full.lastPublish) saveUiState()`（446 行）触发——只写非空，无清空写入路径。
- 切环境的真实用户路径：设置抽屉选环境（`renderer.js selectProfile` 只改表单）→「保存」（`settings:save` 只持久化不打断核心，1059 行）→「按新设置重启」（`edge:restart` → `stopAndRestart` 888 行 → SIGTERM → exit 回调 `startFlow` → `startEdge`）。`startEdge` 重启补丁只清在途 `publish:null`、注释明言 lastPublish 不清（671-682 行）。
- 云端侧（不改，仅约束）：hello 快照按新账号查 `publish_log`，无记录则不带 lastPublish 字段甚至整包不发（`aidcp-cloud/src/comm/ui-snapshot.ts:86-87,108`）；边缘转换层缺字段不产行（`ui-event-lines.ts:156`）。
- 渲染层是纯投影：`lastPublish` 非空即 `mode='last'` 显示旧标题，为空回落 `mode='empty'`「还没有发布过内容」占位（`ui-logic.js:249-277`），无需改动。

约束：不动协议、不动云端；遵守「绝不静默假成功」红线的展示侧对应物——归属不明的内容宁可不显示，也不错挂在别的账号名下。

## Goals / Non-Goals

**Goals:**
- 切换到不同环境后，发布卡不得展示上一环境的「上次发布」；无记录时停留既有空态占位。
- 同环境的普通重启 / 恢复 / 重新登录，历史态行为逐位不变（重启不丢、云端快照到位后以云端为准）。
- 云端快照带回当前账号真实记录时照常覆盖（现有覆盖分支不动语义）。
- 归属判定逻辑可脱离 Electron 单测。

**Non-Goals:**
- 不做多账号历史缓存（按账号存多份 lastPublish）——云端 `publish_log` 才是权威，切回旧账号由 hello 快照回填，本地只需单槽。
- 不给云端加「显式空记录」信号（协议改动，另一条已被否的方案）。
- 不处理统计数字 / 今日用量在快照到达前的短暂陈旧窗口（已证实存在，但属另一问题，影响面小且会被快照纠正）。
- 不实装多环境并行（`edge-multi-environment-fleet` 范畴），只保证键设计与其兼容。

## Decisions

1. **归属键 `envKey` = `self` | `ads:<adsProfileId>`，由设置推导。**
   与核心 edgeId 派生规则同源（adspower 路径 edgeId=`ads-<id>`），多环境 change 实装时可直接复用。不用小红书账号 id 做键：壳层在核心确立身份前就要做采纳判定（应用启动时），彼时只有环境 id 可用；环境↔账号在 adspower 模型下一一对应，够用。

2. **新增纯逻辑模块 `src/electron/ui-state.cjs`，main.cjs 只做接线。**
   仓内既有惯例（`ads-runtime.cjs` / `ui-events.cjs` 等从 main.cjs 拆出可单测模块）。导出：`envKeyFromSettings(settings)`、`adoptStoredLastPublish(parsed, currentEnvKey)`（返回采纳后的 lastPublish 或 null）、`serializeUiState(envKey, lastPublish)`。判定规则集中一处，load / restart / save 三个接线点共用。

3. **清空时机 = 核心（重）启动时刻（`startEdge`），不在 `settings:save` 时。**
   保存设置不打断在跑核心（1061 行注释是既有产品决策）；保存后旧核心仍在跑旧账号，此刻清卡反而把「正在跑的账号」的历史清掉了。`startEdge` 是环境真正生效的唯一入口（启动 / 保存后重启 / 恢复 / 重新登录全走它），在此比较「内存中 lastPublish 的归属键 vs 本次 spawn 的环境键」，异键则把 `lastPublish: null` 并入既有重启补丁（675 行那次 `updateStatus`），同键不动。

4. **归属键随「spawn 时刻」快照，不随 settings 实时取。**
   `startEdge` 时把 `envKeyFromSettings(settings)` 存进模块级 `runningEnvKey`；两处 `lastPublish` 写入点（发布成功 / 快照回填）一律记归属为 `runningEnvKey`。防「保存了新设置但未重启」窗口内，旧核心的发布事件被记到新环境名下。

5. **持久化文件带键：`{ envKey, lastPublish }`；加载时异键或缺键一律不采纳。**
   缺键 = 旧版文件，无法判归属 → 丢弃（升级后一次性回空态，核心启动后云端快照自愈）。备选「缺键按当前环境认领」被否：用户若在升级前已切过环境，正好把 bug 状态固化下来——与本次要修的问题自相矛盾。
   清空路径**不写盘**：文件里留着的是「旧环境的记录 + 旧环境的键」，数据本身是对的；下次加载靠键判定即可，且用户切回旧环境时（快照到达前）还能立即显示正确历史。`updateStatus` 的「只写非空」门保持不变。

6. **测试按仓内克制惯例：新模块少数关键用例，渲染层不加测。**
   `test/electron/ui-state.test.ts`：同键采纳 / 异键丢弃 / 缺键丢弃 / 序列化带键往返，约 4 例。空态渲染已有覆盖（`ui-logic.test.ts` / `companion-ui.test.ts`），不重复。切环境后卡片实际回空态属真机验收，登记 `docs/real-machine-acceptance-backlog.md`。

## Risks / Trade-offs

- [升级后一次性空窗] 旧版 `ui-state.json` 无键被丢弃，用户升级后、核心启动前发布卡显示空态 → 核心启动、云端 hello 快照带回真实记录即自愈；有发布史的账号只是「晚一步显示」，无发布史的账号本就该显示空态。
- [快照到达前的空窗] 切到**有**发布史的账号，卡片先空态、快照到位后回填 → 与「显示错误账号的内容」相比，短暂空态是正确的一侧；快照在 hello 后即推，窗口秒级。
- [快照丢失则停在空态] hello 快照推送失败无重试（云端既有行为）→ 停在空态占位而非错误内容，且下次发布成功 / 重连快照会纠正；不在本 change 加补偿。
- [与 `edge-multi-environment-fleet` 的 main.cjs 交叠] 该 change 未实装、0/30；本改动面小（三个接线点 + 新模块），且键设计与其同构，届时按环境分文件或分键扩展即可 → 冲突风险登记在 proposal，实装顺序由 fleet 层协调。

## Migration Plan

纯客户端改动，随下一次安装包 / `electron:dev` 生效；无数据迁移脚本——旧 `ui-state.json` 靠「缺键不采纳」自然淘汰，首次新写入即带键。回滚 = 回退代码，新文件多出的 `envKey` 字段被旧代码忽略（旧 `loadUiState` 只读 `lastPublish`），双向兼容。

## Open Questions

（无——方案已由用户拍板：无记录用默认占位内容。）
