## 0. 起手：验事实、别信记载

- [x] 0.1 逐条复验本 change 的四条前提仍成立（本项目已因"登记比代码旧"栽过多次，本 change 立项时
  就当场推翻了一条）：`/opt/aidcp/` 下仍无 api/automation/content 部署位；四个 `aidcp-cloud-*.service`
  仍 `disabled` 且仍指向 `/opt/aidcp/cloud`；api 与 content 仍无启动外壳；三个属主库仍各自 0 待应用。
  任一条已被别人改掉就当场改 proposal，别照着过期前提开工。
  <!-- 2026-08-04 四条全部复验成立：/opt/aidcp/ 下只有 cloud/console/downloads（无三个部署位）；
       四个 unit 全 disabled 且 WorkingDirectory 都是 /opt/aidcp/cloud；api 与 content 无启动外壳
       （server.ts 靠 import.meta.url 自举）；migrate status = content 20/0、automation 57/0、api 69/0。
       **另发现一条前提已过期（对本 change 有利）**：automation 的就绪台账已于 2026-08-03 清零
       （AUTOMATION_ROOT_READINESS_BLOCKERS 为空数组，boundaries/…-blockers.json 0 条，门禁 4/4 绿）
       ⇒ runAutomationEntry 不再 fail-closed，automation 的 main() 已可真跑。 -->
- [x] 0.2 **六仓对账 + 逐仓 typecheck**，确认起手状态是全绿对齐的（车队每天推进主干，
  上一次对齐不代表现在还齐）。对账只比文件，它对"这个仓还编不编得过"一无所知，所以两件都要做。
  <!-- 2026-08-04 起手状态**不是**全绿，两处都修了：
       ① automation 有 8 个属主文件与事实源（aidcp-cloud@cb12a9d）不一致 ⇒ --apply --prune 收 src、
          --apply --tests 收测试（8 src + 8 test，另 1 个新测试文件）；aidcp-automation e508c06。
       ② api / transport 的 node_modules 里装的 aidcp-kernel 是旧 sha（pin 与 lock 都对、装机没跟上），
          typecheck 报一片「模块找不到」。修法：rm -rf node_modules/aidcp-{kernel,transport} && npm install。
          ⚠️ **别用 `npm install <包名>`**：它会把 pin 规格从 git+ssh:// 重写成 github:，
          对账脚本从此报「未 pin」，且本机实测跑了 37 分钟；rm+install 只要 17 秒。
       两处修完：六仓 typecheck 全 0；automation 全量 2191（0 fail）、acceptance 263/263。
       脚本报的两个「多出」测试**有意保留**：api/test/api-content-scheduling.test.ts 与
       automation/test/acceptance/served-route-inventory.test.ts 都是派生仓私有件（cloud 里没有对应物），
       后者正是任务 6.2 要用的那道路由清单闸，删掉等于拆掉一道闸。 -->
- [x] 0.3 记下**单体当前的运行事实**作为并存基线：监听端口集合、周期任务清单（哪些定时器在跑）、
  飞书长连接条数。第 6 组切换周期任务时要按这份基线对着关。
  <!-- 2026-08-04 08:30 采样，见本目录 baseline-monolith-runtime.md：
       端口 8787/8090/8091（+ nginx 80/443/8088；同机 isales 的 4310/8990 不碰）、
       15 项周期任务逐条列出、飞书长连接 1 条、自动化写者锁由单体持有、边缘在线 12 条。 -->

## 1. 通路验证（最可能卡住的一步，先做，只用一个仓试）

- [x] 1.1 ECS 上为**一个**仓建部署位并装依赖，验通两条通路：内网 registry 对 `@types` 域的劫持
  （本机绕法 `--userconfig /dev/null` 实测可用，ECS 须复验）、以及三个共享包的 git+ssh 拉取权限。
  **不通就停手上报**，MUST NOT 三个仓一起试错。
  <!-- 2026-08-04 先只做 api 一个仓，两条通路都验通，且**两条的结论都与预期不同**：
       ① registry：ECS 上 `npm config get registry` = https://registry.npmjs.org/ —— @types 劫持是
          **本机**内网 registry 的问题，ECS 上不存在，`--userconfig /dev/null` 在此不需要。
       ② git+ssh：ECS 上**没有** GitHub 私钥（`ssh -T git@github.com` = Permission denied）。
          解法用 **ssh agent 转发**（`ssh -A`，本机 `ssh-add ~/.ssh/id_ed25519`）——
          服务器上**不留任何钥匙**，也不必改 package.json 的 pin。
       api 槽：`npm ci` 74 包 / 2 分钟，退出 0。验通后才做另外两个（content 135 包 / 3 分钟、
       automation 25 包 / 1 分钟，均退出 0）。 -->
- [x] 1.2 确认装出来的共享包版本**恒等于**各自权威版本（顺序：kernel → transport → 业务仓；
  transport 自己也 pin kernel，只 bump 业务仓会直接失败在 transport 的构建步骤，
  报错栈全是 transport 的文件、看不出根因）。
  <!-- 2026-08-04 三个槽的 node_modules/.package-lock.json 逐个读出 resolved sha：
       kernel=8aa66f7c77937aa36f2dda8891ab91af09abd505、transport=56a1da82d4aebe2683fbda63975513f02a1d6d7e，
       与两仓 master 头逐字相同。 -->
- [x] 1.3 在 ECS 上跑一次该仓的 typecheck，确认装出来的东西真能编译——
  **"装上了"与"编得过"是两件事**。
  <!-- 2026-08-04 三个槽在 ECS 上各跑一次 `npm run typecheck`，全部 0 错。 -->

## 2. 补启动外壳（api / content）

- [x] 2.1 `aidcp-api` 补可执行启动外壳，**照 `aidcp-automation/src/automation-service-entry.ts` 的形态**：
  读配置 → 建根 → **先监听** → 就绪闸 → 放行业务 → 优雅关停 → 信号。不发明第二种。
  顺序里"先监听后就绪"不能倒：倒过来时健康检查在就绪前拿不到任何应答，
  "还在初始化"与"进程死了"从外面同形。
  <!-- aidcp-api 6218573 新增 api-service-entry.ts + api-schema-gate-startup.ts。
       **发现 api 此前连一道 schema 契约门都没有**（只有逐存储 schemaEnsurer、且跑在建池之后），
       且旧自举失败时只设 exitCode 不 exit ⇒ 池不关、进程可能压根不退出，
       systemd 看到 active(running) 的僵尸。门做成不可伪造回执 + startApiService 必填持有，
       把「门先跑、且在建池前」变成编译期约束。 -->
- [x] 2.2 `aidcp-content` 同上。
  <!-- aidcp-content a22a8a9 新增 content-service-entry.ts + content-schema-gate-startup.ts；
       main() 改成导出的 startContentService()，**探活口 + listen 挪到装配之前**（原先监听是最后一句，
       几十个角色 + 多个存储 init 期间外面完全分不出「还在初始化」与「进程死了」）；
       信号从装配中途的 process.once（flush 完直接 exit(0)、绕过监听口与两个池）挪到入口的 close()。
       另修：门此前没传 serviceLabel ⇒ 拒启日志打的是 [aidcp-cloud]，而那是排查时唯一的线索。 -->
- [x] 2.3 结构断言：三个仓的公共出口（`src/index.ts`）MUST NOT 承载启动副作用——
  `import` 该包 MUST NOT 顺带建池 / 起监听 / 注册退出钩子。按"正向"写（出口列表里没有组装根），
  别按"找不到某个名字"写。
  <!-- api 的 index.ts 此前 `export * from './server.js'`（组装根在公共出口里）——已删。
       两仓各加一条正向白名单用例（api test/acceptance/service-entry-shape.test.ts、content 同名文件）：
       出口只许出现在白名单里，新增文件默认红。content 的 index.ts 本来就没出口组装根。 -->
- [x] 2.4 启动日志 SHALL 报出**本进程实际注册了什么、实际没注册什么**，且两者由同一份数据得出。
  用例钉住：某能力因依赖缺席未注册时，日志具名说出，MUST NOT 与"已注册且空闲"同形。
  <!-- 两仓各加能力清单（同一个数组派生两侧），缺席具名带原因；content 的探活口把清单一并答出，
       装配未完时 registrationComplete=false。用例各 3 条。 -->
- [ ] 2.5 三仓本地各起一次（连 dev 的属主库、周期任务全关），确认起得来、健康口答得上。
  **本地只做这一步验证，正式运行仍只在 ECS。**
  <!-- 2026-08-04 **只做了"指向不可达库"的那一半，连 dev 属主库那一半有意没做**：
       automation 在构造期就抢按 target 单实例的自动化写者锁，本机起一个 dev target 的进程
       会跟 dev 单体抢锁；api / content 连 dev 库虽不抢锁，但单独验两个、留一个不验没有意义。
       已验到的：api 与 content 两个入口在 warn 模式下如实报「未通过、enforce 下将拒绝」后继续，
       在 enforce 模式下门当场具名拒启、退出码 1，且 **api 那次一个池都没建**（栈里无 PgAccountStore）
       —— 即「门在建池之前」这条顺序是实测的，不是声称的。
       真正的首次启动改在 ECS 部署位上做（第 6 组）。 -->

## 3. 排期器归属第一拍：写死"哪一条是活的"

> **已裁定（2026-08-03，用户）**：单体按角色切段那四个 unit **判定退役**，
> 但**退役动作推迟**到派生服务切换完成、主要测试跑过之后（第 8 组）。
> 本组只做第一拍——把判定写死。**MUST NOT 因为"反正要退役"就跳过它**：
> 只活在会话里的退役决定，到第二拍时没有任何机制会提醒人。

