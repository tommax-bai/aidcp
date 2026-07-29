## 0. 准入与三个岔口的裁决（**未完成前不写任何代码**）

- [x] 0.1 控制仓 `./scripts/task-preflight` 通过；按 CLAUDE §7 为 cloud / kernel / transport / api /
  automation / content 各开 `../<repo>.wt/split-cloud-automation-production-runtime` worktree
  （控制仓在 `main` 上直接写本 change 目录，不切分支）。
  <!-- 2026-07-29 六个 worktree 已建，分支名 codex/split-cloud-automation-production-runtime，
       均自各仓 origin/master 切出；四仓 preflight 全绿。 -->
- [x] 0.2 重跑 `./scripts/sync-split-repos --ref origin/master --tests`，确认除组装根外零差异；
  把实测 HEAD 回写 design.md §0，**不要沿用文档里的快照**。
  <!-- aidcp-kernel d7153b3 / aidcp-transport 6cd3339 / aidcp-api 02396d8 /
       aidcp-automation 71e5299 / aidcp-content d72d653，源 aidcp-cloud@babdd84。
       cloud 期间前进 4 提交带来 4 个文件漂移，已 --apply --tests 同步；kernel 契约变更
       连带四仓 pin 快进（见 design.md §0 那段 pin 纪律）。同步后各仓 typecheck 0、
       测试 57/470/1841(+3 skip)/455 全绿。复跑对账仅剩组装根差异（按设计从不同步）。 -->
- [x] 0.2a 六仓 worktree 装依赖（`npm install --userconfig /dev/null`，绕内网 registry 对
  `@types` 域的劫持）。
  <!-- 2026-07-29 cloud / kernel / transport / api / automation / content 六个 worktree 各自独立装，
       不共享 node_modules 软链（CLAUDE §7）。 -->
- [x] 0.3 逐条重放 12 条 blocker 的 evidence（`aidcp-cloud/boundaries/composition-root-independent-blockers.json`
  按 `file#符号` 定位），确认每条今天仍成立；不成立的当场记下并说明为何。
  <!-- 2026-07-29 六路勘察 + 三路对抗性复核。12/12 全部仍成立，无一条已被消解。
       cloud 侧 11 条另有机械证据：test/acceptance/composition-root-4a-inventory.test.ts
       的 AST 派生探针实跑 6 pass / 0 fail（该测试自熄——依赖真被解决就会 deepEqual 失败）。
       第 12 条由读 runAutomationEntry 源码确认。复核同时推翻 / 补正了 8 处，见 design.md §5.5。 -->
- [ ] 0.3a **台账其实有三份，第三份已静默漂到 20 条**：
  `aidcp-automation/boundaries/composition-root-independent-blockers.json` 是手写台账的陈旧快照、
  全仓零读取点（多出的 8 条是 4b 已关闭的镜像项）。§4 的「两份同批收缩」实为**三份**。
- [ ] 0.3b **给 automation 台账加机械锚**：cloud 那份是 AST 派生、自熄；automation 那份是手写、
  无任何机械力量把它钉在现实上——**这正是它会漂的原因**。清零前先补锚，否则清完还会再漂一次。
- [ ] 0.3c **三条 `identifier` 探针不具判别力**（`concept` / `curated` / `facebookPublishMedia`）：
  `src/server.ts:3900` 是 segC 开头一整行解构，三个名字都在里面——真实调用点改成 HTTP 后探针照样命中，
  删解构而真实调用还在则探针静默放行。**改法必须与 census 探针一起定**，否则「台账清零」证明不了任何事。
- [ ] 0.3d **补进台账：文字卡 OCR 整条子链**（segC 内构造、属主全是 content、automation 仓全无）：
  `OpenAiCompatVisionClient` ×2（6473/6486）、`createCoverFormSensor`（6479）、
  `createTextCardTranscriber`（6493）、两个 provider/model 解析闭包（6460/6461），
  另有 `new PersonaGenerator`（5290）、`new ReplyAiService`（4693）、`hasUserRejectionEvidence`（7506）。
