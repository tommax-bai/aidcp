## Context

当前内容排期配置由 `account_content_schedule` 承载：`auto_enabled` 是账号级总闸，`post_enabled`、`comment_enabled`、`contact_comment_enabled` 是动作布尔开关。调度器按动作布尔值触发；发帖落 `pending_approval` 后由飞书审批信号触发 `PublishDispatcher`；评论链在撰写后通过 `CommentApprovalPort` 发审批卡并轮询同一类 `/tmp` 授权信号。

这意味着「免审」不能只把飞书审批卡换成通知卡。发帖若没有授权信号会卡在 `pending_approval`；评论若不调整审批入口会在 90s 后跳过。实现必须把免审建模为“后台预授权”，保留授权痕迹和通知。

## Goals / Non-Goals

**Goals:**
- 让后台对发帖、评论、联系评论分别选择 `off / review / auto_approve`。
- 让 `auto_approve` 模式自动写入或等价产生授权结果，并向飞书发普通通知卡。
- 保持既有安全闸：账号总闸、内容时段、浏览活跃时段、风控状态、日上限、配额、单飞、去重、联系方式、边端在线、发布 dispatcher 复核。
- 兼容现有 boolean 数据和旧前端请求，降低部署窗口风险。

**Non-Goals:**
- 不改变手动 `/publish`、`/comment`、精选页手动评论入口的审批语义。
- 不增加 edge 协议或桌面端能力。
- 不解决评论目标命中率、媒体上传、配图应用等既有后续问题。

## Decisions

1. **新增 mode 列，保留 boolean 兼容列。**
   - 选择：新增 `post_mode/comment_mode/contact_comment_mode`，取值 `off|review|auto_approve`；读取时 mode 优先，缺失时从旧 boolean 推导（true→`review`，false→`off`）。写 mode 时同步旧 boolean 为 `mode !== 'off'`。
   - 原因：Postgres 直接把 boolean 列改 enum/text 会破坏旧代码和回滚；并行列可自愈迁移、可灰度部署。
   - 备选：原列类型原地改为 text。放弃，因为回滚和旧版本兼容差。

2. **发帖免审通过自动写审批信号触发现有 dispatcher。**
   - 选择：PublishExecutor 落 `pending_approval` 后，如果触发上下文携带 `approvalMode='auto_approve'`，自动写 `approved=true` 信号，带当前 `contentVersion`，再调用与飞书按钮同源的 dispatch trigger，并发送通知卡。
   - 原因：保留 AC-PUB 第二闸、版本闸、离线回待审、lease、发布结果写回等既有行为。
   - 备选：新增直接 publish 方法。放弃，因为会复制并绕过 dispatcher 的多道兜底。

3. **评论免审在审批口层短路，不绕过提交链路。**
   - 选择：`triggerManual/triggerTargeted` 接收 `approvalMode`，传入 `compose-approve` 与 Facebook 审批入口；`auto_approve` 时发送通知并直接返回 approved。
   - 原因：撰写、去 AI、目标读取、commit lease、提交验证仍照旧；只替换“等待人点按钮”。
   - 备选：不注入 approval port。放弃，因为现有代码会按未接线 fail-closed。

4. **飞书通知使用普通结果卡，不带审批按钮。**
   - 选择：复用/扩展 `buildCommandResultCard` 或新增轻量 notification card，文案明确“后台免审配置已预授权”。
   - 原因：避免用户误以为还需要操作，也避免按钮回调重复写信号。

## Risks / Trade-offs

- [Risk] 免审语义被误读成绕过所有风控。→ 文案、规格和代码命名统一为 `auto_approve` / 后台预授权，且只跳过飞书等待。
- [Risk] 旧 boolean 与新 mode 双写漂移。→ store 单写，所有 API patch 都经同一 store；mode 写入同步 boolean，读取 mode 优先。
- [Risk] 发布免审自动授权后边缘离线。→ 沿用 dispatcher 现有离线处理：作废信号、保留待审、通知重批。
- [Risk] 热帖自动联系评论被遗漏。→ `contactCommentMode` 成为浏览 detector 与排期联系评论共同真源。
- [Risk] 回滚到旧代码后 mode 列存在但旧代码只读 boolean。→ 新写入同步 boolean，旧代码仍能把 `review/auto_approve` 视作开启。

## Migration Plan

1. Cloud 启动自愈新增三列与 CHECK 约束，默认从旧 boolean 推导。
2. API 同时接受旧 boolean patch 和新 mode patch；旧 boolean 请求映射为 `review/off`，便于前后端分步部署。
3. Console 上线后只写 mode 字段，读取时展示 mode；若服务端缺 mode，可从 boolean 兼容显示。
4. 部署 `dev` 后验证旧数据读取、三档写入、免审发帖自动 dispatch、免审评论通知与现有审批模式回归。
