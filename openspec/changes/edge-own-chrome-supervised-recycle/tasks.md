# Tasks — edge-own-chrome-supervised-recycle

> 改动落 sub-repo(edge 为主 / cloud 仅回归测试),进度回写本仓。顺序遵循 design.md 迁移计划:**§1 看护杀进程模型修复(BLOCKER③)最先做**。

## 1. aidcp-edge — 看护进程杀进程模型修复(BLOCKER③,前置)

- [ ] 1.1 改 `scripts/launch-multinode.ts` 子进程拉起方式:去掉 npm/shell 外壳层(直跑 tsx)或改进程组负 PID 信号,使停止/重起信号真正送达执行体而非只停在 `/bin/sh`(`launch-multinode.ts:97-102`)
- [ ] 1.2 验证停止路径:看护进程 SIGINT/SIGTERM → 各子节点 `main.ts` shutdown 真正运行 → 真杀其独占 Chrome(`launch-multinode.ts:110-116`)
- [ ] 1.3 加测试 / 手验:看护进程收到终止信号后 **零孤儿 edge 进程、零孤儿 Chrome 进程**,各节点调试端口与登录锁均释放(ps + 端口探测)

## 2. aidcp-edge — 可重起单元与退出码契约

- [ ] 2.1 从 `launch-multinode.ts:79-108` 抽出 `spawnNode(spec, i)`,按**固定 index i** 决定端口/登录目录/edgeId/accountId(重起复用同一槽位,勿用漂移的循环下标)
- [ ] 2.2 在 `spawnNode` 内**快照冻结**每节点 env、并保持删除复用开关;重起时复用该快照,勿重新展开看护进程活动 env(防复用开关漂移泄漏,D10)
- [ ] 2.3 参数化 `main.ts` shutdown(exitCode):真关机(SIGINT/SIGTERM)退 0=不重起;回收(终态)退非零=请重起(`main.ts:328-342`);保留 `shuttingDown` 幂等卫

## 3. aidcp-edge — 终态分类与诚实下线(BLOCKER① + 快判)

- [ ] 3.1 在 page-WS 断连**进入有界重连之前**加浏览器进程级探测(GET /json/version)做终态快判:端口拒连=进程级终态→立即回收;探测通但页面 target 持续归零=终态→立即回收;否则走既有有界重连(D3,`client.ts:248-283` / `chrome-launcher.ts:159-171`)
- [ ] 3.2 替换 `main.ts:316-319` 的 `cdp.unrecoverable` 处理:保留 `supervisor.stopAll()`,改为「诚实下线 + 回收 + 退出」入口
- [ ] 3.3 诚实下线改异步:**await 边-云连接 `close` 事件(带 ~1-2s 上限)再 `process.exit`**,勿同步立即退出(BLOCKER①);`EdgeClient.close()` 返回可 await 的 Promise(`edge-client.ts:276-279`)
- [ ] 3.4 加测试:终态时云端侧观察到的是**干净关闭(非超时/RST)**,掉线清理即时生效

## 4. aidcp-edge — 回收前确认旧浏览器真死(BLOCKER②)

- [ ] 4.1 回收路径退出前:真杀本进程独占的 Chrome 后,**轮询调试端口探测到空**再退;优雅终止超时则升级 SIGKILL(D5,`chrome-launcher.ts:690-703`)
- [ ] 4.2 确认屏障置于**仍活着的旧进程**内(勿依赖已退出进程或仅信 kill 返回值)
- [ ] 4.3 加测试:端口/登录锁未释放时不退出(防新进程被 `clearStaleSingletonLock` 诚实拒启致烧光预算,`chrome-launcher.ts:239-244`)

## 5. aidcp-edge — 看护重起预算 / 退避 / 诚实放弃(MAJOR⑥)

