## Context

发帖流水线是云端事件驱动多角色（黑板 `PipelineContext` + `watchKeys`/`waitAll`）。当前**标题链路是断的**：

- `ContentCreator` 产出 `createdContent.title`（提示词约束 ≤18，`content-creator.ts:73` 还截了一次 20），但 `ContentAssembler` 只取 `tags`（`content-assembler.ts:50-59`），`AssembledContent` 无 `title` 字段（`types.ts:109-119`）——标题在装配处被丢弃。
- `PublishExecutor.deriveTitle(assembled)`（`publish-executor.ts:273-277`）从 `finalContent` **首行盲切 30 字**当"标题"，用于 DB 写入（`:153`）、下发 edge（`:227`）、飞书审批卡（`:290`）；`manual_review`（`:304`）/`abort`（`:342`）记录用 `finalContent.slice(0,50)`。
- edge 再把收到的标题盲切 20（`publish-command-handlers.ts:370`，`XHS_TITLE_MAX:166`）。

净效果：平台显示的"标题"实为正文开头一句、`publish_log` 记 30 字而真发 20 字（失真红线）、两处 `String.slice` 可能切碎汉字/emoji。已由真机发帖 publish-11（2026-06-21）实测暴露。

约束：红线 MUST NOT 静默假成功；边轻云重（edge 只做原子操作、不做策略）；状态/长度收口云端；不动协议 v2 与 DB 结构；复用既有按角色取模型通道（`RoleConfigStore` 零回归回落）；并发会话在改两仓 `protocol.ts`（comment-like），本 change 不碰之。

## Goals / Non-Goals

**Goals:**
- 标题由独立角色 `TitleCreator` 在**正文定稿后**单独生成（治注意力稀释、质量可控）。
- 标题真正接通到底：记录==下发==审批卡==真实发布（修失真红线）。
- 长度收口云端一处、字形安全（不从字/emoji 中间切、绝不返空）。
- 标题失败=发布失败（诚实硬失败，不造假标题）。
- 发布严格接在标题就绪事件之后；审批卡显示真实标题。
- 标题角色模型可后台独立配置，默认继承全局（qwen3.7-max）。

**Non-Goals:**
- 不做 A/B 多标题候选、不做标题打分（YAGNI；如需，后续给 `titleSelection` 加字段，零下游改动）。
- 不做派生兜底/降级出标题（用户明确：失败就失败）。
- 不改协议、不加 DB migration、不动风控/浏览闭环。
- 不在 edge 做任何长度策略（反而移除现有 edge 截断）。
- 不动 `createdContent.title` 及其 `content-creator.ts:73` 截断（`ImagePlanner` 经 `prompts.ts:240` 仍用它配图）。

## Decisions

### D1：独立角色，而非在 ContentCreator 内补一个标题子提示
- **选**：新增 `TitleCreator` 角色。**因为**标题须基于**去 AI 味后的定稿正文**——而定稿在 `ContentCreator` 之后才产生，无法在 `ContentCreator` 内拿到；独立角色还能经既有通道独立配模型/温度/超时。
- **弃**：在 `ContentCreator` 提示词里加强标题约束。**因为**正文未定稿、且这正是注意力稀释的来源（要修的 bug）。
- **弃**：只修管线、不加角色（仅让 `deriveTitle` 用字形安全 clamp）。**因为**那只把"正文首行当标题"做得更整齐，标题质量仍不可控；用户明确要独立角色。

### D2：输入取最终定稿正文 `assembledContent.finalContent`，而非草稿
- `watchKeys=['assembledContent']`。标题忠于真正发出的文字；代价是装配后多一次 LLM 往返（短任务、可接受）。不并行抢跑草稿以省延迟（会重新引入草稿/定稿不一致）。

### D3：失败策略 = `abort`（失败即发布失败，不造假标题）
- 用户决策覆盖了评审初版的"永不阻断+派生兜底"。`TitleCreator` 失败时不写 `titleSelection`，下游因 `waitAll` 缺键而不发布、流水线判 `failed`。
- **必须验证**：`abort` 让流水线**即时**判失败而非干等 `pipelineTimeoutMs`（18 分钟）。`ContentCreator` 已是 `abort`，按其现成失败收敛行为接；apply 时先确认 `abort` 的传播路径（base-role 失败处理 + orchestrator 如何在某 `waitAll` 上游永不写键时收敛），若现状是"干等超时"，则需让 `abort` 即时 reject 流水线（作为本 change 的一部分明确处理，不留 18 分钟挂死）。
- 默认 `timeoutMs=120000`（与 `ContentCreator` 一致，容 qwen3.7-max）。

