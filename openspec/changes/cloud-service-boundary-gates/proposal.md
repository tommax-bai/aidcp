## Why

拆仓决策已定：`aidcp-cloud` 将拆成 `aidcp-api` / `aidcp-content` / `aidcp-automation` 三个独立 Git 仓库（方案 §1、§16）。拆分方案 §12 阶段 1 把「增加模块导入和数据所有权检查」写成一句话、且排在阶段 1 末位。这个顺序是错的，理由是实测出来的三条：

1. **边界会被边建边打穿**。`aidcp-cloud` 近 30 天 462 次提交、其中 447 次动 `src/`，`src/server.ts`（4804 行）被 237 次提交触碰，占 src 提交的 53%、平均每天约 8 次。门禁排在阶段 1 末位，意味着阶段 1 前段建好的边界要在约 200 次提交里靠人记纪律守住。
2. **今天没有任何机械手段度量边界**。`aidcp-cloud` 无 lint 工具链（`package.json:11-18` 只有 build / typecheck / test / test:acceptance / start），CI 为 0。跨边界耦合的现存规模只能靠一次性脚本测出来，测完就散失。
3. **现存违规量级已经超过「顺手修一修」**。按方案 §4 的三条边界对 318 个源文件实测：三边之间已有 217 条跨边界 import；把 63 个（19256 行）无归属文件按同一判据补齐后，跨边界 import 总量上界 462 条；另有 5 张表被两个不同边界的文件各自写入。等到阶段 1 末位再建门禁，这些数字只会更大。

门禁的价值不依赖「先把历史债修完」。棘轮式豁免清单让门禁当天生效：起手把实测违规全量冻结，只保证不新增；此后每削减一条，清单少一条。**豁免清单的剩余条数就是拆仓就绪度的可读数**——阶段 3（提取 `aidcp-content`）的准入条件应当直接引用它，而不是靠主观判断「边界够不够干净了」。

同时必须裁决方案 §6.4「禁止共享包含业务逻辑的公共包」与现实的张力：实测有 16 个文件被 api / content / automation 三边共同导入，其中 `src/event-bus/types.ts:558` 的 `RoleName` 联合类型今天正靠同源类型检查兜底（CLAUDE.md §2 记录了两处此类保护失效各自付出的真实代价）。照 §6.4 复制三份，等于在拆仓当天先亲手拆掉唯一还在生效的防漂移手段。

## What Changes

- 建立一张覆盖 `aidcp-cloud/src` **全部**源文件的模块归属表，层枚举为 `kernel` / `api` / `content` / `automation` / `composition`，**没有「未分配」这个取值**；新增文件未声明归属即门禁失败。
- 新增导入方向门禁：解析全量静态与动态 import，按归属层判方向，违规方向即失败。
- 新增表写入归属门禁：扫 SQL 字面量里的 `INSERT` / `UPDATE` / `DELETE` 与 `CREATE TABLE` / `ALTER TABLE`，对照表归属清单，非属主层写入或建表即失败。
- 两道门禁都配棘轮式豁免清单：起手记录实测全部现存违规，此后**只允许减少**；清单里出现源码中已不存在的条目同样失败（不留空位给新违规回填）。
- 裁决 §6.4：**承认并命名一个共享内核层 `kernel`**，不复制三份。`kernel` 有准入测试（不得含 SQL、HTTP 路由、LLM 调用、进程内活状态、业务判定），有单写者纪律（进 CLAUDE.md §7 热点文件清单），拆仓时以版本化包发布、由 `aidcp-automation` 单一拥有。
- 给出两条削减路径并写成 tasks：反方向 `content→automation` 79 条中 69 条经 kernel 归零；正方向 `automation→content` 53 条中 43 条集中在 `src/orchestrator/role-dispatcher.ts` 一个文件。
- 实现方式：照抄仓内既有「读源码做结构断言」的验收测试范式，零新依赖、零 CI 依赖，落在 `test/acceptance/` 由既有 `npm run test:acceptance` 与 `scripts/land-change:38-42` 当天生效。
- 把「豁免清单剩余条数」写成拆仓阶段 3 的可判定准入条件，并同步进拆分方案文档。
- 本 change **只提出、不实装**；也不改动任何 `aidcp-cloud` / `aidcp-edge` / `aidcp-console` 业务代码。

## Capabilities

### New Capabilities

- `cloud-service-boundary-gates`: 云端模块归属表、导入方向门禁、表写入归属门禁与棘轮式豁免清单，构成拆仓前后的机械边界执行机构。

### Modified Capabilities

<!-- 无。本 change 新增一项机械门禁能力，不改变任何既有运行时行为契约。 -->

## Impact

- Cloud（`aidcp-cloud`）：新增 `boundaries/` 下四份清单文件与 `test/acceptance/` 下两个门禁用例及其扫描器；为满足 kernel 准入，需搬动 `DEFAULT_PG_CONFIG`（`src/cache/pg-anchor-cache.ts:33`）并把 `src/agents/base-role.ts:8-11` 对具体实现的导入收窄为接口。除此之外不改业务逻辑、不改数据库、不改协议。
- Edge（`aidcp-edge`）：无代码改动。`src/comm/protocol.ts` 进 kernel 不改变「协议五处同步」铁律，边缘侧那份 `protocol.ts` 仍逐字对齐。
- Console（`aidcp-console`）：无改动。Console 只消费云端面板 API，不受模块归属影响。
- Control（`aidcp`）：更新 `docs/cloud-service-decomposition-proposal.md` 的 §6.4（kernel 例外）、§12 阶段 1（门禁提到首位）、§12 阶段 3（准入引用豁免条数）；在 CLAUDE.md §7 热点文件清单加入 kernel 目录与两份归属清单。