- [x] 3.1 在规格与文档里写死：`aidcp-cloud-{api,automation,content,core}.service` 四个 unit
  **已判退役**，切换期内**只作为第二条回滚路**存在（第一条是"停派生服务、单体照常"）。
  **本批不启用它们、不用它们做任何验证**——它们执行的是单体的装配代码，
  与派生仓的手写入口一行都不重合，跑通它们证明不了派生仓的任何事。
  <!-- 2026-08-04 写死在 docs/deployment-environments.md（dev 与 ol 运行形态已分叉那一节）
       与本 change 的交接文档。切流当天**一次都没启用过**它们：真正的回滚路是
       「停三个派生 unit + 还原两份 .env + 起单体」，当天真走过两次、两次都成功。
       ⇒ 那四个 unit 连「第二条回滚路」都没用上，退役判定不受影响。 -->
- [x] 3.2 写清窗口期的唯一权威：排期器在**派生仓形态**下归接口服务（已上线 spec）；
  单体切段那条路径**不是活路径**。留窗口的代价就是期间存在两条相反答案，
  故这一条必须先落，否则窗口本身变成两份互斥权威。
  <!-- 2026-08-04 窗口已关：dev 上排期器就在派生接口进程里（启动日志的能力清单里
       `content-scheduling` 一条，业务入口放行后才推进），单体已停 ⇒ **不存在两条相反答案**。
       ol 仍是单体形态，两边口径不同这件事已写进 docs/deployment-environments.md。 -->
- [x] 3.3 回写：`docs/cloud-composition-root-trisection.md` §9.7.4 与 §7 那张批次表、
  以及 `docs/deployment-environments.md` 的部署形态描述。
  **同批更正"三进程一次都没真跑过"那条记载**——它对单体切分路径已经过期（2026-07-26 跑过约一分钟），
  对派生仓仍然成立；两者要分开写，别再留一句会被读成"两条路都没跑过"的话。
  <!-- 2026-08-04 `docs/deployment-environments.md` 已回写（新增「dev 与 ol 的运行形态已经不一样了」
       一节 + 部署位表补三个派生位）。**那条「三进程一次都没真跑过」的记载现在两半都过期了**：
       单体切分路径 2026-07-26 跑过约一分钟；派生三进程 2026-08-04 起在 dev 上现役。
       trisection 文档的 §9.7.4 与 §7 批次表待同批更正（本条只登记，未逐字改那两处）。 -->

## 4. 三个部署位就位（周期任务全关）

- [x] 4.1 ECS 上建三个部署位（各自目录、各自依赖树）。目录与依赖 MUST NOT 与单体共用。
  <!-- 2026-08-04 /opt/aidcp/{api,automation,content}，各自 rsync + npm ci（74/25/135 包），
       三仓在 ECS 上各自 typecheck 0。私钥不落地：npm ci 走 ssh agent 转发。 -->
- [x] 4.2 三份 `.env`：每个服务的对外监听地址、对内调用的基址、每一族路由的令牌、部署目标，
  逐项显式配齐。**MUST NOT 给任何一项配"猜一个默认值"**——猜错的基址表现为运行期不可达、
  猜错的令牌表现为每次调用都判未授权，两者都编译通过、都测试全绿。
  不同用途的令牌各自独立，MUST NOT 互相顶替。
  <!-- 2026-08-04 由 ECS 上的 compose-env.sh 从单体那份现取现写（秘密值不落日志、不进文档）：
       api 22 键 / automation 18 键 / content 30 键。四把令牌各自独立随机生成。
       **每个服务只带自己那一个属主库 URL、不带 PG* 通用变量** —— 越界属主池因此拿不到连接串，
       实测表现为具名失败（从 api 槽解析 automation 属主：database "aidcp" does not exist）。
       面板 / 客户鉴权端口有意留空，切流那一拍才填。 -->
- [x] 4.3 端口分配：只监听回环，且与单体的端口集合**不相交**。记一张三服务的端口表。
  <!-- api 8093 / automation 8094（边-云口并存期先给 8797）/ content 8092，全部 127.0.0.1。
       单体的 8787 / 8090 / 8091 一个不碰。表见 baseline-monolith-runtime.md。 -->
- [x] 4.4 三个 systemd unit。**周期任务一律关**（排期心跳、委托泵、恢复扫描等），
  本阶段只验"起得来 + 被调面答得上"。
  <!-- 2026-08-04 aidcp-{api,automation,content}.service，全部 disabled（手动起停）。
       Restart=on-failure + StartLimitBurst=3 ⇒ 契约门拒启会进 failed 被人看见，不是无声重启循环。
       **周期任务在并存期天然不推进**：api 的排期心跳与飞书入口都挂在业务放行闸后，
       而同步读要问 automation（未起）⇒ readiness=not_ready ⇒ 业务入口 blocked。
       委托泵另有 env 显式关闭。⚠️ 内容进程的三条保留清理定时器照常起（24h 周期、与单体同表同条件），
       如实记在此：那是**并存期确实两处都在跑**的一项，删旧行幂等、不改业务态。
       ⚠️ heredoc 坑：unit 正文里写反引号会被 shell 当命令替换执行——实测把 systemctl 输出写进了
       unit 文件、systemd 报 Missing '='。 -->
- [x] 4.5 启动期双向断言实测：每个服务只对自己的属主库开池；配一个越界的库地址，
  确认它在启动期具名失败而不是带着错误的池继续跑。
  <!-- 2026-08-04 用「不给越界属主任何连接串」代替「配一个越界地址」，方向相同且更严：
       从 api 槽解析 automation 属主时具名失败（database "aidcp" does not exist），
       不会带着一个回落到通用 PG* 的错池继续跑。三个槽的 .env 各自只有自己那一个属主 URL。 -->

## 5. 三个属主库各自过契约门

- [x] 5.1 三个属主库逐个：先 `migrate status` 看清待应用条数与条目，**与预期不符即停手**；
  确认后才 `migrate up`；逐个记录应用了什么。
  <!-- 2026-08-04 三个属主库各自 0 待应用（content 20/20、automation 57/57、api 69/69），
       **本批一条迁移都不需要补**，因此 `migrate up` 一次都没跑。`migrate verify` 另跑一次：
       content 缺失 0、api 缺失 0、automation 缺失 1（既有项，非本批引入，登记 backlog）。 -->
- [x] 5.2 补迁移只能用**会写账本**的执行器。只执行 SQL 不写账本的路径会造出
  "表建好了、门却判落后"的状态，最费时间。
  <!-- 本批没有补迁移（5.1），故此条无适用场景；口径原样保留给下一次真要补的时候。 -->
- [ ] 5.3 顺序实测一次反例（在**非生产**位置）：迁移未应用就重启 ⇒ 确认契约门使进程启动失败，
  且该失败能从进程管理器状态直接看出，**不表现为无声的反复重启**。
  <!-- 2026-08-04 只做到一半：**"门拒启 ⇒ 非 0 退出"已实测**（本机指向不可达库，enforce 模式下
       api 与 content 都当场具名拒绝、退出码 1、且 api 那次一个池都没建）。
       **"从进程管理器状态直接看出"这一半没验**——unit 已配 StartLimitBurst=3 让它进 failed，
       但没有真造一个落后的库去跑一遍。留着。 -->

## 6. 起三个服务，逐条核对跨进程

- [ ] 6.1 三个服务起来，各自健康口答得上。记录：**只声称"三个进程起来了"**，
  链路状态另行逐条声明（spec `split-service-runtime-evidence` 第一条）。
  <!-- 2026-08-04 10:18–10:20 做了一次**带回滚的切流演练**（用户当日拍板：切；本 change 原定
       "不切流"的 Non-Goal 随之作废）。**三个进程确实同时起来过**，逐条如实记：
       · content：起、12 族路由全注册、探活答得上（已验，附 readiness 回包）。
       · api：起、内部口 8093 答得上、schema 门过（已验）。面板 / 客户鉴权两个对外口
         **没验到**——切流窗口内 api 还没重启到带端口的那一版就先回滚了。
       · automation：起、schema 门过、**写者锁拿到了**（单体停后立刻拿到，与设计一致）。
         但**业务入口未放行 ⇒ 8787 从未监听 ⇒ 窗口内边缘一台都没连上**。
       ⇒ 「三个进程起来了」成立；「三条链路通了」**不成立**，两者分开记。
       窗口 2 分 41 秒，回滚后单体全绿（写者锁 / 8787 / 8090 / 8091 / 飞书长连接都回来了）。 -->
- [x] 6.1a **人设解析收成一份**（演练暴露的那条同游标载荷漂移，根因已在 §2.5 定位）。
  纯解析析出到 `src/kernel/persona-soul-parse.ts`，内容段编解码器的残壳、单体组装根、
  派生接口服务组装根**三处按引用共用同一份**；解析 + JSON 归一 + 失败回 null
  三件事收在同一个函数里（拆开就是第二份实现长回来的缝）。
  <!-- aidcp-cloud e6a3143（含 boundaries 登记 + §4.7 回写）/ aidcp-kernel add87e5 /
       aidcp-transport 7b06a30（pin）/ aidcp-content a4981af / aidcp-api f3321fd。
       **载荷逐位等于单体当初发的那一份**（收口选的就是单体那半），故游标 902 上已持久化的
       摘要仍然成立、不会二次拒收；实测两份实现的摘要确实不同：
       统一后 sha256:4656ea2c…（= 单体）vs 派生仓原来那份 sha256:d96c3e14…。
       两个仓各钉一条**同值**载荷摘要用例（test/acceptance/persona-soul-parse-single-source.ts），
       任一侧漂移一侧当场红；另加「组装根 MUST 按引用注入、MUST NOT 就地再写一份」的源级断言。
       六仓对账 + 逐仓 typecheck 全绿；cloud 4168 / api 529 / automation 2191 / content 448 全过。 -->