- [ ] 5.1 `launch-multinode.ts:104-106` 改 log-only 为有界重起:**连续失败计数**(非墙钟滑动窗口)+ 指数退避;仅非零/异常退出重起,clean SIGINT/SIGTERM 不重起
- [ ] 5.2 健康清零:节点重起后进入 ACTIVE 并健康存活 ≥ min-uptime 才把连续失败计数清零
- [ ] 5.3 连续失败到上限 → **诚实放弃**:打可识别「已放弃」日志、留节点下线、不无限重起、兄弟节点不受影响
- [ ] 5.4 收紧重起子进程登录等待到 ~30-60s(headless 无 TTY,登录态应秒级命中,否则按崩溃快速计入预算,`chrome-launcher.ts:497-532`)
- [ ] 5.5 新增 env 配置:`AIDCP_EDGE_RESPAWN_MAX` / `_BACKOFF_BASE_MS` / `_MAX_MS` / 健康清零 min-uptime / 重起登录等待上限(读取有缺省、缺失不 brick)

## 6. aidcp-edge — 回收 vs 真关机仲裁(MAJOR⑤)

- [ ] 6.1 看护进程收到 SIGINT/SIGTERM 即置「正在关机」,`child.on('exit')` 期间**无条件抑制重起**(任意退出码,关机优先)
- [ ] 6.2 边缘侧用 `recycleRequested` 标记,确保真终态即便终止信号撞入也以请重起码退出(勿被掩成 clean exit)
- [ ] 6.3 加测试覆盖两种时序:关机先到(不误重起)/ 回收先到(不被掩成 clean exit)

## 7. aidcp-edge — 在途发布回收契约(MAJOR④,选项 A)

- [ ] 7.1 回收路径检测在途发布:若有未提交的发布在执行中,先把该次发布**诚实判失败**上报再退(让审批/通知侧看到失败而非半成品)
- [ ] 7.2 确认/坐实「提交」是发布链最后一个不可逆动作,使回收发生在提交前不留半张帖
- [ ] 7.3 验证新进程握手后 **MUST NOT 自动重放**断连前的在途发布 / 互动命令(复用既有「重连不重放半截动作」约束)

## 8. aidcp-edge — 复用模式 / 独占断言(隔离)

- [ ] 8.1 终态处理按「是否复用」分支:复用外部浏览器模式只**诚实下线 + 退出**,不尝试回收本进程不拥有的浏览器(`chrome-launcher.ts:593-618` 复用分支 kill 为空操作)
- [ ] 8.2 回收能力节点断言本进程**自启并独占**浏览器;检测到复用开关泄漏到独占节点即拒回收并诚实失败(勿把空操作终止当成已回收)
- [ ] 8.3 验证单机裸跑 `npm start` 终态只诚实退出一次、无看护重起(行为与多节点一致)

## 9. aidcp-edge — 测试与回归

- [ ] 9.1 单测:终态快判分类(端口死 vs 页面归零 vs 可重连)/ 诚实下线时序(等关闭再退)/ 回收前端口释放确认 / 看护重起预算+退避+诚实放弃 / 多节点回收隔离(回收 i 不碰 j)
- [ ] 9.2 `npm run test:acceptance`(安全红线优先)→ 全量 `npm test` → `npm run typecheck` 全过

## 10. aidcp-cloud — 回归测试守不变量(零业务码改动)

- [ ] 10.1 加回归测试:高频回收下同 edgeId 快速重连 → 干净掉线 teardown + 新握手 restartSession,**只活一个会话运行时**、`resolveEdgeIdForAccount` 解析到新连接、**不广播 session.end**(守 a38fb96 不变量,`ws-server.ts` / `role-dispatcher.ts` / `connection-runtime.ts`)
- [ ] 10.2 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck` 全过(确认零业务码改动不破现状)

## 11. aidcp(中控)— 校验与归档

- [ ] 11.1 `openspec validate edge-own-chrome-supervised-recycle --strict` 通过
- [ ] 11.2 sub-repo 任务全绿后,按 HTML 注释标 `[x]` 并记 commit-sha / 偏离说明
- [ ] 11.3 全部完成 → archive(delta 合并进 `openspec/specs/`)
