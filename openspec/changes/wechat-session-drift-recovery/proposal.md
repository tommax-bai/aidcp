## Why

视频号浏览器仍处于登录状态时，Edge 保存的 API Cookie / 请求上下文仍可能被平台轮换并失效。现场证据显示：加密会话曾连续同步成功，随后 `authData`、`postList` 与 `dmHistory` 同时返回 HTTP 200、平台业务码 `300334`（`request failed`）；浏览器中的两枚相关 Cookie 均已不同于加密快照。现有实现把该结果压成 `INTERACTION_UPSTREAM_UNAVAILABLE`，却不推进授权状态，也不重新采集浏览器会话，导致定时同步永久重复失败。

同时，Edge 客户端工作区首次读到 `login_required` 后会停止列表轮询。即使 Cloud 数秒后已经持久化 `active + browserState=closed`，界面仍永久显示旧的“等待登录 / 未回报”。

## What Changes

- 仅把已经通过真机证据确认的微信业务码 `300334` 识别为授权请求上下文失效，进入既有重新授权路径；其他未知平台拒绝保持原分类，避免扩大误判。
- 重新授权复用既有 AdsPower V2 sidecar：打开或接管原 profile、刷新页面、重新采集 Cookie 与请求上下文、校验身份和已启用只读能力，成功后重新加密落盘并回到 API-only 模式。
- 视频号工作区在可见且环境在线时持续低频刷新 Cloud 真态，不再因为当前状态不是 `active` 或读取开关关闭而永久停止收敛。
- `browserState=closed` 在非 active 状态下显示为“已关闭”；只有状态字段确实缺失时才显示“未回报”。
- 定时同步失败日志增加安全的 endpoint、HTTP 状态和平台业务码，不记录 Cookie、请求头、请求正文、平台响应正文或身份原文。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `wechat-channels-interaction`: 增加授权请求上下文漂移的精确恢复、客户工作区鉴权真态持续收敛，以及安全诊断字段契约。

## Impact

- Edge TypeScript runtime：错误分类、授权恢复和定时同步诊断日志。
- Edge Electron renderer：工作区轮询与浏览器状态文案。
- 不修改 Edge/Cloud 协议、Cloud 数据库、风险状态、写能力门禁或 AdsPower V2 接口。
- 不构建或发布安装包；代码验证在 Edge worktree 完成。
