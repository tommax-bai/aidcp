## Why

视频号回复发送目前主要按错误类别区分 `failed` 与 `ambiguous`，没有先判断平台写请求是否真正离开 Edge 进程。这样会把端点未捕获、请求无法序列化等“确定未发送”的本地失败误记为“发送结果待核验”，长期占住任务并制造并不存在的重复发送风险。

## What Changes

- 冻结发送结果的第一判据：只有请求可能已经抵达平台时，结果未知才允许进入 `ambiguous`；能够证明请求未派发时必须返回 `failed`。
- 明确本地前置失败、平台明确拒绝、平台确认成功、派发后超时/断连/响应不可解析四类结果的状态、核验和重试语义。
- Edge API client 保留请求构造阶段的未派发证据，并把平台响应解析阶段的错误标记为已派发；回复发送器消费该证据，只对真正可能已写入的平台请求执行历史/评论回查。
- 补齐回归测试，证明确定未派发不会进入待核验或触发回查，派发后不确定仍禁止盲目重发。
- 不改变 WS v2 message type、payload shape、Cloud 最终风险状态单写者或写能力默认关闭策略。

## Capabilities

### New Capabilities

- `wechat-send-failure-semantics`: 定义视频号回复从 Edge 本地准备、平台派发到结果回查的诚实失败与歧义判定边界。

### Modified Capabilities

<!-- None. The existing interaction result envelope already carries failed/ambiguous and needs no schema change. -->

## Impact

- Control repo：新增发送失败语义规范、设计和实施任务；同步相关开发文档时不得声称真实写已验证。
- `aidcp-edge`：`src/wechat-channels/api-client.ts` 的派发证据传播、`src/wechat-channels/reply-sender.ts` 的结果分类与对应单元测试。
- `aidcp-cloud`：协议和持久化形状不变；以现有结果消费测试确认 `failed` 与 `ambiguous` 仍按冻结语义落账。
- 部署：Edge 运行时行为变化需要合入 `master` 后发布到 `dev`；不构建或发布桌面安装包，除非另有明确要求。