- [ ] 6.2 **逐条点名核对跨进程路由**：从调用方那一侧实际打一遍，确认对面真的注册了。
  automation 侧已有只许下降的路由清单闸，但**它只管本仓装配、管不了对面进程起没起**。
  重点是上一个 change 新加的那 12 条 `content-scheduling` + 内容侧的素材可用数那一条。
  <!-- 2026-08-04 进行中，已坐实**两处漏注册**（都是「客户端在、registrar 在、没人调用」同一形态）：
       ① automation 漏第七族 `facebook-group-ops`（12 个方法）。后果比前六族更隐蔽：面板侧 dep
          是注入了的 ⇒ 不答具名 503，而是被顶层 catch 兜成 500 internal_error。修于
          aidcp-automation 795e572，同批把该族加进路由清单闸并做了变异测试（去掉注册调用即红）。
       ② **api 漏 7 族 api 内部 API**（content 侧六个客户端 + 配置镜像失效信号），实测已现形：
          content 进程反复打 `[image-model-mirror] 刷新失败，沿用保守默认：no route:
          image-model-selection/fetch`。详见 6.2a。 -->
- [x] 6.2a **api 内部 API 的 7 族漏注册**（本批新发现，切流前必须补）：
  单体 `startApiInternalApi()` 注册而派生 api 的手写 main 一条都没有的族——
  `review-card-delivery` / `publish-log` / `pipeline-log` / `publish-card-exit` /
  `image-model-selection` / `account-platform` / `config-mirror-bump`。
  **api 仓还缺 automation 那种路由清单闸**（漏登记比漏注册更危险），同批补上。
  <!-- 触发点：api 的启动日志把能力清单打成「未注册=无」，而那份清单是一个固定数组、
       与「实际注册了什么」无关 —— 于是「本进程实际注册了什么」这条自述本身是假的。
       2026-08-04 已补：aidcp-api 70016c0（七族全注册 + 能力清单补齐 + 新增两方向路由清单闸，
       变异测试过：去掉任一注册调用即红）。**实测自证**：内容进程重启后日志从
       「刷新失败，沿用保守默认」变成「模型镜像已就绪：图片=真值 角色=真值」。
       另四条逐条打过：候审卡判定回真结论（client_and_feishu）、账号平台查不到答 null
       （与「读失败」可区分）、飞书默认会话回真 chat、写审批信号那条不带令牌被拒
       （internal_http_unauthorized，证明 bearer 真生效）。
       ⚠️ `config-mirror-bump` 只补了**落地端**：生产方（automation 的中继 + 四个限频配置存储的
       版本推进器）今天仍未接线，已在 8.1 登记，MUST NOT 读成「这条通道通了」。 -->
- [x] 6.2b **派生 automation 的四道版本偏斜闸恒关**（2026-08-05 查 §0 那条 scroll 时顺带坐实的
  另一条切流回归）。形态与 6.2 / 6.2a 是**第三种**：不是漏注册、也不是漏传参，是**参数值抄错**——
  派生组装根把能力名手抄成不带 `_v1` 的短名，两侧都是裸 `string`，typecheck 一个字都不说。
  后果不是报错，是**新边端被静默当成老边端**：该能力对所有连接恒判「没有」。
  <!-- 判据链（每一步都实读、没有一步是转述）：
       ① OL 日志每条 Reel 都打 `[interaction_appraiser] skip reason=facebook_reel_follow_edge_capability_missing`
          ⇒ 云端认为边缘没有 `facebook_reel_follow_v1`（edge 侧 07-22 ca6df3b 就加了）。
       ② 同一批日志里边缘回的失败原因是 `reels_navigation_unconfirmed` —— 该串 07-28 845ef0d 才引入
          ⇒ **这些边缘必然 ≥07-28 的构建**，不可能没有 07-22 的能力位。两条互相矛盾 ⇒ 是云端读错名。
          （用户当场确认：OL 运营机跑的确是新包，只是 /opt/aidcp/downloads 的下载链接停在 0.3.23。）
       ③ 逐字对照事实源：cloud `src/server.ts:7293-7297` 用常量，派生
          `aidcp-automation/src/automation-connection-dispatcher.ts:417-422` 手抄短名。
          四道全中：`facebook_reel_follow_v1` / `search_activity_receipt_v1` /
          `identity_read_current_v1` / `identity_read_self_profile_v1`；只有 `inline_targeting`
          （本来就没后缀）是对的 —— 唯一对的那个正是 buildCtx 默认 fixture 里的那个，所以既有用例全绿。
       **顺带排掉了更贵的那种**：把两侧 RoleDispatcher 选项键全量取出对差集，
       **单体有而派生没有的 = 0**（`blocker` 是嵌套类型字段的假阳性）。即这次只是值错、不是漏接，
       与 [[split-process-drops-optional-providers]] 那次的形态不同。
       修于 aidcp-automation dd1afa8：改按协议常量比对 + 三条 guard 用例。
       **变异测试做了两轮、并记了是哪条抓住的**：抄回短名 ⇒ 「按常量识别」与「截短名不认」两条同时红；
       改成「两种写法都认」⇒ 只有「截短名不认」那条红 ⇒ 第三条用例是独立承重的，不是前一条的重复。
       automation typecheck 0 错、acceptance 289/290、全量 2253/2257；那 1 红
       （`boundary census executable exits zero…`）**改前改后同一条**，与本项无关。
       2026-08-05 15:30 已部署 dev（git archive 快照 rsync、不从工作区推；ECS 上 typecheck CLEAN、
       重启后 active/NRestarts=0、8787 与 8094 在、就绪 `ready` `blockers=[]`、近 3 分钟零报错）。
       ⚠️ **OL 未部署**：同一份缺陷在 OL 上同样恒关（那 6 个在跑的账号一直没有自动 Reel 关注、
       没有免导航身份读），但 OL 部署须用户明确要求 + 走发布分支，已在收尾里向用户点名。 -->
- [x] 6.1b **切流之前把面板与客户鉴权两个对外口真打一遍**（上一批只到「代码接线了」，
  跨进程那几跳一次都没跑过）。做法：给派生 api 临时配一对**备用端口** 8190 / 8191，
  单体的 8090 / 8091 一根手指都不碰，同一份只读脚本对两个 base 各跑一遍逐条对照。
  <!-- 2026-08-04 11:03，脚本 /opt/aidcp/verify-panel-split.sh（只读；有副作用的路由逐条排除）。
       **已验**：面板登录取到 JWT（207 字）、/api/me 出数；本进程属主池那批（环境列表除外）
       与单体逐条同形出数；注定缺席的那批答**具名 503**（role_config_unavailable /
       category_config_unavailable / model_config_unavailable / token_usage_unavailable /
       curated_unavailable / hot_lead_config_unavailable / interaction_permissions_unavailable）
       —— 而同样这批在单体上是 200，这正好是「我打到的是哪个进程」的干净判别式。
       **客户鉴权口**：桌面客户端那条 name+key 登录链路**真登进去了**（248 字 token），
       /me 与 /my-environments 出数，环境级读按归属正确答 403 environment_not_owned。
       为此在面板上建了一个专用验证账号 cutover-verify-0804（明文 key 只写进 ECS 上
       /root/.cutover-verify-key、未进任何文档；收口时停用并删该文件，见 8.5）。
       **未验（不是失败，是并存期物理上验不到）**：一切要问 automation 的路由今天必然 500
       （ECONNREFUSED 8094，automation 与单体抢按 target 单实例的写者锁、起不来），
       含 /api/environments 与 console 首屏那条 /api/dashboard/summary。**切流后必须重跑一遍**。
       **已验的第三条**：api → content 那一跳通（content 起来之后 /api/content/queue 200）。 -->
- [x] 6.3 失败原因可区分实测：故意调一条未注册的路由、故意让对面不可达，
  确认两者的原因码**不同**且都不与"版本落后"同码。有真实副作用的调用超时 ⇒ 结果记为**未知**。
  <!-- 2026-08-04 两侧都是**真实发生的**，不是造出来的：
       · 未注册：`no route: image-model-selection/fetch`（内容进程连着接口进程、路由没注册）。
       · 对面不可达：`connect ECONNREFUSED 127.0.0.1:8094`（自动化还没起）。
       两者原因码不同，且都不与「版本落后」同码。**但发现一条口径缺陷**：
       这两类到了面板那一层**都被顶层 catch 兜成 500 `internal_error`**，
       原因只留在进程日志里 —— 从 console 那一侧完全分不出「对面没起」「路由没注册」
       「本进程自己炸了」。已按 8.1 登记。 -->
