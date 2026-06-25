# Tasks — edge-own-chrome-supervised-recycle

> 改动落 sub-repo(edge 为主 / cloud 仅回归测试),进度回写本仓。顺序遵循 design.md 迁移计划:**§1 看护杀进程模型修复(BLOCKER③)最先做**。
>
> 实装提交:edge `7b893cd`(核心:诚实下线/快判/杀进程确认/退出码/在途发布) + `a260588`(看护:杀进程模型/spawnNode/重起预算/测试,rebase 到已提交的 slot 模型 launcher);cloud `7af05da`(回归测试,零业务码)。验证全绿:edge full 360 + acceptance 11 + typecheck;cloud 回收回归 3 + 触及区 integration 11 + 该区 typecheck。
> **迁移说明**:并发会话已将 launcher 从「按账号」重写为「按 slot(node-<n> profile,账号登录读出)」并提交;本 change 的看护逻辑 rebase 到该 slot 模型之上(spec「复用同一登录目录」不依赖命名,仍成立;原 design 的 `<accountId>-<n>` 命名以实际 `node-<n>` 为准)。

## 1. aidcp-edge — 看护进程杀进程模型修复(BLOCKER③,前置)

- [x] 1.1 改 `scripts/launch-multinode.ts` 子进程拉起方式:直接 spawn tsx 执行体(去 npm/shell 外壳层)+ detached 自成进程组,停止/重起对整组发信号(`process.kill(-pid)`) <!-- edge a260588 -->
- [x] 1.2 验证停止路径:整组信号必达执行体 `main.ts` shutdown → 真杀其独占 Chrome(killAndConfirmDead) <!-- edge a260588 7b893cd -->
- [ ] 1.3 真机验:看护进程终止信号后零孤儿 edge / 零孤儿 Chrome(进程组级行为,**gated 真机**,单测覆盖不到)

## 2. aidcp-edge — 可重起单元与退出码契约

- [x] 2.1 抽出 `spawnNode(plan)`,按固定槽位(端口/目录/edgeId)决定参数,重起复用同一计划 <!-- edge a260588 -->
- [x] 2.2 `spawnNode` 内**冻结 env 快照**、保持删除复用开关;重起复用快照不重新展开活 env(防漂移) <!-- edge a260588 -->
- [x] 2.3 参数化 `main.ts` shutdown(exitCode):关机 0 / 回收非零(EXIT_RECYCLE=75);保留 shuttingDown 幂等卫 <!-- edge 7b893cd -->

## 3. aidcp-edge — 终态分类与诚实下线(BLOCKER① + 快判)

- [x] 3.1 进有界重连**之前**加终态快判(/json/version 进程级 + 页面 target):无可用 target 即立即放弃回收、不磨满重连 <!-- edge 7b893cd (client.ts classify + session.ts wiring), tested a260588 -->
- [x] 3.2 替换 `cdp.unrecoverable` 处理为「诚实下线 + 回收 + 退出」入口(autoBrowse 与否都接) <!-- edge 7b893cd -->
- [x] 3.3 诚实下线改异步:await 边-云连接 `close` 事件(有界~1.5s)再退,EdgeClient.closeAndWait <!-- edge 7b893cd -->
- [x] 3.4 测试:closeAndWait 等真关闭后才 resolve + 超时兜底 <!-- edge a260588 test/client/edge-client-closewait.test.ts -->

## 4. aidcp-edge — 回收前确认旧浏览器真死(BLOCKER②)

- [x] 4.1 ChromeInstance.killAndConfirmDead:杀后轮询端口探测到空再退;优雅 SIGTERM 超时升级 SIGKILL <!-- edge 7b893cd -->
- [x] 4.2 确认屏障置于仍活着的退出中进程内(不依赖已退出进程/不仅信 kill 返回) <!-- edge 7b893cd -->
- [x] 4.3 测试:SIGTERM 即释放→不升级;未释放→升级 SIGKILL 后确认;复用实例 no-op <!-- edge a260588 test/cdp/recycle-kill-confirm.test.ts -->

## 5. aidcp-edge — 看护重起预算 / 退避 / 诚实放弃(MAJOR⑥)

