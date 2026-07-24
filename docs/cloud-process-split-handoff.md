# Cloud 拆进程 · Session 交接（Block ② 2d 进行中）

> 2026-07-24 写。给下一个 session 冷启动接手用。上位设计见 `docs/cloud-process-split-design.md`，接缝地图见 `docs/cloud-decoupling-seam-inventory.md`，路线图见 `docs/cloud-decomposition-roadmap.md`，执行记忆见 memory `cloud-decoupling-execution-progress`。**本文件只记「当前 checkpoint + 下一步怎么接」**，不重复设计。

## 一句话现状

Block① 代码解耦已到地板（跨边界 import `frozenTotal` 266→**101**，全 land+dev、行为零变更）。Block② 拆进程：2a 传输原语 + 2b 数据网关已 land+dev。**2d step1（共享地基从 segB 上移到 segA）+ step2（读端 HTTP 网关拓扑收口）已 land + dev 部署 + 冒烟绿（2026-07-24）**——core 现在能开机了（见下）。Block③ 物理拆库仍 gated，不碰 ol 生产。

## 当前代码位置（务必先对齐）

- cloud `origin/master` = **05bceca**（`block2-content-process-split: hoist shared foundation from segB into segA`）。frozenTotal = **101**（未变）。
- **2d step1 已 land + dev 部署 + 冒烟绿（2026-07-24，05bceca）**：worktree 已清、分支已删。dev `/opt/aidcp/cloud/.deploy-sha` = 05bceca，进程照常开机（active + 8787 监听 + 飞书长连接 onReady + config-mirror 变化=0，启动~4s）。全量验证一次过：typecheck EXIT=0 / test:acceptance 105/105 / `npm test` 3155 pass·0 fail·10 skip / frozenTotal 101。
- **step1 做法**：把整个 `segBContent` 构造体**纯搬运**到 `segAApiFoundation` 尾部（零改行），删掉 segB 的 `const {...}=ctx` 解构（那些名字现在就是 segA 同名局部）。搬运块里唯一的 `ctx.*` 读只剩三个运行期后向引用（`publishScheduler`/`uiSnapshot`/`runtimes`，都在延迟回调里）→ 无「读到尚未赋值的 ctx 字段」。构造顺序逐字不变 → monolith 逐字节等价。`segBContent` 现为空桩（`_ctx`），段计划保留供 2e 复用。
- **step2 做法（同一提交）**：core 的 http `DataGateway` 现在只把「content 域」读端口（精选库 curated）remote 到 content 进程；`delegatedTask`/`interaction` 属 automation 域、core 本地拥有，一律保持 local（content 的内部读 API 只服务 curated 路由，误投 delegated-task 会 404）。删掉了不再用的 `DelegatedTaskHttpClient` import。
- **step2 读端已真机冒烟坐实（安全隔离，不扰动线上 monolith）**：单起一个 content 进程（`AIDCP_SERVICE=content AIDCP_CONTENT_PORT=8092`，且 `AIDCP_DEPLOY_ENV` 置空使 target 门控的认领/恢复全不触发）→ 只跑 segA+读API、不碰 8787、不连飞书、不认领任务。HTTP `list-for-client(creationStatus=all)` 回 `ok total=186 items=5`，与该账号 PG 直查 `curated_content` 行数 **186 完全一致**；unknown-route 回结构化 `route_not_found`（路由为真、非静默 200）。用完即杀、无残留、monolith 全程 active。

## 2d 这一刀做了什么（87b3429）

给 `server.ts` 的 `main()` 加了环境变量 `AIDCP_SERVICE` 三模式（一套代码、多入口，不是三仓）：

- **monolith（默认 / 未设 / 未识别值）**：四段全跑（segA→segB→segC→segD），无新监听，网关默认 local。**逐字节等价**——这是唯一不可破的不变量。
- **content（`AIDCP_SERVICE=content`）**：跑 segA+segB、跳 segC/segD；起 InternalHttpServer 在 `127.0.0.1:(AIDCP_CONTENT_PORT ?? 8092)`，只服务它拥有的 curated-content 读端点。
- **core（`AIDCP_SERVICE=core`）**：跑 segA+segC+segD、跳 segB；配 `AIDCP_GATEWAY_MODE=http` + `AIDCP_GATEWAY_BASE_URL` 指向 content 进程时，curated 读走 DataGateway 的 HTTP client。

