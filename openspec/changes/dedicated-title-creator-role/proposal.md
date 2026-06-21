## Why

发帖流水线今天**根本没有"标题"这回事**。`ContentCreator` 按提示词产出的 `createdContent.title`（已约束 ≤18 字）在 `ContentAssembler` 处被整条丢弃——`AssembledContent` 压根没有 `title` 字段（`types.ts:109-119`），装配器只从 `createdContent` 取 `tags`（`content-assembler.ts:50-59`）。真正发出去的"标题"是 `PublishExecutor.deriveTitle(assembled)` 从**正文首行盲切 30 字**派生的（`publish-executor.ts:273-277`），用于 DB 写入（`:153`）、下发 edge（`:227`）、飞书审批卡（`:290`）。

后果有三，全是已实测的真问题（2026-06-21 真机发帖 publish-11 暴露）：
1. **标题质量不可控**：LLM 在「标题+正文+标签」一次性 JSON 里写标题，注意力被稀释；而且就算写好了也被丢弃，平台上显示的"标题"其实是正文开头一句。
2. **记录 ≠ 真实发布（红线失真）**：`publish_log.title` 存 30 字、edge 又盲切 20 字（`publish-command-handlers.ts:370`，`XHS_TITLE_MAX:166`）——数据库记的和真正发出去的不是一个东西。
3. **从字/emoji 中间硬切**：两处都是 `String.slice` 盲切，可能切碎汉字词、拆断 emoji 代理对。

用户决策：把标题生成拆成一个**独立角色**，排在**内容定稿之后、发布之前**，依据定稿正文单独写标题——既治注意力稀释，又顺带把"标题"这个产物真正接通到底（记录=下发=审批卡=真实发布）。

## What Changes

> 一句话：新增一个只管写标题的小角色，让它在正文定稿后产出唯一标题、卡到发布前；标题失败则发布失败（不造假标题）；长度收口到云端一处、edge 不再做任何截断。

- **【云端·新角色】`TitleCreator`（角色 id `publish:TitleCreator`）**：`watchKeys=['assembledContent']`，取**最终定稿正文** `assembledContent.finalContent`（不取草稿——正文会被去 AI 味环节改写，标题须忠于真正发出的文字）。短提示单独写一个 ≤18 可见字符的钩子标题，产出新黑板字段 `titleSelection`。默认 `timeoutMs=120000`（与 `ContentCreator` 一致，容得下 qwen3.7-max）。
- **【云端·失败=发布失败】**：`TitleCreator` 失败策略 `abort`——生成不出标题就**不写 `titleSelection`、不发布、流水线判失败**，**绝不派生兜底、绝不写假标题**（红线 MUST NOT 静默假成功）。必须验证 `abort` 让流水线**即时**判失败而非干等 18 分钟超时（参照 `ContentCreator` 现成 `abort` 行为）。
- **【云端·发布严格接在标题之后】**：`PublishExecutor` 改 `watchKeys=['gateDecision','titleSelection']` + `waitAll:true`——只有标题成功写出 `titleSelection` 才会激活发布；标题 `abort`=无 `titleSelection`=不发布。由此**审批卡片发出时标题必已就绪**：飞书审批卡的标题栏即真实 ≤18 字标题（不再是正文首行假标题），人工"通过"= 同时认可真实标题+正文+配图。
- **【云端·一处截断、记录=真发】**：新增 `src/publish-agent/title-clamp.ts` 的字形安全 `clampTitle(s, max=18)`（`Intl.Segmenter` 按 grapheme 计数；超长回退到最近词/标点边界，无边界则硬切 18，**绝不返空**；空正文给出明确空标题策略）。云端**一处**把标题收到 ≤18，同一个值写进 DB（`:153`）、下发 edge（`:227`）、飞书卡（`:290`）、`manual_review`（`:304`）/`abort`（`:342`）记录——全路径记录==下发==真实发布。`deriveTitle` 仅降级为"字段意外缺失时的最后兜底"。
- **【edge·不做策略】**：移除 `aidcp-edge/src/flows/publish-command-handlers.ts` 的标题截断（`XHS_TITLE_MAX:166` + `slice :370`，即撤回本会话早先 commit `472cda1`）。edge 只把云端标题**原样填入**、失败就失败（边轻云重：长度保证收口云端）。**此移除必须与本 change 的云端标题角色同 change 一起上线**——否则云端仍发 30 字、单撤 edge 会复发"发布按钮静默失效"。
- **【云端·可后台配模型】**：`TitleCreator` 经 `roleLlm('publish:TitleCreator')` 调用、在 `role-catalog.ts` 加目录行（`displayName 技术帖标题创作`, `group publish`, `llmKind text`, `tunableTemperature true`），使管理后台「角色配置页 /roles」可**独立配置**其模型/温度；**默认继承全局模型（qwen3.7-max）**，不配则零回归回落全局。
- **【保留】** `createdContent.title` 及 `content-creator.ts:73` 的截断**不动**——`ImagePlanner` 经 `prompts.ts:240` 仍读 `createdContent.title`（删了会坏配图）；该值可作为 `TitleCreator` 的可选 seed。
- **【验收】AC-TITLE-***：`clampTitle` 边界（18 不变 / 19 截断 / 单超长 CJK 词不返空 / emoji 不拆 / 空正文策略）；角色 `abort` 即时失败、不写假标题；标题全路径一致（记录==下发==审批卡）；端到端 `record == published title`。

