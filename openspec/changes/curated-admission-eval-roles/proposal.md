## Why

`curated-inspiration-corpus`（Phase 1/2/2b，已上线 ECS）让「过门槛的内容」进精选语料、喂发帖创作。但 **2026-06-28 真机验（账号「测评酱」）暴露了准入判定的两处质量缺口**：

1. **相关性只到「标题层」**：决定「开哪篇笔记」的浏览侧评估是看 **feed 卡片的标题/作者/赞数**判「值不值得点开」，**没看正文**。所以「被打开」只代表标题像那么回事，**正文与账号领域的真实匹配度、内容是否扎实，从未评过**。
2. **精选准入没有内容质量关**：精选的相关性闸原是「拿账号兴趣硬子串匹配正文」，真机验证实其恒不命中（兴趣是描述性长短语、人设亦明示「不用于硬匹配」），已临时关闭。于是当前准入 = **「人群收藏够多」这一个客观信号**——一篇高收藏但**跑题 / 单薄（标题党 / 蹭热点 / 纯广告）**的笔记照样进精选，污染创作素材。

**需要一道真正的「内容层」相关性 + 质量筛选**：不是看标题、不是子串硬匹配，而是**让模型读全文判断**。但模型评估有成本，不能每篇浏览过的笔记都评——故用既有的便宜共鸣预筛（收藏/比率）挡在前面，**只对人群已验证有共鸣的少量候选**才调模型。

## What Changes

> 把精选准入从「事件后一道便宜判定直接落库」改成**两段式**：便宜预筛在前、模型评估在后；并按用户决策**新建两个独立评估角色**（正文 / 评论分开）。基于 `curated-inspiration-corpus` 的语料表与共鸣门槛，不改边端、不改协议。

- **【准入两段式】** 第一段 = **便宜共鸣预筛**（确定性、零 LLM）：笔记按收藏地板 / 收藏赞比率，评论按评论赞数；不过者直接弃，**绝不进第二段**（成本红线）。第二段 = **模型评估角色**（仅跑在第一段幸存者上）：读全文判**内容层相关性 + 内容丰富度 + 非纯广告/标题党/蹭热点**；过了才落精选语料。
- **【新建「正文进精选」评估角色】**（`curated_note_evaluator`）：消费笔记详情事件 → 跑共鸣预筛 → 过则按账号人设领域用 LLM 评估笔记**全文**的相关性与丰富度 → 准入则 `upsertObservation`。**取代**当前全局事件处理器里「笔记观测直接落精选」那段（把该捕获挪进角色，以拿到账号绑定的 LLM 与人设）。
- **【新建「评论进精选」评估角色】**（`curated_comment_evaluator`，**独立于正文角色**）：消费确认点赞评论事件 → 共鸣预筛（评论赞数达标 **∪** 已确认点赞）→ LLM 评估评论的相关性与作为「角度/口吻范例」的价值 → 准入则 `archiveComment`。评论与正文判定标准、prompt 完全不同，故拆两个角色。
- **【自有收藏免评估直接纳入】**（用户决策）：机器人自己收藏的笔记（自有收藏自动纳入路径）**绕过 LLM 评估直接进**——机器人主动收藏本身已是一次受风控约束的策展判断，比预筛更强，无需再评。
- **【相关性硬子串闸退役】**：`curated-gate` 的「兴趣硬子串相关性」缺省已关（minTopicOverlap=0），本 change 后由模型评估承担相关性，硬子串闸正式退役为「保留但缺省关、可配」。

> 用户三项决策（2026-06-28，本 change 采纳）：① 自有收藏免 LLM 评估直接进；② 评论预筛 = 评论赞数达标 ∪ 已确认点赞；③ 评估维度 = 相关性 + 内容丰富度 + 排除纯广告/标题党/蹭热点。

## Capabilities

### Modified `curated-inspiration-corpus`

