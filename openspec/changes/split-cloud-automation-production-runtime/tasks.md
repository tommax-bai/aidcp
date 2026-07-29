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
- [x] 0.3a **台账其实有三份，第三份已静默漂到 20 条**：
  `aidcp-automation/boundaries/composition-root-independent-blockers.json` 是手写台账的陈旧快照、
  全仓零读取点（多出的 8 条是 4b 已关闭的镜像项）。§4 的「两份同批收缩」实为**三份**。
  <!-- aidcp-automation a09a956。多出的 8 条**恰好全部是 4b-mirror**（4b 已由同步读镜像关闭，
       TS 常量早就删了，JSON 停在旧快照）。已删并经官方写出口重新派生，未手改 JSON。
       cloud 那份与 automation 那份不是同一口径（前者单体全量、后者收窄子集），不能直接比总数。 -->
- [x] 0.3b **给 automation 台账加机械锚**：cloud 那份是 AST 派生、自熄；automation 那份是手写、
  无任何机械力量把它钉在现实上——**这正是它会漂的原因**。
  <!-- aidcp-automation a09a956 + 32f3aa8。新增 test/acceptance/automation-root-readiness-ledger.test.ts
       （带 aidcp:test-owner=derived 标记，属派生私有、不被同步覆盖）。四条断言：TS 常量与 JSON 必须
       deepEqual（含顺序与 id 序列）；summary 三个字段必须从台账算出且四个分类键齐全（含当前为 0 的那类，
       防「零值被省掉→漏了看不出来」）；id 唯一 + owner/category 取值合法；4b-mirror 分类恒为空
       （那 8 条是被关闭的，重新出现即镜像回归，须裁定而非静默回填）。
       **锚的有效性用双向变异实测过**：JSON 单加一条 → 3 个用例红；TS 常量单删一条 → deepEqual 红。
       **边界要知道**：它锚的是**自洽**不是与现实一致——两侧一起改仍然全绿。docstring 已收敛到如实
       （32f3aa8）。继承自熄性的做法见 0.3e。 -->
- [x] 0.3c **三条 `identifier` 探针不具判别力**（`concept` / `curated` / `facebookPublishMedia`）：
  `src/server.ts:3900` 是 segC 开头一整行解构，三个名字都在里面。
  <!-- 2026-07-29 已改：在 census 既有机制内新增探针种类 identifier-use（沿用同一 EvidenceProbe 与
       分发，不另造一套），语义＝该标识符在 scope 内**非声明绑定位置**的出现次数 > 0；
       排除解构条目 / 变量与参数声明名 / import 说明符 / 对象与类型成员键，成员读与简写转发仍算真实使用。
       判别力用变异实验坐实：变异「只删解构行里三个名字」→ 三条 segC 证据仍在；
       变异「保留解构行、把 segC 内其余 19 处出现全改名」→ 新探针三条全消失，
       同一变异下 kind 临时改回 identifier 则照样出——假阳当场复现、修复有效。
       **原任务描述有一半是错的**：所谓「删解构而真实调用还在 → 静默放行（假阴）」机械上不会发生，
       containsIdentifier() 遍历整个 scope 匹配任意同名标识符，真实调用点照样命中。
       真正成立的只有假阳那一半。记下来免得后来人照着错的失败模式设计判据。 -->
- [x] 0.3c1 **同类弱探针九条已补齐**（原记 10 条，其中一条是误记）。
  <!-- aidcp-cloud abdadae。segD 五条（curatedContentStore / facebookPublishMediaStore /
       draftRefinementStore / llm / tokenUsageStore——segD 开头 src/server.ts:7794 确实是与 segC
       一模一样的大解构）+ segC 四条（mirrorVersionStore / accountStore / llm / tokenUsageStore）。
       **`CONTENT_ROLE_FACTORIES` 不在此列，上一轮把它列进去是错的**：它是模块级 import，
       在 segC body 内零声明绑定、唯一出现就是真实取用，换 kind 只是同一条探针换个更长的名字。
       结论已就地写进注释钉住。变异实测两个方向各一轮，改后 src/server.ts 经 cmp 逐字节还原。
       台账条目数 / 顺序 / id / 分类计数全不变（55），只有 9 行证据串改了 kind。 -->
