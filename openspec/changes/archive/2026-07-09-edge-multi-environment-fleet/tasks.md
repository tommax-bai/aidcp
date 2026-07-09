# Tasks — edge-multi-environment-fleet

> 全部落 `aidcp-edge`。核心 `src/main.ts` 及定位/浏览/发布/看门狗栈逐字复用、不改。云端与 console 本 change 零改动。
> 热点文件单写者纪律：改 `main.cjs` 进程/状态/设置层、`preload.cjs`、renderer 时标记需串行、勿与他人并行撞车。
> **实装 sha**：aidcp-edge master `c6292d8`（rebase 合并含并发 `b37f491` persona-onboarding + `9c5991e` env-switch-last-publish；后者的单环境 lastPublish env-scoping 被本 change 的**按 envId 分桶** rewrite 逐位覆盖，其 `ui-state.cjs` 留作独立模块未接线）。

## 1. Phase 0 — 真机去风险（零新代码）

> Phase 0 是**真机观测**，无代码产物；本机无 AdsPower + 运营机不可达，未实测。Phase 1 参数按 design 缺省值落地（错峰 1.1s = AdsPower ~1req/s 口径；单环境内存估值 ~1GB = OPERATOR.md），实测校准转真机 backlog 簇 24。
- [ ] 1.1 在真实运营机用现成 `scripts/launch-multinode.ts` 同时跑 2 个 AdsPower 分身，验证两 headful 窗口 / 两云端隔离运行时 / 内存余量 <!-- 转真机 backlog 簇 24（本机无 Ads、运营机不可达） -->
- [ ] 1.2 实测 AdsPower ~1req/s 限频在两环境同时 `browser/start` 下表现，量化是否需错峰 <!-- 转真机 backlog 簇 24；Phase 1 已按「需要」实装错峰队列 -->
- [ ] 1.3 刻意复现配图临时目录串扫 → 记录为 Phase 1 必修 <!-- 已由 task 2.1 直接修复 + 桩回归锁定（test/flows/image-uploader.test.ts 沙箱串扫用例），无需先真机复现 -->
- [ ] 1.4 把 Phase 0 观测结论回写本 change 备注 <!-- 未实测；Phase 1 用 design 缺省值，实测校准转簇 24 -->

## 2. Phase 1 — MVP 边缘外壳（2–4 环境）

