## Context

词汇蓝图批 1 的执行 change。核实记录（2026-08-06，全部为当日 grep 实测）：

| 命令 | 云端发送点 | 边缘处理器 | 结论 |
| --- | --- | --- | --- |
| `browse.next` | 0（仅协议定义 + 登记表） | `browse-session.ts` 留有 deprecated 分支 | 删 |
| `browse.scroll` | 0（同上） | 同上 | 删 |
| `publish.request` | 0 | 生产无处理器（登记表注释自证「墓碑」） | 删 |
| `plan.response` | **≥2 个活发送点**（v1 应答构造 `comm/handler.ts:1550` / 点赞触发工具 `comm/like-command.ts:60`） | v1 路径仍接线 | **留待 v1 退役轮** |

## Goals / Non-Goals

**Goals:** 三条死命令从两份协议穷举表、三份登记表、边缘路由与处理器、测试中彻底消失；`docs/protocol.md` 计数同步；蓝图批 1 行更新 `plan.response` 结论；迁移流程（直接切换）首跑验证。

**Non-Goals:** 不动 `plan.response` 与 v1 路径；不动其余 43 条；不出包（三条都是 cloud→edge 方向且云端零发送，删除对旧客户端零影响）；不做批 2 的改类。

## Decisions

- **直接切换**：旧名从 `MessageType` 穷举删除 → 两份 protocol.ts 的 `Record<MessageType,true>` 穷举与 typecheck 即守卫，漏删任何一处消费方当场编译红。这正是语法规格「类型穷举即迁移守卫」的首次实证。
- **`plan.response` 的处置按蓝图前置条款走**：核出活发送点 ⇒ 不删。它的死期绑定 v1 每步循环整体退役，那是独立的清理 change，不塞进本批。
- **AC-PUB 验收的处理原则**：删除 `publish.request` 相关断言时，「未授权绝不静默发布」这条红线 MUST 在现役 `publish.command` 路径上保有等价断言；只删对已死类型的引用，不削弱红线覆盖。
- **规格引用的分治**：publish-pipeline 里 5 处引用全是「禁止复活旧路径」的反面条款，删除命令使禁令对象消失但禁令语义仍然成立（禁止重建该模型），**不动**；真正依赖该命令存在的两处场景出 delta（见 proposal）。

## Risks / Trade-offs

- **[与并行的说明书收口 change 撞登记表]** → 集成串行：先到者先 land，后到者 rebase 解冲突（4 条删除 vs 全表加维，冲突局部且机械）。
- **[AC 验收误删]** → 每个被改的验收文件跑前后对比，红线断言只许换对象不许消失。
- **[protocol.md 计数改错]** → 以两份 protocol.ts 的 `MessageType` 穷举为准数（CLAUDE.md 明令），改后人工复核表与计数一致。
