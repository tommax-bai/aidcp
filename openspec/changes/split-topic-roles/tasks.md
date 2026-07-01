## 1. aidcp-cloud — 话题生成 / 评判角色 + 解耦正文（Phase A）

- [ ] 1.1 `src/publish-agent/types.ts`：新增 `interface TopicCandidates { candidates: string[]; generatedAt: number }`（置于 `TopicSelection` 旁），并在 `PipelineFields` 新增 `topicCandidates: TopicCandidates;`（`topicSelection` 相邻）；`TopicSelection` 形状不变。
- [ ] 1.2 `src/publish-agent/prompts.ts`：`buildCreatorPrompt` 去掉输出 schema 与示例里的 `tags` 字段；新增 `buildTopicGenerationPrompt(body, persona)`（system marker「话题生成」，输出 `{"topics":[...]}`，规则：不带 `#`、trim、贴合正文、粗细搭配、宁缺毋滥不编造）与 `buildTopicEvaluationPrompt(candidates, title, body)`（system marker「话题评判」，按相关性/质量/合规判、`kept ⊆ candidates` 只筛不加，输出 `{"kept":[...]}`）。
- [ ] 1.3 `src/publish-agent/roles/content-creator.ts`：`parseOutput` 的 `tags` 恒返回 `[]`（不再解析 `obj.tags`）；`CreatedContent.tags` 类型保留。
- [ ] 1.4 新增 `src/publish-agent/roles/topic-generator.ts`（镜像 `title-creator.ts`）：`config={name:'TopicGenerator', watchKeys:['assembledContent'], timeoutMs:≥180000(env 可调), fallback:'default'}`，`outputKey='topicCandidates'`，input=`assembledContent.finalContent`（+persona），`execute` 调 LLM→解析→strip `#`/trim/dedup，`getDefaultOutput()={candidates:[],generatedAt:clock()}`。
- [ ] 1.5 新增 `src/publish-agent/roles/topic-evaluator.ts`（镜像 `quality-scorer.ts` 的 fallback+正则解析）：`config={name:'TopicEvaluator', watchKeys:['topicCandidates'], timeoutMs:≥180000, fallback:'default'}`，`outputKey='topicSelection'`，input=候选+title/body(unwatched)，`execute` LLM 打分→`kept⊆candidates`→确定性 `Array.from(new Set(kept)).slice(0,30)`，`getDefaultOutput()={selectedTopics:[],selectedAt:clock()}`；红线：绝不加候选外话题、绝不凑数。
- [ ] 1.6 删除 `src/publish-agent/roles/topic-strategist.ts`；`src/publish-agent/roles/index.ts:17` 换 export 为 `TopicGeneratorRole` + `TopicEvaluatorRole`。
- [ ] 1.7 `src/server.ts`：import 块（:91）换成两新角色；注册（:1209）替换为 `registerRole(new TopicGeneratorRole({ llmClient: roleLlm('publish:TopicGenerator') }))` 与 `registerRole(new TopicEvaluatorRole({ llmClient: roleLlm('publish:TopicEvaluator') }))`（置于 TitleCreator :1207 之后）。
- [ ] 1.8 `src/config/role-catalog.ts`（:85 之后）：新增两 roleId `publish:TopicGenerator`（displayName「话题生成（依定稿）」）与 `publish:TopicEvaluator`（displayName「话题相关性评判」），供后台配模型。
- [ ] 1.9 测试：删 `test/publish-agent/topic-strategist.test.ts`；加 `topic-generator.test.ts` + `topic-evaluator.test.ts`（镜像 `title-creator.test.ts`：stub llmClient、断言 LLM 失败时 R1 默认空；evaluator 断言 `kept⊆candidates`、cap≤30、不编造）。

## 2. aidcp-edge — 真实加话题填写（Phase B）

- [ ] 2.1 `src/flows/publish-command-handlers.ts`：新增开关 `AIDCP_PUBLISH_TOPIC_CDP`（默认 OFF）读取；`add_with_candidate{topic}` 分支在开关 ON 时路由到新 `runAddTopic`，OFF 时保留现有 `buildTagInputRequest` + `PublishStepValidator(input_tag)` 路径。**不**以 `this.cdp` 存在与否判启用。
- [ ] 2.2 实现 `runAddTopic`（镜像 `runFillField` :456-508 的 focus + `findShadowButtonCenter` :511-560 的盒模型走查 + `dispatchClick`）：聚焦 `.tiptap.ProseMirror` → `typeHumanized('#'+kw)` → 轮询等建议下拉容器（≤4s）→ 盒模型中心点点文本匹配建议（无命中 Enter 兜底）→ 后置校验真 token → 诚实 `no_target`/`post_validate_failed`。时长封在云端 30s 单步超时内。
- [ ] 2.3 `src/flows/publish-post.ts`：新增 `topicPillValidator`（断言真话题 token/pill 节点存在，非全局子串），供 `runAddTopic` 后置校验；保留旧 `input_tag`（供开关 OFF 兜底路径）。
- [ ] 2.4 edge 单测：`runAddTopic` 在选择器未命中（校准前）fail-closed 回 `no_target`/`post_validate_failed`；桩 pill 节点的 happy-path 回 `ok`。
- [ ] 2.5 **[GATED — 实机 CDP 校准]** 真机 Chrome 打开创作发布页，校准：① 话题建议下拉容器选择器；② 已提交话题 token/pill 选择器/class；③ 确认「点建议」vs「Enter 提交」行为。抓一份 DOM 样本存档；未完成此项 MUST NOT 打开 `AIDCP_PUBLISH_TOPIC_CDP`（本 task 未勾选前 Phase B 不得标记完成）。

## 3. aidcp-cloud — 审批==下发接线（Phase C）

- [ ] 3.1 `src/publish-agent/roles/publish-executor.ts`：`watchKeys` 加入 `publishMetadata`；`ExecutorInput`/`extractInput` 增 `publishMetadata`。
- [ ] 3.2 `publish-executor.ts` 四处发卡/落库（成功 + `failed` + `abort` 记录）tags 全部改读 `publishMetadata.topics ?? []`，移除对 `assembled.finalTags` 的引用；确认 `publish-dispatcher.ts:175` 仍读 `metadata.topics`（不改）→ 卡==落库==下发。
- [ ] 3.3 `publish-executor.test.ts`：断言 `watchKeys` 含 `publishMetadata`、卡 tags 源为 `publishMetadata.topics`；加集成测试断言 executor/aggregator 不早于 `publishMetadata` 触发、且 `TitleCreator` abort 仍能干净判 failed。

## 4. 回归与校验

- [ ] 4.1 `test/publish-agent/publish-orchestrator.test.ts`：import/注册换两新角色；fakeLlm 路由加「话题生成」「话题评判」分支（返回 `{"topics":[…]}`/`{"kept":[…]}`）；角色数断言 23→24。
- [ ] 4.2 `test/publish-agent/model-call-timeout-invariants.test.ts`：把 `TopicGeneratorRole`/`TopicEvaluatorRole` 加进 `llmRoles`，覆盖 ≥180000 下限不变量。
- [ ] 4.3 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（`AC-PROTO-*`/`AC-PUB-*` 必过；本 change 无协议改动天然成立）。
- [ ] 4.4 edge：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。
- [ ] 4.5 `openspec validate split-topic-roles --strict` 通过。
