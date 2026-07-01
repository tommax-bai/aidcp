## Why

飞书消息入口在处理一条命令时会一路 `await` 到命令执行完成才回执长连接事件——对 `/publish` 这类要跑完整条发帖生成流水线的命令（实测约 3 分钟），处理器长时间不回帧，飞书判「超时未送达」并在约 20 秒后**重推同一条消息**，导致同一条 `/publish` 被执行两次：第二次撞上发帖编排并发闸（`status==='running'`），弹出误导性的「⚠️ 发帖未产出／已有一轮在运行中」卡。ECS 日志已坐实这条链（首次触发→+20s 重推→并发闸拦截→首轮 3 分钟后正常完成，全程无重连日志，是纯 ack 超时重推）。根因是「事件回执」被「命令执行」阻塞。

## What Changes

- 飞书消息事件（`im.message.receive_v1`）处理器改为**受理即返回（fast-ack）**：立即返回以触发 SDK 回帧，飞书不再因超时重推。
- 命令执行与结果卡发送**改为后台 fire-and-forget**（异步 `.then()`/`.catch()`），不再阻塞事件回执。
- 命令**终态卡照旧发送**（「已触发发帖编排／发帖未产出／失败」及审批卡），措辞与配色一字不改——只是从「阻塞后发」变为「异步发」。honest-status 判级逻辑不变（据真实编排终态判 ok/level）。
- **不新增**「任务启动中／已触发」中间卡。
- **不新增** `message_id`/`event_id` 显式去重（本次仅治根，去重留待后续按需）。
- 发帖编排并发闸（`status==='running'`）**保留**为重复执行的最终兜底，绝不重复发帖。

## Capabilities

### New Capabilities
- `feishu-command-ingestion`: 飞书命令消息的受理契约——事件回执与命令执行解耦（fast-ack 不阻塞于命令执行），据此消除「长耗时命令→超时重推→重复执行」；命令结果异步回卡，honest-status 不变；重复执行由既有并发闸兜底。

### Modified Capabilities
<!-- 无：honest-status 回执判级、发帖编排并发闸、发布管线各 spec 的 REQUIREMENT 均不变，本次只改「入口何时回执」的接线，属新增受理契约。 -->

## Impact

- 代码：`aidcp-cloud/src/feishu/ws-receiver.ts`（`im.message.receive_v1` 处理器接线；`handleMessage` 内命令执行→回卡改异步）。
- 行为：飞书对长耗时命令不再超时重推；用户不再收到由重推引发的误导性「发帖未产出」卡；终态卡/审批卡时序与内容不变。
- 已知残留（见 design 权衡）：① 长连接**重连 replay** 仍可能重推，但并发闸挡住真正重复发帖，最坏仅再弹一张 ⚠️ 卡；② fast-ack 后若后台流水线随进程崩溃中断，该次 `/publish` 会静默丢失（手动可重发；已授权待审有 `scanAndDispatchApproved` 兜底）。
- 无 DB / 协议 / 部署形态变更；不碰 edge、不碰同机 isales。