- [x] 0.3d **补进台账：文字卡 OCR 整条子链**（segC 内构造、属主全是 content、automation 仓全无）。
  <!-- 2026-07-29 走派生机制补记（不是手写 JSON）：在 REVIEWED_BLOCKER_BINDINGS 追加 3 条
       content-owner 条目，台账由 refresh-ledger 重新派生。cloud 台账 52→55，automation 收窄台账 12→15。
       **`new PersonaGenerator`（5290）经核不该补，已从清单剔除**——它在 seamMode === 'monolith'
       分支里（5288-5305），core 走 HTTP 客户端，而 automation 模式下该句柄保持 undefined、
       账号人设端口取自 4a 的 accountPersona（5327-5330），不阻塞 automation 独立根。
       cloud inventory 测试 258-264 行本来就显式断言「任何证据含 PersonaGenerator 的条目不得留在台账里」，
       补进去会当场撞既有裁定。裁定理由已写进那条断言的失败消息。 -->
- [ ] 0.3f **把 seam 过滤判据放宽到「automation 模式下不执行的分支」（已裁定要做，本轮未做）。**
  本轮给 `new` / `call` 探针补的过滤器只认 `seamMode === 'monolith'`。但草稿精修那条的 segC 探针
  指向的构造坐在 `if (seamMode !== 'automation' && ...)` 里——**automation 进程里根本不构造它**，
  按台账的语义（「automation 独立起根被什么挡住」）同样不该算欠账。
  **裁定：放宽。** 与 0.6a 是同一条判断的两面（那条已定「草稿精修撤出岔口 C」），
  不放宽就会出现「文档说不算欠账、机器说算」的长期不一致。
  **但放宽 MUST 响亮**：过滤掉哪几条证据要当场报出来，MUST NOT 静默少几行；
  且要顺带扫一遍 segC 里其余 `seamMode !== 'automation'` 守卫（约 5919 / 6259 / 6295 一带）。
  **注意后果不是「条目消失」而是「条目变成纯 api 侧证据」**——收录判据是「任一探针命中即保留」，
  segA / segD 那两条还在。真正会消失的是它在 **automation 收窄台账**里的位置，而那正是 0.6a 要的结果。
- [x] 0.3g **automation 那份 census helper 是有意的手写分叉，不是派生物**（本轮核实）。
  <!-- 2026-07-29 实测：文件第 1 行是 `// aidcp:test-owner=derived`，
       按 scripts/sync-split-repos 的 derived_private 逻辑，带该标记的派生仓测试**被排除出同步对账**
       ——所以它不会被 cloud 那份覆盖，也不会被 --prune 删掉。
       代价要知道：cloud 侧的探针改进（identifier-use、seam 过滤）**不会传播到它**；
       它的 deriveIndependentRootBlockers() 直接把手写常量映射成条目、不读任何生产源码。
       这也正是 0.3e 那条「更强的锚」要解决的东西。
       **复核把这条查得更透、结论比原判更麻烦**：读 scripts/sync-split-repos:851-863，
       带该标记的文件被从**两侧同时**减掉（wanted -= derived_private，synced_actual = actual - derived_private）
       ——所以它既不会被覆盖，**也永远不会被报成 drift**。
       后果：两个同路径、同导出名的文件（cloud 1916 行 / automation 1792 行）**永久分叉且零机械信号**，
       本轮 cloud 侧的 identifier-use / seam 过滤 / 更正后的注释一条都到不了那份 fork，
       而且没有任何东西会告诉你。真正要裁的不是「是不是派生物」，而是
       **「要不要给同名分叉加一道对账」**——见 0.3e。 -->
- [ ] 0.3e **更强的锚（已提出，本轮未做，需裁定）**：即使有了 deepEqual 自洽锚，
  automation 那份仍是「两侧一起改就能一起漂」——锚住的是自洽，不是与现实的一致。
  真正继承自熄性的做法：cloud 侧按 `consumer` 含 automation 从 AST 派生台账过滤出 id 集合，
  随 `sync-split-repos` 落一份只读投影进 automation 仓；automation 侧断言自己的 id 集合 ⊆ 该投影。
  这样 cloud 那边依赖一被解决，automation 台账当场红。**代价是给同步脚本加一个新产物（跨仓改动）。**
  本 change 会把台账清到零，届时 deepEqual 锚 + 「4b-mirror 分类恒为空」两条已够守「保持零」；
  这条留作后续。
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
- [x] 0.5b 先修「缺席被静默吞掉」：`curated-note-evaluator.ts:145` 与 `:179` 的
  `this.textCardTranscriber?.enabled()` 改成显式能力状态，让「旗标关掉」与「依赖没接上」可区分。
  <!-- aidcp-cloud 1d31c30。kernel 新增能力二态（wired / unavailable+具名 reason）与调用点三态
       （active / flag_off / unavailable）+ 两个纯结算函数。缺席在构造期结算并打一条具名日志、
       **全程不抛**（该角色是 fire-and-forget，抛出会打断浏览闭环）；跳过日志带 once-guard 不刷屏。
       既有行为逐条保住：刷新返回 falsy 仍继续重评，enabled() 的调用时机与次数不变。
       组装根工厂表的条件展开改成必给字段的三元（句柄缺 → 显式 unavailable）。 -->