### D4：发布门 = `waitAll(['gateDecision','titleSelection'])`
- `PublishExecutor` 改双键 `waitAll`。黑板天然保证：标题没就绪不发布；标题 `abort` 不发布。**审批卡由 `PublishExecutor` 在激活后发出**，故卡片必带真实标题（`:290` 改读 `titleSelection.title`）。`waitAll` 要求 `keys.length>1`，已满足。

### D5：长度收口云端一处，字形安全 clamp，记录=真发
- 新增 `title-clamp.ts` 的 `clampTitle(s, max=18)`：`Intl.Segmenter` 按 grapheme 计数；超 18 回退最近词/标点边界，窗口内无边界则**硬切到 18**（绝不返空）；空输入给出明确空标题策略（保留空串、诚实，不编造占位——XHS 允许空标题）。
- 收口点在 `TitleCreator`：写入 `titleSelection.title` 即已 ≤18。`PublishExecutor` 的全部标题出口（DB `:153`、序列 `:227`、卡片 `:290`、`manual_review :304`、`abort :342`）改读 `titleSelection.title`，`deriveTitle` 仅保留为"字段意外缺失时的最后兜底"。
- **ceiling=18**：提示词目标 18，XHS >20 静默拒发；云端切 18 留 2 字余量吸收"我方 grapheme 计数 vs XHS 自己计数"的分歧。

### D6：edge 移除标题截断（不做策略）
- 删 `publish-command-handlers.ts` 的 `XHS_TITLE_MAX`（`:166`）与标题分支 `slice`（`:370`），edge 原样填云端标题。**必须与本 change 云端部分同批上线**：先撤 edge、云端仍发 30 字会复发"发布按钮静默失效"。

### D7：模型经按角色通道、默认全局、后台可配
- `server.ts` 用 `roleLlm('publish:TitleCreator')` 构造角色；`role-catalog.ts` 加目录行（`displayName 技术帖标题创作`/`group publish`/`llmKind text`/`tunableTemperature true`），使「角色配置页 /roles」可独立配。默认无 `role_config` 行→回落全局（qwen3.7-max），零回归。

### D8：新黑板字段 `titleSelection`，不动 `AssembledContent`
- `types.ts` 加 `TitleSelection{title,source,decidedAt}` 与 `PipelineFields.titleSelection`。不往 `AssembledContent` 塞字段（它是稳定边界）。`source` 诚实标注来源。

## Risks / Trade-offs

- **[`abort` 可能让流水线干等 18 分钟而非即时失败]** → apply task 先坐实 `abort`+`waitAll` 上游不写键时的现状收敛行为；若非即时，则在本 change 内让标题失败即时 reject 流水线（明确验收：标题失败→秒级 `failed`，不挂 18 分钟）。这是本设计**最大风险点**，列为 BLOCKING 验证。
- **[多一次 LLM 往返（默认 qwen3.7-max ~47s）增加每帖耗时]** → 仍远小于人审窗口（15 分钟）与流水线预算（18 分钟），可接受；后台可换更快模型，但默认不变（用户决策）。
- **[`clampTitle` 边界回退返空 / 切碎 grapheme]** → 单测覆盖：18 不变、19 截断、25 连续汉字不返空、emoji 不拆代理对、空正文策略。
- **[行号漂移：`publish-executor.ts`/`prompts.ts` 近期被 commit `9630364`/`3c5214c` 改过]** → apply 前 `git pull --rebase`，按符号（函数/字段名）而非行号定位。
- **[并发 WIP 改 `protocol.ts`]** → 本 change 不碰协议；提交精确 `git add` 仅本 change 文件（不 `-A`）。
- **[edge 撤截断与云端不同步上线]** → 流程纪律：两端同批部署；先云端（保证 ≤18）后 edge，或一并发布。

## Migration Plan

1. **云端实装**（types→clamp util→prompt→TitleCreator 角色→executor 改接线→catalog→server 注册）→ cloud `test:acceptance`→全量 `test`→`typecheck` 全绿（AC-PUB-*/AC-PROTO-*/AC-RISK-* + 新 AC-TITLE-*）。
2. **edge 实装**（移除标题截断）→ edge `test`+`typecheck` 绿。
3. **部署**：云端按安全序列（备份→dry-run surface scope→rsync 仅本 change 文件→restart→healthcheck→失败回滚）；edge 本地重启。**两端同批**。
4. **真机验证**：飞书 `/publish`→审批卡显示真实 ≤18 标题→通过→发布成功→核对 `publish_log.title` == 平台显示标题（≤18、未切碎）。
5. **回滚**：云端解 `.bak.<ts>.tar.gz`+restart；edge 回退本 change commit。

## Open Questions

- `abort` 即时失败 vs 干等超时的现状——apply task 1 必先坐实（见 Risks 最大风险点）。
- 空 `finalContent` 时的空标题：保留空串（诚实）已定；若运营反馈 XHS 空标题体验差，再议占位策略（不在本 change）。
