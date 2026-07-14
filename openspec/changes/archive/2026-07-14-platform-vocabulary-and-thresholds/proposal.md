## Why

浏览闭环的角色 prompt 与阈值仍是小红书口径，Facebook 复用时是隐性语义污染，且有一处内容维度的静默假成功：

- **8 处 prompt 硬编码「小红书 / 笔记 / 收藏」**：`agents/content-evaluator.ts`、`content-curator-role.ts`、`comment-reviewer.ts`、`comment-appraiser.ts`、`comment-like-appraiser.ts`、`concept-extractor-role.ts`、`follow-agent.ts`、`hot-lead/heat-velocity.ts`（按小红书时间文本解析）。Facebook 选卡/质量关卡/撰写全用这些小红书话术。
- **精品评论门槛对 FB 近乎恒关**：`comment-appraiser.ts` 判据 `likeCount>300 && (collectCount>100 || likeCount>10000)`，FB `collectCount` 恒 0 ⇒ 实际只有万赞爆帖能评。且 spec `comment-interaction` 写的是 1000/300，与代码 300/100/10000 **早已漂移**。
- **DeepReader 启发式对 FB 图片帖失效**：`deep-reader.ts:115-127` 只看 content.length；FB 图片帖 content 常空 ⇒ 误走「长正文」分支。
- **note.detail.comments[] 在浏览闭环被丢弃**：协议已有该字段（FB 图片帖常无正文时评论是撰写主要依据），但浏览闭环的撰写器（`agents/comment-composer.ts`，小红书口径）拿不到；定向评论支线另有一套 FB 撰写器（`server.ts` 的 `facebookCompose`）。两套不共享。

本变更把这些差异按平台参数化（扩现有 `CommentPlatformProfile`，不另开第二张词汇表），并登记门槛漂移。**cloud-only、无协议改动。**

> ⚠️ 依赖：`comment-interaction` / `interaction-appraisal` 的精品门槛与判定 prompt requirement **正被 `humanize-interaction-prompts`（活跃 22/23）MODIFY**。本 change 的**门槛平台化**必须等 humanize 归档后、对着 post-humanize spec 文本写 MODIFIED delta（否则归档会顶掉 humanize 的改动）。本 change 现落的 spec delta 只含**不冲突的新能力**（ADDED `platform-content-adaptation`）；门槛 MODIFIED 在 tasks 里标为实装期依赖。

## What Changes

- **词汇平台化**：8 处 prompt 去「小红书 / 笔记 / 收藏」，改从**扩展后的 `CommentPlatformProfile`**（已被 `comment-search-term-generator.ts`/`comment-target-picker.ts` 注入消费）取站点名/内容名词/指标名词，**MUST NOT 另开第二张 lexicon 表**。
- **DeepReader 启发式按平台**：图片帖判定不再只看 content.length（FB 图片帖 content 空不再误判长正文）。
- **热度速率解析按平台**：`hot-lead/heat-velocity.ts` 时间文本解析参数化。
- **comments[] 接进撰写**：云端事件层 `NoteDetailData` 增补 comments 字段，浏览闭环撰写器消费；合并浏览闭环与定向评论两套 FB 撰写器为共享 helper + 平台专属 caller（延续现有「helper 只返草稿、xhs `withApproval` 与 FB `withValidators` 分别包裹」模式）。
- **消散落裸分支**：dispatcher 6 处 `platform==='facebook'` 与 edge `main.ts:1069/1077/661-664` 收进 driver/registry 接口。
- **门槛平台化（实装期，post-humanize）**：`hasCollect=false` 只放宽收藏合取支、主条件 `likeCount>阈值` 保留（MUST NOT 退化为无门槛）；同时登记 spec↔code 门槛漂移。
- **contentTruncated + N6（条件）**：若 C2 探针 P1 证明 See more 展开路径需要显式截断标志，`note.detail.contentTruncated` 字段与其消费者护栏（ContentCurator MUST NOT 因正文短判 thin_content、CuratedNoteEvaluator MUST NOT 收截断正文进精选库）**同批落**（本 change 或后续，与字段同旗标门控）。

## Capabilities

### New Capabilities

- `platform-content-adaptation`: Browse-loop role prompts, deep-read heuristics, and heat-velocity parsing are parameterized per platform from the existing comment profile (no second lexicon), and post comments captured on detail feed the compose step.

### Modified Capabilities

- `comment-interaction`（实装期，post-humanize）：精品门槛按平台参数化，收藏-less 平台只放宽收藏合取支、主 like 阈值保留、绝不退化无门槛；登记 spec↔code 门槛漂移。

## Impact

- Cloud roles/prompts: `aidcp-cloud/src/agents/{content-evaluator,content-curator-role,comment-reviewer,comment-appraiser,comment-like-appraiser,concept-extractor-role,follow-agent,comment-composer}.ts`、`src/hot-lead/heat-velocity.ts`、`src/agents/deep-reader.ts`。
- Cloud profile + event types: `aidcp-cloud/src/platform/registry.ts`（扩 `CommentPlatformProfile`）、`src/event-bus/types.ts`（`NoteDetailData` 增 comments）、`src/server.ts`（合并 FB 撰写器）。
- Bare-branch cleanup: `aidcp-cloud/src/orchestrator/role-dispatcher.ts`（6 处）、`aidcp-edge/src/main.ts:1069/1077/661-664`。
- **撞车**：`humanize-interaction-prompts`（22/23）MODIFY comment-interaction/interaction-appraisal 同名 header ⇒ **门槛 MODIFIED 必须等它归档**（它还卡 `category-adaptive-images-and-judgment` 32/35 先归档）。无协议改动；edge、console、数据库、`ol` 不受影响。
