## Why

参照洗稿已经能把原文配图保存为 `referenceImages`，发布审计也能显示 provider 是否实际使用参考图。但当前两个图片客户端仍是文生图路径：Wanxiang 和 Seedream 都在收到 `referenceImages` 时返回 `unsupported`，导致洗稿配图只能按文本重画，视觉版式和原文参考图差异很大。

阿里云 Wan 2.7 官方接口已支持在 `messages.content` 中混合图片 URL 和文本指令，且支持多图参考生成。先把这个可验证路径接入，让运营可通过 `image_provider=dashscope` + `image_model=wan2.7-image` 或 `wan2.7-image-pro` 使用真实参考图生成。

## What Changes

- Wanxiang 客户端在收到可用 `referenceImages` 时，把参考图 URL 作为 `image` content 传给 DashScope Wan 2.7，并把文本 prompt 作为同一条 user message 的 `text` content。
- 参考图路径默认使用 `2K` 输出规格，使 Wan 2.7 在有图片输入时按最后一张参考图比例输出，减少文字长图/截图类参考图被强行方图化。
- 成功返回真实新图 URL 时标记 `referenceStatus='used'`、`referenceUsed=true`；缺 key、提交失败、轮询失败、超时或无 URL 时标记 `unavailable`，不伪造 used。
- Seedream 仍保持 `unsupported`，直到火山官方参考图参数形状经文档或线上探针确认。
- 增加 focused tests 锁定 Wanxiang 文生图零回归、参考图请求体和审计状态。

## Capabilities

### Modified Capabilities

- `publish-multi-image`: DashScope/Wanxiang 图片 provider 支持实际消费参考图，并将真实使用状态汇总到既有参考图审计。

## Impact

- aidcp-cloud: `WanxiangClient` 请求形状、参考图状态、单测。
- aidcp control repo: OpenSpec proposal/spec/tasks。
- Production: cloud 需要重启。若希望现网立即使用此能力，还需要把全局图片厂商切到 `dashscope` 并使用 Wan 2.7 image 模型；当前 `volcengine` 配置在火山参考图字段确认前仍会诚实显示 unsupported。
