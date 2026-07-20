## Why

2026-07-20 的 dev 真机事故中，Facebook 评论撰写角色调用火山模型后超过 19 分钟仍既不 resolve 也不 reject；现有 `AbortController` 只尝试取消底层 fetch，无法保证调用方 Promise 必然收敛，`commentInflight` 因而长期压住浏览。现场同模型与通用 Abort 探针均正常，说明系统需要防住不可复现的单请求悬空，而不能把恢复浏览押在网络栈一定响应 abort 上。

## What Changes

- 把文本 LLM 的 `timeoutMs` 从“触发 Abort 的时间”升级为“调用方 Promise 必须结算的硬 deadline”：即使注入的 fetch 忽略 signal、永不返回，模型调用也必须按时 reject。
- 为文本模型调用记录不含 prompt/密钥的开始与终局阶段元数据；超时时明确记录 deadline、最后到达阶段和厂商请求 ID（若已取得）。
- 给浏览评论评估、撰写和去 AI 味改写配置独立的短模型 deadline，避免沿用面向慢 thinking 模型的 180 秒全局上限；超时仍按既有诚实 skip/原稿回退语义处理。
- 收紧评论支线最后保险的默认总 deadline，使任何未知悬空点也能在人可感知的窗口内释放浏览；迟到事件继续 fail-closed。
- 增加 fetch 永不 settle 且忽略 Abort、响应阶段标记、评论角色超时覆盖和浏览恢复的回归测试。

## Capabilities

### New Capabilities

<!-- 无新增 capability。 -->

### Modified Capabilities

- `role-llm-config`: 文本模型调用的配置超时必须保证 Promise 硬结算，并提供不泄密的开始、最后阶段、请求 ID 与终局可观测性。
- `comment-interaction`: 评论支线各 LLM 阶段使用独立短 deadline，并缩短总暂停保险；模型悬空只能诚实跳过或回退，不能继续钉住浏览。

## Impact

- **代码（Cloud-only）**：`src/llm/qwen.ts`、浏览角色公共 LLM 调用选项、`RoleDispatcher` 与服务装配，以及相关单元/集成测试。
- **配置**：新增带安全默认值的评论模型调用超时环境变量；评论支线总超时默认值收紧，已有合法 env 覆盖继续生效。
- **行为**：所有文本 LLM 调用在 deadline 到达时都能向调用方结算；评论模型超时只会如实跳过/回退并继续浏览，不会生成模板兜底、自动授权或伪造评论成功。
- **边界**：不改角色模型配置、不改全局 180 秒默认、不改 Edge/Console/协议/数据库 schema。
