## 1. aidcp-cloud — 话题生成 / 评判角色 + 解耦正文（Phase A）

- [x] 1.1 `src/publish-agent/types.ts`：新增 `interface TopicCandidates { candidates: string[]; generatedAt: number }`（置于 `TopicSelection` 旁），并在 `PipelineFields` 新增 `topicCandidates: TopicCandidates;`（`topicSelection` 相邻）；`TopicSelection` 形状不变。 <!-- aidcp-cloud abf6769 -->
- [x] 1.2 `src/publish-agent/prompts.ts`：`buildCreatorPrompt` 去掉输出 schema 与示例里的 `tags` 字段；新增 `buildTopicGenerationPrompt(body, persona)`（system marker「话题生成」，输出 `{"topics":[...]}`，规则：不带 `#`、trim、贴合正文、粗细搭配、宁缺毋滥不编造）与 `buildTopicEvaluationPrompt(candidates, title, body)`（system marker「话题评判」，按相关性/质量/合规判、`kept ⊆ candidates` 只筛不加，输出 `{"kept":[...]}`）。 <!-- aidcp-cloud abf6769 -->
- [x] 1.3 `src/publish-agent/roles/content-creator.ts`：`parseOutput` 的 `tags` 恒返回 `[]`（不再解析 `obj.tags`）；`CreatedContent.tags` 类型保留。 <!-- aidcp-cloud abf6769 -->
- [x] 1.4 新增 `src/publish-agent/roles/topic-generator.ts`（镜像 `title-creator.ts`）：`config={name:'TopicGenerator', watchKeys:['assembledContent'], timeoutMs:≥180000(env 可调), fallback:'default'}`，`outputKey='topicCandidates'`，input=`assembledContent.finalContent`（+persona），`execute` 调 LLM→解析→strip `#`/trim/dedup，`getDefaultOutput()={candidates:[],generatedAt:clock()}`。 <!-- aidcp-cloud abf6769 executeWithFallback 保证失败必写键 -->
- [x] 1.5 新增 `src/publish-agent/roles/topic-evaluator.ts`（镜像 `quality-scorer.ts` 的 fallback+正则解析）：`config={name:'TopicEvaluator', watchKeys:['topicCandidates'], timeoutMs:≥180000, fallback:'default'}`，`outputKey='topicSelection'`，input=候选+title/body(unwatched)，`execute` LLM 打分→`kept⊆candidates`→确定性 `Array.from(new Set(kept)).slice(0,30)`，`getDefaultOutput()={selectedTopics:[],selectedAt:clock()}`；红线：绝不加候选外话题、绝不凑数。 <!-- aidcp-cloud abf6769 失败保守置空 -->
- [x] 1.6 删除 `src/publish-agent/roles/topic-strategist.ts`；`src/publish-agent/roles/index.ts:17` 换 export 为 `TopicGeneratorRole` + `TopicEvaluatorRole`。 <!-- aidcp-cloud abf6769 -->
- [x] 1.7 `src/server.ts`：import 块换成两新角色；注册替换为 `registerRole(new TopicGeneratorRole({ llmClient: roleLlm('publish:TopicGenerator') }))` 与 `registerRole(new TopicEvaluatorRole({ llmClient: roleLlm('publish:TopicEvaluator') }))`（置于 TitleCreator 之后）。 <!-- aidcp-cloud abf6769 -->
- [x] 1.8 `src/config/role-catalog.ts`：新增两 roleId `publish:TopicGenerator`（displayName「话题生成（依定稿）」）与 `publish:TopicEvaluator`（displayName「话题相关性评判」），供后台配模型。 <!-- aidcp-cloud abf6769 rebase 与 publish-prompt-preview 并入无冲突 -->
- [x] 1.9 测试：删 `test/publish-agent/topic-strategist.test.ts`；加 `topic-generator.test.ts` + `topic-evaluator.test.ts`（stub llmClient、断言 LLM 失败时 R1 默认空；evaluator 断言 `kept⊆candidates`、cap≤30、不编造）。 <!-- aidcp-cloud abf6769 失败用例 waitMs=2600（含 executeWithFallback 退避） -->

## 2. aidcp-edge — 真实加话题填写（Phase B）