## Impact

- **Specs**: `publish-pipeline`（ADDED 标题创作相关 requirement；与 stage-1/2/3/4 及 media-upload 的 `publish-pipeline` delta requirement 名互不重叠，归档时依序并入同一 spec）。
- **Code**:
  - `aidcp-cloud`：`src/publish-agent/types.ts`（+`TitleSelection`，`PipelineFields`+`titleSelection`）、`src/publish-agent/roles/title-creator.ts`（新）、`src/publish-agent/roles/index.ts`（导出）、`src/publish-agent/title-clamp.ts`（新）、`src/publish-agent/prompts.ts`（+`buildTitlePrompt`）、`src/publish-agent/roles/publish-executor.ts`（`watchKeys`+`waitAll`、`extractInput`、`:153/:227/:290/:304/:342` 标题改读 `titleSelection`、`deriveTitle` 降级为字段缺失兜底）、`src/config/role-catalog.ts`（+目录行）、`src/server.ts`（注册 `TitleCreator` + `roleLlm`）、对应单测/验收。
  - `aidcp-edge`：`src/flows/publish-command-handlers.ts`（移除 `XHS_TITLE_MAX` 与标题 `slice`）、对应单测。
- **协议**: 零改动（无新 `MessageType`）；`titleSelection` 仅黑板内字段，不入协议。`docs/protocol.md` 无需改。
- **DB**: 零 migration（标题仍写既有 `publish_log.title` 列，只是来源从派生改为真标题）。
- **不变量/红线**: MUST NOT 静默假成功（标题失败诚实判失败、不造假标题）；记录==真发（clamp 收口在 DB 写入与下发 edge 之前）；复用按角色取模型通道（`QwenClient` per-call opts + `RoleConfigStore`，零回归回落）；不碰风控、不碰浏览闭环、不碰同机 isales。
- **部署**: 云端随 master 部署（rsync 快照含累积 master，部署前 dry-run surface scope）；edge 本地重启生效。云端标题角色与 edge 撤截断**同批上线**。
- **冲突面**: 另一会话在改两仓 `protocol.ts`（comment-like change）——本 change **不碰 `protocol.ts`**；提交务必精确 `git add` 仅本 change 文件（不 `-A`）；改前先 pull/rebase（`publish-executor.ts`、`prompts.ts` 近期被标题相关 commit `9630364`/`3c5214c` 动过，行号可能漂移）。