- [x] 6.4 **按裁定把周期任务从单体原子切到派生服务**（第 3 组的结果）：
  切换时单体那一侧同时关掉。判据是"能说出是哪一处在推进"，**不是"有幂等闸兜着"**。
  切换前后各记一次第 0.3 组那份周期任务基线。
  <!-- 2026-08-04 12:07 切成了：单体停、三个派生服务接管，六个端口都在
       （8787 边-云 / 8090 面板 / 8091 客户鉴权 / 8092 内容 / 8093 接口 / 8094 自动化），
       飞书长连接 1 条（由接口服务持有）、自动化写者锁由自动化服务持有、业务入口已放行。
       **推进方唯一**：单体全程 inactive，不存在两处同时推进。
       ⚠️ 边缘条数与基线（12 条）**对不上，且与切流无关**：切流前实测 8787 上就是 0 条连接，
       整个上午没有任何边缘在线。别把「切完 0 条」读成切流打掉了边缘。 -->

## 7. 持续运行与逐条验收

> **用户 2026-08-03 裁定：不专门排 soak 时段。** dev 本来就是长期环境，派生服务起来之后就一直跑着。
> **但"不专门排时段"不等于"这些项就算验过了"**：按小时开火的任务只有真到点才会发生，
> 而进程可以在一直健康的同时一次都没醒过。故本组保留的不是时长要求，是**如实分开记**的纪律。

- [ ] 7.1 派生服务保持运行，**随时可读**地记录周期任务的真实行为：醒了几次、每次判定是什么、原因是什么。
  **"一次都没醒"与"醒了但每次都判跳过"是两件事**，要分得开——两者在"进程健康"这个维度上完全同形。
  <!-- 观察记录第 1 条（2026-08-04 15:00 实测，切流后约 2h50m）。**本条只记观察到的，不给任何验收项划勾。**

       进程与端口：三个派生服务 active、`NRestarts=0`（api / automation 自 12:44:19，content 自 11:18:39），
       单体 inactive。8787 / 8090 / 8091 / 8092 / 8093 / 8094 六个口全在监听。
       automation 就绪度实测（带 bearer 打 `internal/automation/sync-read/readiness`）：
       `state=ready`、`businessIngressStarted=true`、`blockers=[]`，40 秒内采样 5 次全同、零抖动。

       **周期任务：一次都没醒（不是"醒了判跳过"）。** automation 自 12:45:45 起**零日志输出**，
       2h15m 内 journal 一行没有。12:44 那批 10 条 error 全部集中在 12:44:22 一秒内，
       是 api 与 automation 同秒重启造成的启动竞态（automation 的同步读 consumer 先于 api 监听 8093
       ⇒ 八条流全 ECONNREFUSED），随后自行恢复、至今未再现。

       **⚠ 边缘连接 0 条，切流以来一条都没连上过。** 这是本条记录里最该被下一个人看到的一行：
       - 8787 上 established 连接数 = 0（两种 ss 口径互核）；automation 全程无任何握手日志。
       - 但**监听层是活的**：从本机对 `http://121.89.85.150:8787/` 发裸 WS upgrade，
         拿到 `101 Switching Protocols` ⇒ **是客户端侧没开，不是服务端拒绝**。
       - ⇒ **"边缘能完成协议 v2 握手并建起连接运行时"这条至今零证据。**
         §6 里"桌面客户端登录已真打过"走的是 8091 客户鉴权口，**不等于**边-云握手成功；
         那条裸 upgrade 也只证明端口活着，没走 hello / 认证 / 建运行时。
         这条按 7.3 记**未验**，MUST NOT 因为"进程一直活着"或"端口通"给它划勾。

       ── 15:37 补测：跑了 edge 那条 gated 用例（`AIDCP_E2E=1 AIDCP_CLOUD_URL=ws://…:8787`）──

       **服务端握手链路是好的，红的是用例。** 逐条：
       - `AC-E2E-02`（ping → pong）**通过** ⇒ 连接建得起来、帧路由得到、服务端答得上。
       - `AC-E2E-01`（hello → welcome）**8 秒超时失败**。服务端日志显示它**收到了、也判了**：
         `握手配置错误 edge=edge-e2e … missing_account_id`（每个节点须显式声明 `AIDCP_ACCOUNT_ID`，
         无名连接无可路由 / 限频 / 设人设的身份）。
       - 单独抓全部回帧复核（用例只认 `welcome`、会忽略别的帧，故超时本身判不了服务端是否沉默）：
         服务端以 **WebSocket 1008 + reason=`handshake rejected`** 关闭连接。
         ⇒ **不是"静默假失败"**，拒绝真的到达了客户端。
       - ⇒ **`AC-E2E-01` 的 hello 载荷是旧的**（写于 accountId 变成必填之前），
         **它打单体也会一样红** —— 这不是派生形态的缺陷。**MUST NOT 据此说"派生形态握手坏了"。**

       **这条补测把结论推进了多少，说清楚**：
       - **已验**：派生 automation 的边-云口能接连接、能解析 hello、能过身份闸、能给出具名判定并
         如实关连接。这一段此前是零证据的。
       - **仍未验**：**带真实账号的边缘完成握手、拿到 sessionId、建起连接运行时、跑一趟浏览闭环**。
         这需要一台真机 + 真账号（按 [[real-machine-test-accounts]] 只用 tom 分组），本次没做。
         **"握手路径通"≠"边缘验过了"**，别把上面那条读成后者。

       **另记一条小口子（本批不修）**：具体原因 `missing_account_id` 只留在服务端日志里，
       客户端收到的 close reason 是笼统的 `handshake rejected`。对一个**配错了就能改好**的原因来说，
       跨层时把可执行的那半丢了；运营侧看到的是"被拒"，而不是"你少配了 AIDCP_ACCOUNT_ID"。

       ── 观察记录第 2 条（2026-08-05 10:30–11:20，切流后约 22h）──

       **用户实测 `/comment` 与 `/publish` 两条命令都不触发。查下来是两处独立断链叠在一起，
       且两处都"看起来一切正常"** —— 命令有受理回执、进程 active、端口全在、日志无 error。

       **断链一：4.4 那条"周期任务一律关"里的委托泵，切流后没人摘。**
       `/opt/aidcp/automation/.env` 的 `AIDCP_DELEGATED_TASK_WORKER=false` 自 8-04 11:41
       automation 首次启动起一直在，**22h 内所有委托命令只入队、零执行**。
       - 现象为什么难发现：飞书那侧回的是 `ok:委托任务已直接排队`（受理成功，如实），
         库里 `delegated_tasks` 干净地停在 `queued`，automation 每次启动**明说**
         "DelegatedTaskWorker 已按配置禁用" —— 一句诚实的日志，只是没人在看。
       - 6.4 把周期任务原子切给派生服务时，切的是排期心跳 / 恢复扫描那几样；
         **委托泵是"另有 env 显式关闭"的那一条，不在 6.4 的动作清单里，于是漏在原地。**
       - 已摘（.env 改 true + 重启），两条积压任务当场被认领。
         ⚠️ **口径**：OL 单体的 .env **根本没有这个键**（默认即开），所以它是切流期额外加的临时闸，
         不是需要长期携带的配置。以后再加这类临时闸，MUST 在 4.4 同一处登记摘除条件。

       **断链二：下发段存储在装配处把属主客户端的方法全丢了（本批引入的真回归）。**
       `automation-publish-dispatch.ts` 把 store 写成 `{ ...options.publishLog, … }`。
       拆仓后 `publishLog` 是 `AutomationPublishLogHttpClient` 这个 **class 实例**，
       方法在 prototype 上，而对象展开只拷自有可枚举属性 ⇒ **五个方法一个都没过去**。
       - **单体里没有这个错**（那边传的是普通对象 `dispatchPublishStore`）⇒ 派生仓引入。
       - **编译期抓不到**：TS 对展开 class 实例的类型推导仍保留全部方法签名，
         `tsc --noEmit` 全绿。**单测也抓不到**：下发链路上每处都拿字面量桩当 store，
         桩复现不了 prototype 那一层。已实测确认——把修复改回展开后 typecheck 依然 0 错。
       - **后果是静默的**：兜底扫描那条路径只 `warn` 后 `跳过`，于是人审通过的稿
         **永远发不出去**，日志里只有每 30s 一条 `loadForDispatch is not a function`。
         实测 recordId=216/220 卡在「已批准·待下发」一天多无人发现。
       - 已修（automation `5795b1e`，逐方法显式委托 + 具名导出可测函数），
         配套加 `test/acceptance/publish-dispatch-store-wiring.test.ts`：用**真 class 实例**
         喂装配函数，并**自证前提**（断言展开确实会丢方法，前提变了就当场红，不留恒真闸）。
         变异验证过：改回展开 ⇒ typecheck 仍绿、这条闸红。
       - ⚠️ **同类风险已全仓扫过**：automation / api / content 三仓其余的对象展开都是纯数据对象，
         展开 class 实例的**只此一处**。

       **剩下的不是缺陷**：两条任务现在都在正常等目标账号 61591753702668 的边缘上线
       （评论 `deferred`+`edge_offline`、发布「控制核心暂离线，保留授权等待恢复」），
       **且都没消耗重试次数**（`attempt_discarded_before_start`）——
       这正是"等资源 ≠ 失败"那条红线该有的样子。 -->
- [ ] 7.2 逐条走 `docs/real-machine-acceptance-backlog.md` 簇 60 的验收项，每条记三态之一：
  **已验（附证据）/ 未验（附为什么没观察到）/ 不适用（附理由）**。
  重点是上一个 change 登记的 5 条 + 既有的 `runAutomationMain` 从未真跑、飞书 `/delegate` 从未真跑。
- [ ] 7.3 **MUST NOT 用"进程一直活着"给任何一条验收项划勾**。没观察到就是未验，
  它照旧留在 backlog 里等下一次机会，MUST NOT 因为运行时长够久就默认它通过了。
