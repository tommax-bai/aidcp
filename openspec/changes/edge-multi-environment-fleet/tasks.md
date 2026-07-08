# Tasks — edge-multi-environment-fleet

> 全部落 `aidcp-edge`。核心 `src/main.ts` 及定位/浏览/发布/看门狗栈逐字复用、不改。云端与 console 本 change 零改动。
> 热点文件单写者纪律：改 `main.cjs` 进程/状态/设置层、`preload.cjs`、renderer 时标记需串行、勿与他人并行撞车。

## 1. Phase 0 — 真机去风险（零新代码）

- [ ] 1.1 在真实运营机用现成 `scripts/launch-multinode.ts` 同时跑 2 个 AdsPower 分身（`AIDCP_ADS_USER_IDS="p1,p2"`），验证：两条独立 headful 窗口、两条云端连接在云端各成一套隔离运行时（按 edgeId）、内存余量（每环境 ~1GB）
- [ ] 1.2 实测 AdsPower 本机 ~1req/s 限频在两环境同时 `browser/start` 下的表现，量化是否需错峰（预期需要）
- [ ] 1.3 刻意复现配图临时目录串扫：一环境写 `aidcp-img-*` 在途、另一环境启动清扫，确认会误删 → 记录为 Phase 1 必修
- [ ] 1.4 把 Phase 0 观测结论（内存估值 / 限频阈值 / 串扫复现）回写本 change 备注，作为 Phase 1 参数依据

## 2. Phase 1 — MVP 边缘外壳（2–4 环境）

- [ ] 2.1 修配图临时目录串扫：`sweepImageTempDirs`（`src/main.ts:79`）与上传目录（`src/flows/image-uploader.ts:176`）按分身/pid 命名空间隔离，或清扫只扫本子进程自己名下；同步修 `launch-multinode` 同 bug（对应 `edge-multi-environment-supervisor` 临时目录隔离需求）
- [ ] 2.2 `main.cjs` 把单例 `edgeProcess`（`:31/:604`）改为 `Map<envId, EnvHandle>`；每 EnvHandle 持子进程句柄 + 冻结 env + 状态投影 + 重起失败计数 + 意图标志（对应「按环境监督一组子进程」需求）
- [ ] 2.3 spawn 前构建每环境冻结 env：设 `AIDCP_ADS_USER_ID`、令核心派生 `AIDCP_EDGE_ID=ads-<分身id>`、删 `AIDCP_ACCOUNT_ID`/`AIDCP_CDP_PORT`/`AIDCP_CHROME_PROFILE`；无法派生唯一稳定身份则拒绝启动、绝不回落 `host-<hostname>`（`edge-id.ts:54`）（对应「唯一稳定边缘身份」需求）
- [ ] 2.4 设置迁移：`settings.adsProfileId` 单值（`main.cjs:86/148`）→ 环境列表；`loadSettings` 向后兼容把旧单值加载为单元素列表；`buildProviderEnv`（`:137`）改为按单个环境配置的纯函数
- [ ] 2.5 每子进程各起一份 `createUiEventStream()` + `mergeStats()`（`ui-events.cjs`）；活动/计数按 envId 归属，交织 stdout 不串号
- [ ] 2.6 `updateStatus`/`broadcastActivity` 两个广播出口（`main.cjs:436/503`）与 `preload.cjs` 控制 IPC（start/pause/resume/restart/relogin）加 envId 路由键；状态改为按 envId 的 keyed map；浏览器停放 stdin 与持久 UI 态（`ui-state.json`）按 envId 键（对应「每环境外壳态隔离」需求）
- [ ] 2.7 子进程改非 detached、随外壳退出终止；应用退出时对全部在跑环境经串行队列有序「全部停止」+ 确认关闭、不留孤儿（对应「非 detached + 优雅全停」需求，仅 Phase 1 的退出优雅停止部分；重启对账放 Phase 2）
- [ ] 2.8 启动/停止经外壳级串行队列错峰下发（相邻 ≥1.1s），避开 AdsPower ~1req/s；单环境启动失败不阻塞队列其余环境（对应「错峰串行」需求）
- [ ] 2.9 保留单实例锁（`main.cjs:1103`），重写其拒绝文案为「一台机一个监督者、其下并行托管 N 个环境」
- [ ] 2.10 每环境独立有界重起复用 `src/supervise/respawn-policy.ts`；某环境崩溃只重起自己、不牵连兄弟（Phase 1 只做每环境重起隔离；放弃重启终态 UI 放 Phase 2）
- [ ] 2.11 renderer：把 `render(status)`（`renderer.js:756`）包成「按 envId 的 keyed map 迭代」；新增左侧环境栏（列表态即可，收起态放 Phase 2），点选某环境把右侧主区域切到该环境的既有陪伴视图（内容/交互不变）（对应 `edge-fleet-console` 环境栏列出 + 主区域路由 + `edge-companion-ui` 按环境隔离）
- [ ] 2.12 AdsPower 环境选择改多选加入运行花名册（`renderer.js:1038` `populateEnvs` 由单选改多选）；每成员各带其 `user_id`、持久化为列表；同一分身/账号防重复加入（对应 `adspower-desktop-env-picker` 两条 MODIFIED）
- [ ] 2.13 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（安全红线 `AC-PROTO-*`/`AC-PUB-*`/`AC-RISK-*` 不破）

