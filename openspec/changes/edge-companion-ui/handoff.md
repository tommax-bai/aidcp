# edge-companion-ui 尾巴任务交接（接真数据）

> 交接日期 2026-07-03。前序会话已完成客户端界面全量改版并经用户六轮验收通过；本文档交接**剩余的「接真数据」部分**。
> 接手方式：`/impl edge-companion-ui`（或直接按本文档开工）。先读本文档，再读 `tasks.md`（§7 收口 + §8 云端回填）与 `design.md`（D2/D3 是本批的契约设计）。

## 0. 一句话背景

客户端（aidcp-edge Electron 壳）已是「陪伴式」新界面：叙述活动流 / 在场感 / 健康合成都已由真实事件驱动；**还差两根数据线**——①发布卡的进行中状态没有真实事件源（审批发生在云端，边缘看不到候审）；②标题带昵称与「上次发布」历史目前用本地兜底（AdsPower 环境名 + 本机记录），应改由云端下发真数据。

## 1. 当前状态（接手时先核对）

- edge master：`6b9d708`（2026-07-03，538 测试 + typecheck 绿）；worktree `../aidcp-edge.wt/edge-companion-ui` 仍在、与 master 同步。**master 被多条并行线频繁推进，动手前先 fetch。**
- 本 change 已完成 §1–§6 全部任务（见 tasks.md 勾选与 sha 注记）；未完成：**7.4（[ui-event] 发射点）、8.1（云端快照）、7.5（archive 收口）**。
- **前置条件**：并行 change `publish-edge-command-runtime`（2026-07-03 时点 43/56）**收口/归档后才能动发布链路文件**（判据：`openspec list` 不再列出它，或 `openspec/changes/archive/` 出现其归档目录）。未收口前绝不碰发布文件与协议热点。
- 安装包提醒：worktree `dist-electron/` 里的 mac dmg / win NSIS 是六轮修复**前**打的，分发前必须重打（`npm run electron:build:mac` / `:win`，mac 交叉打 win 免 wine）。
- Windows 真机验收项挂在 `docs/real-machine-acceptance-backlog.md` 簇 7。

## 2. 壳侧已就绪的契约（这边不用再改，照喂即可）

核心进程 stdout 打一行结构化日志即可直达界面（解析器 `aidcp-edge/src/electron/ui-events.cjs`，结构化优先于中文行映射）：

```
[ui-event] {"kind":"publish","publish":{"state":"pending","title":"笔记标题","code":"A-83"}}
[ui-event] {"kind":"identity","account":{"id":"<accountId>","name":"<小红书昵称>"}}
```

- `publish.state` 枚举：`pending / reminded / approved / published / rejected / failed`。
  - `pending`：发布卡展开、第三节点琥珀呼吸；`reminded` 仅在飞书**真的**再次提醒后发（红线：不发则界面只琥珀化时长、绝不谎称已提醒）。
  - `published`：卡片转「上次发布」态 + 折一条进活动流 + 计入今日小结；壳会把 `{title, at}` 落盘 `userData/ui-state.json`（云端快照到位后应以云端为准覆盖）。
  - `code` 可选：飞书审批卡当前**不显示** requestId，故界面编号显示「—」占位；云端若在卡片上印出编号，这里带 `code` 即自动点亮（灰底等宽小片已就绪）。
- `identity`：`name` 非空即视为真实小红书昵称（标题带带 @ 前缀、优先级高于 AdsPower 环境名兜底）；空 name 不要发（壳有环境名/尾4位兜底链）。
- 壳侧状态字段：`status.account {id,name,source:'xhs'|'env'}`、`status.publish`、`status.lastPublish`；渲染逻辑在 `renderer/ui-logic.js`（publishView 三态 + publishDock 收展），全部有单测锁定（`test/electron/ui-logic.test.ts`、`companion-ui.test.ts`）。

## 3. 任务 7.4：发布链路四节点插 [ui-event] 发射点

**关键认知（前序会话已坐实，tasks.md 1.1）**：生产发布是**命令式**路径——云端生成草稿→飞书审批→**审批通过后**才给边缘下发发布指令。所以：

