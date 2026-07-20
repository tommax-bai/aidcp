## Why

2026-07-20 的 dev 真机事故中，Facebook 浏览闭环在第五条内容后进入评论支线，随后永久停止浏览：`CommentComposer` 在调用模型前等待可选语料召回，该 Promise 没有超时也没有返回，`commentInflight` 因收不到 `comment.skipped` / `comment.approved` 终局而一直压住 `scroll` 与 idle nudge。现有评论审批虽有 90 秒等待上限，但评论支线进入暂停态后的前置阶段仍允许无界等待，违背“失败必须收敛、不死锁浏览”的既有契约。

## What Changes

- 给评论撰写前的可选语料召回增加短超时；超时或失败按空参考降级，继续正常撰写，不把可选增强升级成浏览闭环硬依赖。
- 给 `commentInflight` 评论支线暂停态增加总等待上限；超时必须诚实发出 `comment.skipped{reason:'comment_subline_timeout'}`、恢复看门狗并释放浏览。
- 评论支线总超时后，任何迟到的 `comment.appraised` / `comment.approved` 都不得重新钉住页面或下发评论，避免“浏览已恢复后旧评论突然落地”。
- 增加稳定超时日志与回归测试，覆盖永不 resolve 的语料 Promise、暂停态自动释放、迟到授权不提交和正常快速路径不受影响。

## Capabilities

### New Capabilities

<!-- 无新增 capability。 -->

### Modified Capabilities

- `comment-interaction`: 把“评论支线任一阶段失败必须 `comment.skipped` 收敛”明确扩展到可选语料召回和整条 `commentInflight` 暂停窗，并规定超时后的迟到事件不得提交评论。

## Impact

- **代码（cloud-only）**：`aidcp-cloud` 的评论评估 / 撰写 / 去 AI 味 / 审批角色、`src/orchestrator/role-dispatcher.ts`、服务装配与聚焦测试。
- **配置**：新增有安全默认值的评论语料召回超时与评论支线总超时环境变量；缺省配置即可修复，无数据库或协议迁移。
- **行为边界**：只影响异常慢/悬空的评论准备链；正常评论仍须经过既有人审，超时只会“不评论并继续浏览”，绝不自动授权或伪造成功。
- **部署**：Cloud 运行时行为变化，完成测试、typecheck 与 OpenSpec 严格校验后部署 `dev`；Edge/Console 不改。