- [x] 0.4 **岔口 A 拍板**：模型调用出口归属。
  <!-- 2026-07-29 用户裁定 A1：提进 aidcp-transport，三家各自 new，密钥各自从 env 读。
       理由＝符合 transport 准入（三家都可能调用 + 不含任何属主表 SQL），且热路径不加内网跳。 -->
- [x] 0.5 **岔口 B 拍板**：四个内容属主角色工厂归属。
  <!-- 2026-07-29 用户裁定 B1：四个角色类改判归 automation，写 content 表走 §3 写口。
       理由＝与 §10.7 发帖调度器同形，端口包不了工厂函数。
       尾巴未决：curated_note_evaluator 的可选 textCardTranscriber 依赖仍需在实施时一并处置，
       见 0.5a。 -->
- [x] 0.5a 处置 `curated_note_evaluator` 的**可选** `textCardTranscriber`（content 属主视觉行为类，
  旗标默认关）：一并改判、或显式走 content 调用口。**不许默默不传**——可选实参缺席不报错。
  <!-- 2026-07-29 用户裁定方案 A：转写器留 content，automation 经 content 内部调用口使用。
       实测推翻了「一并改判」：它依赖的 cover-form-sensor.ts 是真·双段共用——组装根在
       segB(3664) 与 segC(6479) 各建一个实例，另有 cover-card-writer / post-image-form-profile
       两个 content 消费者；搬会打断 content，复制则两份实现只有真跑才对不上。
       详见 design.md §2.5。 -->
- [ ] 0.5b 先修「缺席被静默吞掉」：`curated-note-evaluator.ts:145` 与 `:179` 的
  `this.textCardTranscriber?.enabled()` 改成显式能力状态，让「旗标关掉」与「依赖没接上」可区分。
  **与 0.5a 选哪条无关，都必须做**（CLAUDE §8.5 的裸 `?.` 静默吞形态）。
- [ ] 0.5c 抬两个纯函数进 kernel：`normalizeCuratedReferenceImages` / `orderedTextCardTexts`
  （现居 `src/cache/curated-content-store.ts`，实测零 SQL）。**这一步与 0.5a 的裁决无关也该做**——
  `orderedTextCardTexts` 本来就还有一个 content 侧消费者（发布链封面卡撰写角色），不抬必出两份实现。
- [ ] 0.5d 修「假消边」残留：`curated-note-evaluator.ts` 与 `text-card-transcriber.ts` 的类型 import
  改指 `../kernel/curated-content-types.js`，不再经 `../cache/curated-content-store.js` 的再导出壳
  （类型早已抬进 kernel，消费方没改指；扫描器认 import 说明符，那条边账面上仍在。CLAUDE §8.3）。
- [ ] 0.6 **岔口 C 落实**：content 属主存储写走 content 内部 HTTP 写口，在既有
  `AIDCP_CONTENT_PORT` 监听上扩，不新造监听。**范围按 0.3 复核修正**（见 0.6a–0.6c）。
- [ ] 0.6a **撤掉草稿精修那一条**：`src/server.ts:6171` 的守卫是 `seamMode !== 'automation' && ...`，
  该 worker 在 automation 模式下本来就不跑；剩余两条证据都是 api 侧。
  automation 方向现存 runtime 边为零，**不开这个写口**。
- [ ] 0.6b **概念池端口面补齐到 6 个方法**：除 `addCandidate` / `loadPool` / `markSearched`，
  还有 `countNewSince` / `getNewConceptsSince` / `getNewConceptsWithSourceSince?`
  （`aidcp-automation/src/publish-agent/publish-scheduler.ts:34-39`）。
  `getNewConceptsSince` 是**回落分支**，漏了只有回落时才炸。
- [ ] 0.6c **精选库补跨界读 `selectForCreation`**：两个调用方（发帖调度器 / 评论调度器），
  **投影形状不同**。今天 `server.ts:7024` 的 `: Promise.resolve([])` 降级形状跨进程后会把
  「连不上」吃成「没有精选素材」，MUST 换成可区分的结果。
  另：`server.ts:4986` 与 `:5311` 只把 store 当「有没有」用，MUST 换成显式可用性查询。