- [x] 0.5c 抬纯物件进 kernel。**对象按 0.5a 的裁决重算过**：真正跨过去的不是
  `normalizeCuratedReferenceImages`（它只有 content 侧消费者，随转写器留 content），
  而是评估角色值引用的 `mergeBodyWithTextCardTranscription` + 它内部调的 `orderedTextCardTexts`
  （后者还有一个 content 侧消费者＝发布链封面卡撰写角色，不抬必出两份实现），
  外加转写器的三个纯接口。
  <!-- aidcp-cloud 1d31c30。两个纯函数进 kernel/text-card-transcription.ts；三个接口进新文件
       kernel/text-card-transcriber-port.ts（那个文件是这一族的运行时纯函数家，kernel 既有约定是
       口与数据模型只放类型，故不并进去）。**两处都没留再导出壳**——留壳会让扫描器继续看到那条边。 -->
- [x] 0.5d 修「假消边」残留：`curated-note-evaluator.ts` 与 `text-card-transcriber.ts` 的类型 import
  改指 `../kernel/curated-content-types.js`，不再经 `../cache/curated-content-store.js` 的再导出壳。
  <!-- aidcp-cloud fbb66e7 + 1d31c30。 -->
- [x] 0.5e **可选实参已升级成编译期错误**。
  <!-- aidcp-cloud b50fec1。`textCardTranscriber` 由可选改必填（类型仍是 实现 | 能力态），
       省略即**编译红**，不再是要靠人看见的运行期日志。
       **之所以负担得起**：单体里转写器是无条件构造 + 无条件注入的，
       没有任何合法调用方会省略它——代价只是三个测试构造点，其中两个是编译器替我找出来的。
       不接该能力仍允许，但必须明说 `{state:'unavailable', reason}`。
       运行期兜底（对 undefined 判 not_injected）保留不动：它守的是绕过类型的调用方，
       不是给 TS 侧留后门。相关 27 个测试全过。 -->
- [x] 0.5f **测试侧工厂镜像已与生产对齐**。
  <!-- aidcp-cloud 0dcd0eb。漂移方向是**测试比生产宽松**：省略字段正是让「依赖没接上」
       读起来跟「旗标关掉了」一模一样的那个写法，所以拆仓引入的漏传在测试里会照样绿。
       typecheck 0，相关两个测试 16/16。 -->
- [x] 0.5h **测试派生落点已用真工具验过**（不是推理）：拿 `sync-split-repos` 的真 `classify_tests`
  跑改前 / 改后两个 ref 对比。
  <!-- 改前四条全是 STAY-cloud；改后 curated-note-evaluator.test.ts / text-card-transcription-absence.test.ts /
       helpers/role-factories.ts → aidcp-automation，text-card-transcription-honesty.test.ts → aidcp-content。
       即那条「专为拆仓失败态写的用例落不进目标仓」已解决。
       **顺带查清一条前瞻性隐患、不是当下 bug**：`src/cache/curated-content-store.ts` 还留着 24 个类型的
       再导出壳，但当前 124 条 STAY-cloud 测试里只有 3 条唯一 content 依赖是它，且那 3 条本来就该归 content。
       别当待修项排期。 -->
- [ ] 0.5i **既有判例 `FacebookPublishMediaError` 没有 `code`，同样跨不过传输那一跳**（潜伏项）。
  它今天只在同进程内用，所以**还不是活 bug**；但拆进程后一旦它需要跨边界，
  守卫会恒不命中、失败静默退化。本 change 新写的错误加 `code` **不是镀金，是补了判例本身的缺口**。
  等它真要跨边界时，照同一形状补。
- [ ] 0.5j **AC-TCT-3 有一处已知脆性**（可接受，记下来免得将来误判）：
  留痕函数带一次性闸、有两个调用点（图片快照 stage 与准入评估 stage），
  而该用例只触发后者。若将来这条 fixture 先触发前者，跳过断言会因为**与不变量无关**的原因变红。
