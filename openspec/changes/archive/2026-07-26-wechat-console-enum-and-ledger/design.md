## Context

Cloud 已把 `wechat_channels` 作为账号与客户环境的稳定平台 ID，并且 `GET /api/accounts/:accountId/reply-config/audit` 已实现 limit、HMAC opaque cursor、按账号过滤和 `nextCursor`。Console 的账号列表已认识视频号，但客户环境归属页的展示元数据和手动登记下拉仍只有小红书/Facebook；回复设置组件也只保存 audit 首屏 `items`，没有保存 `nextCursor`。

本 change 只补 Console 消费端。Cloud API、数据库、权限和审计保留策略不需要改动。实现必须延续现有账号切换 AbortController 防串号模式，并保留枚举漂移时“不白屏、不伪造中文含义”的既有准则。

## Goals / Non-Goals

**Goals:**

- 让运营在客户环境归属页正常选择和识别 `wechat_channels`。
- 把已有审计 cursor 消费成可逐页追加、可重试、有明确到底状态的台账。
- 切换账号、关闭抽屉或刷新首屏时，中止旧账号的追加请求。
- 未知未来 audit action/entity 继续显示原始 wire 值，而不是空标签或整页崩溃。

**Non-Goals:**

- 不新增或修改 Cloud API、数据库表、审计事件、权限 grant 与保留周期。
- 不把 `wechat_channels` 加入 delegated-task 支持范围；该平台当前仍不支持旧的主动浏览/互动委托动作。
- 不自动预取所有审计页，不执行任何视频号真实读写或 Edge 打包。

## Decisions

### 1. 平台候选仍由 Console 显式维护，并保留未知值回落

在客户环境页的共享平台元数据中加入 `wechat_channels -> 视频号`，手动登记下拉复用同一组已知候选。现有 registry DTO 的 `platform: string | null` 不收窄为封闭联合，因为 Cloud 或未来平台可能先扩值；未知历史值仍显示原始值。

未选择从账号接口动态推导候选，因为客户环境可能尚未绑定 account，账号集合不是平台目录；也不为这一项新开 Cloud 枚举 API。

### 2. 审计使用显式“加载更多”，不自动拉完整历史

`loadReplyAudit` 接受可选 cursor 并原样 URL 编码。组件保存 `auditNextCursor`，首次读取替换列表，点击“加载更多”才追加下一页。追加按 `eventId` 去重，以防服务端重放边界或重复点击；`nextCursor=null` 时显示已到底真态。

未选择无限滚动或自动循环拉取，因为审计历史可增长到保留期上限，自动拉全既浪费请求也会增加后台页面渲染成本。

### 3. 首屏与追加分页分别管理请求生命周期

账号聚合读取继续使用现有主 AbortController；分页追加使用独立 controller。账号切换、抽屉关闭、重新加载首屏和写后刷新都会中止追加请求并清空 cursor/page error。每次回包落 state 前同时核对 active account 与 abort 状态，旧账号结果不得追加。

分页失败只在现有记录下方显示“后续审计加载失败”和重试入口，不把已成功加载的台账替换成整页错误；首屏失败仍沿用独立 permission/error 状态。

### 4. Wire 枚举按开放字符串读取，已知值只负责中文映射

Audit DTO 的 action/entity 接收字符串；已知 action 映射为中文，未知 action/entity 直接显示原值。这样 Cloud 先增加事件类型时，旧 Console 不会显示空动作或因穷举映射抛错，同时也不猜测未知值含义。

## Risks / Trade-offs

- [Risk] Console 本地平台候选未来再次落后于 Cloud。 -> 保留 string DTO 与原值回落，并用测试锁住视频号候选；本 change 不把未知值变成拒绝。
- [Risk] 写后刷新与正在进行的分页追加交错，旧页覆盖新首屏。 -> 刷新前中止分页 controller，首屏回包替换 items/cursor，分页回包做 account + abort 双校验。
- [Risk] 多页存在重复 event。 -> 追加时按稳定 `eventId` 去重，保持服务端顺序，不基于摘要或时间猜测同一事件。
- [Trade-off] 操作员需手动点击加载更多。 -> 以明确的页级控制换取有界请求与渲染成本，并显示是否还有后续记录。

## Migration Plan

1. 在隔离 Console worktree 完成平台候选、分页 API/状态与 focused tests。
2. 运行相关 Vitest、Console 全量测试、typecheck/build；严格验证 OpenSpec。
3. 通过 fast-forward 流程集成 Console 与 control 默认分支并推送。
4. 按部署规范只发布 Console 到 `dev`，验证客户环境下拉和 mock/已有审计的分页 UI；不触发视频号真实发送。
5. 回滚时恢复上一版 Console 静态资源即可；Cloud 无迁移、无回滚动作。

## Open Questions

无。Cloud 的 cursor、权限与保留策略已经存在且不在本 change 内调整。