- [ ] 0.6e **「能力探针」跨进程后恒为真——比可选方法漏实现更糟。**
  今天的回落写法是 `this.d.conceptStore.getNewConceptsWithSourceSince ? … : …`，
  一个 `typeof` 能力探针。跨进程后客户端类**总是**定义着那个方法，探针恒真、**回落分支变死代码**，
  而真实的能力缺口（对面版本落后 / 路由没注册）反被静默吞掉。
  → 端口上两个读方法**都不带可选标记**，回落改由具名的 `unsupported_method` 驱动。
  **保留 `?` 等于保留一张假的安全网。**
- [ ] 0.6f **降级形状有三处，只改一处等于没改**：
  ① `src/server.ts:7024` 的 `: Promise.resolve([])`（组装根层）；
  ② `aidcp-automation/src/comment-agent/comment-scheduler.ts:1603` 的 `.catch(() => [])`
  ——**即使组装根那层改了，调度器自己这个 catch 仍会把端口抛出的传输失败重新吃成空数组**；
  ③ `role-dispatcher.ts:2456` 的「PG 不可用 / 装载失败 → 回退空池」。
- [ ] 0.6g **调用点比原记录多两处**（接线时都要改）：`markSearched` 有两个
  （`role-dispatcher.ts:3411` 下发搜索后 + `:3714` 回执后）；`countNewSince` 有两个
  （`publish-scheduler.ts:263` 聚合输入 + `:323` 概念积累扳机）。
- [ ] 0.6d **Sink 的可选方法是第二处静默陷阱**：`CuratedNoteSink` 的 `refreshReferenceImages?`
  与 `getTextCardContext?` 都用 `?.` 调用（`:153` / `:182`）。换成 HTTP 客户端后**少实现一个方法
  编译通过、运行不报**——少 `getTextCardContext` 则缓存恒空、每篇图文帖重跑视觉转写（纯成本爆炸、
  零错误信号）。端口面 MUST 显式声明可选能力的在场与否。
- [x] 0.7 落实 B1 的归属改判：先改控制仓 `docs/cloud-service-decomposition-proposal.md` §4.x
  （**归属的唯一事实源**），再手工 Edit 增量追加 `boundaries/ownership-rules.json`，
  最后 `npm run boundaries:refresh` 生成派生物；MUST NOT 直接手改生成物，
  MUST NOT 脚本整体重序列化规则表（CLAUDE §8.2）。
  <!-- 2026-07-29 事实源新增 §7.2.1（判据三的四个角色改判 automation，persona_generator 不在范围内）；
       ownership-rules.json 手工 Edit 六条 fileOverride：四个角色 + content-role.ts 由 content 改
       automation，另新增 curated-gate.ts 的点名（src/publish-agent/ 目录默认 content，必须逐文件点名）。
       改判闭包实测：content-role.ts 的消费者恰好只有那四个角色（persona-generator 与
       cover-form-sensor 的命中都只是注释，已逐条核过）。boundaries:refresh 待并行流的新 kernel
       文件归属条目补齐后统一刷一次。 -->
- [ ] 0.7a **改判的连带项：角色名合同测试会横跨两个属主。**
  `test/agents/content-role-names.test.ts` 同时引用四个改判角色与 `PersonaGenerator`（留 content），
  改判后它按 import 派生就成了跨属主测试、**留守 cloud，两个派生仓都不跑它**。
  那道闸守的是「角色名写错一个字母 → 调度器按名字查不到模型配置 → 静默用默认模型跑、零日志」，
  **不能就这么失效**。按属主拆成两份，或明确记录它为何留守。
- [ ] 0.7b **同步时需要 `--prune`**：四个角色 + `content-role.ts` + `curated-gate.ts` 要从
  `aidcp-content/src` 移除、进 `aidcp-automation/src`。`sync-split-repos` 默认只报不删，
  **必须显式 `--prune`**，否则 content 仓会同时留着旧副本（两份实现，本项目点名的失败形态）。