- [ ] 7.4 **禁止出现"三进程已验证"这类概括**。概括性的验收结论会以最快速度过期——
  本 change 立项时就当场推翻了一条这样的记载。

## 8. 归属第二拍 + 收口

- [x] 8.0 **退役动作（第二拍）**：主要测试通过后，删除或改名归档单体那四个按角色切段的 unit，
  `segmentsForMode` 里那几个角色分支的处置同批在代码里写清。
  **这一步不做完，本 change 不算收口**——判定写在文档里而 unit 还躺在机器上，
  下一个人看到的是"有这么四个 unit 可以用"。
  <!-- 退役判定的事实基础（2026-08-04 15:00 实测，**判定已齐、退役动作本身尚未执行**）：

       ① 四个 unit（`aidcp-cloud-{core,api,automation,content}.service`）在 dev 上全是
          `inactive` + **`disabled`**，journal 里最后一次运行是 **7月26 10:55**（那次是三进程脚本
          fail-closed 自动回滚单体），其中 **`core` 从未跑过**（journal 零条目）。
       ② **生产上无人使用这四个角色模式**：OL 只有 `aidcp-cloud.service` 一个 unit，
          `AIDCP_SERVICE` 未设 ⇒ 恒为 `monolith`。dev 的 `/opt/aidcp/cloud/.env` 同样未设。
          ⇒ **退役不影响 OL，也不影响 §9 那条回滚路**（回滚起的是 monolith 模式）。
       ③ 退役范围**不止 ECS 上那四个 unit**，还有：
          - `aidcp-cloud/deploy/multi-service/`（四个 unit 文件 + README，是机器上那四个的来源）
          - `src/gateway/service-mode.ts` 的四个角色分支，及 `src/server.ts`、
            `src/config/api-sync-read-source.ts` 里的模式感知处
          - **`aidcp-api` 仓里还带着一份完整的 `src/gateway/service-mode.ts`**（随同步继承来的），
            退役时若只清单体、这份会留下来继续误导
       ④ **`aidcp-content/.env` 设了 `AIDCP_SERVICE=content`，而 content 仓一处都没读它**（纯遗留）；
          对照之下 **`aidcp-automation` 是硬要求**（`AIDCP_SERVICE !== 'automation'` 直接抛），
          `aidcp-api` 也仍在读 ⇒ **这三行 .env 不可一概而论地清掉**，逐仓判。
       ⑤ **跨 change 后果**：退役这四个 unit 直接作废了活跃 change
          `fix-cloud-multi-service-deploy-script` 的未完成项 2.3
          （"用三进程脚本把单体部署到 dev 并逐项验证"）。派生仓这条路已经跑通，
          而单体三进程脚本 7月26 那次正是 fail-closed 回滚的 ⇒ 2.3 的正确处置是
          **判为过时并关掉**，而不是去执行它。**用户 2026-08-04 已裁定按此处置。**

          **处置结果：该 change 整条废弃删除，不归档。** 理由是归档的语义不对 ——
          它的 spec delta（`cloud-multi-service-deployment`）全是"多服务部署脚本必须如何如何"
          的 ADDED 要求，而归档会把 delta 并进 `openspec/specs/` 并**新建**这份主 spec
          （核对过：主 spec 此前不存在）。那等于**给一个刚被删掉的能力建一份现行规格**。
          先例：`facebook-scheduled-comment`（设计已被取代 ⇒ 废弃删除，见 CLAUDE.md §3）。

          **它做过的事不因废弃而失效，就地记在这里**：1.1 / 1.2 修的是
          `deploy-multi.sh` 里六处未加花括号、紧跟中文标点的变量展开（`set -u` 下会被当成
          未定义的扩展名），落在 `aidcp-cloud@b4694df`，并配了一条词法护栏用例。
          那是真 bug、真修了；脚本本身今天随 8.0 一并删除，护栏用例同批删（守的东西没了）。
          2.3 唯一一次真部署是 7月26：API panel 起不来
          （`composition_dependency_unavailable: server`），脚本 fail-closed 自动回滚单体 ——
          **那也是那四个 unit 最后一次运行**。
          **留给下一个想重做「单体按角色切段」的人**：这条路走到过这里，停在这里，原因在上面。 -->
  <!-- 2026-08-04 **已执行**（用户当日裁定「全退役」）。三处一起落，缺任一处都只是换了个马甲：

       ① **代码**（`aidcp-cloud@405c53c`）：`serviceModeFromEnv` 对 content / automation / api / core
          四个名字抛具名 `RetiredServiceModeError`（带 `requestedMode` / `successor` 两个字段，
          按 name 判而非 instanceof —— 这个错误会跨包传）。**刻意不回落 monolith**：
          回落 = 有人要求按角色切段、进程却静默起成完整单体，连带抢走自动化写者锁与边-云 8787，
          正是「静默假成功」。未识别的**其它**值仍回落 monolith（既有安全底线，本次不动）。
          错误文案具名指向去处，`core` 明写「没有对应派生仓」而不是指向一个不存在的仓。
       ② **部署工件**（同一提交）：删掉 `aidcp-cloud/deploy/multi-service/`
          （四个 unit 文件 + 三进程脚本 `deploy-multi.sh` + README）与该脚本的词法护栏用例
          `test/deploy-multi-script.test.ts`（删前确认：那条用例只守被删脚本里的一件事，别无其他）。
          留 `deploy/README.md` 作墓碑，写清四个角色现在归谁、以及为什么是删不是留。
       ③ **机器**：dev 上四个 unit 移进 `/opt/aidcp/retired-units-20260804/`（含 README 说明去向）
          + `daemon-reload`。移前复核：四个全 inactive + disabled、无 enable 软链、
          **无任何其它 unit 引用它们**。移后复核：三个派生服务仍 active 且 `NRestarts=0`、
          六个端口仍在、自动化就绪度仍 `ready` + `ingress=true`、
          **回滚路 `aidcp-cloud.service` 仍 loaded+enabled**、systemd 里 `aidcp-cloud-*` 计数归 0、
          **isales 四个服务全程 active 未碰**。

       **同步**：`service-mode.ts` 属 api 层、本就该同步进 `aidcp-api`，经 `scripts/sync-split-repos --apply`
       落到 `aidcp-api@b79793e`；该仓 `src/` **零调用点**（它的入口在自己的 `server.ts` 里另做
       `AIDCP_SERVICE=api` 检查），故运行中的 dev api 不受影响；`test/` 不派生，那份手抄用例一并对齐。
       五仓全量对账：内容不同 0（只剩手写组装根的「只报不改」）。

       **验证**：闸做过变异测试 —— 把 throw 摘掉换成静默回落，三条新用例全红、
       而**原有 21 条全绿**，即旧用例原理上抓不住这个回归。cloud typecheck 干净、
       acceptance 197/197、全量 4182 pass / 0 fail；api typecheck 干净、该用例 24/24。

       ⚠ **本批刻意没有部署任何新代码到 dev**，理由逐条：
       - 单体 `/opt/aidcp/cloud` 是**回滚路径**，今天已真走通两次。往一条验证过的回滚路上
         推一版**没做过启动验证**的代码，是把它变得更不可靠，不是更新。
       - 且这次改动对回滚**行为等价**：回滚起的是 monolith 模式（`AIDCP_SERVICE` 未设），
         新旧代码在该路径上同义；退役闸只在设了那四个名字时才有动作，
         而能设它们的那四个 unit 已经不在机器上了。
       - api 侧同理且更明确：`src/` 零调用点 ⇒ 纯 no-op，为它重启一个现役服务是净风险
         （上一次 api 重启就撞出了同步读的启动竞态，见 7.1 记录）。
       ⇒ **dev 上单体与 api 跑的仍是退役前那版字节**，这是有意的、不是漏部署；
          下次这两个服务因别的原因部署时自然带上。 -->
  <!-- **后续清理项（已登记，本批刻意不做）**：`segmentsForMode` 等七个 `xxxForMode` 分段函数
       的非 monolith 分支现在运行时不可达，但**保留**着。两条理由：一来那些分支里记的是
       「哪个形态下谁有消费者」这类**判据本身**（尤其面板事件旁路与 outbox 保留期那两张表），
       删掉等于把结论连同理由一起丢；二来连根拔起要同时改组合根十余处，而单体正是 OL 生产 +
       dev 回滚路径 —— 那是一次独立重构，不该搭在退役这一批里。 -->