- [ ] 0.5g **缺席的真正上游在角色调度器**：`role-dispatcher.ts:2170` 决定要不要把不透明句柄
  放进工厂 options。链路现在是「调度器可能不给 → 组装根**显式**翻译成 unavailable → 角色留痕」，
  缺席不会再被压成假；但若要让「漏传」变成**编译期**错误，得从那里连同工厂选项类型一起收紧。
  该文件是热点文件，需串行。
- [ ] 0.6 **岔口 C 落实**：content 属主存储写走 content 内部 HTTP 写口，在既有
  `AIDCP_CONTENT_PORT` 监听上扩，不新造监听。**范围按 0.3 复核修正**（见 0.6a–0.6c）。
- [ ] 0.6a **撤掉草稿精修那一条**：`src/server.ts:6171` 的守卫是 `seamMode !== 'automation' && ...`，
  该 worker 在 automation 模式下本来就不跑；剩余两条证据都是 api 侧。
  automation 方向现存 runtime 边为零，**不开这个写口**。
- [x] 0.6b0 **两个端口的契约已定义**（只定义、未接线）：`src/kernel/concept-pool-port.ts`、
  `src/kernel/curated-selection-port.ts`，失败信号 `src/kernel/content-port-error.ts`。
  <!-- aidcp-cloud 1d31c30 定义，abdadae 按用户裁决改回既有范式（裸值返回 + 失败抛）。
       信封文件 content-port-result.ts 已删。精选库刻意是**两个方法而非一个**：发帖侧要全字段，
       评论侧只要三字段窄投影——全字段视图挂着参照图集 / 视觉分析 / 文字卡转写等大块 JSON，
       搬过边界只为留三个字段，投影本就该在属主侧做。签名照抄属主真实签名，故属主实例可原样注入。
       缺失计数用 null 而非 0，区别「不知道」与「真是 0」。
       **一处只有读传输层才发现的事**：内部 HTTP 的错误编码只保 code + message，
       name / reason 跨那一跳会全丢，所以错误另带 code 与还原函数；
       **还原不出返回 null、绝不套默认 reason**——套默认会把「对面不支持这个方法」
       吞成「对面报错了」，概念池的回落分支就第二次变成死代码。 -->
- [x] 0.6b1 **`ContentPortResult` 信封已删，统一到既有约定**（用户 2026-07-29 裁定）。
  <!-- 见 design.md §3.0。理由：抛出本来就不是空数组，「分得开」既有约定做得到；
       病根在五处把抛出压成空数组的代码（0.6f）。两套并存的实际后果是接线的人顺手照抄既有范式、
       新端口被整体绕过。 -->
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
- [ ] 0.6f **降级形状有五处，只改一处等于没改**（复核补出后两处）：
  ① `src/server.ts:7024` 的 `: Promise.resolve([])`（组装根层）；
  ② `aidcp-automation/src/comment-agent/comment-scheduler.ts:1603` 的 `.catch(() => [])`
  ——**即使组装根那层改了，调度器自己这个 catch 仍会把端口抛出的传输失败重新吃成空数组**；
  ③ `role-dispatcher.ts:2456` 的「PG 不可用 / 装载失败 → 回退空池」；
  ④⑤ `aidcp-automation/src/publish-agent/publish-scheduler.ts:267` 与 `:272` 的
  `: Promise.resolve([] as CuratedSelectItem[])`（精选库未注入即静默空）。
  **这五处正是用户裁决「把力气花在堵吞点」所指的地方**——失败靠抛这条约定本身分得开
  「没问到对面」与「对面回答了空」，被吃掉是因为这五处把抛出重新压成了空数组。
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
  <!-- 2026-07-29 已对改判分支实跑预演坐实（--ref origin/codex/<change>，只读）：
       automation 227→233（新增 6）、content 85→79（**多出 6**）、kernel 96→101（新增 5）。
       「多出 6」就是不 prune 会留在 content 的那批。 -->
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
- [x] 0.8b **错误族抬进 kernel**（已完成，见下方原文与 <!-- --> 记录）
  <!-- aidcp-cloud 1d31c30。新建 src/kernel/llm-errors.ts，5 个符号整体搬入（原处已删定义、非复制），
       连同它们的私有格式化闭包；formatLlmMeta 提升为 export——留在 qwen.ts 的 LlmTimeoutError
       也用它拼同一套排障字段，不导出就得复制第二份、字段位次会悄悄漂。
       vision.ts → qwen.ts 这条边已彻底消失。四条准入正则实跑全 CLEAN，第五条（不 import 业务层）
       也满足——该文件 import 说明符列表为空。另补一条会红的测试：视觉出口抛的错误类
       与 kernel 那个是**同一个引用**，钉死「以后谁再复制一份」。 -->