- [x] 5.1 重起决策收口纯函数 `respawn-policy.ts`:**连续失败计数**(非墙钟窗口)+ 指数退避;仅非零退出重起 <!-- edge a260588 src/supervise/respawn-policy.ts -->
- [x] 5.2 健康清零:节点重起后健康存活 ≥ min-uptime 才把连续失败计数清零 <!-- edge a260588 -->
- [x] 5.3 连续失败到上限 → 诚实放弃(日志 + 留下线,兄弟节点不受影响) <!-- edge a260588 -->
- [x] 5.4 收紧重起子进程登录等待(launcher 注入 ~45s,main.ts 读 AIDCP_CHROME_LOGIN_TIMEOUT_MS 接 launchChrome) <!-- edge 7b893cd a260588 -->
- [x] 5.5 新增 env 配置:RESPAWN_MAX / BACKOFF_BASE/MAX_MS / HEALTHY_UPTIME_MS / CHILD_LOGIN_TIMEOUT_MS(有缺省、缺失不 brick) <!-- edge a260588 -->

## 6. aidcp-edge — 回收 vs 真关机仲裁(MAJOR⑤)

- [x] 6.1 看护进程收到信号即置 shuttingDown,`child.on('exit')` 期间无条件抑制重起(决策纯函数 stop 分支) <!-- edge a260588 -->
- [x] 6.2 边缘 recycleRequested 标记,确保真终态即便信号撞入也以回收码退出 <!-- edge 7b893cd -->
- [x] 6.3 测试:重起策略 shuttingDown/清零/退避/放弃多时序(respawn-policy.test.ts 8 例) <!-- edge a260588 -->

## 7. aidcp-edge — 在途发布回收契约(MAJOR④,选项 A)

- [x] 7.1 回收前检测在途发布 → 诚实判失败上报(关 WS 之前发,按 publish.result / publish.command.result 各自形状) <!-- edge 7b893cd -->
- [x] 7.2 核实「提交」是发布链最后不可逆步:submit_publish 为最后一步(publish-post.ts:375 / publish-command-handlers.ts:209),之前不在平台留帖 <!-- edge 已核实 -->
- [x] 7.3 验证新进程握手后不自动重放:发布为定向手动命令、云端不自动重发;浏览侧复用既有「重连不重放半截动作」约束 <!-- 设计保证 -->

## 8. aidcp-edge — 复用模式 / 独占断言(隔离)

- [x] 8.1 终态按 chrome.reused 分支:复用模式只诚实下线+退出,不回收外部浏览器(killAndConfirmDead no-op) <!-- edge 7b893cd, tested a260588 -->
- [x] 8.2 回收路径独占判据:!chrome.reused 才杀+确认;复用即跳过(空操作不当成已回收) <!-- edge 7b893cd -->
- [x] 8.3 单机裸跑终态只诚实退出一次、无看护重起(行为一致;单机无 supervisor) <!-- edge 7b893cd -->

## 9. aidcp-edge — 测试与回归

- [x] 9.1 单测:终态快判分类 / 诚实下线时序 / 杀进程端口确认 / 重起预算+退避+诚实放弃(15 例全绿) <!-- edge a260588 -->
- [x] 9.2 `test:acceptance`(11 绿,含 AC-PUB) → 全量 `npm test`(360 绿) → `typecheck`(绿)全过 <!-- edge a260588 -->

## 10. aidcp-cloud — 回归测试守不变量(零业务码改动)

- [x] 10.1 回归测试:回收(断连)拆除运行时 + 同槽位重连干净起新 + 回收一节点不广播结束给兄弟(a38fb96) + 同 edgeId 顶替收敛单运行时(3 例绿) <!-- cloud 7af05da test/integration/recycle-reconnect.test.ts -->
- [x] 10.2 我的回归 3 绿 + 触及区 connection-runtime integration 11 绿 + 该区 typecheck 通过;**注**:cloud 全量 typecheck/test 当前被并发会话 publish-multi-image / model-provider WIP 半成品阻断(非本 change,我的区域干净) <!-- cloud 7af05da -->

## 11. aidcp(中控)— 校验与归档

- [x] 11.1 `openspec validate edge-own-chrome-supervised-recycle --strict` 通过
- [x] 11.2 sub-repo 任务标 `[x]` + commit-sha 回写(本节)
- [ ] 11.3 全部完成 → archive(delta 合并进 `openspec/specs/`)。**留待**:§1.3 真机零孤儿验证 gated;归档≠真机验证(参照债务台账惯例)