- [x] 2.1 `src/flows/publish-command-handlers.ts`：新增开关 `AIDCP_PUBLISH_TOPIC_CDP`（默认 OFF）读取；`add_with_candidate{topic}` 分支在开关 ON 时路由到新 `runAddTopic`，OFF 时保留现有 `buildTagInputRequest` + `PublishStepValidator(input_tag)` 路径。**不**以 `this.cdp` 存在与否判启用。 <!-- aidcp-edge 873fd0d -->
- [x] 2.2 实现 `runAddTopic`（镜像 `runFillField` 的 focus + `findShadowButtonCenter` 的盒模型走查 + 真实鼠标事件）。已校准流程：聚焦**正文** `.tiptap.ProseMirror` → `typeHumanized(' #'+kw)` → 轮询等 `.tippy-box[role="tooltip"]` 下拉（≤4s）→ 在 `#creator-editor-topic-container .item` 选目标项（**优先文本精确匹配关键词**者；无则点首项「新建话题」）→ 取其中心用 **`Input.dispatchMouseEvent`** 点击（`.click()` 实测无效）→ 后置校验（`deps.dom.getRoot()` + `committedTopicPill`）→ 诚实 `no_target`/`post_validate_failed`。 <!-- aidcp-edge 873fd0d 后置校验用 dom 快照+纯函数，便于单测 -->
- [x] 2.3 `src/flows/publish-post.ts`：新增 `committedTopicPill(root, keyword)` + `topicPillValidator(keyword)`——断言编辑器内存在 `a.tiptap-topic[data-topic]` 且其文本 / `data-topic.name` 与关键词匹配（**非**全局子串、**非**纯文本 `#kw`）。保留旧 `input_tag`（供开关 OFF 兜底路径）。 <!-- aidcp-edge 873fd0d -->
- [x] 2.4 edge 单测：`committedTopicPill`（真 token→true、纯文本→false）；`runAddTopic` 下拉未命中→`no_target`、点了无 token→`post_validate_failed`、happy→`ok`、开关 OFF→不碰 CDP 走兜底。 <!-- aidcp-edge 873fd0d 快进时钟避免真等 4s 轮询 -->
- [ ] 2.5 **[已实机校准，代码已接线，待真机复跑 + 开开关]** 选择器已由探针实证并写进 `runAddTopic`/`committedTopicPill`（下拉 `.tippy-box[role="tooltip"]`、候选 `#creator-editor-topic-container .item` / 首项「新建话题」、真实鼠标提交、已提交标记 `a.tiptap-topic[data-topic]`；DOM 样本见 design「实机校准」节）。**剩余动作**（本次未做）：真机打开 `AIDCP_PUBLISH_TOPIC_CDP` 跑一遍发布、确认编辑器真出现 `a.tiptap-topic`，无误后才在生产开开关；未复跑确认前开关保持 OFF、Phase B 不算完成。

## 3. aidcp-cloud — 审批==下发接线（Phase C）

- [x] 3.1 `src/publish-agent/roles/publish-executor.ts`：`watchKeys` 加入 `publishMetadata`；`ExecutorInput`/`extractInput` 增 `publishMetadata`。 <!-- aidcp-cloud abf6769 -->
- [x] 3.2 `publish-executor.ts` 四处发卡/落库（成功 + `failed` + `abort` 记录）tags 全部改读 `publishMetadata.topics ?? []`，移除对 `assembled.finalTags` 的引用；`publish-dispatcher.ts` 仍读 `metadata.topics`（不改）→ 卡==落库==下发；顺带消除 `context.get('publishMetadata')` 取值竞态。 <!-- aidcp-cloud abf6769 -->
- [x] 3.3 `publish-executor.test.ts`：断言 `watchKeys` 含 `publishMetadata`、卡/落库 tags 源为 `publishMetadata.topics`（默认 topics≠finalTags 以证明取自 topics）；加集成测试断言缺 `publishMetadata` 时不激活、补齐后激活。 <!-- aidcp-cloud abf6769 -->

## 4. 回归与校验

- [x] 4.1 `test/publish-agent/publish-orchestrator.test.ts`：import/注册换两新角色；fakeLlm 路由加「话题生成」「话题评判」分支；角色数断言 23→24。 <!-- aidcp-cloud abf6769 -->
- [x] 4.2 `test/publish-agent/model-call-timeout-invariants.test.ts`：把 `TopicGeneratorRole`/`TopicEvaluatorRole` 加进 `llmRoles`，覆盖 ≥180000 下限不变量。 <!-- aidcp-cloud abf6769 -->
- [x] 4.3 cloud：`npm run test:acceptance`（27）→ `npm test`（1023）→ `npm run typecheck` 全绿；`AC-PROTO-*`/`AC-PUB-*` 过（本 change 无协议改动）。 <!-- aidcp-cloud abf6769 -->
- [x] 4.4 edge：`npm run test:acceptance`（11）→ `npm test`（437）→ `npm run typecheck` 全绿。 <!-- aidcp-edge 873fd0d -->
- [x] 4.5 `openspec validate split-topic-roles --strict` 通过。 <!-- aidcp abf6769/873fd0d -->