- [ ] 0.8b0 **错误族抬进 kernel**（原文，保留供追溯）：`ProviderKeyMissingError` / `LlmErrorMeta` / `buildLlmHttpError` /
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
- [x] 0.8f **模型出口的传输包成员已点名**（闭包＝恰好两个文件，实测证明）。
  <!-- 控制仓 scripts/sync-split-repos 的 TRANSPORT_MEMBERS 手工增量追加 qwen.ts + providers.ts。
       **不需要动任何归属条目**：transport 分支只读该名单，属主仓的应有集在另一处独立按 layer 算——
       这两个文件在归属表里仍是 content，与既有先例同形（src/transport/* 是 automation 属主、
       同样既落本仓 src/ 又复制进包）。**本次是第一批非 automation 属主的成员。**
       闭包用 transport 自己的 tsconfig（strict + noUnusedLocals）实跑证明：只放这两个 + 三个 kernel
       文件即 tsc 退出码 0，多一个都不需要。视觉栈**没有被顺带拖进去**——vision.ts 消费者全是 content，
       index.ts 是桶文件（`export * from './vision.js'` 在模块图里就是一条边，收进来等于把整条视觉栈拖进包）。
       对账实测：transport 47/45 → 新增 2，其它仓零连带变化。 -->
- [ ] 0.8g **⚠️ 活缺口：三进程形态下厂商密钥读必然失败，且失败被吞成「本来就没配」。**
  `aidcp-api` 的手写 main **既没注册 `provider-secret/get-for-runtime`、也没注册
  `role-model-selection/fetch`**，而单体两条都注册。后果：content 的库内密钥读**必失败**，
  调用点是 `.catch(() => null)` → 落到 env 回退，**没有任何一行日志说明这次是「读失败」还是
  「本来就没配库内值」**（传输层文件头明写「失败原样抛、绝不吞成没配」，但调用侧的 catch 又吞回去了）。
  模型选择那条至少还有「真值 / 保守默认（取源未成功）」的自证行，密钥这条没有。
  → **0.4 要改的不只是「env 读」那句措辞，还得连带补上 api 侧这两条 route 的注册**，
  否则「库内优先」在派生栈里目前只是纸面成立。
- [ ] 0.8h **顺序依赖，别倒过来做**（已实测为红）：transport 同步 qwen **必须排在**
  kernel 同步 + `aidcp-kernel` 提交 + 三仓与 transport 的 kernel pin 上抬**之后**。
  否则 transport 编译当场 `TS2307`（找不到 `aidcp-kernel/kernel/llm-errors.js`）。
  **这次是编译期就红，反而是好事**——它是 pin 漂移那类「编译照过、只有真跑才炸」的镜像版本。
- [ ] 0.8i **automation 第一次真需要 `aidcp-transport` 依赖**：它今天没 pin
  （对账工具明确打「未 pin aidcp-transport（用得上它的仓才需要）」），因为它自己是 `src/transport/` 属主、
  一直用本地副本。而 `src/llm/*` **不是** automation 属主，只能走包。接线时要新增这条 pin。
- [ ] 0.8j **`qwen.ts` 有一个静默兜底，automation 的 main MUST 显式传 key 绕开它**：
  `this.apiKey = options.apiKey ?? process.env.DASHSCOPE_API_KEY ?? ''`——不传 key 时既不报错也不抛，
  直接落成空串；**更坏的是构造非 dashscope 厂商的出口时也会去读 `DASHSCOPE_API_KEY`**。
  content 的 main 是显式传的，automation 照抄。
- [ ] 0.8k **归属不变意味着派生栈里会有两份模型客户端实现**（content 的 `src/llm/` 本地副本 + 包里那份）。
  今天不致命（错误族已抬 kernel，跨副本 `instanceof` 问题已消），但两份各带一份默认 base URL
  与 env 读取默认值，**会悄悄漂**。建议让 content 的手写 main 改指包里那份
  （与它已经在用的 `aidcp-transport/transport/*.js` 同口径），本轮只登记。
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