- [ ] 0.8 落实 A1：模型出口进 `aidcp-transport`。核对准入判据实跑一遍
  （`test/acceptance/module-boundary.test.ts` 的真正则，别凭记忆用「四条硬禁」），
  再按 kernel → transport → 三个业务仓的顺序快进 pin。
  <!-- 0.4 的裁决实质成立且已实跑核过：qwen.ts 548 行、SQL/池/存储引用零命中、import 只指 kernel。
       但 0.4 记的理由有一条是错的，见 0.8a。落点闭包见 0.8b/0.8c。 -->
- [ ] 0.8a **更正 0.4 的密钥口径**：0.4 写的「密钥各自从 env 读」与生产事实不符——真实做法是
  **库内优先、env 回退**（`server.ts:2295-2297` / `:2337-2341` 走 `credentialStore.getSecretForRuntime`），
  content 手写 main 已改成经属主侧窄读口取（`aidcp-content/src/server.ts:421-428`）。
  **按字面实施会让后台「厂商密钥」页对 automation 进程彻底失效且无任何信号。**
  照 content 的做法接窄读口，**MUST NOT 复刻四层回落逻辑**（复刻正是两侧悄悄不一致的来源）。
- [ ] 0.8b **错误族抬进 kernel**：`ProviderKeyMissingError` / `LlmErrorMeta` / `buildLlmHttpError` /
  `buildLlmApiError` / `buildLlmShapeError`（共 53 行，四条准入正则实跑全 CLEAN）。
  理由是结构性的：`src/llm/vision.ts:19-24` 从 `qwen.ts` 取这 5 个符号，
  qwen 进包而 vision 留 content 会各持一份错误类，跨副本 `instanceof` 静默退化——
  把「密钥没配」报成「模型不可用」。**一份定义才能让 `instanceof` 跨进程仍然成立。**
- [ ] 0.8d **`LlmTimeoutError` 暂未随迁，登记为后续项**：它不在错误族那 5 个符号里，留在 `qwen.ts`、
  现从 kernel 取 `formatLlmMeta` 拼消息。**现状风险为零**（全仓只有 qwen 侧一处对它 `instanceof`）；
  但**拆仓后若 content 侧也需要识别「模型调用超时」，它必须跟着进 kernel**——否则原样重演
  跨副本 `instanceof` 恒 false 那个坑。
- [ ] 0.8e **`src/llm/index.ts` 与 `src/server.ts` 是否改指 kernel 由集成时定**：
  两者经 `src/llm/index.ts` 这个 barrel（`export * from './qwen.js'`）取错误族，
  而它们同时也从同一 barrel 取模型客户端本体，所以 `index.ts → qwen.ts` 这条边**本来就存在**，
  再导出既没新增也没假消掉任何边。真正要消的 `vision.ts → qwen.ts` 已彻底消失。
- [ ] 0.8c **`vision.ts` 留 content**（其消费者全是 content：视觉分析 / 保真核验 / 封面形态 / 文字卡转写）；
  **`providers.ts` 随 qwen 进 transport**——厂商 base URL 字面量当场命中准入正则
  （正则只剥注释、**不剥字符串字面量**），进不了 kernel。

## 1. 四条运营指令通道（api 飞书入站 → automation 处理器）

- [ ] 1.1 `aidcp-kernel`：为四条指令定义窄接口与纯类型（请求 / 结果 / 具名失败原因）；不放行为类。
- [ ] 1.2 `aidcp-transport`：四条指令的「服务端注册 + 客户端 + 路径常量」三件套各一份，两端共用同一定义。
- [ ] 1.3 `aidcp-cloud`（事实源）：按 4a paired command 形态实现 route + receiver + api 侧 client；
  自由文本委托的**意图解析留在 automation**，api 侧 MUST NOT 自己拼 intent 调结构化入口。
- [ ] 1.4 调度启停：**「飞书 dispatch」这条通道自始至终不存在**（`feishu/command-face.ts` 的动作全集是
  `status/pause/resume/bindChat/delegate/publish/comment`，无 dispatch）；那个 `:dispatch` 文案只服务
  **面板路由**与 dashboard 状态灯。台账两条证据是同一条通道的两个证据。
  一条 paired command 一次接线即同时点亮面板按钮与状态灯，**飞书侧零改动**。
