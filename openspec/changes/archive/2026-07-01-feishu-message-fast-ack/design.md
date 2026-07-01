## Context

飞书消息入口（`aidcp-cloud/src/feishu/ws-receiver.ts`，官方 `@larksuiteoapi/node-sdk` WSClient 长连接）当前把「事件回执」耦合在「命令执行完成」上：`im.message.receive_v1` 处理器 `await this.handleMessage(...)`，而 `handleMessage` 内 `await commandRouter.handle(...)` 一路 await 到发帖编排完成。SDK 是在处理器 promise resolve 之后才向飞书回帧的，于是 `/publish`（实测约 3 分钟）会让回帧迟到，飞书判超时未送达、约 20 秒后重推同一条消息，命令被执行两次。第二次撞并发闸 `status==='running'` 弹出误导性「发帖未产出」卡。

约束：
- 边轻云重、honest-status 红线（不静默假成功、不把触发染成已发布）不得破坏。
- 发帖编排并发闸是既有的、进程内全局的重复执行防线，保留。
- 只改 cloud 入口接线，不碰协议、不碰 edge、不碰同机 isales，无 DB 变更。

## Goals / Non-Goals

**Goals:**
- 事件回执与命令执行解耦：受理即回帧（fast-ack），消除「长耗时命令→超时重推→重复执行」这条根因。
- 命令终态卡（含审批卡）异步照发，措辞/配色/时序内容不变，honest-status 判级不动。
- 改动面最小、可回滚，落点单一文件。

**Non-Goals:**
- 不新增「任务启动中／已触发」中间卡。
- 不新增 `message_id`/`event_id` 显式去重（留待后续按需）。
- 不改发帖编排并发闸、不改 honest-status 判级逻辑、不改命令语义。
- 不追求「恰好一次」的强保证（见 Risks）。

## Decisions

**决策 1：fast-ack 用「fire-and-forget 后台执行」实现，而非线程/队列。**
在 `handleMessage` 内把「命令执行 + 结果卡发送」从 `await` 改为不阻塞返回的后台 promise（`.then()` 发终态卡、`.catch()` 记日志），处理器随即 return → SDK 回帧 → 飞书不再超时重推。表情回应本就是 `void addReaction`（不 await），保持不变。
- 备选：给 SDK 手动提前回帧——SDK 未暴露稳定的「先 ack 后处理」API，侵入性大且脆弱，弃。
- 备选：把 `/publish` 丢进持久化任务队列——引入新组件/存储，远超本次范围（YAGNI），弃。

**决策 2：入口对所有命令统一 fire-and-forget，不区分快/慢命令。**
统一路径最简、无分支判断；快命令只是结果卡晚一个事件循环发送，无可感知回退。避免维护「哪些命令算慢」的名单。

**决策 3：不发启动中间卡。**
用户明确只要 fast-ack。终态卡与审批卡已能表达结果；`/publish` 的审批卡本就是异步补发，用户体验闭环完整。少一张卡少一次打扰。

**决策 4：不加显式去重，靠既有并发闸兜底。**
fast-ack 已消除超时重推这一主因；残余的重连 replay 重推由并发闸挡住真正的重复发帖。入口层不引入 SeenSet，避免为低频场景增设状态与其 TTL/内存管理复杂度。

## Risks / Trade-offs

- [长连接**重连 replay** 仍可能重推同一事件] → 并发闸 `status==='running'` 拦截，绝不产出第二篇帖子；最坏仅再弹一张 ⚠️ 卡（无害、非静默假成功）。后续若该噪声可感，再按需加 `message_id` 去重（已在 spec 明确本次不做）。
- [fast-ack 后，后台流水线若随进程崩溃中断，该次 `/publish` 会静默丢失]（飞书已收到回执、不再重推）→ 手动 `/publish` 可直接重发；已授权待审有 `scanAndDispatchApproved` 兜底补下发。取舍：从「宁可重跑」变为「宁可丢一次」，对手动命令可接受。
- [结果卡从阻塞发改异步发，理论上多条并发命令的卡序可能与到达序不同] → 各命令卡自带指令与账号上下文，语义自洽，不依赖顺序；实际手动命令低频，影响可忽略。
- [后台 promise 未被 await，异常若不接住会成 unhandledRejection] → 强制 `.catch()` 记日志兜住，杜绝外溢。

## Migration Plan

1. 单文件改 `ws-receiver.ts`，配套单测（受理即返回不阻塞、终态卡仍发、异常被 catch）。
2. `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（安全红线 AC-PUB/AC-RISK/AC-PROTO 不受影响，须仍绿）。
3. 部署走标准安全序列（ECS 先备份 → rsync 排除 .env/node_modules/.git → restart → healthcheck：active + 8787 监听 + 飞书长连接已建立 + PG select 1），失败即回滚；绝不碰同机 isales。
4. 回滚：还原备份包 + 重启即恢复阻塞式旧行为，无 DB/协议迁移需回退。

## Open Questions

- 无。（去重是否要做已明确为「本次不做、留待后续按需」。）
