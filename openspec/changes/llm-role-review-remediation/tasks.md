# Tasks — llm-role-review-remediation

## 1. aidcp-cloud — 浏览侧解析防线

- [x] 1.1 `src/agents/content-evaluator.ts`：解析层 `verdict=valuable` 时 `index` 非整数即判解析失败（不再默认 0）；使用处对 `candidates` 做域界校验，越界按 skip 如实处理（独立 reason，绝不 `?? candidates[0]` 静默换卡）+ 单测（越界/非数字/负数三例） <!-- aidcp-cloud bc18972 -->
- [x] 1.2 `src/agents/search-evaluator.ts`：`verdict=search` 时校验 `keyword` ∈ 提示词给定的候选集，编造词按解析失败走既有安全回退（绝不真实搜索）+ 单测（编造词/合法词两例） <!-- aidcp-cloud bc18972 命中时回写候选集原词(canonical),下游搜索与归因用原词 -->

## 2. aidcp-cloud — 发布侧输出契约

- [x] 2.1 `src/publish-agent/roles/title-creator.ts`：`parseTitle` 接 `escapeControlCharsInJsonStrings`（与 content-creator 同源修复）+ 单测（裸换行标题 JSON） <!-- aidcp-cloud bc18972 -->
- [x] 2.2 `src/publish-agent/prompts.ts` `buildDeAiRewritePrompt`：增加「只输出重写后的正文本身，不要任何前言、解释或格式包裹」约束；顺修「口吾」→「口吻」笔误；同步受影响断言/预览测试 <!-- aidcp-cloud bc18972 新增 test/publish-agent/de-ai-rewrite-prompt.test.ts;role-prompt-preview 既有断言(includes 去除AI味)不受影响 -->
- [x] 2.3 `src/publish-agent/roles/quality-scorer.ts`：`buildAssemblerPrompt` 第一参改传「正文替换为清洗稿」的内容对象（`{...input.created, content: input.cleaned.content}`），标题/标签维持定稿来源 + 单测（rewritten=true 时 prompt 含清洗稿不含草稿） <!-- aidcp-cloud bc18972 -->

## 3. aidcp-cloud — 配置兜底

- [x] 3.1 `src/config/model-config-store.ts` `MODEL_CONFIG_DEFAULTS.textModel`：`qwen-turbo` → `qwen3.7-plus`（qwen-turbo 百炼 2026-07-13 下架）；同步受影响单测与注释 <!-- aidcp-cloud bc18972 qwen.ts 构造默认仍 qwen-turbo(仅存于无解析器注入的单测路径),注释已标注 -->

## 4. 测试 / 提交 / 部署

- [x] 4.1 `cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck` 全绿（安全红线 AC-* 必须全过） <!-- 2026-07-03 acceptance 36/36、全量 1143/1143、typecheck 干净 -->
- [x] 4.2 commit（显式列文件——工作区有并发 WIP：content-scheduler 三文件，绝不 `git add -A`）+ push origin master（non-ff 先 rebase） <!-- aidcp-cloud bc18972 fast-forward push,12 files -->
- [x] 4.3 ECS 部署安全序列：备份 `/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak` → surgical rsync 仅本次改动文件（不连带并发 WIP）→ restart → healthcheck（active + 8787 + 飞书长连 + PG select 1） <!-- 2026-07-03 deployed 备份 20260703-140753;6 文件 rsync 前后 md5 双向核验(旧=HEAD~1 无并发漂移,新=本地一致);healthcheck 全绿 -->

## 5. ECS 线上配置（psql 直写 + 重启热载；绕面板探活 8s 假 model_invalid）

- [x] 5.1 三表旧模型名巡检（deepseek-v3/r1、旧 kimi、glm-4.x、qwen-turbo）：**零残留** <!-- 2026-07-03 psql SELECT 核验,干净 -->
- [x] 5.2 qwen-flash 存活探测：compatible-mode 直探 HTTP 200 仍可调，但已从官方文档消失、同批 qwen-turbo 定 7-13 下架 → 维持防御迁移决策 <!-- 2026-07-03 ECS curl 实测;deepseek-v4-flash + enable_thinking:false 同测 200 -->
- [x] 5.3 批次 A：`publish:TopicGenerator` INSERT 温度 0.5；`publish:ApprovalGatekeeper` thinking `on`→`off`；核验 `publish:ImagePromptComposer` 温度 0.6（已被先行改好，2026-07-03 psql 确认在线） <!-- 2026-07-03 psql 写入+回读确认 -->
- [x] 5.4 批次 B：INSERT `browse:content_evaluator` / `browse:concept_extractor` / `browse:comment_like_appraiser` = `deepseek-v4-flash`(dashscope)；UPDATE `browse:comment_reviewer` / `browse:search_evaluator` `qwen-flash`→`deepseek-v4-flash` <!-- 2026-07-03 psql 写入+回读确认,role_config 现 15 行 -->
- [x] 5.5 `.env` 追加 `AIDCP_PUBLISH_CATEGORY_TIMEOUT_MS=180000` <!-- 2026-07-03 追加于重启前,已随重启加载 -->
- [x] 5.6 restart 后核验：psql 回读 6 行配置 + healthcheck + 运行日志抽查（llm 调用行的 model 分布） <!-- 2026-07-03 psql 回读 15 行全符预期;healthcheck 全绿(active/8787/8090/PG/飞书长连);model 分布留观察窗随真实浏览会话核 -->

## 6. 观察窗（3-7 天，不阻塞本 change 代码部分收口）

- [ ] 6.1 `llm_token_usage` 按 role×model 对比改前后：calls / ok_calls / token 单耗；content_evaluator 重点看 valuable 率与下游 content_curator reject 率（误判代理指标）；异常即 psql 改回 `qwen3.7-plus`