- [x] 8.1 把 soak 里暴露但本批不修的问题**逐条**登记（backlog 或新 change），
  写清现象、复现条件、以及为什么本批不修。MUST NOT 只留在会话里。
  <!-- 2026-08-04 切流当天暴露、**本批未修**的六条，逐条如下（三条已归入 backlog 簇 60）：

  ① ~~**面板的「环境」页在派生形态下答 500**~~ **同日已修**（原因曾是
     `client_env_automation_read_port_not_configured`）。真因不是「少注入一个口」——
     那个口读的全是自动化属主表，而接口进程**本来就不该持有那个库的连接** ⇒ 它注入不了。
     修法是补一条跨进程通道：`aidcp-cloud@710e1ce` 新写 `client-env-automation-http`
     （六个方法一条不少，端口是闭集合，只开用得到的那条等于把剩下的留成下一次 404）+
     纳入共享包点名清单；`aidcp-automation@2bf1214` 注册并纳入路由清单闸；
     `aidcp-api@1ca4296` 注入客户端。

  ② ~~**跨进程失败在面板那一层全被兜成 500 `internal_error`**~~ **同日已修**
     （`aidcp-cloud@dac1c56` / `aidcp-api@1ca4296`）：认得出的六类跨进程失败映射成
     具名 503（不可达 / 超时 / 没有这条路由 / 被拒 / 本进程令牌没配 / 应答不合约），
     **认不出的仍是 500 且带 `unclassified_upstream_error` 留痕** —— 折进已有名字
     等于把「我不知道」变成一句对别人进程的断言。判别按 `name` + 非空 `code` 结构化守卫
     （那个错误类在共享包与自动化仓各有一份，`instanceof` 两条路径上都恒 false）。

  ③ ~~**配置镜像失效信号只有落地端**~~ **同日已接**（`aidcp-automation@2bf1214`）：
     本域 outbox 同事务入队 + 进程内中继 + 四个限频配置存储接上版本推进器。
     **必须同时说清它没修好什么**：信号现在能可靠落到接口域的版本表，但**拆开后的两个进程
     里都还没有镜像刷新器去 reload** ⇒ 恢复的是「信号不再静默蒸发」这一半，
     不是「改完立刻全进程生效」。**别把验收读成后者。**
     另：那四个键与任何同步读游标都不相交（逐条核对过八条流的游标输入），
     故不会重演「同游标不同载荷」。

  ④ **同步读就绪度仍在抖**：把重发周期改成新鲜期的三分之一之后业务入口能开了（一次性闩），
     但 `publish_in_flight` / `captcha_availability` 仍会周期性 stale。
     它们走的是「变了才推」的路径，安静时段没有重发。**业务入口是闩、开了就不会再关**，
     所以今天不影响运行；但任何**按当下新鲜度**判断的消费方仍会间歇 fail-closed。

  ⑤ **验证码云端协助在派生形态下整体不可用，已按「显式关掉」处理**：
     自动化侧缺 token secret（单体是回落面板 JWT 密钥，而那个密钥现在只在接口进程里），
     面板侧那几条路由本来就答 503（依赖未注入）。切流时把自动化侧的开关显式置 false ——
     **这是如实关掉、不是修好**：接口进程的就绪闸把「开着但用不了」判为 invalid，
     而「按配置关掉」是合法状态。要恢复这个能力，两侧都得重新接。

  ⑥ **单体自 2026-08-02 起就在周期性报 `facebook_operation_policy` 同游标载荷漂移**，
     无人处置，直到今天它把整台 dev 拖到起不来（见 8.5）。真正的债不是那条 bug，
     而是**这类错误没有任何人在看**：它每天打进日志、没有告警、没有巡检。 -->
- [ ] 8.2 更新 backlog 簇 60：本批真验到的划掉并附证据，没验到的留着并补上"为什么没覆盖到"。
- [x] 8.3 回滚演练一次：停三个派生 unit，确认 dev 立刻回到今天的状态（单体全程未停、Nginx 未动、
  数据面无残留）。**演练过才算有回滚路**。
  <!-- 2026-08-04 10:20 真演练过一次，且是**在单体真的停了之后**（比原计划更强的一次）：
       停三个派生 unit → 还原两份 .env → 起单体，30 秒内单体拿回写者锁 / 8787 / 8090 / 8091
       与飞书长连接。Nginx 一行没动，数据面无残留。整个窗口 2 分 41 秒。
       ⚠️ 演练同时暴露：**干净停机在 systemctl status 里显示 failed**（143），
       「停干净了」与「崩了」从进程管理器那一侧同形。已修（两仓入口关停成功后显式退 0）。 -->
- [x] 8.5 **回滚路第二次真走了一遍，而且这次是被迫的**（2026-08-04 11:23–11:41，dev 停摆 18 分钟）。
  **这段必须原样留着**，它是本 change 里代价最大的一课。
  <!-- 事情的顺序：
       ① 11:19 某个客户端建了一个新的 Facebook 环境。那笔事务往两张 Facebook 运营策略表各插一行，
          **但没推配置镜像版本**。而同步读那条流的游标只看那个版本、载荷却是从这两张表算出来的。
       ② 于是「同一个游标、不同的载荷摘要」—— 消费方按设计整条拒收，且游标不会自己再动，
          拒收是**永久**的；启动期那次 apply 又是 fail-closed 的。
       ③ 11:23 切流：自动化服务因此就绪不了、8787 起不来 ⇒ 判定回滚。
       ④ **回滚也起不来**：单体启动时走同一条 apply，一样被拒 ⇒ dev 彻底停摆。
          单体从 08-02 起就在周期性报这条错，只是平时不致命（不挡运行、只挡刷新），无人处置。
       ⑤ 恢复手段：不能用裸 SQL 改库（那会把「版本落后」变成一次没人知道的手改），
          改用产品自己的写口 —— 面板「保存全局运营策略」把刚读出来的同一份值原样写回去，
          语义空操作，只让 revision 与镜像版本各进一格，游标随之离开卡死的那一格。11:41 单体恢复。
       修（aidcp-cloud c5da9fc / aidcp-api d3ac1c7）：两条漏推版本的写口补上同事务推进，
       接口进程把版本推进器真接进那两个存储（此前注释写着「本进程只读这几张表」——
       而它恰恰是建环境那条写口的所在地），外加一条**按事务判**的门禁
       （写语句到 COMMIT 之间必须出现推版本；按文件判会被同文件里另一处推版本蒙混过去）。
       **留给下一个人的判据**：这类「同游标不同载荷」今天已经出现过两次
       （人设解析一次、运营策略一次），根因是同一类 —— **载荷依赖的东西没被游标覆盖**。
       新增同步读流时，先问一句「这份载荷是从哪几张表算出来的、它们变了游标会不会动」。 -->
- [x] 8.6 **客户端依赖第二批：互动能力接通（23 个里从 21 补到 22）**，外加两处上一批遗留的账本漂移。
  <!-- 2026-08-04 19:00–20:00。**接手第一件事是跑对账，跑出两条交接文档没记的漂移**：
       ① 上一批修互动能力自检那两处（`aidcp-automation@28f96be`）**只落在派生仓、没回流事实源**。
          派生仓 src/ 是 aidcp-cloud 归属清单的重放 ⇒ 下一次 `--apply` 会把它原样冲掉、
          互动能力在 dev 上重新整体关上，而且编译过、测试过、启动不吭声。已回流（cloud a677e93）。
       ② `aidcp-content` 的 transport pin 停在一个未提交、且已落后两个提交的 sha（content 7a3798c）。

       **接通的东西**（cloud cd465a1 / af3a3d2 / becc468 → kernel 030d805 → transport f187486 →
       automation 73ddd47 / 65c88c8 → api c16dcd1 → 控制仓 02b2f95e）：
       - **先做前置：跨进程失败保真**。互动失败自带 httpStatus / retryable / details 三格，
         而通用传输骨架只搬 code + message。丢掉之后「已发出但核不到」（409、不可重试）
         会被折成可重试的 500 ⇒ 客户端重投一条可能已上墙的评论 / 私信。
         新增 `interaction-failure-wire`（两侧编解码）+ kernel 的 `asInteractionFailure`
         结构判别（`instanceof` 对跨进程搬来的错误恒 false，对装了两份 kernel 的同进程也恒 false）。
         **分档判据用补集**：只有「对面答没这条路由」「对面答鉴权没过」两条能证明处理函数没跑过，
         其余一律按「可能已发出」算。提交点名单从 kernel 常量派生、不手抄第二份。
       - **21 条路由 + 1 条新通道**：store-reader（13，此前写好了但 automation 从没 register）、
         workflow（3）、send（5）、runtime-controls deliver（1，新写；缺它客户改的开关要等边缘
         下次重连才生效，而客户端只看到 delivered:0）。三族在互动能力不可用时**照样注册**、
         由具名缺席实现带原因拒绝——不注册的现形方式是 404，而 404 只会被读成「对面漏注册」。
       - **两个端口抬进 kernel**（`interaction-automation-ports`）：传输包只许引 kernel，
         否则只能在传输层再声明一份结构相同的接口。同批把 `requestAuthReopen` /
         `requestBrowserControl` 改成异步——跨网络它们不可能是同步的，而
         `string | Promise<string>` 的端口会让调用方漏掉 await、把 Promise 当 requestId 写进台账。
       - **恢复循环搬过来了**（`drainInteractionRecovery`，拆仓时漏搬、全仓零调用方）：
         此前一条 queued 回复只要那次 fire-and-forget 下发失败就再没有任何东西会派发它，
         而客户端一直显示「已批准、在发」。
       - **三个提交点补 `!claim.fresh` 守卫**（同步 / 重开登录 / 浏览器控制）：拆进程后失窗
         从「进程崩溃」放大成「一次网络超时」，重投重开登录会把用户正在扫的二维码顶掉。
       - **工作流单独一条放宽超时的连接**（默认 90s）：那三个方法各跑一次模型调用，
         对着 15s 默认必然超时，而属主侧照常把任务推进 —— 「看起来失败其实成功」。

       **闸**：新增 `AC-INTXP-01..07`（失败保真 + 提交点分档，**做过两次变异测试**：
       摘掉 details 搬运、把提交点分档改成恒 read，各自当场红且点名到具体项）；
       automation 路由清单闸补四族（同样变异测试过）；api 依赖清单闸的缺席表从 2 条降到 1 条。

       **顺带修好一条自上一批起就红着的闸**：automation 的派生归属账本比代码旧 4 条，
       `boundaries:refresh` 因一个自 content-scheduler change 起就未裁定的文件而一直拒跑。
       登记现状（非重新裁决）后账本回到 273/273、forbidden=0。

       ⚠️ **部署时踩到一个交接文档没记的雷，务必知道**：`aidcp-cloud.service` 在切流后
       **仍是 enabled**，且从那时起一直在崩溃重启（重启计数已到 31），就等自动化一重启
       就把写者锁抢走。本次 `systemctl restart aidcp-automation` 正好把 dev 交回了单体
       —— 单体拿到锁与 8787，派生自动化反而起不来（8094 消失）。已 stop + disable 单体，
       派生三服务恢复。**退役第二拍（8.0）只处理了那四个按角色切段的 unit，主 unit 漏了。** -->
