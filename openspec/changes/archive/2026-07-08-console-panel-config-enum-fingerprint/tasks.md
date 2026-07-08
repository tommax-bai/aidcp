# Tasks — console-panel-config-enum-fingerprint

> 回写：完成 `[ ]`→`[x]` + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。
> 前置：控制台侧崩溃兜底（v1）已上线（console `cd76716`：`tagOf` 容错取值 + `enumTagSafety` 源码扫描闸）。本 change 是「探测」那一半。
> 热点单写者：不碰两份 `protocol.ts` / `command-bridge` / 风控状态机 / 角色注册（§7）；cloud 仅动 `version.ts`（类型定义原地不动，并列加 runtime 数组 + `_AssertNever`）。

## 1. aidcp-cloud — /api/version 指纹扩到配置枚举

- [x] 1.1 `src/panel/version.ts`：为 `LlmKind` / `ModelEffectiveSource` / `PersonaSource` / `ThinkingModeApi` 各加 runtime `as const` 数组 + `_AssertNever` 双向守卫（照 `PANEL_ACCOUNT_FIELDS` 范式，强制数组 ≡ 类型全集）；类型定义在 `role-catalog.ts` / `panel/types.ts` 原地不动。验证：cloud `typecheck`（改类型不改数组即编译失败）。 <!-- aidcp-cloud 316de98 仅动 version.ts：并列加 4 数组 + 8 个 _AssertNever（Missing/Extra 双向）；type import LlmKind/ThinkingModeApi(role-catalog)+ModelEffectiveSource/PersonaSource(panel/types)；typecheck 通过 -->
- [x] 1.2 扩 `VersionPayload.enums` 4 字段 + `buildVersionPayload()`；`PANEL_API_VERSION` 2→3。验证：`npm run test:acceptance`（AC-PROTO-*）→ 全量 `npm test` → `npm run typecheck`。 <!-- aidcp-cloud 316de98 enums 补 llmKind/effectiveSource/personaSource/thinkingMode；PANEL_API_VERSION=3；panel-server.test.ts 加断言（含 vision）；acceptance 46/46 + 全量 1588/1588 + typecheck 通过 -->

## 2. aidcp-console — 镜像 + 单源 + 对拍

- [x] 2.1 `src/types/aidcp-enums.ts`：加 `LLM_KINDS` / `MODEL_EFFECTIVE_SOURCES` / `PERSONA_SOURCES` / `THINKING_MODES_API` 镜像 `as const` + 派生导出类型 `LlmKind` / `ModelEffectiveSource` / `PersonaSource` / `ThinkingModeApi`。 <!-- aidcp-console 2e1ea75 -->
- [x] 2.2 `src/types/api.ts`：这 4 个类型改从 `./aidcp-enums` 复出（消灭第二处手抄定义）；`RoleConfigRow.llmKind: LlmKind`；`VersionPayload.enums` 补 4 字段。验证：`npm run typecheck`（32 消费方导入名不变）。 <!-- aidcp-console 2e1ea75 import+re-export；删本地 ModelEffectiveSource/ThinkingModeApi/PersonaSource 定义；typecheck 通过、32 消费方零改 -->
- [x] 2.3 `aidcp-enums.test.ts`：扩快照断言 4 镜像 + live `/api/version` 对拍。验证：`npm test` + `npm run build`。 <!-- aidcp-console 2e1ea75 快照 4 镜像 + live diff 4 字段；npm test 17 文件全过 + build 通过；AIDCP_PANEL_URL=https://aidcp.tommax.cc 跑 live 对拍 3/3 绿（哨兵已接线真机） -->

## 3. 部署

- [x] 3.1 部署 dev cloud（clean snapshot / `git archive HEAD`，勿从脏共享工作树；备份 → rsync → `systemctl restart aidcp-cloud.service` → healthcheck：active + 8787 监听 + `/api/version` 返 `panelApiVersion:3` + 新枚举字段）。绝不碰同机 isales。 <!-- 2026-07-08 deployed：git show HEAD:version.ts 抽 clean 副本单文件 rsync（避开并发 WIP）；backup cloud.bak.20260708-233018.tar.gz；restart aidcp-cloud.service→active；/api/version 返 panelApiVersion:3 + llmKind/effectiveSource(含vision)/personaSource/thinkingMode；飞书长连接已建立；8787 监听；未碰 isales -->
- [x] 3.2 dev console 无需重发：v2 控制台改动为类型 + test-only 镜像数组，无组件运行时消费、渲染产物与已上线 v1 包等价（crash 兜底 v1 已在 index-Z5dTkEHn.js）。live 对拍已验证：`AIDCP_PANEL_URL=https://aidcp.tommax.cc npm test` → aidcp-enums 漂移哨兵 3/3 绿（含 live /api/version 配置枚举对拍）。 <!-- aidcp-console 2e1ea75；哨兵接线经真机 live diff 验证 -->