- [ ] 1.4a **批 1 的前置改动**：`feishu/command-face.ts:27-35` 那份 `PanelCommandActions` 的
  `dispatch` / `dispatchActive` 是**必填**，而 `panel/types.ts:270/275` 那份是**可选**。
  api 因此被迫必须传一个函数——「诚实地不注入」在类型层做不到，只能在「抛错」与「撒谎」之间选。
  先把前者改成可选，顺带消掉两份同名类型的漂移。
- [ ] 1.4b **委托卡片动作的处理器其实是 api 属主**（`src/feishu/` 整目录 15/15 归 api）：
  方向仍是 api→automation（缺的是服务端口注入），但**没有任何代码需要搬家**。
- [ ] 1.4c **委托的跨进程通道已经写好、只差接线**：
  `aidcp-automation/src/transport/delegated-task-http.ts` 服务端注册 + 客户端 + 7 个路由方法齐全，
  文件头明写「不接线、不改默认注入」；cloud 全仓对这两个符号零消费。
- [ ] 1.4d **`DataGateway` 与 paired command 二选一**：委托服务在 api 侧有**三个**消费者
  （飞书入站 `8316`、面板 `8615`、客户端 API `9157`），后两个走 `DataGateway`，
  而 `DataGateway` 在 `8539-8563` 已预留 remote thunk 位置。两条都建会出现
  「飞书走一条、面板与客户端 API 走另一条」的分叉，两者鉴权 / target 校验 / 错误归一都不同。
- [ ] 1.5 契约测试：鉴权、版本 / target 校验、幂等重放、**结果未知**（传输失败不得改写领域结局）。
- [ ] 1.6 `aidcp-automation` / `aidcp-api`：同步派生并各自跑 typecheck + 聚焦测试。

## 2. content 属主 authority（automation → content）

- [ ] 2.1 `aidcp-content`：在既有内部 HTTP 服务端上注册四组写口——草稿精修 / FB 发帖素材 /
  概念池 / 精选库；每组独立注册，**一组初始化失败不得连带关闭其它组**（照 content 现有纪律）。
- [ ] 2.2 `aidcp-content`：token 用量记账写口。成本 MUST 由厂商账单反算，
  **禁止**在这一层硬编码价目表。
- [ ] 2.3 `aidcp-transport`：上述各口的三件套；`aidcp-kernel`：对应窄接口与失败原因联合类型。
- [ ] 2.4 `aidcp-automation`：新增 content 客户端组与 `AIDCP_CONTENT_URL` /
  `AIDCP_CONTENT_INTERNAL_TOKEN`（本仓第一次有 content 方向的出边）。
- [ ] 2.5 按岔口 A 的裁决落地模型调用出口；按岔口 B 的裁决落地四个角色工厂。
- [ ] 2.6 处置 `ReplyWorkflow` 的 content 属主具体类实参（与模型出口是两件事，单独处置）。
- [ ] 2.7 **传递性检查**：逐个构造点核对跨属主实参，**特别点名 optional 参数**
  （`PublishDispatcher` 的 `FacebookPublishMediaStore` 漏传不报错、三个写静默消失）。
  写一条会红的用例钉住它。**同形共四层，逐层都要处置**（见 design.md §5.5.6）：
  ① 转写器可选实参；② `CuratedNoteSink` 的两个可选方法（见 0.6d）；
  ③ `CoverFormSensor.senseAt?` 缺席时降级成错误态 → 转写产出空、不抛、不 warn；
  ④ `ContentRoleOptions` 的 `soul?`/`getSoul?` 皆缺时构造期不报、第一次读才抛，
  而读它的位置在 fire-and-forget + try/catch 里 → 静默不纳入；
  `llmTimeoutMs?` 缺席则 per-role deadline 悄悄消失（角色调度器公共选项本来就不传它）。
- [ ] 2.7a **新用例落点已定**：转写器在今天的单体里是**无条件构造、无条件注入**
  （`server.ts:6493` / `:6761`），旗标只作回调传进去、在内部判——
  所以 `server.ts:116` 那个条件展开的 false 分支**生产上从未走过**，
  **「漏传」这个失败态只可能由本次拆仓引入**，现有测试不可能覆盖它。
  新用例作 `AC-TCT-3` 加进 `test/acceptance/text-card-transcription-honesty.test.ts`。