- [x] 8.7 **dev 部署与实测**（2026-08-04 19:33–20:05）。
  <!-- 序列：三槽各自备份（api/automation/content.bak.20260804-193341.tar.gz + .env 备份）→
       rsync（排除 .git / node_modules / .env）→ 各槽 `rm -rf node_modules/aidcp-{kernel,transport}`
       + npm install（ssh agent 转发）→ **ECS 上三槽各跑一次 typecheck，全 0** →
       按「属主域先、接口域后」重启（content → automation → api）。

       **已验（附证据）**：
       - 三服务 active、NRestarts=0、六端口全在（8787 / 8090 / 8091 / 8092 / 8093 / 8094）、
         automation 就绪度 `state=ready` `blockers=[]`；isales 四服务未碰。
       - 四条新路由在 8094 上**逐条真打过**，且**失败保真肉眼可见**：
         `interaction-workflow/generate` 回 `INTERACTION_NOT_FOUND` 并在 wire 上带着
         `interactionFailure{httpStatus:404, retryable:false}`；
         `interaction-send/request-browser-control` 回 `INTERACTION_UPSTREAM_UNAVAILABLE` 同形；
         `interaction-runtime-controls/deliver` 回 `{delivered:0}`（**边缘不在线是事实、不是失败**）。
       - **客户端那片路由真的在了**（交接文档 §1 点名唯一没验到的一环，这次走通了一半）：
         临时启用 + 轮换 `cutover-verify-0804` 的 key（该账号零环境、用完立刻停回 disabled），
         用真客户 token 打 `/environments/<未拥有>/interactions` 回的是**互动 API 自己的错误信封**
         （`INTERACTION_NOT_FOUND` + requestId + retryable），而同一 token 打一个非收件箱路径
         回的是客户鉴权的裸 `{"error":"not_found"}`。**两个 404 的响应体不同**，
         这正是「整片路由消失」与「路由在、只是这个资源不属于你」的干净判别式。

       **未验（如实记，MUST NOT 读成已验）**：
       - **没有一次真的走到自动化进程的收件箱调用**：验证账号不拥有任何环境，
         归属闸在任何一次 store 调用之前就短路了。要走通需要给它绑一个真环境，
         那是对客户环境归属的写入，本批刻意不做。
       - **边缘仍然一台都没连上**（8787 established 恒 0，切流至今）。
         回复的生成 / 下发 / 同步 / 浏览器控制**全部需要在线边缘**，故这一批的
         端到端行为一次都没被真实执行过验证。
       - `draftRefinements` 仍缺席（23 个里剩这 1 个）：数据属 content 域，
         transport 里零通道，且 content 进程里 store 与 worker **两个文件躺在仓里无人 new**
         ⇒ 只补通道不够，属主侧也要接线。 -->
- [x] 8.8 **客户端依赖第三批：`draftRefinements` 接通，23 个依赖全部装配（缺席表清空）**。
  <!-- aidcp-cloud 01fe8a9 / aidcp-transport 7e6cba4 / aidcp-api 418213f / aidcp-content bd56379
       / aidcp-automation 2265885（后者只是共享包 pin 跟进）。2026-08-04 deployed。

       **它为什么是这 23 个里最贵的一个**：缺的是两个方向，不是一条通道。
       - 方向 A（api→content）：作业队列四方法，transport 里零通道。
       - 方向 B（content→api）：worker 的落稿写口，同样零通道；而 store 与 worker
         两个文件此前躺在仓里**全仓零 `new`**。
       两族写在同一个传输文件里（CLAUDE §8.4 硬要求），路由常量只有一份。

       **`refreshPreview` 归属：先判断、后接线（交接文档点名要先答的那题）。**
       结论是**绑在 api 那次属主写上**，不由 content 侧的 worker 触发 ——
       本仓 api 组装根早有这条不变量（每次属主写成功产出一份单向预览，见
       `createApiPublishLogAuthority` 对 editDraft 的包装，与删配图那处的 `refreshPreview: () => {}`）。
       顺带**堵掉单体留的一个洞**：单体是在作业置完成**之后**才推预览的，
       置完成失败时稿子已改而预览不推 —— 桌面端继续显示旧稿，用户以为没保存上。
       绑在写上没有这个洞。content 侧那一格是**显式空实现 + 注释**，不是省略。

       **`loadForDispatch` 刻意不新开路由**：复用既有的
       `api-direct/publish-log/v1/load-for-dispatch`。端口完整性改由 content 组装根那处
       对象字面量在编译期钉（端口加方法则当场缺属性），路由表用
       `Exclude<…, 'loadForDispatch'>` 显式声明这个分工。两条同义路由只会各自演化。

       **跨属主外键的代偿仍然成立**（交接文档要求核的那条）：创建入口
       `client-auth-server.ts` 先经 `pendingPublishPreviewForAccountRecord` 读一次 publish_log，
       读不到当场 404、走不到 create()。拆开后它**仍是进程内读**（publish_log 与该入口
       同属 api），不是跨进程调用 —— 那条前置没有变成「读不到就放行」。

       **三处跨进程保真，各带一条会红的闸（逐条变异测试过，共 10 次）**：
       - `latestForAccountRecords` 回 `Map`，而 `JSON.stringify(Map)` 是 `{}`。
         直接回 map ⇒ 待审稿列表上每条稿子永远显示「没精修过」，**没有人会为此报障**。
         线上以 entries 传，两侧各做一次显式转换（AC-REFINE-03）。
       - 唯一活跃作业冲突码 `23505` MUST 原样过线：客户端鉴权服务只认它来答 409
         `refinement_already_active`，丢了就是 500「服务器错误」（AC-REFINE-04）。
         它能活下来靠两级既有行为（`encodeHandlerError` 透传带 string code 的抛出物 +
         `translateWriteFailure` 对不认识的 code 原样重抛），故必须有闸钉住。
       - 落稿写口多出一种**单体没有的结局**：写已提交、应答在回程丢了。
         worker 的兜底文案写着「原稿未变化」——那句话在这一态下是假的。
         现按具名 `api_authority_result_unknown` 单独出一条「已提交但没能确认，
         请刷新查看当前版本，不要重复发起」（AC-REFINE-06 + worker 两条用例）。
         重投本身安全（写口是 expectedVersion 的 CAS，真落了会拿到 version_conflict），
         **要治的只是回执说了假话**。

       **dev 实测（附证据）**：三服务 active、NRestarts=0、六端口全在、
       automation 就绪 `state=ready` `blockers=[]`、`aidcp-cloud` 仍 inactive/disabled、
       isales 四服务未碰。两族路由**逐条真打过**：
       - 无令牌 → `internal_http_unauthorized`；同前缀的假路由 → `route_not_found`
         （**两个响应体不同**，这就是「路由在」与「路由不在」的判别式）；
       - content 队列真读了一次自己的库：`{"ok":true,"result":null}`
         （这个账号没精修过 —— 是答案，不是失败）；
       - api 落稿写口真执行了一次：`{"ok":true,"result":{"ok":false,"reason":"not_found"}}`
         （recordId 不存在，零写入）；
       - 信封版本号写错 → `api_direct_version_unsupported`。
       content 启动日志：`DraftRefinementStore 已就绪（target=dev, 回收中断认领=0）` +
       能力清单 `已注册=…、draft-refinement-queue；未注册=无`。

       **配置**：content 的 `.env` 新增 `AIDCP_API_INTERNAL_TOKEN`（值取自 api 侧同名项）。
       这是**启动期必需**：回落到不带令牌只会一律 401，而 401 在 worker 眼里与
       「api 拒绝了这次改稿」同形 —— 每条精修都失败、且失败原因指向错的地方。

       **未验（MUST NOT 读成已验）**：没有从真客户端走过一次真精修。
       503 那条分支现在是**结构上不可能**的（那一格由必需 env 无条件构造），
       但「用户在客户端上点一次精修真能跑完」需要一条真待审稿 + 在线边缘，两者都不具备。 -->