- `published / failed`：边缘自己知道（发布指令执行结果处），可直接在边缘发布执行侧插发射点（`console.log('[ui-event] …')` 一行即可）。
- `pending / reminded / approved / rejected`：**只有云端知道**（审批不经过边缘）。必须由云端经协议告知边缘 → 与 8.1 是同一条通道，一起设计（见 §4）。
- 旧 v1 整页路径（`aidcp-edge/src/main.ts` 约 205–256 行的审批文件闸）只服务本地 mock/e2e，别在它身上花功夫。
- 发射点具体插哪：等 `publish-edge-command-runtime` 收口后看它落地后的发布执行文件（当前在 `src/flows/publish-command-handlers.ts` 一带，可能被它重构）。

## 4. 任务 8.1：云端快照下发（昵称 + 最近发布摘要）

**目标**：边缘连上云端后，云端把该账号的 {小红书昵称, 最近一次发布 {title, at}} 发下来；此后候审/批准/驳回状态变化也经同一通道通知。核心收到后转成 §2 的 `[ui-event]` 行打到 stdout 即达界面。

**数据源（云端都有）**：昵称在账号主数据（另有 change `nickname-capture-on-login` 做登录昵称捕获，真机回归挂 backlog 簇 1）；发布历史在云端 PG。

**设计建议（接手后先坐实再定）**：
1. 先查协议里边缘 `hello` 握手有没有云端回执消息——有则在回执载荷上加快照字段（改动最小）；没有则新增一条 cloud→edge 消息（如 `ui.snapshot` / `publish.status`）。
2. **协议四处同步纪律（CLAUDE.md §2，热点串行）**：两份 `src/comm/protocol.ts` 逐字一致 + `aidcp-cloud/src/comm/command-bridge.ts`（若走动作映射）+ `docs/protocol.md`（头部计数与 §2 表是人工维护的，别忘更新）。
3. **已知大坑（typecheck 抓不到）**：新增 cloud→edge **主动下发**消息，必须在 `aidcp-edge/src/client/edge-client.ts` 的 onMessage 主动命令路由白名单放行，否则消息被静默丢弃（前科：notification-monitor 6.5.1，云端已发、边缘无动作、看门狗杀会话）。
4. 云端顺手项（可选）：在飞书审批卡上印 requestId 尾 4 位（`aidcp-cloud/src/feishu/cards.ts` buildPublishApprovalCard 的 fields），边缘事件带 `code`，界面编号即点亮。

## 5. 验收标准（做完的定义）

1. 真实发布链路端到端走一遍：云端出草稿 → 客户端发布卡**自动**展开到「等你确认」→ 飞书通过 → 卡片转「择时发布」→ 发布落地 → 卡片收起为「上次发布 · 刚刚」、活动流记一条、今日小结计数 +0（发布不计入互动四计数）。
2. 清掉本机 `userData`（模拟新装机）再打开客户端：标题带显示**真实小红书昵称**、发布卡直接显示云端返回的上次发布。
3. 回归纪律：两仓 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（协议改动必须过 AC-PROTO-*）；edge 侧 `test/electron/` 全部单测不破。
4. 界面红线复核：端上零审批控件；`reminded` 只在真提醒后出现；无事件不造活跃。

## 6. 收口顺序（7.5）

7.4 + 8.1 完成 → 真机验一轮（含发布卡真数据流转）→ 重新打包 mac/win 安装包 → `openspec validate edge-companion-ui --strict` → archive（归档目录 `<日期>-edge-companion-ui/`）→ 删 worktree `../aidcp-edge.wt/edge-companion-ui` 与本地分支 → 把 backlog 簇 7 的 win 项留给真机批次。

## 7. 流程与纪律速查

- 开发在 worktree 分支、集成前 `git fetch && git rebase origin/master`、全绿后 ff 合回 master（本批六轮反馈期间 master 被并发方推进过 4 次，rebase 是常态）；push 遇 non-ff 绝不 force。
- 云端改动部署走 ECS 安全序列（CLAUDE.md §5）；edge 无 ECS 部署、合 master 即交付，分发靠重打包。
- 相关项目记忆：`edge-companion-ui-rollout`（冒烟注意/单实例锁/假核心技巧）。
