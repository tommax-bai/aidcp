## Why

延续「委托任务确认卡对精确输入是过度设计」的收口。管理后台的洗稿 / 定向评论、候选稿批准 / 驳回 / 修改，以及 Edge 快捷入口，点一下就是明确指令——账号、目标、动作都已在 UI 里选定，却还要再弹一张「请确认用户委托任务」卡做二次确认。确认卡只对**推断型**输入（自然语言：账号 / 数量 / 截止 / 尝试靠解析猜）有价值；对结构化精确入口纯属多一次点击。

## What Changes

- `DelegatedTaskService.createDraft`：`source !== 'feishu'` 的任务在创建后**直接确认入队**（`awaiting_confirmation → queued`）并返回 `autoQueued`，不再返回待确认态。自然语言（`source=feishu`）不变，仍先创建 `awaiting_confirmation` 并展示确认摘要。`createFromText` 相应简化（旧 slash 命令的直接排队由此统一决定）。
- console 移除 `CuratedContentPage`（洗稿 / 定向评论）与 `ContentPage`（候选稿批准 / 驳回 / 修改、待审删图）的「请确认用户委托任务」Modal 及其 `confirmTask` 二次确认；动作直接入队 + 成功 toast。保留各自的操作 Popconfirm / 参考模式与评论选项弹窗（那是选项 / 单次操作确认，不是委托二次确认）。
- Edge 快捷入口：结构化精确入口直接入队、不再弹确认卡。
- 人审（下游内容 / 评论审批）、幂等去重、CAS 版本校验、账号平台事实校验、昵称 fail-closed 均不变。

## Capabilities

### Modified Capabilities

- `user-delegated-tasks`: 结构化确认卡要求收窄到自然语言入口；结构化精确入口（console 行级动作 / Edge 快捷入口 / api / 旧 slash 命令）直接入队。

## Impact

- `aidcp-cloud`: `createDraft` 加 source 分流 + `autoQueued`；`createFromText` 简化；相关单测改写。不碰热点文件。
- `aidcp-console`: `CuratedContentPage` / `ContentPage` 移除确认 Modal + `pendingTask`/`confirmTask` + 测试改写；「生成确认」按钮文案改为诚实动作名。
- `aidcp-edge`: `renderer.js` 的 `draftDelegatedTask` 增直接入队分支（源码改动；按长期约定不打安装包）。
- 部署：cloud 与 console 的 `dev`；edge 仅源码合入 master（不打包）。