- [x] 2.1 修配图临时目录串扫：`sweepImageTempDirs`（`src/main.ts`）+ 上传目录（`image-uploader.ts`）按 edgeId 命名空间隔离；清扫只扫本环境 `aidcp-img-<edgeId>-*` 名下 <!-- aidcp-edge c6292d8 imageTempPrefixFor(edgeId) + sweepImageTempDirs(ownPrefix) 导出并接线；核心侧公式与外壳 fleet.cjs imageTempNamespace parity 用例锁一致；沙箱串扫回归证兄弟在途不被误删 -->
- [x] 2.2 `main.cjs` 单例 `edgeProcess` → `Map<envId, EnvHandle>`；每 EnvHandle 持子进程句柄 + 冻结身份 + 状态投影 + 重起计数 + 意图标志 <!-- aidcp-edge c6292d8 envs Map + makeEnvHandle（含 stopRequested 取消闸、respawnStreak、removed 等）-->
- [x] 2.3 spawn 前构建每环境冻结 env：设 `AIDCP_ADS_USER_ID`、核心派生 `AIDCP_EDGE_ID=ads-<分身id>`、删 `AIDCP_ACCOUNT_ID`/`AIDCP_CDP_PORT`/`AIDCP_CHROME_PROFILE`；无法派生唯一稳定身份则拒绝、绝不回落 host <!-- aidcp-edge c6292d8 fleet.buildEnvSpawnEnv（ENV_KEYS_MUST_DROP 剔除继承污染 + 缺分身诚实拒绝）+ startEdge 身份闸 + dupRunning 最后闸；fleet.test.ts 锁 -->
- [x] 2.4 设置迁移：`adsProfileId` 单值 → 环境列表；`loadSettings` 向后兼容加载为单元素花名册；provider env 改按单个环境的纯函数 <!-- aidcp-edge c6292d8 fleet.migrateEnvironments + legacyMirrorOf（platform 只在 adspower 镜像，防 self 污染）+ buildAdsProviderEnv/buildSelfProviderEnv；fleet.test.ts 锁迁移/去重 -->
- [x] 2.5 每子进程各起一份 `createUiEventStream()`；活动/计数按 envId 归属，交织 stdout 不串号 <!-- aidcp-edge c6292d8 每 handle 持 uiEvents 实例 + broadcast 带 envId；fleet-console.test.ts 并发不串号用例 -->
- [x] 2.6 `updateStatus`/`broadcastActivity` + 控制 IPC（start/pause/resume/restart/relogin）加 envId 路由键；状态按 envId keyed map；停放 stdin + 持久 UI 态按 envId 键 <!-- aidcp-edge c6292d8 status:update/ui:activity/fleet:update 带 envId；preload IPC 全带 envId；uiState.byEnv 分桶 -->
- [x] 2.7 子进程非 detached、随外壳退出终止；退出时对全部在跑环境经串行队列有序全停 + 确认关闭、不留孤儿 <!-- aidcp-edge c6292d8 spawn 非 detached + before-quit preventDefault → gracefulStopAllAndQuit（错峰 SIGTERM + 有界等待 + quitFinal 放行）-->
- [x] 2.8 启动/停止经外壳级串行队列错峰（相邻 ≥1.1s）避开 AdsPower ~1req/s；单环境启动失败不阻塞队列 <!-- aidcp-edge c6292d8 fleet.createStaggerQueue（吞单任务 throw 不断链）+ queueLifecycle 统一出口；fleet.test.ts 锁间隔与失败隔离 -->
- [x] 2.9 保留单实例锁，重写拒绝文案为「一台机一个监督者、其下并行托管 N 个环境」 <!-- aidcp-edge c6292d8 单实例锁保留 + 文案改写 -->
- [x] 2.10 每环境独立有界重起（复用 respawn-policy 语义）；某环境崩溃只重起自己、不牵连兄弟 <!-- aidcp-edge c6292d8 fleet.decideRespawn（与 src/supervise/respawn-policy.ts parity 用例锁）+ 每 handle respawnTimer/streak 独立 -->
- [x] 2.11 renderer 按 envId 路由主区域；新增左侧环境栏 + 点选切换到该环境既有陪伴视图（内容/交互不变）<!-- aidcp-edge c6292d8 routeStatus/routeActivity 按 envId + 环境栏 + selectEnv 整体切换（含活动缓冲/日志/发布折流按 envId 分桶）；旧无 envId 形状归 __local__ 零回归 -->
- [x] 2.12 AdsPower 环境选择改多选加入运行花名册；每成员带 `user_id`、持久化为列表；同一分身/账号防重复加入 <!-- aidcp-edge c6292d8 populateEnvs 多选 + roster 去重 + 「已加入」标记/移出钮；唯一环境自动加入；fleet-console.test.ts 锁 -->
- [x] 2.13 `test:acceptance` → `test` → `typecheck` 全过（红线 AC-PROTO-*/AC-PUB-*/AC-RISK- 不破）<!-- aidcp-edge c6292d8：789 test + 15 acceptance + typecheck 全绿 -->

## 3. Phase 2 — headful 收益 + 稳健

- [x] 3.1 环境栏默认收起窄图标条：头像安静 + 状态由外圈色环承担 + 需处理脉冲 + 展开钮待处理计数徽标 + 悬停出名字 + 点击展开；失联绝不呈现为在线 <!-- aidcp-edge c6292d8 env-rail collapsed 默认 + rail-ava 色环 lv-* + pulse + rail-badge；ui-logic.fleetLevel stale（心跳超 5min）判失联；fleet-console.test.ts 锁失联不呈现为在线 -->
- [x] 3.2 环境栏按紧迫度排序、「需要处理」浮顶 + 顶部待处理计数 <!-- aidcp-edge c6292d8 ui-logic.fleetRailModel（error>attention>launching>stale>running>offline，同级保花名册序）+ pendingCount -->
- [x] 3.3 引导式登录/验证码流：待处理环境排队、一次引导一个（聚焦窗口→人工→完成·重检→自动续跑前进）；新到项实时并入 <!-- aidcp-edge c6292d8 guide-panel + guideQueue 每步重算 + maybeAdvanceGuide（红线修正：只在 edge==='running' 真恢复才退休，绝不在 relogin 瞬态误判）；fleet-console.test.ts 锁瞬态不误退休 -->
- [x] 3.4 「打开窗口」尽力抬前 + 窗口错位 + 行↔窗口对应；抬不动诚实告知窗口所在 <!-- aidcp-edge c6292d8 sendBrowserParkingCommand 回执带窗口所在 hint（绝不宣称已抬最前）+ ENV_WINDOW_CASCADE_PX 级联错位；同名/同色受平台限制以诚实文案补足 -->
- [x] 3.5 「全部启动」内存上限预检（预计在跑数 × ~1GB vs 可用内存），超限诚实拦阻/让运维确认 <!-- aidcp-edge c6292d8 fleet.ramAdmission + startAllEnvs（超限 ok:false reason:ram，force 才放行）+ 渲染层确认流 + 实时 k/N 进度；fleet.test.ts/fleet-console.test.ts 锁 -->
- [x] 3.6 每环境连续失败达上限 → 终态「错误·已放弃重启」在其行如实呈现 + 人工重试入口；失败绝不被聚合掩盖 <!-- aidcp-edge c6292d8 respawnGaveUp 终态 + fleetLevel error 浮顶 + queueStartEnv 清放弃态人工重试；每环境独立行呈现，绝不聚合 -->
- [x] 3.7 外壳重启 spawn 前经 `browser/active` 对账已在运行分身、接管/不重复 spawn，防孤儿 + 防 edgeId 撞车 <!-- aidcp-edge c6292d8 ads-local-api.listActiveProfiles + reconcileRunningProfiles（标 browserAlreadyRunning、接管不重拉）；非 detached + 单 handle/envId 保证不双拉；ads-local-api.test.ts 锁 -->
- [x] 3.8 加入/启动防重复认领同一分身/账号 + 同账号铺多环境告警 <!-- aidcp-edge c6292d8 roster 去重 + envIdForProfile + refreshSameAccountWarnings（只认登录真实身份 + syncEnvHandles 移出后重算撤告警）；fleet.test.ts/fleet-console.test.ts 锁 -->
- [x] 3.9 `test:acceptance` → `test` → `typecheck` 全过 <!-- aidcp-edge c6292d8 全绿（同 2.13）-->