**新增文件**：`src/gateway/service-mode.ts`（零 import 的纯模式选择器，被 server.ts 单独 import，好让单测不触发 main() 启动整进程）+ `test/gateway/service-mode.test.ts`。**改动文件**：`src/server.ts`、`boundaries/module-ownership.json`（service-mode.ts 按 src/gateway/ 的 inherit=api 自动归属，frozenTotal 不变）。

**绿灯证据（impl 亲跑）**：`npm run typecheck` EXIT=0；`npm test`（默认 monolith）3155/3155 pass、10 skip（历史环境门）、58.5s；service-mode + module-boundary 单测 22/22；frozenTotal 101→101。热文件零改动，无新 npm 依赖。

## ⚠️ 关键真实发现（已被 step1/step2 处理 + 新暴露的真约束）

**（已解）core 开机崩根因**：原「segB = content only」是错的——segB 还构造了 ~34 个共享地基对象，segC/segD 构造期硬依赖它们，跳过 segB 起 core = 开机崩。step1 把**整个 segB 构造体**上移到 segA 后此症状消除。**注意**：这 ~34 == segB 全部 ctx 输出（含 imageProvider/curatedContentStore/postProcessor/publishOrchestrator/conceptStore/anyImageKeyPresent），加上它们的本地依赖（wanxiang/seedream/ark/firstPostCoordinator）是一个互相咬合、不可分的构造块——所以「移 34、segB 只剩真 content 私有」这句是原交接的理想化措辞，实际是**整块搬**、segB 变空。因 segB 现为空桩（no-op），**core 的段执行 = A + 空B + C + D ≡ monolith**：`core` 开机 iff monolith 开机，而 monolith 线上 healthy → core 开机由此可证，无需冒扰动线上的整核起进程。

**（新暴露·决定 2e 的真约束）当前「拆」还只拆了读端，没拆生成端。** content 模式实测只跑 `segA + 内部读 API`——**发布/评论/生成的调度器与执行体（PublishScheduler / CommentScheduler / publish dispatcher / DraftRefinementWorker / 通知巡视）全在 segC/segD**，content 模式一律跳过。所以现拓扑下：**core 做全部生成与发布，content 只服务 curated 读**（与「content 进程拥有生成管线」的目标恰好相反）。要真做到「content 拥有生成、core 委托过去」，必须把这些生成/发布调度器从 segC/segD 迁进 content 段 + 建 core→content 触发生成的跨进程命令通道——这是 2e 的实质工作量，也是原 brokenPath ①「content 生成/发布运行路径」/「写·生成侧跨进程传输未建」的本体。

## 下一步（给新 session 的明确剧本）

**第 0/1/2 步 ✅ 已完成（2026-07-24，05bceca land + dev 部署 + 冒烟绿）**：安全骨架 + 共享地基上移 + 读端 HTTP 网关拓扑收口 + 读端真机冒烟。新 session 无需再碰，直接从第 3 步（2e）接。

**遗留·真机 backlog（本轮没做、避免扰动线上）**：dev 上**同时**起 core（`AIDCP_SERVICE=core AIDCP_GATEWAY_MODE=http AIDCP_GATEWAY_BASE_URL=http://127.0.0.1:8092` + 自定 `AIDCP_PORT`）与 content（`AIDCP_SERVICE=content AIDCP_CONTENT_PORT=8092`）跑端到端读闭环。**为何暂缓**：整核起进程会拉起第二条飞书长连接 + 按 target=dev 认领持久任务，与线上 monolith 双跑会双发飞书卡/双认领任务（扰动大）。读端两半已各自证过（server 半真机 total=186 对得上 DB；client 半 `CuratedContentHttpClient` 同一份 `CURATED_CONTENT_ROUTES` 线契约 + 单测覆盖），端到端只差「同时起两进程」这一步，留给专门窗口或先把飞书/worker 在实验态可关掉再做。