- [ ] 2.8 失败语义测试：写口只报真态行数；跨进程错误识别用**结构化守卫**，不用 `instanceof`。

## 3. automation 生产运行时真接线

- [ ] 3.1 `aidcp-automation`：在 `createAutomationCompositionRoot` 之上写真 `main()`——
  边-云 WebSocket 服务端、事件总线 + 角色调度器、风控单写者、各调度器与监测体。
- [ ] 3.2 启动 readiness gate 与 api 同形：同步读镜像首次装载完成、readiness 到 `ready` 之前
  **不放行业务入口**。
- [ ] 3.3 缺依赖时**停在具名原因上**：MUST NOT 用空数组 / `false` / 未绑定 / 代码默认放行。
  现在那个 fail-closed 壳守的东西，接线后必须仍然守得住——为此写回归用例。
- [ ] 3.4 持久任务仍按 `AIDCP_DEPLOY_ENV` 写 `execution_target`；target 缺失或非法时
  **不启动那个 worker**。
- [ ] 3.5 逐段对着 cloud `segCAutomation` 核对装配清单，确认没有「本进程里根本没有消费者」的对象
  被顺带 new 出来（判据：先问它的结果在本进程有没有去处）。
- [ ] 3.6 `aidcp-automation`：`npm run typecheck` + 全量 `npm test` 全绿。

## 4. 台账清零与门禁

- [ ] 4.1 `aidcp-automation/src/automation-composition-root.ts` 的
  `AUTOMATION_ROOT_READINESS_BLOCKERS` 逐条删除并同批下调；**只许下降，不留空位**。
- [ ] 4.2 `aidcp-cloud/boundaries/composition-root-independent-blockers.json` 同批收缩；
  **实为三份**（见 0.3a）：还有 `aidcp-automation/boundaries/composition-root-independent-blockers.json`
  那份已漂到 20 条的陈旧快照。三份 MUST 在同一批次内一致，任一单改都会让门禁与现实对不上。
- [ ] 4.3 台账清零后，`runAutomationEntry()` 从 fail-closed 切到真启动；
  切换本身要有测试证明「台账非空时仍然拒绝启动」这条闸没被删掉。
- [ ] 4.4 `npm run boundaries:refresh` + 逐条对账 `git diff boundaries/`；
  `crossBoundaryEdges` / `crossLayerReads` / `crossLayerWrites` / `exemptionEntries` 保持 0。
- [ ] 4.5 acceptance 全过：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权绝不静默发布）、
  `AC-RISK-*`（绝不自残）、`AC-OWN-*`、`AC-BOUND-*`、`AC-SPLIT-CROSSSEG`。

## 5. 派生对账、验收与收尾

- [ ] 5.1 `./scripts/sync-split-repos --ref <cloud sha> --apply --tests`；
  共享包 pin 按 kernel → transport → 三个业务仓的顺序快进，逐仓 `npm install` 刷 lock。
- [ ] 5.2 六仓各自 typecheck + 全量测试；**红项不得写成绿色**，逐条说明是既有还是本 change 新增。
- [ ] 5.3 **分层验收如实分开记**：loopback 契约测试证明 route/client；dev 单体部署只证明现网零回归；
  **三进程真跑属批次 5，本 change 不声称**。
- [ ] 5.4 dev 部署按 CLAUDE §5 安全序列（先备份 → rsync → restart → healthcheck → 失败即回滚）；
  **绝不碰同机 isales**。ol 一律等用户明确要求且走发布分支。
- [ ] 5.5 本地桩验不了的登记 `docs/real-machine-acceptance-backlog.md`（簇 60）。
- [ ] 5.6 回写 `docs/cloud-composition-root-trisection.md` §0.0 与
  `docs/cloud-split-next-session-handoff.md` §0.1/§0.2 的实测现状。
- [ ] 5.7 `openspec validate split-cloud-automation-production-runtime --strict` 通过后归档；
  删除 worktree 与分支。
