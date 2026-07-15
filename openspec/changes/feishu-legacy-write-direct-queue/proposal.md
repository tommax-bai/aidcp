## Why

`user-delegated-tasks` Phase 1 把所有 Feishu 写入口统一收口为「先出结构化确认卡 → 明确确认 → 入队」。这对**自然语言**委托是必要的：账号昵称、目标数量、截止时间、尝试上限都是从散文里**推断**出来的，确认卡是「我有没有把你的话理解对」的检查点。

但同一条规则也套到了**精确旧命令** `/publish <昵称>` / `/comment <昵称>` 上——这些命令里账号与目标已经显式给定、没有可推断的歧义，确认卡只是多加一次点击，没有挡住任何东西。运营反馈「审批卡都变成了委托卡」的直接体感就来自这里：精确命令本应直接排队，却被迫先点一次确认。

## What Changes

- 精确旧 slash 写命令（`source='legacy_command'` 的 `/publish`、`/comment`）在解析成功后**直接确认并入队**（`awaiting_confirmation → queued`），不再展示结构化确认卡；回执改为「已直接排队」的任务进度卡。
- 自然语言委托（`source='feishu'`）**保持不变**——因账号/数量/截止/尝试均为推断，仍先展示结构化确认卡，明确确认后才入队。
- 直接排队**不削弱下游人审**：`/publish`、`/comment` 单次任务保留 `review` 审批模式，逐篇内容/评论人审在任何平台写动作前仍然触发；昵称重名或找不到仍 fail-closed 拒绝、绝不静默改选。
- 幂等与去重不变：相同命令在同一去重窗口内重复触发仍归并到同一任务，`confirm` 幂等，不产生双任务或双发。
- 单次任务的既有人工额度语义保留，且 MUST NOT 被批量/异步任务继承（沿用 `manual-command-override` 约束）。

## Capabilities

### Modified Capabilities

- `feishu-command-ingestion`: 旧 slash 写命令由「先确认卡」改为「直接排队」；确认卡要求收窄到自然语言 / Edge / console 等**推断型**入口。

## Impact

- `aidcp-cloud`: `DelegatedTaskService.createFromText` 对 `legacy_command` 自动确认入队并返回 `autoQueued`；server `delegate` 出口按 `autoQueued` 选卡（进度卡 vs 确认卡）。新增单测；无迁移、无协议改动、不碰热点文件（协议 / 风控状态机 / 角色注册）。
- `aidcp`: 本 change 的 proposal / spec delta / tasks。
- 部署：仅 cloud `dev`；不涉及 Edge 安装包、console、OL。