**第 3 步（2e，下一大块，值得新鲜上下文 + 工作流编排）**：真功能拆分 + 物理化。三条并行线：
  1. **生成端下移**：把 PublishScheduler / CommentScheduler / publish dispatcher / DraftRefinementWorker / 通知巡视等生成·发布调度器从 segC/segD 迁进 content 段；建 core→content 的跨进程触发通道（写/生成侧传输，补齐 brokenPath ①）。守 monolith 逐字节等价。
  2. **kernel 抽共享包**：kernel 抽成 content 与 core 都依赖的共享 npm 包（守 AC-BOUND-03 kernel 准入门禁：禁 SQL 字面量 / HTTP-fetch / LLM 供应商标识符 / 模块级活状态 / setTimeout）。
  3. **deploy-target 多服务化**：deploy-target + systemd 支持一机多服务（core + content 各一 unit、各自端口与 env），dev 先落。

**第 3 步以后**：Block③ 物理拆库（gated，碰 ol 生产，等用户拍板从发布分支走）。

## 一直有效的红线 / 约束（务必带走）

- **速度第一、可承担风险、过程中 dev 受影响可接受**（用户 2026-07-24 反复强调）。批量收口测试:每刀只 typecheck + 模块单测,整批末尾跑一次全量。
- **monolith 默认逐字节等价 = 唯一不可破不变量**（改 main() 的命门）。
- 提交/推送/dev 部署长期授权,不用逐次问;**ol 部署只在用户明确要求、从发布分支走**。commit 末尾 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
- **canonical checkout 永远停默认分支**（aidcp=main, cloud=master）;分支隔离一律用 worktree。**绝不 git add -A**。部署只从干净 `git archive HEAD` 快照 + 先备份。**dev 同机 isales 绝不碰。**
- **热文件单写、绝不并行碰**:两份 protocol.ts、command-bridge、event-bus/types RoleName、role-catalog、risk-state-machine、src/risk 内部。
- **kernel 准入门禁**（AC-BOUND-03,比机械纯净严）:kernel 文件禁 SQL 字面量 / HTTP-fetch / LLM 供应商标识符（含 `LlmClient`/`ChatLlmClient` 名字）/ 模块级 `new Set`·`new Map`（活状态）/ `setTimeout`（定时器）。
- **Block③ 拆物理库 gated**:碰 ol 生产,只做逻辑准备、不动物理库,等用户拍板从发布分支走。
- 已登记真机 backlog（本轮别顺手做）:① dev 迁移账本整个未 baseline;② 建议把 `scripts/` 纳入 typecheck（现只 src/+test/,曾漏掉搬 pg-config 后的脚本崩）。

## 说人话总结

- 上一轮试出的「core 那档开不了机」这次修好了:把原本挤在「内容段」里、其实大家都要用的一整块地基**整体挪到了公共段**。默认那档(线上现在跑的)行为**一字没变**,全量测试 3155 条全绿,已经部署到 dev、进程开机健康。
- 因为那块地基挪走后「内容段」变成了空壳,所以「core 档」= 公共段 + 自动化 + 接口,跟默认档跑的是**同一套构造**——默认档在线上是健康的,所以 core 档也必然开得了机,不用冒着扰动线上的风险去真起一遍。
- 还顺手验证了「跨进程取数」的一半:单独起了个「内容进程」,让它用 HTTP 把精选内容吐出来,取到的条数(186)和数据库里一模一样,证明这条取数通道是通的。
- 但也看清一个真问题:**现在只拆了「读」,没拆「写/生成」**。真正生成内容、发帖、评论的那些活儿其实都还在 core 这边,内容进程目前只负责「把已有内容读出来」。要让内容进程真正接管「生成」,是下一大块工作(2e),得把那些生成调度器搬过去、再建一条 core 喊 content 去生成的通道。
- 交接文档已更新(就是本文件),记忆也更新了。新 session 照「下一步·2e」三条并行线接着走即可。
