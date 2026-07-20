## Context

Cloud 与 Edge 已通过既有 `publish.state = submitted` 表达“提交动作已被平台页面接受，但尚未取得公开 `postId/postUrl`”。Electron 的 `publishView` 也会为该状态生成一条活动记录，但随后复用终态回退逻辑，卡片本体继续显示旧 `lastPublish` 或空态，因此最新动作只在活动流中短暂可见。

首版只调整了 Edge Electron 的实时只读投影。实际新版客户端声明 `client_data_plane_automation_engine_v1` 后，Cloud 会从自动化 WebSocket 快照中剥离发布业务数据；客户端重启时必须通过 customer-auth HTTP 的环境 overview 恢复当前发布与最近已发布，否则本地 `ui-state.json` 只剩旧 `lastPublish`，仍会重现旧标题。

本变更因此把重启恢复纳入同一用户行为契约，但复用 `separate-client-data-plane-automation-engine` 已建立的 overview 数据面，不恢复 WebSocket 业务数据，也不改变发布执行、状态落库、协议枚举或平台确认规则。

## Goals / Non-Goals

**Goals:**

- 让 `submitted` 成为发布卡可见的独立状态，并优先显示本次稿件。
- 用“已提交、公开结果确认中”表达不确定性，禁止冒充 `published`。
- 保留既有活动流记录、旧 `lastPublish` 数据和收到 `published` 后的转换行为。
- 让新版客户端在登录、重启、切换环境及失效刷新后，从客户鉴权 HTTP 恢复相同的 `submitted` 真态。

**Non-Goals:**

- 不新增即时发布的 postId/postUrl 对账机制。
- 不把客户业务数据重新塞回自动化 WebSocket 或 cloud hello 快照。
- 不构建或发布 Electron 安装包。

## Decisions

1. **在 `publishView` 中先于历史态回退处理 `submitted`。** 返回独立 `mode: 'submitted'`，使用本次 `publish.title/code/at`，避免旧历史覆盖。相比改写 `lastPublish`，独立模式不会把未确认提交污染成已发布历史。
2. **提交确认态保持展开。** `publishDock` 对 `submitted` 与进行中 `flow` 一样返回展开，确保最新且仍未收敛的状态不会藏在旧历史薄条后面。
3. **第四节点保持 calm current，而不是 done。** 前三步已经完成，第四步表示公开结果仍待确认；文案使用“已提交，平台确认中”和“公开结果确认后会更新”，不出现“已发布”。
4. **继续生成 submitted 活动流记录。** 卡片承载当前状态，活动流保留发生过的提交事实；既有按环境签名去重不变。
5. **新版客户端重启恢复以环境 overview 为单一来源。** Electron main 只接收本地 `envId`，服务端按 customer token 与 `envKey` 解析持久绑定，响应只返回 `currentPublishState`、`lastPublished` 等显式 DTO，不接受或暴露 `accountId`。Renderer 在选中环境、聚焦、低频轮询和本地自动化结果失效时刷新；HTTP 首次结果到达前显示未知/读取中，不用旧本地历史冒充云端当前状态。
6. **`submitted` 与 `published` 分开投影。** Cloud 当前发布查询只从在途状态产生 `currentPublishState`，`lastPublished` 只查询 `status = published`；客户端同时收到二者时仍由当前 `submitted` 覆盖卡片主体，只有平台确认后的 `published` 才进入历史。

## Risks / Trade-offs

- [客户端重启后实时事件已丢失] → 新版客户端从环境级 customer-auth HTTP overview 恢复，WebSocket 仅负责自动化与触发失效刷新；聚焦测试覆盖旧历史与当前 submitted 同时存在。
- [“平台确认中”可能长期停留] → 这是数据库真实状态的直接呈现；在没有可靠对账前不设置虚假自动完成时间。
- [新增 mode 影响收展或样式] → 复用现有蓝色封面与 calm 当前节点，只对纯函数和 dock 分支做窄改，并以聚焦测试锁定。
- [HTTP 暂时不可用时展示陈旧数据] → 首次失败显示未知而非旧历史；已有成功 overview 则可保留并明确标注缓存，后台按有界频率重试。
