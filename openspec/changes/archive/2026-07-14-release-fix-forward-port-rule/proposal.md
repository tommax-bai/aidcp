## Why

现行发布分支规范（`deployment-environments` 的「Release branches are append-only」）允许把 OL 热修**追加**到发布分支上，但**没有任何一条要求它回流主干**。于是「在发布分支上修一次」成了一个可以永久停在那里的终点。

代价已经付过两次，且是同一种：

- **2026-07-14（本次）**：`210f386 fix persona auto prompt race` 只活在 `release/20260712-ol-recut`，从未回 master。用户跑的正是 master 客户端——所以「人设弹窗修了几次还复发」，因为**那个修复他从来没拿到过**。同批搁浅的还有 `36fe38f`（建号环境归属客户）、`5ee9d2d`（客户端更新人设）、`e2e9f88`（飞书群选项恢复）、`e36eddd`（token 记账连错库，对 OL 是真 bug）。
- **更早**：打包 spawn cwd/asar 的修复只活在签名分支，一到 master 发版就把同一个 regression 原样打包发出去（见 CLAUDE.md「打包红线」）。

共同的失效模式：**发布分支是「已上线」的，主干是「将上线」的。修复只落在前者，就等于给一个必然到来的未来埋了一颗一模一样的雷。**而且没有任何机械手段会提醒——控制仓对这些 sha 全文 grep 零命中，只能靠人现场 `git log master..release` 重建。

## What Changes

- 新增硬性需求：**发布分支上的任何改动，落地时必须同时回流主干**（forward-port），不得只停在发布分支上。
- 明确「回流」的验收口径：内容到主干即可（cherry-pick / 冲突解决 / 在新代码上重新实现皆可），**不要求 patch-id 相同**；判据是「主干上有等价行为 + 有测试覆盖」，而非 `git cherry` 的符号。
- 明确唯一的例外：**发布态工件指针**（如安装包版本号、下载页指向哪个包）是「哪台机器上放了哪个包」的部署状态，不是代码修复；它必须显式对账，但不得机械照搬（照搬会让主干指向另一台机器上并不存在的产物）。
- 明确回流失败时的处置：回流受阻（冲突大 / 已被主干取代 / 需重新实现）**必须当场登记**，不得静默留在发布分支上。

## Capabilities

### New Capabilities

### Modified Capabilities
- `deployment-environments`: 发布分支改动的回流义务 + 工件指针例外。

## Impact

- 文档：`CLAUDE.md` §6（git 纪律）、`docs/deployment-environments.md`。
- 无代码改动；这是流程契约。
- 本次已按新规范把积压的发布分支修复全部回流主干（edge `3a737e6` / `2f69cc9`，cloud `7bae1e5` / `ecefe7c`；另有 3 条经核验内容已在主干）。