> 本 change 扩展（尚未归档的）`curated-inspiration-corpus` capability 的「准入」语义：在既有共鸣门槛之后加一道模型评估段，并新增两个评估角色的契约。按 openspec 约定，base capability 仍未并入 `openspec/specs/`，故本 change 的 delta 写在 `## ADDED Requirements` 下，归档时与 `curated-inspiration-corpus` 的 delta 依序并入同一 capability（requirement 名互不重叠）。

- `curated-inspiration-corpus`（本阶段补充）：两段式准入（便宜共鸣预筛 → 模型评估）、`curated_note_evaluator`（正文全文相关性+丰富度+非广告标题党）、`curated_comment_evaluator`（评论相关性+范例价值，独立角色）、自有收藏免评估直接纳入、模型评估只跑预筛幸存者的成本红线。

## Impact

- **aidcp-cloud（主体，纯云端）**
  - 新增 `src/agents/curated-note-evaluator.ts`（`curated_note_evaluator` 角色，仿 `content-curator-role.ts` 订阅 `note.detail.arrived` + 仿 `comment-like-appraiser.ts` 持 LLM）：共鸣预筛（复用 `curated-gate` 的 resonance 部分）→ LLM 评估 → `curatedStore.upsertObservation`。
  - 新增 `src/agents/curated-comment-evaluator.ts`（`curated_comment_evaluator` 角色）：消费 `comment_like.confirmed`（带 Phase 2b 的 likeCount）→ 共鸣预筛 → LLM 评估 → `curatedStore.archiveComment`。
  - 新增评估 prompt（正文 / 评论各一套；输出严格 JSON：{admit, reasons, relevanceOk, richnessOk, isPromoOrClickbait}）。
  - 改 `src/event-bus/types.ts`：`RoleName` 枚举加 `curated_note_evaluator` / `curated_comment_evaluator`。
  - 改 `src/orchestrator/role-dispatcher.ts`：注册两角色（仅 `curatedStore` 可用时注册，仿 `concept_extractor` 仅概念池可用时注册）；注入账号绑定 LLM、`getSoul`、`getNoteData`、`curatedStore`。
  - 改 `src/server.ts`：**移除**全局 `note.detail.arrived` 处理器里「笔记精选捕获」那段（挪进 `curated_note_evaluator` 角色）；**保留**自有收藏自动纳入（`markBotAction collect` 仍在全局处理器、免 LLM 评估）与点赞标记；**移除**评论双写里的直接 `archiveComment`（挪进 `curated_comment_evaluator`，仅保留 `valuableCommentStore.archive` 不变）。
  - 改 `src/publish-agent/curated-gate.ts`：拆出「resonance-only」判定供预筛复用；相关性闸保留但缺省关（已是 0），文档标注「相关性由模型评估承担」。
  - 配置：共鸣预筛阈值（沿用 Phase 1）+ 评估开关 / 模型选择（判定类，复用既有 role-model 配置）。

- **aidcp-edge / 协议**：**零改动**（Phase 2b 已采评论赞数；本 change 纯云端判定）。

- **DB**：无新表 / 无新列（复用 `curated_content`）。

- **依赖与红线**
  - 依赖 `curated-inspiration-corpus`（语料表 `curated_content`、`upsertObservation` / `archiveComment` / `markBotAction`、共鸣门槛）。
  - 复用既有角色架构（`BaseRole` + `RoleDispatcher` + 账号绑定 LLM + `getSoul`），不改架构。
  - 成本红线：模型评估 MUST 只跑在共鸣预筛幸存者上，MUST NOT 每篇浏览笔记都评。
  - 诚实红线：评估失败 / LLM 降级 → 诚实不纳入（不静默纳入、不编造分），不阻塞浏览主路径（fire-and-forget）。
  - 安全红线仍全过（`AC-RISK-*` 等）：本 change 不改风控、不改发布。

> 拆分说明：本 change 是 `curated-inspiration-corpus` 的 Phase 3（准入质量化）。与 Phase 1/2/2b 解耦——前者管「采集 + 存储 + 消费 + 共鸣门槛」，本 change 只在「准入判定」处插入模型评估段。可独立实现、上线、真机验。
