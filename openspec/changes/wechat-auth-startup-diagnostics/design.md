## Context

视频号鉴权协调器已经拥有完整决策信息，但现有日志只覆盖浏览器最终打开/关闭，启动分支本身不可观测。日志需要在鉴权协调器内产生，避免桌面外壳根据浏览器进程结果反推原因。

## Decisions

### Stable trigger tags

鉴权协调器为浏览器授权入口传入有限枚举的触发标签。只有真正创建新的浏览器授权流程时打印 `browser authentication required`；已有授权流程在飞行中时打印 `already in progress`，避免重复日志声称重复启动。

启动期至少使用：

- `startup_stored_session_missing`
- `startup_stored_session_unavailable`
- `startup_stored_session_expired`
- `startup_challenge_required`

客户主动重新授权与运行时失效使用独立标签，避免把非启动期动作冒充成冷启动判定。

### Safe stage logs

本地会话只记录 `found` / `not found` / `unavailable`，身份与探针只记录结构化类别或既有原因码。日志不拼接异常原文、文件内容、身份值或任何会话材料。

### Preserve lifecycle semantics

本变更不改变任何状态迁移、恢复计时器、浏览器开关或能力门禁。临时失败仍调用原恢复逻辑；新增日志只在现有分支旁记录真实决策。

## Testing

通过注入日志收集器与假浏览器 sidecar，断言：有效会话不打开浏览器且记录 API-only；缺失/过期会话在打开前记录稳定原因；临时失败不打开浏览器且记录等待接口恢复；日志不包含合成测试凭据。
