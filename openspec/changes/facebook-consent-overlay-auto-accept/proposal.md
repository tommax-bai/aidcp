## Why

Facebook 接入后首次打开页面（或清 cookie / 新建环境后）会弹出「允许 Facebook 使用 Cookie」的页面内 DOM 同意浮层，而边缘的 Facebook 专属浮层分类器只认 `captcha / login / unknown / none` 四类、**没有「同意条」这一类**。每次 Facebook 定向评论 / 加群提交前都会跑浮层探针，**浮层 ≠ `none` 就直接中止动作**：同意条正文含「登录 Facebook」字样可能被误判成 `login` → 动作被误报「需要登录」而中止（账号其实已登录）；即便判 `none`，模态仍盖在页面上挡住点击 → 动作落空报 `no_target`。结果是**每次新建环境 / 清 cookie 后，Facebook 评论 / 加群必然卡住**。这是一个每个真人首次访问都会顺手点掉、但当前系统既不识别也不清理的合规浮层。

## What Changes

- **新增 Facebook 同意浮层识别**：在边缘 Facebook 浮层分类器中新增一类 `consent`，靠**稳定的人类可读语义锚点**识别（cookie 政策标题 + 「允许所有 Cookie / Allow all cookies / 仅允许必要 Cookie」等按钮 aria/文案），不锁 Facebook 的哈希 class。
- **修正判定优先级**：`captcha` > 真登录门（URL 命中 `/login`、`/checkpoint`、`/recover`）> `consent`，确保同意条正文里的「登录 Facebook」字样不再把它误判成登录门；真登录门（无 cookie 接受按钮、命中登录 URL）仍优先胜出。
- **新增边缘本地自动接受动作**：在 Facebook 评论 / 加群动作前，若探针判为 `consent`，以**拟人点击**（复用现有拟人点击基建）点「允许所有 Cookie」；默认 accept-all，提供 env 开关切换 necessary-only。
- **后置校验 + 诚实回执**：点击后复探确认横幅已消失、页面可交互；未清掉或找不到接受按钮则如实回报（`no_target` / `blocked_by_consent`），**绝不静默假成功**；有界重试，连续清不掉到上限则升级上报、不空转。
- **红线约束（非目标）**：只自动点被识别的同意条，**绝不做「关闭任意模态」**——避免点穿真 `/checkpoint`、验证码。不引入云端 LLM、不新增云端角色、不新增协议消息类型。

## Capabilities

### New Capabilities
- `facebook-consent-overlay`: Facebook 页面内 cookie 同意浮层的识别（新增 `consent` 浮层类别 + 判定优先级）、边缘本地拟人自动接受、点击后后置校验与诚实失败回执、有界重试，以及「绝不误点真门 / 验证码」的准入不变量。

### Modified Capabilities
<!-- None. 刻意不改 captcha-incident-handling（同意条明确在验证码远程协助射程之外）、不改 platform-runtime-abstraction（驱动接口不变）。 -->

## Impact

- **代码（仅 aidcp-edge）**：`../aidcp-edge/src/facebook/overlay.ts`（新增 `consent` 分类与优先级）、`../aidcp-edge/src/facebook/probes/gated-submit.ts` 与 `../aidcp-edge/src/facebook/join-executor.ts`（动作前 pre-clear 一步 + 回执原因）、复用 `../aidcp-edge/src/browse/captcha-assist.ts` 的拟人点击、可能触及 `../aidcp-edge/src/facebook/comment-executor.ts`。
- **协议**：不新增 / 不修改边云消息类型（edge 本地清理，无需云→边命令）；不动两份 `protocol.ts`、不动 `command-bridge.ts` 动作映射。
- **云端**：不改；不加角色、不接线 `RiskController`。可选：沿用现有边→云状态 / 遥测通道记一笔「已自动接受同意」，但**绝不作为 blocking 浮层上报、绝不路由到验证码协助、绝不暂停会话**。
- **配置**：新增一个 env 开关控制 accept-all vs necessary-only（默认 accept-all）。
- **部署**：edge 客户端本地代码改动，**无 ECS 部署**；cookie 接受写入 AdsPower 持久 profile，通常一个环境只需处理一次。
- **测试**：新增分类器单测（同意条 → `consent`；真登录门仍 `login`；验证码仍 `captcha`；含「登录 Facebook」字样的同意条不误判）+ 自动接受动作的后置校验 / 诚实失败 / 有界重试单测（jsdom 桩，脱离浏览器）。