## 4. 回归 / 真机验收 / 分发

- [x] 4.1 补关键回归断言：多环境交织 stdout 按 envId 归属不串号；spawn 拒绝主机名回落；退出全停不留孤儿；临时目录串扫不再发生 <!-- aidcp-edge c6292d8 新增 fleet.test.ts（11：迁移/身份闸/错峰/内存/同账号/decideRespawn+temp parity）+ fleet-console.test.ts（14：环境栏/路由不串号/引导流/内存拦阻/花名册/overlay 需处理/引导不误退休/persona 不跨账号）+ image-uploader 串扫隔离 + ads-local-api listActiveProfiles；桩验不了的（真机内存/限频/无孤儿/双拉）转簇 24 -->
- [x] 4.2 真机项登记 `docs/real-machine-acceptance-backlog.md` 簇 24 <!-- 控制仓：新增簇 24 -->
- [ ] 4.3 打安装包在运营机冒烟（先清单实例锁/旧版本）<!-- 真机项，转簇 24（本机不打包上线；等运营机）；安装包版本仍 0.2.7 -->
- [x] 4.4 `openspec validate --strict` → 回写 sha/偏离 → archive <!-- 控制仓：validate 通过 + 本回写 + archive -->

> **两轮对抗性评审（多 agent workflow）**：第一轮 6 维 find（37 agent）出 15 候选、14 经双 verifier 确认；第二轮 6 组 fix 逐条对抗验证均 closes+noRegression。据此修 14 项（含 6 major 红线：退出孤儿/暂停被排队启动覆盖、子进程 spawn-error 无 handler 崩监督者、persona persist 跨账号误绑、引导流 relogin 瞬态误退休、验证码阻断浮层未浮顶需处理、设置/清理若干）+ 3 项残留加固（persona 严格 envId 不回落、overlay 恢复信号「已消失」也归一、pauseEdge 停 self 登录轮询）。

## 5. 超出本 change 范围（规模化，未来 change，不在此实装）

> 以下仅记录、不作为本 change 的完成项；真要规模化再另起 change。

- 抽取共享 `src/supervise` spawn 循环给 CLI + 外壳共用（当前 `respawn-policy.ts` 已共享，spawn 循环先内联外壳、二者真分叉时再抽；本 change 用 `fleet.cjs` 的 CJS parity 副本，因 Electron 主进程 CJS 无法 require 编译后 ESM）
- 并发上限 cap（超串行错峰之外的最大并发启动数）
- AdsPower 生命周期收进外壳统一限流网关（子进程改成「接管已给调试端口」而非自起），使 ~1req/s 预算跨进程真共享
- 云端 `listEdges()` 端点 + 点亮 console 里已写好但无数据源的边缘在线徽标（online/stale/offline）
- 面向数十环境的网格密集/虚拟滚动视图（单机 ~1GB/环境 物理上到不了该量级，暂不做）
- 引导流微优化：当前环境中途干净下线（非 needsAction 原因）时自动前进（现留手动「跳过/退出」，评审判为可接受权衡）；「全部启动」精确「下一个 Ns 后」倒计时（现以每行「第 N 位」+ 聚合 k/N 传达）