## 3. Phase 2 — headful 收益 + 稳健

- [ ] 3.1 环境栏默认收起为窄图标条：头像退安静样式、状态由头像外圈色环承担、需处理项脉冲、展开钮带待处理计数徽标、悬停出名字、点击展开完整列表；失联态绝不呈现为在线（对应「默认收起 + 状态环」需求）
- [ ] 3.2 环境栏按紧迫度排序、「需要处理」浮顶 + 顶部待处理计数（对应「按紧迫度排序」需求）
- [ ] 3.3 引导式登录/验证码流：把全部待处理环境排队、一次引导一个（聚焦其窗口 → 人工处理 → 完成·重检 → 自动续跑并前进）；新到项实时并入（对应「引导式登录流」需求）
- [ ] 3.4 「打开窗口」尽力抬前 + 窗口错位摆放 + 行↔窗口同名/同色；抬不动诚实告知窗口所在（对应「打开窗口诚实」需求）
- [ ] 3.5 「全部启动」内存上限预检（预计在跑数 × ~1GB vs 本机可用内存），超限诚实拦阻/让运维确认（对应「内存上限预检」需求）
- [ ] 3.6 每环境连续失败达上限 → 终态「错误·已放弃重启」在其行如实呈现 + 人工重试入口；失败环境绝不被整体状态聚合掩盖（对应「诚实放弃」+「每环境失败诚实呈现」需求）
- [ ] 3.7 外壳重启时 spawn 前经 `browser/active` 对账已在运行的分身、接管/不重复 spawn，防孤儿 + 防 edgeId 撞车（对应「重启对账」需求）
- [ ] 3.8 加入/启动时防重复认领同一分身/账号 + 同账号铺到多环境告警（对应「同账号告警」+ 花名册防重复需求）
- [ ] 3.9 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过

## 4. 回归 / 真机验收 / 分发

- [ ] 4.1 补关键回归断言：多环境交织 stdout 按 envId 归属不串号；spawn 拒绝主机名回落；退出全停不留孤儿；临时目录串扫不再发生（少量关键用例即可，桩验不了的转真机项）
- [ ] 4.2 真机项登记到 `docs/real-machine-acceptance-backlog.md`（新簇）：2–4 环境并行内存实测、AdsPower 限频错峰实测、双 headful 窗口人工登录/验证码引导流、退出无孤儿、重启对账无双拉、同账号告警
- [ ] 4.3 打安装包（`../aidcp-edge` 构建产物），在真实运营机做冒烟（先清单实例锁/旧版本）
- [ ] 4.4 完成后 `openspec validate edge-multi-environment-fleet --strict` → 按勾选进度回写各 task 的 commit-sha/偏离说明 → archive

## 5. 超出本 change 范围（规模化，未来 change，不在此实装）

> 以下仅记录、不作为本 change 的完成项；真要规模化再另起 change。

- 抽取共享 `src/supervise` spawn 循环给 CLI + 外壳共用（当前 `respawn-policy.ts` 已共享，spawn 循环先内联外壳、二者真分叉时再抽）
- 并发上限 cap（超串行错峰之外的最大并发启动数）
- AdsPower 生命周期收进外壳统一限流网关（子进程改成「接管已给调试端口」而非自起），使 ~1req/s 预算跨进程真共享
- 云端 `listEdges()` 端点 + 点亮 console 里已写好但无数据源的边缘在线徽标（online/stale/offline）
- 面向数十环境的网格密集/虚拟滚动视图（单机 ~1GB/环境 物理上到不了该量级，暂不做）