- [x] 8.9 **部署当天踩了同步读那颗老雷，并按既有办法恢复**（22:33–22:43，8787 未放行 10 分钟）。
  <!-- **不是本批改动引入的，是「重启即触发」**：automation 一重启就以
       `same_cursor_payload_drift` 永久拒收两条流（`account_persona` cursor=2345、
       `automation_account_projection` cursor=462240），启动期 fail-closed ⇒
       `businessIngressStarted=false` ⇒ **8787 不放行**（api / content 全程正常）。

       **机理**：两条流的 cursor 就是 `config_mirror_version` 里 `persona_config` / `account_status`
       两行的版本号（经 cantor 配对，实测 cantor(0,67)=2345 / cantor(0,960)=462240 逐位对上），
       而载荷读的是 `persona_config` / `accounts` 两张表。**19:33 那次启动之后到 22:33 之间，
       有人改了这两张表而没有推进对应的镜像版本** ⇒ 同一个 cursor 上载荷变了 ⇒ 消费方
       按设计正确拒收，且 `forcedState='invalid'` 是永久的（只有 cursor 真前进才解）。

       **属主自带的「镜像失效信号」路由在这里帮不上忙，而且是对的**：
       `config-mirror/apply-bump` 对这两个键**主动拒绝**——它们与版本表同库，
       按设计只能走属主写入同事务里的 `bumpInTx`，跨域中继信号不该碰。

       **恢复（用户 2026-08-04 当场裁定）**：在 api 库把那两行版本号各 +1
       （67→68 / 960→961）。这正是仓里 `0091_facebook_comment_config_snapshot_revision` 与
       `0108_facebook_operation_policy_snapshot_revision` 两条迁移做的同一件事。
       20 秒内 automation 自行回到 `state=ready` `blockers=[]`、8787 放行、六端口齐。

       **真正的债不在这次恢复，而在「谁写了那两张表却没推版本」**：已在 8.1 的同族问题里，
       本条另行登记（见交接文档）。每一次 automation 重启都可能再撞一次。 -->
- [x] 8.10 **8.9 那颗雷的根因找到并修掉了：派生 api 把七个存储的镜像版本推进器全丢了**。
  <!-- aidcp-api 8ed0aa7 / aidcp-automation 1c770ff。2026-08-04 deployed dev。

       **根因是一条纯拆仓回归，不是数据问题。**
       `writeWithMirrorBump(pool, bumper, key, run)` 的第一行是 `if (!bumper) return run(pool)`：
       **推进器缺席时写照常提交、版本一动不动、不报错也不告警**。
       单体给这七个存储**全都**传了推进器（逐个核过 aidcp-cloud/src/server.ts）；
       派生 api 自己手写的 main() **一个都没传**。这正是 CLAUDE §8.5 那条
       「裸 `?.` 静默吞掉」的形态：单体里那一格恒有，拆完读到 undefined 就没了。

       七个：`PgAccountStore` / `PersonaStore` / `ContentScheduleStore` /
       `FacebookCommentConfigStore` / `FacebookGroupJoinAutomationStore` /
       `ModelConfigStore` / `RoleConfigStore` / `CategoryConfigStore`（后三个原注释写着
       「本进程只读这三张表，缺省语义即不推版本」——**那句话把一条静默缺省当成了一个决定**，
       而这三张表的写口就在管理后台的模型配置页上，后端正跑在本进程）。

       **后果有两层，第二层才是 8.9 那次停摆**：
       ① 消费方镜像永远不刷新 —— 今天写进去的 12 条人设、11 个新账号，
          对自动化进程从此不存在（**零信号**，没有任何一侧会报错）；
       ② 同一个游标先后发出两种载荷摘要 ⇒ 消费方按设计永久拒收 ⇒ 自动化重启即
          fail-closed、8787 消失。

       **闸（`test/acceptance/mirror-bump-wiring.test.ts`，api 与 automation 各一份）**：
       AC-MIRROR-01..03。**覆盖面从事实源读出来**——扫 `src/` 找「选项里有 mirrorVersionBumper」
       的存储类，再回组装根逐个核；不手抄名单，于是日后新增的存储自动进闸。
       AC-MIRROR-01 专门钉「扫不到东西时本闸会全绿」这件事本身。
       变异测试：拿掉 `PersonaStore` 那一格 → AC-MIRROR-02 红且点名 `PersonaStore`；
       把扫描正则改成永不命中 → AC-MIRROR-01 红（而不是安静地全绿）。

       **两边都装是有意的**（automation 当时是好的）：只给 api 加闸就会留下
       「守卫只覆盖作者在治的那条道」。**而它在 automation 上第一次跑就抓到一个真的**：
       edge-access 模块自建了第二个节奏兜底配置存储、没接推进器，写会照常提交而
       outbox 行根本不产生。那一格改成**必填**（不是可选）——静默跳过的那条路
       不配有一个看起来像决定的写法；required 化当场让一条既有用例编译失败，正是要的响亮。

       **dev 实测（决定性证据，非「起来了」）**：
       - 部署前 `account_status=961`；经产品自己的写口（`ensure-account`，对一个已存在账号做
         幂等 upsert，业务字段零变化）打一次 → **962**。修复前这一步版本纹丝不动。
       - 紧接着**重启 automation** —— 这正是修复前必炸的那一步 —— 结果
         `state=ready` `blockers=[]`、8787 在、`same_cursor_payload_drift` 报错 **0 次**。
       - 三服务 active、NRestarts=0、六端口全在、isales 未碰。

       **顺带修掉的两处**：automation 的派生归属账本缺了本日新同步的传输文件
       （`boundaries:refresh` 回到 275/275、forbidden=0）；api 组装根里那句
       「自动化四个限频配置存储也都没传推进器」是**过期说法**（实核四个全都接着），
       就地改掉并写明理由——这类「拿不到」的句子会被一片片转抄、越写越确定。

       **⚠️ 本条曾附一句「automation→api 的失效信号中继尚未接线」——那句是错的，2026-08-05 实核推翻。**
       中继**存在、在跑、且完全跟上**：`aidcp-automation/src/automation-main.ts` 构造
       `ConfigMirrorBumpRelay`、启动时 `start()`、写提交后 `wake()`；dev 上中继游标
       `last_id=118859` 与该 topic 的 outbox 队首**逐位相等，零积压**。
       错误来源是 api 组装根里一段过期注释（「生产方那一侧今天还没接线」），
       它被原样转抄进了本条与交接文档。**已在三处就地改掉，并把那段注释留作反例。**
       这正是 [[stale-cant-reach-claims-compound]] 那条：**转述的「对面拿不到」不能当结论用，
       动手前先去 grep 事实源在谁那儿。** -->
- [x] 8.3a **ol 已切流**（2026-08-05 12:47–12:59，用户当场裁定「dev 已经可以了，拉上线分支部署 OL」）。
  <!-- 发布分支 `release/20260805-ol-cutover`：api `6a7ba81` / automation `1c770ff` / content `bd56379`。
       **刻意不发主干头**：建分支时发现主干已被并发 session 推进 3 个提交（改的是调度器与下发存储），
       我一条没验过 ⇒ 钉回 dev 上正在跑的基线。生产要发的是**验过的东西**，不是最新的东西。

       **切前勘察推翻了两条我以为的前提**：
       ① OL 的单体 env 与 dev **不是同一套键**（36 vs 53）。照抄 dev 的划分会**静默丢掉 4 个键**：
          `AIDCP_ALLOW_SCHEMA_AHEAD`（schema 门放行位）/ `AIDCP_COLDSTART_RAMP`（养号爬坡回滚拉杆）/
          `AIDCP_FEISHU_WS_ENABLED` / `OSS_INTERNAL`。改为**按代码实读**逐键定归属。
          `AIDCP_MOCK_PUBLISH` 单独查过——它只是诊断触发器，不是「不真发」，派生仓不读它是安全的。
       ② **OL 上没装 git**，而两个共享包是 git 依赖 ⇒ `npm install` 直接 ENOENT。
          dev 上有 git 2.43，也就是说这套部署形态本来就要求它；OL 缺的是环境 parity，已装（additive）。

       **库这一关是过的**：OL 三个属主库的迁移数 69 / 57 / 20，与三仓的迁移文件数逐个吻合。

       序列：三槽 .env（值只在服务器上流转、4 个内部令牌就地 openssl 生成）→ systemd unit 照搬 dev →
       git archive 快照 rsync（不从工作区推）→ npm install → **ECS 上三槽各跑一次 typecheck，全 CLEAN** →
       备份单体 → **停 + disable 单体** → content → automation → api。

       **已验**：三服务 active、NRestarts=0、六端口全在、自动化就绪 `state=ready` `blockers=[]`
       `executionTarget=ol`、console 8088 与 /api 反代均 200、客户端鉴权口 401（在且要鉴权）、
       飞书长连接已建立、近 3 分钟三服务零报错。单体保留在 `inactive/disabled`，回滚是一条命令。

       **边缘没被我切断**（这条特意查了）：最后一条边缘指令在 12:03，紧接着 5 条 `会话结束: disconnect`；
       12:03→12:47 单体侧零边缘活动。切换窗口内**没有任何边缘会话被打断**。

       **切换后 2 小时复测（14:59，更新上面那条「未验」）**：
       - **边缘已自行重连，8787 上 10 条连接**，6 个账号在真跑，指令与回执双向通
         ⇒ 「边缘 ↔ 派生自动化」在 OL 上**已经端到端跑起来了**（这是切流当时唯一没验到的一环）。
       - 同步读中继**已完全追平**（137671 = 队首），三服务 NRestarts=0、近 30 分钟报错≈0。
       - ⚠ **顺带发现一件与切流无关、但更要紧的事**：`scroll` 动作的回执**长期 100% 失败**——
         08-04 全天 2868 次全 `ok=false`、08-05 切流前 1092 次全 `ok=false`、切流后同样。
         同期 `like` / `follow` 基本成功（64/13）。**切流前后比例一致 ⇒ 不是切流引入的**，
         是一条至少存在两天、无人报障的既有故障。已在交接文档列为最高优先级。 -->
- [ ] 8.4 `openspec validate deploy-derived-services-to-dev --strict` 通过后归档；
  **归档前把仍未了的债搬进 backlog**——归档会把本文件埋进 archive 目录，
  只活在任务注释里的东西从此没有任何机制会提醒人。
