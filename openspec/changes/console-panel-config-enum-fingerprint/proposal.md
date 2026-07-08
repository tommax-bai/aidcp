## Why

`GET /api/version` 漂移哨兵（change `console-cloud-panel-hardening` #4/#5/#6）目前只覆盖风控 / 告警 / 厂商枚举 + PanelAccount 字段指纹，**未覆盖面板「角色 / 模型配置」那组枚举**（`llmKind` / `effectiveSource` / `personaSource` / `thinkingMode`）。这些枚举正是控制台用来索引 `{text,color}` 徽标映射的键——一旦云端新增成员而控制台镜像未同步，`MAP[新值].color` 读到 `undefined` 就整页 white-screen。

2026-07-08 已真实发生：云端为封面视觉角色引入 `llmKind:'vision'` / `effectiveSource:'vision'`（change `textcard-cover-form`），控制台角色页 `/roles` 全崩（"Unexpected Application Error!"）。该崩溃已由控制台侧兜底修复（`tagOf` 容错取值 + `enumTagSafety` 源码扫描闸，console `cd76716`）——未知值现在诚实回落成灰底原值标签、不再崩。

本 change 补上**探测**那一半：把这组配置枚举纳入既有 `/api/version` 指纹，使「云端领先、控制台镜像未跟上」在能连 dev 云端时被预部署侦测，而非只在页面上默默显示灰标签。设计评审（2026-07-08，7-agent + 对抗评审）已否决 codegen / 独立共享包（三仓 + 无 CI + 云端常未 clone + 控制台本地静态构建下属过度设计，且单靠它不防白屏——过期副本照样崩），定案「兜底（已上线）+ 指纹（本 change）」，与既有 protocol.ts「两份镜像 + 一处双方对拍的指纹」范式同源。

## What Changes

- **cloud**：`src/panel/version.ts` 为 `LlmKind` / `ModelEffectiveSource` / `PersonaSource` / `ThinkingModeApi` 各加一份**权威 runtime `as const` 数组**（就地 `_AssertNever` 双向守卫强制数组 ≡ 类型全集，照同文件 `PANEL_ACCOUNT_FIELDS` 既有范式），纳入 `buildVersionPayload().enums`；`PANEL_API_VERSION` 2→3。**只动 `version.ts`**——类型定义在 `role-catalog.ts` / `panel/types.ts` 原地不动，仅并列加数组 + 守卫，不碰 `protocol.ts` 等热点单写文件、零血面。
- **console**：`src/types/aidcp-enums.ts` 加 4 份镜像 `as const` 数组并派生同名类型；`src/types/api.ts` 改为从 aidcp-enums 复出这 4 个类型（消灭手抄的第二处定义，控制台侧收敛为单源），并给 `VersionPayload.enums` 补 4 字段；`aidcp-enums.test.ts` 扩快照 + live `/api/version` 对拍。

> 非 BREAKING：`/api/version` 加字段是向后兼容的加法（旧 console 忽略新字段、且未知值有 v1 兜底）；枚举成员集合不变（仅把既有全集显式化为 runtime 数组）。

## Capabilities

### Modified Capabilities
- `console-panel-api`：把既有「enum 漂移哨兵」要求扩到面板角色 / 模型配置枚举（`llmKind` / `effectiveSource` / `personaSource` / `thinkingMode`），使这组会扩张、且被控制台用作徽标映射键的枚举漂移也由 `/api/version` 哨兵检出（而非只靠控制台侧运行时兜底把崩溃降级为灰标签）。

## Impact

- **aidcp-cloud**：`src/panel/version.ts`（仅此一文件）。
- **aidcp-console**：`src/types/aidcp-enums.ts`、`src/types/api.ts`、`src/types/aidcp-enums.test.ts`。
- 部署：dev cloud（`PANEL_API_VERSION` bump，须重启）+ dev console。绝不碰同机 isales。
