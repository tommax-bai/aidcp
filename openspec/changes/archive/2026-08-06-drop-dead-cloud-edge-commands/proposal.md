## Why

词汇蓝图批 1（`docs/edge-command-grammar.md` §6.3）：删掉协议里的死命令，让词汇迁移的「直接切换」流程第一次真跑一遍。前置核实已做（2026-08-06）：

- `browse.next` / `browse.scroll`：已 `@deprecated`，云端**零发送点**（全仓只剩协议定义与登记表两处尸位）。
- `publish.request`：协议墓碑，云端零发送点，边缘生产无处理器（登记表注释自证）。
- `plan.response`：**核出活的发送点**（v1 兼容路径的应答构造 + 点赞触发工具仍在用）——按蓝图前置条款「核不实则留待下轮」，**本批不删**，随 v1 路径退役时再处理。蓝图批 1 行随本 change 更新此结论。

## What Changes

- **删除 3 条消息类型**（`browse.next` / `browse.scroll` / `publish.request`）：两份 `protocol.ts`（类型 + 载荷 + 载荷映射，逐字一致）、三份操作登记表（edge / cloud / `aidcp-automation` 经同步脚本）、边缘入口路由分支与相关处理器、命令诊断标签、涉及测试。
- **直接切换、无兼容层**：旧名从穷举表直接删，typecheck 即守卫；不留别名、不留墓碑（语法规格既定）。
- `docs/protocol.md` 头部计数与 §2 表随删同步（CLAUDE.md §2 明令）。
- **BREAKING（仅内部协议）**：删除后旧客户端若仍上报这三条…它们本来就不会——三条都是 cloud→edge 方向且云端零发送，删除对运行中的旧客户端**零影响**，本批不需要出包。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `captcha-incident-handling`: 「普通命令仍被暂停闸拦截」场景的示例命令从已删除的 `browse.next` 换成现役的 `page.scroll`（要求本身不变——暂停闸拦普通命令）。
- `read-to-write-note-lane`: 删去「旧整页发布路径也进入写笔记状态」场景——它要求边缘对 `publish.request` 有行为，该消息类型删除后此场景失去对象（原子路径与快照路径两个场景不变，覆盖不降）。

## Impact

- `aidcp-edge`：`src/comm/protocol.ts`、`src/client/{operation-registry,edge-client,command-diagnostics}.ts`、`src/main.ts`、`src/browse/browse-session.ts`、`src/publish/approval-gate.ts`、`src/native-page-engine/command-mapper.ts` + 4 个测试文件（含 `AC-PUB` 验收——删除后其「未授权绝不静默发布」断言 MUST 仍对现役 `publish.command` 路径成立）。
- `aidcp-cloud`：`src/comm/protocol.ts`、`src/comm/operation-registry.ts` + 相关测试。
- 控制仓：`docs/protocol.md` 计数、`docs/edge-command-grammar.md` 批 1 行的 `plan.response` 结论。
- 派生仓 `aidcp-automation`：登记表经 `scripts/sync-split-repos` 同步（MUST NOT 手搬）。
- **并行注意**：`close-account-layer-operation-manual` 正由后台并行实装，与本批在两份登记表 + 一个测试文件上有重叠——集成时串行 rebase，后到者解冲突。
