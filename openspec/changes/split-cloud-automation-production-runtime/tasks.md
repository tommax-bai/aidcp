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
- [x] 0.3f **把 seam 过滤判据放宽到「automation 模式下不执行的分支」（已裁定要做，本轮未做）。**
  本轮给 `new` / `call` 探针补的过滤器只认 `seamMode === 'monolith'`。但草稿精修那条的 segC 探针
  指向的构造坐在 `if (seamMode !== 'automation' && ...)` 里——**automation 进程里根本不构造它**，
  按台账的语义（「automation 独立起根被什么挡住」）同样不该算欠账。
  **裁定：放宽。** 与 0.6a 是同一条判断的两面（那条已定「草稿精修撤出岔口 C」），
  不放宽就会出现「文档说不算欠账、机器说算」的长期不一致。
  **但放宽 MUST 响亮**：过滤掉哪几条证据要当场报出来，MUST NOT 静默少几行；
  且要顺带扫一遍 segC 里其余 `seamMode !== 'automation'` 守卫（约 5919 / 6259 / 6295 一带）。
  **注意后果不是「条目消失」而是「条目变成纯 api 侧证据」**——收录判据是「任一探针命中即保留」，
  segA / segD 那两条还在。真正会消失的是它在 **automation 收窄台账**里的位置，而那正是 0.6a 要的结果。
  <!-- aidcp-cloud <pending> 已放宽：过滤判据从「只认 `seamMode === 'monolith'`」扩到「三个独立根都不执行的分支」，
       并把「放宽 MUST 响亮」做成机械的：新增 `deriveSeamSuppressedProbeMatches()` + 一条把**被过滤掉的证据全集**
       逐条钉死的断言（含每条的三行理由：automation 被哪个守卫挡、api / content 不跑 segC）。
       此前这个过滤器唯一的失败模式就是沉默——它做的是「减掉证据行」，而减掉的行与从来没派生出来的行长得一模一样。
       实测后果与本条预判一致：台账里只少了 `segCAutomation:new:DraftRefinementWorker` 一行，
       `content-draft-refinement-authority` 这个条目**仍在**（靠 segA 建店 + segD 读两条证据），
       `4b-b4-account-identity-status-mirror` 也仍在（它那条 `accountDisplayName` 还有另一处无守卫的 segC 调用点）。
       即：过滤只缩短证据，不熄灭条目——这正是收录判据「任一探针命中即保留」应有的行为，现在有断言钉着了。 -->
  <!-- 顺带扫完 segC 其余 `seamMode !== 'automation'` 守卫：真正被过滤的只有两处（草稿精修 worker、
       待派发看门狗那次 `accountDisplayName`），其余守卫内没有 new/call 探针指向。 -->
  <!-- 判据比本条原文更严，是**有意的**：写成「automation 不执行就过滤」会在 segA（三个模式都跑）里
       误删 api / content 的真欠账——那一段里的 `seamMode !== 'automation'` 分支恰恰是它俩的欠账。
       实际判据是「**没有任何一个独立起根会执行这个节点**」，由段归属 + 守卫抽象求值两条独立排除合成。
       在 segC 里两种判法结果完全等价（api / content 压根不跑 segC），所以本条要的结果一分不少；
       差别只在将来有人往 segA 写下第一条 seam 守卫的那一刻才显现。
       另外判据不再是字符串正则而是真实语义求值（模式全集来自 `ServiceMode` 的 `Record` 穷举，
       新增模式会编译红而不是被静默漏掉；认不出的表达式一律当「可能执行」，即只朝**保留**方向失败）。 -->
- [ ] 0.3g **`identifier-use` 家族不在 seam 过滤范围内（实测有真命中，本轮如实不处理）。**
  0.3f 只放宽了 `new` / `call`。实测 `segCAutomation:identifier-use:llm` 有 **2/11** 处落在
  automation 不执行的分支里；因另 9 处存活，条目与证据行零影响，故本轮未动。
  若日后要求 identifier 家族也按 seam 过滤，**需另行裁定**——那会真的删掉证据行，不是零影响改动。
- [ ] 0.3h **`isApiOwnerModeOnly`（segA 属主 store 过滤器）仍是老式字符串正则，未随 0.3f 统一。**
  它回答的是另一个问题（「是否只有 api 模式构造」），且它产出的 blocker 声明的消费方是
  「automation 与 content 两个根」，量词与 0.3f 的判据不同——混用会改变 segA 输出。
  属可选的后续统一项，**不在 0.3f 范围内**，登记以免以为已统一。
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
- [x] 0.5i **既有判例 `FacebookPublishMediaError` 没有 `code`，同样跨不过传输那一跳**（潜伏项）。
  它今天只在同进程内用，所以**还不是活 bug**；但拆进程后一旦它需要跨边界，
  守卫会恒不命中、失败静默退化。本 change 新写的错误加 `code` **不是镀金，是补了判例本身的缺口**。
  等它真要跨边界时，照同一形状补。
  <!-- aidcp-cloud <pending>。**本条与 0.6i 的记载各错一半，且方向相反，一并更正：**
       ① 0.5i 说「等它真要跨边界时再补」——但结构化守卫、name 常量、shape **早就存在**了
          （由更早的 change `cloud-coupling-phase2-panel-contracts@0bbc43b` 落的），
          api 侧那个消费者**也早已迁完**，测试也已经钉住跨进程用例。
          所以「还没做」的其实只有 `code` 这一件——恰恰是本条标题点名的那件。已补。
       ② 反过来 0.6i 说「有三个 api 侧 instanceof 消费者」——实测是 4 处 / 3 个文件。
       教训一致：**这两条记的都是「凭印象的消费者清单」，实测才作数。** -->
  <!-- 补法照 `content-port-error.ts` 的形状：前缀常量 + 编码 / 还原两个函数，
       **还原不出返回 `null`、绝不套默认**。类的构造里设 `code`。
       理由是传输层的错误编码只保 `code` + `message`，没有 `code` 的抛出物到对面会被压成泛化错误。 -->
- [ ] 0.5j **AC-TCT-3 有一处已知脆性**（可接受，记下来免得将来误判）：
  留痕函数带一次性闸、有两个调用点（图片快照 stage 与准入评估 stage），
  而该用例只触发后者。若将来这条 fixture 先触发前者，跳过断言会因为**与不变量无关**的原因变红。
- [ ] 0.5g **缺席的真正上游在角色调度器**：`role-dispatcher.ts:2170` 决定要不要把不透明句柄
  放进工厂 options。链路现在是「调度器可能不给 → 组装根**显式**翻译成 unavailable → 角色留痕」，
  缺席不会再被压成假；但若要让「漏传」变成**编译期**错误，得从那里连同工厂选项类型一起收紧。
  <!-- 2026-07-29 决定**本轮不做**，理由留档免得被当成漏掉：
       ① 角色调度器是热点文件（需串行，不与并行 session 同时碰）；
       ② 当前链路**已经是诚实的**——调度器可能不给 → 组装根显式翻译成 unavailable + 具名 reason
          → 角色构造期留痕。缺席不会被静默吞掉，只是以运行期具名日志而非编译红的形式暴露；
       ③ 要做成编译红，得把不透明句柄类型本身改成二态并改动它全部构造点，
          换来的只是「把一处运行期具名日志提前到编译期」——这一跳的边际收益远低于 0.5e 那一跳
          （那一跳消掉的是「与旗标关掉长得一模一样」，是质变；这一跳只是提前）。
       若将来要做，连同 `CuratedNoteEvaluatorFactoryOptions.textCardTranscriber`（:207）与
       `DispatcherOptions`（:435）一起收紧，并把 :2170 的条件展开改成必给字段的三元。 -->
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
- [x] 0.6c **精选库补跨界读 `selectForCreation`**：两个调用方（发帖调度器 / 评论调度器），
  **投影形状不同**。今天 `server.ts:7024` 的 `: Promise.resolve([])` 降级形状跨进程后会把
  「连不上」吃成「没有精选素材」，MUST 换成可区分的结果。
  另：`server.ts:4986` 与 `:5311` 只把 store 当「有没有」用，MUST 换成显式可用性查询。
- [x] 0.6e **「能力探针」跨进程后恒为真——比可选方法漏实现更糟。**
  今天的回落写法是 `this.d.conceptStore.getNewConceptsWithSourceSince ? … : …`，
  一个 `typeof` 能力探针。跨进程后客户端类**总是**定义着那个方法，探针恒真、**回落分支变死代码**，
  而真实的能力缺口（对面版本落后 / 路由没注册）反被静默吞掉。
  → 端口上两个读方法**都不带可选标记**，回落改由具名的 `unsupported_method` 驱动。
  **保留 `?` 等于保留一张假的安全网。**
- [x] 0.6f **降级形状有五处，只改一处等于没改**（复核补出后两处）：
  ① `src/server.ts:7024` 的 `: Promise.resolve([])`（组装根层）；
  ② `aidcp-automation/src/comment-agent/comment-scheduler.ts:1603` 的 `.catch(() => [])`
  ——**即使组装根那层改了，调度器自己这个 catch 仍会把端口抛出的传输失败重新吃成空数组**；
  ③ `role-dispatcher.ts:2456` 的「PG 不可用 / 装载失败 → 回退空池」；
  ④⑤ `aidcp-automation/src/publish-agent/publish-scheduler.ts:267` 与 `:272` 的
  `: Promise.resolve([] as CuratedSelectItem[])`（精选库未注入即静默空）。
  **这五处正是用户裁决「把力气花在堵吞点」所指的地方**——失败靠抛这条约定本身分得开
  「没问到对面」与「对面回答了空」，被吃掉是因为这五处把抛出重新压成了空数组。
  <!-- aidcp-cloud 9ae8e1d。**复核结论：确实是 5 处，没有第六处**（行号漂了：① 7024→7031，其余基本准）。
       **降级本身一处没动**——概念池装载失败仍回空池、评论命令仍降到零样本、精选库未接线仍不报错，
       改的是「降级从 catch 顺手吃掉的副产物，变成看着具名原因明写的决定」，且日志明写
       「**未**确认对面为空」。逐处：
       ① 组装根：精选库缺席不再回空数组，改抛具名 `not_configured`（窄投影仍留属主侧就地做）。
       ② 评论调度器：`.catch(() => [])` → 显式 try/catch，仍降级但落带具名原因的 warn。
       ③ 概念池装载：拆成三种情形各有名字（真空池 / 未配置 / 装载失败）；
          「未配置」原本**连一行日志都没有**，「装载失败」原本那行 warn **没有原因码**。
       ④⑤ 发帖调度器：两处收进一个具名缺席分支。
       **④⑤ 刻意只管缺席、不给读失败补 catch**：那条路径今天本来就会冒泡出去、已经分得开，
       补 catch 等于新造第六个吞点。 -->
  <!-- 守卫做法：新增结构化归类函数，按 `name` + 具名字段同时认端口错误与属主自有错误，
       对同进程实例与跨进程反序列化裸对象一视同仁；**认不出来也给名字**，不因「不认识」退回沉默。
       落点是 `src/kernel/curated-content-types.ts`（贴着它认的那个错误类），
       语义上更该在 `content-port-error.ts`，只是那样得反向 import；并行流放开后可顺手搬。 -->
- [x] 0.6h **概念池 + 精选库的传输三件套已落**（只定义 + 注册函数 + 客户端，**未接线**）。
  <!-- aidcp-cloud <pending> src/transport/content-authority-http.ts（零属主表 SQL，继承 src/transport/
       目录规则判 automation，`boundaries/ownership-rules.json` 一个字不用改，只需集成时跑一次
       `boundaries:refresh` 生成一条条目）；同批加进控制仓 TRANSPORT_MEMBERS
       （服务端跑 content、客户端跑 automation，不进名单 content 仓拿不到注册函数）。
       接线期欠账 8 条登记在导出常量 `CONTENT_AUTHORITY_WIRING_DEBT`。
       测试 5 条，做过变异实测：注册函数漏挂一条路由 → typecheck 仍绿、用例当场红
       （`satisfies` 只保证表全，保证不了都挂上）。 -->
  <!-- **四条实装中才看得见的事实，端口注释里没有：**
       ① **`unsupported_method` 真正的触发路径不是端口注释设想的那个。** 端口把两个读方法都定成必选，
          属主实例结构上恒满足，「属主不提供这个方法」其实很难发生；现实路径是**对面跑旧版本、
          这条路由没注册 → 404**。已显式把 404 译成 `unsupported_method`，回落分支才真的活着。
       ② **反过来，版本不支持刻意不译成 `unsupported_method`**：回落方法同属一个契约版本、照样会失败，
          判成回落等于把一次通道级配置错误伪装成一次能力缺口。
       ③ **`ContentPortErrorShape.code` 是可选的，这是端口注释没覆盖的洞。** 线格式只透传带 string
          `code` 的抛出物；属主若抛一个没有 code 的 shape，reason 会在这一跳被压成泛化错误、
          回落分支第二次死掉。故服务端那层**重建**而不是原样透传。
       ④ 召回 `limit` 取下限 1：`limit=0` 会让「问错了的提问」读起来像「库里没素材」。
          今天调用方传 8 / 3 / 默认 20，无 0。 -->
- [x] 0.6i **`CuratedContentUnavailableError` 没有 `code`，与 0.5i 登记的 `FacebookPublishMediaError`
  是同一个判例缺口，但 tasks.md 只登记了后者。**
  它今天已有三个 api 侧 `instanceof` 消费者——跨进程后恒 false（§8.5）。
  本次概念池 / 精选库那条链路不受影响（服务端译成具名原因、原文进 detail），但缺口本身仍在。
  <!-- aidcp-cloud <pending>。**消费者是 4 处 / 3 个文件，不是 3 处**（面板 1、客户鉴权 1、组装根 2）。
       已补 `code` 常量 + 字段 + shape。**守卫刻意仍只按 `name` 判、不要求 `code`**：
       要求 `code` 会让守卫对「跑着旧版本的对面」恒 false——那正是它存在要杀的那个失败。 -->
  <!-- 组装根那两处（在委托任务预检与目标校验闭包里）当轮**未改**（`src/server.ts` 是并行热点）——
       **但集成时已补上，现在别再去找**：`93d339b` 的 `src/server.ts:3067` / `:3103` 已在用结构化守卫
       （旧注释写的 `:3018` / `:3055` 是当轮行号，已漂 ~49 行）。
       不补的后果本来是：它们会掉进兜底重抛、报一个泛化失败而不是具名的「精选库不可用」。 -->
- [x] 0.6j **`src/transport/` 的目录规则描述已与目录实际内容脱节**（可选修文）：
  规则原文写的是「异步事件 outbox 传输原语（有 SQL、不进 kernel）」，
  而本 change 新落的两个文件（运营指令、内容属主召回）都不是那个形态、也都零 SQL。
  归属判定不受影响（`newFile: inherit` 照样对），只是生成物里那句 `note` 会误导后来人。
  <!-- aidcp-cloud <pending> 已校订。原文只描述了本目录的**第一批**成员；此后已长出第二种形态
       （「服务端注册 + 类型化客户端 + 路径常量」三件套，3a/4a 两批 + 本 change 的两个文件），全部零 SQL。
       整目录归 automation 的真实理由是「跨进程运行时原语、有副作用故不进 kernel」，**与是否含 SQL 无关**，
       校订后把这一条写明了。`boundaries:refresh` 后 48 个文件的 `note` 字段随之更新，跨层边仍 0。
       **为什么值得改**：那句 note 是逐文件抄进生成物的，不改会让后来人以为
       「新文件必须有 SQL 才配进这个目录」——一条凭空多出来的准入条件。 -->
- [x] 0.6g **调用点比原记录多两处**（接线时都要改）：`markSearched` 有两个
  （`role-dispatcher.ts:3411` 下发搜索后 + `:3714` 回执后）；`countNewSince` 有两个
  （`publish-scheduler.ts:263` 聚合输入 + `:323` 概念积累扳机）。
  <!-- aidcp-cloud 1b36b74。**复核：恰好 4 处，没有第五处**，计数对、行号全漂（实为 `:3436` / `:3739`
       与 `:288` / `:348`）。两处 `markSearched` 已收进一个带阶段标签的私有函数。 -->
  <!-- 0.6c / 0.6e 同批（同一提交）：四个注入面全改成 kernel 端口类型；
       能力探针删除、回落改由具名的「不支持这个方法」驱动，其余原因一律原样冒泡；
       两处「把 store 当有没有用」的真值判断改成能力二态（形状逐字照文字转写那套，未自创第二套）。
       **单体行为逐位不变**，确认方式是全量测试通过集与基线逐条相同、差值恰好等于新增的 3 条用例。
       变异实测两轮：把回落放宽成「凡端口错误就回落」→ 当场红；把旧探针形态原样复活 → 当场红。 -->
  <!-- **组装根撤桩的连带**（1.4a 的后半）：`src/server.ts` 里两个占位桩删掉后，
       台账少了一条证据行（那条 text 探针指的正是桩里的错误串），
       `feishu-operator-dispatch-start-stop` 条目**仍在**（面板那个调用点还是证据）。
       已跑官方出口重新派生，台账仍 55 条。这是机制在正常工作：台账由源码派生，源码变了它就得变。 -->
- [x] 0.6d **Sink 的可选方法是第二处静默陷阱**：`CuratedNoteSink` 的 `refreshReferenceImages?`
  与 `getTextCardContext?` 都用 `?.` 调用（`:153` / `:182`）。换成 HTTP 客户端后**少实现一个方法
  编译通过、运行不报**——少 `getTextCardContext` 则缓存恒空、每篇图文帖重跑视觉转写（纯成本爆炸、
  零错误信号）。端口面 MUST 显式声明可选能力的在场与否。
  <!-- aidcp-cloud 9ae8e1d。行号已漂到 `:218` / `:253`（差 65~71 行）。
       落法不是「显式声明可选」而是**三个方法全改必选、`?` 全删、调用点去掉 `?.`**。
       判据取自本 change 自己的概念池端口：「提供不了」**MUST 由实现方抛具名原因来说，
       不许靠不定义方法来说**——留着 `?` 等于留一张假的安全网。
       另在组装根把那个宽松断言改成两跳（先断言成真实注入的属主类型、再靠赋值做结构核对），
       于是「换成 HTTP 客户端后少实现一个方法」变成**组装根编译红**，而不是运行时静默跳过。
       转写上下文读到「不支持」时额外响一条一次性告警，点名后果是
       「每篇图文帖重跑视觉转写、不会自愈」。 -->
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
- [x] 0.7a **角色名合同测试横跨三个属主，已裁定不拆、改为声明式留守 + 自熄断言。**
  <!-- ⚠️ 本条原文的因果**是错的**，已实跑证伪，保留在下方供追溯。
       原文说「改判后它才成了跨属主测试」。真相：**它在改判之前就已经跨属主、就已经留守 cloud**。
       实跑派生器（`scripts/sync-split-repos` 的 test 归属分类，只读）在两个 ref 上对比：
       改判后（origin/master）判「留守 cloud」，改判前（1d31c30~1）**同样**判「留守 cloud」。
       根因是**第三个属主**：角色目录 `ROLE_CATALOG` 住在 `src/config/role-catalog.ts`，属主 **api**，
       改判前后都没变。所以这道闸天然横跨 automation / content / api 三层，改判一个字没改变它。 -->
  <!-- 裁定：**不拆**。判据是「角色名漂了会当场红」拆完之后是否仍成立，实测两个方向都不成立：
       ① automation 仓的依赖只有 kernel（连 transport 都没有），**拿不到 api 的角色目录**——
          拆给它的那半只剩类型层，而运行时那一半（目录查不到 → 静默回落默认模型）恰恰是要防的那一种；
       ② content 仓的 src 里既没有事件总线目录也没有配置目录（实测不存在），
          那半连一行断言都写不出来，硬写只会重新引到 automation + api，派生仍判跨属主、还是留守。
       派生仓今天对这道闸**零等价覆盖**（三仓 test 里对角色目录零引用）。 -->
  <!-- aidcp-cloud <pending> 落法：`test/agents/content-role-names.test.ts` 加 `aidcp:test-owner=cloud`
       显式标记（仓内已有 5 个文件用这个约定），让「留守」成为**声明**而不是派生副产物——
       cloud 退役盘点时一条 grep 就能捞出「必须先另找归宿的闸」清单。
       另加**自熄断言**：三样原料一旦收敛到同一属主，测试当场红并指明去拆。
       没有它，那个标记就是一张永久免死金牌。
       负例验证做了 5 个方向（角色名多一个字母 / 类型层掉出联合 / 目录改属主 / 三料收敛 / 原料改名），
       全部当场红，验证后逐字节还原。 -->
  <!-- 遗留：cloud 退役时，这道闸的唯一出路是**跨进程契约测试**（automation 拿到的角色名 ↔ api 的目录），
       不是搬文件。 -->
- [ ] 0.7a0 **原文（已证伪，保留供追溯）**：改判的连带项：角色名合同测试会横跨两个属主。
  `test/agents/content-role-names.test.ts` 同时引用四个改判角色与 `PersonaGenerator`（留 content），
  改判后它按 import 派生就成了跨属主测试、**留守 cloud，两个派生仓都不跑它**。
  那道闸守的是「角色名写错一个字母 → 调度器按名字查不到模型配置 → 静默用默认模型跑、零日志」，
  **不能就这么失效**。按属主拆成两份，或明确记录它为何留守。
- [x] 0.7b **同步时需要 `--prune`**：四个角色 + `content-role.ts` + `curated-gate.ts` 要从
  `aidcp-content/src` 移除、进 `aidcp-automation/src`。`sync-split-repos` 默认只报不删，
  **必须显式 `--prune`**，否则 content 仓会同时留着旧副本（两份实现，本项目点名的失败形态）。
  <!-- 2026-07-29 已对改判分支实跑预演坐实（--ref origin/codex/<change>，只读）：
       automation 227→233（新增 6）、content 85→79（**多出 6**）、kernel 96→101（新增 5）。
       「多出 6」就是不 prune 会留在 content 的那批。 -->
  <!-- 2026-07-29 已真同步：`--apply --prune` 后六仓全对齐（automation 234/234、content 79/79、
       kernel 102/102、transport 48、api 115/115，pin 全对齐），残余「差异」只剩组装根（设计上从不同步）。 -->
  <!-- 实跑还挖出两个预演看不见的坑，都不在原计划里：
       ① **测试要单独一趟 `--apply --tests`，且它不删**。src 搬完不带测试，content 会留下三个引用已搬走
          符号的测试文件（编译红）。`--tests` 与 `--prune` 互斥（脚本硬拦），所以顺序必须是
          先 `--apply --prune` 收 src、再 `--apply --tests` 收测试、最后**人工删**它报出的「多出」那一个
          （`test/publish-agent/curated-gate.test.ts`，脚本只报不删，理由是派生私有测试必须显式保留）。
       ② **派生仓自己那份 `boundaries/ownership-rules.json` 不在同步范围内，会长期静默漂**。
          automation 那份还写着四个角色归 content（我在事实源里已改判 automation），
          且**早就**漏了两条 facebook-rule-mode 裁定——之所以一直没人发现，是因为它的
          `module-ownership.json` 是个更早生成的产物、把窟窿盖住了：census 测试过得去，
          而 `boundaries:refresh` 一跑就抛。本轮按事实源补齐了这三处。
          **这是结构性问题，不是本次的一次性修补**：登记为 0.7c。 -->
- [ ] 0.7d **集成纪律（今晚差点漏掉一半，记下来）：一个任务的改动可能落在**多个仓的 worktree**里，
  集成时 MUST 逐仓查一遍脏状态，不能只看主改的那个仓。**
  实例：0.3f 的改动同时落在 `aidcp-cloud.wt/` 与 `aidcp-automation.wt/`。cloud 侧我提交并合了，
  automation 侧那三个文件（台账 15→14、组装根常量、断言）**还留在 worktree 里未提交**，
  而我已经把 automation 的分支合进 master 并推了。
  **后果不会当场报错**：两份台账各自自洽（automation 的 JSON 与它的常量仍然 deepEqual、
  测试照绿），只是 automation 的台账比 cloud 多留了一条不属于它的欠账，
  且这个差**没有任何机械手段会提醒**——两份台账本来就允许不同（问的是不同的问题）。
  已补合（automation `ed5188d`）。**做法**：land 前跑一遍
  `for r in …; do git -C ../$r.wt/<change> status --short; done`，非空即停。
- [ ] 0.7c **派生仓的 `boundaries/*.json` 目前是手抄件、不在 `sync-split-repos` 的同步范围内。**
  按 §8.1，归属的唯一事实源是控制仓 §4.7 → `aidcp-cloud/boundaries/ownership-rules.json`。
  但 `aidcp-automation/boundaries/ownership-rules.json` 是从 `aidcp-cloud@41f2c73` 抄下来后
  **各改各的**，与事实源已差 88 行；`kernel-non-members.json` 差 49 行、`adjudicated-files.json` 差 4 行。
  漂移不会当场报错，只在有人跑 `boundaries:refresh` 时才炸——而平时跑的是 census 测试，
  它读的是**已生成**的 `module-ownership.json`，正好把窟窿盖住。
  **要么让 `sync-split-repos` 把规则表也纳入对账，要么让派生仓不再自持规则表、直接读事实源那一份。**
  本轮只按事实源补齐了 automation 的三处，没动这个结构。
- [x] 0.8 落实 A1：模型出口进 `aidcp-transport`。核对准入判据实跑一遍
  （`test/acceptance/module-boundary.test.ts` 的真正则，别凭记忆用「四条硬禁」），
  再按 kernel → transport → 三个业务仓的顺序快进 pin。
  <!-- 2026-07-29 完成：`src/llm/qwen.ts` + `src/llm/providers.ts` 进 aidcp-transport（08c4e81）。
       pin 按序快进：kernel 21cc10a → transport 21cc10a → 三个业务仓 21cc10a/08c4e81，
       每一步 `npm install --userconfig /dev/null` + typecheck + 全量测试。
       六仓全绿：cloud 全量 / api 470 / automation 1888 / content 436 / kernel 57 / transport 36。 -->
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

- [x] 1.1 `aidcp-kernel`：为四条指令定义窄接口与纯类型（请求 / 结果 / 具名失败原因）；不放行为类。
  <!-- aidcp-cloud <pending> src/kernel/operator-command-port.ts。形状**逐字复用 4a 已建立的 paired command**
       （信封 + 幂等键 + `applied|duplicate|collision` 回执），没有另造第二套机制——这是本条最重要的落点。
       四条语义钉在类型上：① `executionTarget` 由客户端从本进程部署事实注入，调用方（飞书 handler / 面板路由 /
       卡片回调）**没有任何入口能选它**（DEV/OL 共库，让调用方挑 target 等于把「在哪台机器上真跑」交给一个 body 字段）；
       ② 处理器没接线回 `not_delivered` + 具名原因，api 侧 MUST NOT 表述成已受理 / 已排队；
       ③ 传输失败 / 超时=**结果未知**，既不推断成功也不推断失败（发布 / 评论 / 启停都有真实副作用）；
       ④ 重放按持久台账**原样回放首次结果**，MUST NOT 现算一个 `changed:false`。
       不新造错误类：传输失败复用既有 `ApiDirectHttpError`，业务拒绝复用既有 `DelegatedTaskServiceError`。 -->
  <!-- 顺带查出一个**现役潜伏 bug**（登记在 1.7）：`feishu/delegated-task-card.ts` 与
       `client-auth/client-auth-server.ts` 用 `instanceof DelegatedTaskServiceError` 认错误，
       跨进程后错误是 JSON 反序列化出来的裸对象、原型链上什么都没有，那两处**恒 false**。
       后果不是报错而是静默降级：`version_conflict` 会退化成一条普通错误 toast、刷新卡不再回。
       本轮补了结构化守卫 `isDelegatedTaskServiceError`，迁移调用点留到接线那一轮。 -->
- [x] 1.2 `aidcp-transport`：四条指令的「服务端注册 + 客户端 + 路径常量」三件套各一份，两端共用同一定义。
  <!-- aidcp-cloud <pending> src/transport/operator-command-http.ts（零属主表 SQL），
       同批加进控制仓 scripts/sync-split-repos 的 TRANSPORT_MEMBERS。
       三件套同文件的理由照 §8.4：复制成两份，两端路径会悄悄对不上，且两侧各自编译通过、各自测试通过，
       只有真跑起来才 404。 -->
- [x] 1.7 **接线期欠账（①② 已消，③④ 仍在；`OPERATOR_COMMAND_WIRING_DEBT` 已收缩、消掉的两条移入
  新增的 `OPERATOR_COMMAND_WIRING_DEBT_CLOSED`）**：
  ① `delegated-task-http.ts` 既有 7 条路由**不带信封**（无版本 / 无 target 校验 / 无 Bearer），MUST 与新的
  `create-from-text` 统一到信封形态，否则同一个域会有两套鉴权口径；
  ② 上面那两处 `instanceof` MUST 迁到结构化守卫；
  <!-- aidcp-cloud 5323ee5。**①② 一次做完，因为它俩是同一个文件里的同一次改动**——分两轮做是白费一遍。
       ① 7 条路由迁到信封形态：`registerBearer` + `parseApiDirectEnvelope`（版本 + 执行目标双校验），
          **7 个方法签名一个没动**，故「组装根可原样注入本地实例」这条性质保住、不需要任何适配器。
          读 / 写分两个出口：`get` / `list` 失败译「读不到」，其余五个有真副作用、失败译**结果未知**。
       ② 的另一半（此前无人登记的那半）已补：服务端 `delegatedTaskErrorOriginOf` 把 `name` / `status`
          放进传输错误的附加位（线格式对传输层自己的错误类**是保附加位的**），客户端
          `restoreDelegatedTaskServiceError` 先按 kernel 那条**补集**判据（此前零消费）认出「这是业务原因码」
          再还原。`status` 逐字取服务端给的，**还原不出返回 null、绝不套默认**。
       委托任务的线上形状守卫**收成一份**，家在它所校验的端口面旁边；运营指令那侧改为引入，不再自持第二份。 -->
  <!-- **变异实测两轮，第二轮的结论值得单独记**：
       ① 把服务端那层附加位包装做成死代码（= 修之前的形态）→ 用例 5（版本冲突 409）与 6（平台不支持 422）
          当场红。**这坐实了「修之前那六处在真跨进程链路上恒 false」不是推理而是实测。**
       ② 把客户端还原改成「缺 status 就补 400」→ **用例 5 / 6 照样绿**（那两条路径服务端确实带了字段，
          默认值根本没机会生效），真正抓住它的是**还原判据的单测**与**传输错误透传那条用例**。
       ⇒ 「不许补默认 status」这条不变量的守卫**不在**端到端那两条用例上。谁若日后觉得单测冗余、
          以「409/422 那两条已经覆盖了」为由删掉它，这条闸就无声消失。 -->
  <!-- 顺带修掉裁定文档 J 条（原记「`runDelegated` 把所有异常统一渲染成黄色『需要补充信息』」）：
       aidcp-cloud e790e47。异常改按结构化守卫分流——认得出业务原因码的仍是黄色「需要补充信息」，
       其余一律红色「未受理，结果未知」并把原文带出来 + 提示先查任务列表再决定是否重发。
       **J 条比原记载更糟**：`delegatedTaskService` 缺席时（正是 api 独立起进程的常态）那条
       `automation_operator_command_unavailable:delegate` 也走同一个兜底 ⇒ 运营看到的是
       「你的话没说清楚」。代价是运营会改措辞重发，而重发对「没接线」无效、对「超时」可能真发第二次。 -->
- [x] 1.7a **裁定文档步骤 0-a（分号批命令键分隔符撞车）已修**。
  <!-- aidcp-cloud 5323ee5。子命令 id 的分隔符由 `:` 改 `-`，收进具名函数 `batchSubCommandMessageId`
       并写明单射论证（飞书消息 id 形如 `om_<hex>`、本身不含 `-`，故反解唯一；**刻意不做 replace 归一**
       ——顺手 replace 会把两个不同 id 归成同一个，那是把「一条命令被拒发」换成「两条命令共用一把幂等键」，
       后者更隐蔽也更贵）。
       机械判据落在用例 18：**拿 kernel 真函数算一遍**，不在测试里重述 kernel 的规则——
       重述的话 kernel 哪天把分隔符改成 `-`，用例还是绿的。变异实测：改回冒号，用例 18 当场红。 -->
- [x] 1.7b **裁定文档步骤 0-b 的靶子是死代码；用户 2026-07-30 裁定「以论证消掉台账，契约留着」，已执行。**
  <!-- aidcp-cloud 730f910 / aidcp-automation 30a414b / aidcp-kernel 0a0a94e。
       **这是本 change 第一次真撤掉一条台账**（cloud 55→54、automation 14→13，operator-command 4→3）。
       撤的理由不是「我们接好了」，而是**这条欠账记在了错的条目上**：它那两条证据是
       `automation_operator_command_unavailable:publish` / `:comment` 两个文案探针，指向命令面
       `publish:` / `comment:` 闭包的 `mode === 'api'` 分支——而那两个闭包不可达（见本条正文）。
       api 模式下这两条能力真正的失败发生在**委托通道**上，由 `feishu-operator-natural-language-delegate`
       承接，那条仍在。**能力仍被覆盖，少的只是重复计数。**
       契约（两个手动指令端口）刻意保留：形状是对的，一旦裁定「绕开委托直发」立刻就有消费者。
       三处都写了理由，**其中自动化侧是刻意重写一份**——那份 census 是永久手写分叉、拿不到 cloud 侧的
       任何机械信号（§4.8），指望注释自己传过去就是又踩一次那个坑。
       撤条走的是**官方派生出口**（`--refresh-ledger`），两侧都没手改 JSON。 -->
  <!-- **两道既有计数断言当场把它抓住了，这正是棘轮在工作**：cloud 那条「运营指令必须是 4 条」、
       automation 那条 `blockers.length === 14` + 分类计数。两处都按「只许下降 + 必须写明理由」显式下调，
       并在注释里补了一句判据：**没有配套裁定说明的下降 = 某个探针不再命中 = 回归，不是进展。**
       另按 PersonaGenerator 的撤条判例加了一条自熄断言：该 id 或那两个文案探针**重新出现即红**，
       失败消息里写明「若那两个闭包真变可达（delegate 改回可选、或两条命令改成绕开委托），
       那是前提变了，MUST 重新裁定，不许静默把 binding 加回去」。 -->
- [ ] 1.7b0 **原文（前提已被推翻，保留供追溯）**：手动发帖 / 手动评论拿不到稳定键，需补消息 id 透传。
  原文说「手动发帖 / 手动评论拿不到稳定键：消息 id 只透传给了自由文本委托那条，发帖 / 评论只拿到来源会话 id」。
  **透传缺失属实，但那两条路径在生产里根本不执行**，所以补透传补不到任何活链路上：
  - `CommandRouter` 里 `/publish`、`/comment` 的分支是
    `this.actions.delegate ? runDelegated(...) : runPublish/runComment(...)`；
  - 而统一命令面把 `delegate` 声明成**必填**（`CommandFaceDeps.delegate: NonNullable<CommandActions['delegate']>`），
    组装根恒注入一个函数（缺服务时函数**内部**抛，不是不给函数）⇒ **那个三元永远走委托分支**；
  - `runPublish` / `runComment` 是 `CommandActions.publish` / `.comment` 的**唯一**消费者（全仓 grep 坐实），
    而面板那份动作面（`PanelCommandActions`）**只有** pause / resume / dispatch? / dispatchActive?、
    **没有 publish / comment** ⇒ 面板也到不了它俩。
  ⇒ **两个手动指令端口（`ManualPublishCommandPort` / `ManualCommentCommandPort`）今天没有任何活的 api 侧调用方。**
  生产里 `/publish`、`/comment` 走的是「委托 → automation 意图解析 → 委托任务 → 委托执行器就地调
  `triggerManual`」，而拆完之后**执行器与调度器同在 automation 进程**，这一跳压根不跨进程。
  **两条路都成立、但必须显式选一条，不能默认接线**：
  ① 判定这两个端口当前无消费者，`feishu-operator-publish-comment` 那条台账**以论证消掉**
     （连同契约保留待将来），并把理由写进两个端口的注释；
  ② 或裁定 `/publish`、`/comment` 应绕开委托路径直发，届时 0-b 的透传才有意义。
  **MUST NOT 静默接线**：接一条今天不执行的通道，等于新增一处「看着接好了、其实永不触发」的假绿。
  <!-- ② **已做，且实测是 3 个文件 / 6 个调用点，不是「两处」**（aidcp-cloud <pending>）：
       飞书委托卡片 1 处、客户鉴权服务 **4 处**（本条记成了 1 处）、
       **面板服务 1 处（`panel/panel-server.ts` 的委托任务错误出口，tasks.md 里从来没登记过）**。
       最后那处是同一个潜伏 bug 的第三个受害者：后台控制台发起的委托任务，任何 409 / 422
       都会塌成一条泛化的 500，操作员看不到「版本冲突」这个真原因。
       客户鉴权那 4 处原本是逐字重复的四段，已收成一个本地函数。 -->
  <!-- ⚠️ **上面那句「已做」必须限定范围，否则是过度声称（2026-07-30 自查更正）**：
       做完的是「不再按原型认错误」这一半。**另一半没做，所以真跨进程链路上那 6 处仍然恒 false**——
       内部 HTTP 的线格式对一个带 `code` 的抛出物只保 `code` + `message`，
       **`name` 与 `status` 在那一跳被丢**，而守卫判的正是 `name`。
       后果与 kernel 注释里预言的一字不差：版本冲突退化成普通错误提示且不再回刷新卡、
       客户端 API 的 409 / 422 一律塌成 500、后台控制台发起的委托任务同样塌成泛化 500。
       **这正是我给内容侧两个端口写过的那个陷阱（「只写不用 instanceof 是不够的」），
       却没在委托这一族关上——同一个坑，两处只堵了一处。**
       补法见 `delegated-task-channel-adjudication.md` §2.5：服务端把 `name` / `status` 塞进
       传输错误的 `details`（线格式对传输层自己的错误**是保 `details` 的**），
       客户端用 kernel 里**已经写好但零消费**的补集判据还原；
       **`status` MUST 由服务端带过来，MUST NOT 在客户端补默认 400**（补 400 会把 409/422 一并压平）。
       单体里这 6 处不过那一跳，所以今天行为不受影响——但「已修复」这个说法要等补完才成立。 -->
  <!-- 遗留两条陈述已过时、**已在 1b36b74 修掉**：
       `src/transport/content-authority-http.ts` 的欠账表里那条「精选库错误没有 code」已标为已消；
       `src/kernel/operator-command-port.ts` 的文件头已补上第三个消费者与真实的 6 个调用点。 -->
  ③ 四条写指令的接收方 MUST 建**持久**幂等台账（跨进程重启仍成立），否则 ④ 那条「原样回放首次结果」无处可放；
  ④ `ApiDirectWriteErrorCode` 可按 4a 惯例补四个逐命令的 `*_result_unknown` 码（本轮统一用
  `api_authority_result_unknown`，刻意不改既有 kernel 文件以免与并行任务撞热点）。
- [ ] 1.3 `aidcp-cloud`（事实源）：按 4a paired command 形态实现 route + receiver + api 侧 client；
  自由文本委托的**意图解析留在 automation**，api 侧 MUST NOT 自己拼 intent 调结构化入口。
- [ ] 1.4 调度启停：**「飞书 dispatch」这条通道自始至终不存在**（`feishu/command-face.ts` 的动作全集是
  `status/pause/resume/bindChat/delegate/publish/comment`，无 dispatch）；那个 `:dispatch` 文案只服务
  **面板路由**与 dashboard 状态灯。台账两条证据是同一条通道的两个证据。
  一条 paired command 一次接线即同时点亮面板按钮与状态灯，**飞书侧零改动**。
- [x] 1.4a **批 1 的前置改动**：`feishu/command-face.ts:27-35` 那份 `PanelCommandActions` 的
  `dispatch` / `dispatchActive` 是**必填**，而 `panel/types.ts:270/275` 那份是**可选**。
  api 因此被迫必须传一个函数——「诚实地不注入」在类型层做不到，只能在「抛错」与「撒谎」之间选。
  先把前者改成可选，顺带消掉两份同名类型的漂移。
  <!-- aidcp-cloud <pending> 已做，且**两份同名类型已收成一份**（面板那份改为从飞书侧导入，
       它本来就有那条 import 说明符，没新增模块边；两个文件同属 api，归属零变化）。
       两处的 dispatch / dispatchActive 现在都是可选。
       **本条对「飞书 dispatch 通道自始至终不存在」的记载已核实为真**：飞书那份动作全集是
       `status / pause / resume / publishTest? / publish? / comment? / bindChat?`，没有 dispatch，
       `src/feishu/` 里也没有任何一条路由指向它。 -->
  <!-- ⚠️ **本条现在只是「使能」，还没兑现**：组装根仍在往下传两个占位桩
       （约 `src/server.ts:8219-8229` 的 `?? (() => Promise.reject(...))` / `?? (() => { throw ... })`）。
       桩还在，面板那条「未接线 → 503」分支与状态灯的 null 态就仍然到不了，行为逐位未变。
       改成直接传可选句柄才算落地——`src/server.ts` 是并行热点，本轮没动。 -->
- [ ] 1.4b **委托卡片动作的处理器其实是 api 属主**（`src/feishu/` 整目录 15/15 归 api）：
  方向仍是 api→automation（缺的是服务端口注入），但**没有任何代码需要搬家**。
- [x] 1.4c **委托的跨进程通道差的是「一次升级 + 一次接线」，不是「只差接线」**（措辞按裁定文档 §5 F 条更正）：
  `aidcp-automation/src/transport/delegated-task-http.ts` 服务端注册 + 客户端 + 7 个路由方法齐全，
  文件头曾明写「不接线、不改默认注入」；cloud 全仓对这两个符号零消费。
  <!-- aidcp-cloud 5323ee5：**升级那一半已做**（见 1.7），文件头已从「证明性接线（behavior-zero）」
       改成「正式跨进程传输实现」。接线那一半仍未做（要动组装根，热点，见 1.3 步骤 5）。
       零消费仍成立——所以这批改动**对现网行为零影响**，唯一有行为的是 e790e47 那处飞书渲染分流。 -->
- [x] 1.5 **契约测试 19 条里 17 条已落**（transport 侧 10 条 + 接收方侧 7 条），余 2 条各有具名理由。
  <!-- 接收方侧新落 7 条（aidcp-cloud 843bac6）：8（连发两次 → applied/duplicate 且回执逐字段相同）/
       9（同键不同 scope → collision）/ 10（停在 in_flight 且无同进程调用 → 抛「结果未知」）/
       11（换接收方实例仍判 duplicate）/ 12（调度启停重启后 MUST 重新执行、不判 duplicate）/
       13（未注入 → not_delivered 且**不是**异常）/ 15（状态灯读不到 → unavailable，不压成 active:false）。
       另有 9 条超出清单的：同进程重投等到真结局、非业务抛出物留 in_flight、业务拒绝 status 原样、
       控制类形状翻译、键非法即拒、7 方法不进台账、缺 status 不补默认 等。
       **余下 2 条的处置**：
       ① 用例 16（端口加方法而路由表没跟上 → typecheck 红）是**编译期**闸，运行期测不出来，
          已在路由表注释里写明它「只保证表全、保证不了都挂上」，配一条逐路由注册对账用例（17）兜后半；
       ② 用例 19（手动发帖 / 评论键跨重试稳定）**被 1.7b 挡住**——那条路径今天不执行，
          等重新裁定后再补，现在写等于给死代码配用例。 -->
  <!-- aidcp-cloud 5323ee5。裁定文档 §4 的 19 条用例里，**不依赖接收方的 10 条已落**：
       1（逐条路由无令牌 → 401，7 条全扫）/ 2（版本不符）/ 3（目标不符）/ 4（客户端无从自选目标）/
       5（版本冲突跨线后守卫为真且 status 409）/ 6（422 不被压成 400）/ 7（缺字段判形状不符）/
       14（连不上 → 读译「读不到」、写译「结果未知」）/ 17（逐条路由真被挂上）/ 18（分号批键合法且互异）。
       **余下 9 条全部依赖那个还没写的接收方**：8 / 9 / 10 / 11（幂等台账四态与跨重启）、
       12（启停重放 MUST 重新执行、不判 duplicate）、13（未注入 → `not_delivered` 且不是异常）、
       15（状态灯读不到 MUST NOT 画成 active:false）、16（`satisfies` 那道编译闸——只能靠变异证，
       本批已在路由表注释里写明它「只保证表全、保证不了都挂上」）、19（手动发帖 / 评论键跨重试稳定
       ——**被 1.7b 挡住，那条路径今天不执行**）。 -->
- [x] 1.5a **幂等台账已落（表 + 存储 + 接收方 + 用例），且原清单里的「四处耦合」实测是五处**。
  <!-- aidcp-cloud 843bac6 / aidcp-automation 70addd5。落地物：
       `migrations/0099_operator_command_receipt.sql`（kind=expand，属主 automation）+
       `src/delegated-task/operator-command-ledger.ts`（PG 实现 + 供测试用的内存实现）+
       `src/delegated-task/operator-command-receiver.ts`（自由文本接收方 + 调度启停接收方）+
       16 条用例。归属由目录默认规则判 automation，**归属规则表一个字没改**（与 0.6h 的预判一致）。
       **更正：耦合单元是五处，不是四处。** 第五处是 `test/schema/sync-read-checkpoint-migration.test.ts`
       里**第二次写死** `KNOWN_MAX_SCHEMA_VERSION`——那条是逐字字面量，而 `schema-contract.test.ts`
       那条是从 migrations/ 目录**算**出最大版本再比。加迁移时两处都红，改完一处会以为完事了。
       已在该断言旁写明「这是第二处」。 -->
  <!-- **`REQUIRED_SCHEMA_VERSION` 刻意没抬**，判据是这条常量自己的门槛（缺了它链路写不了）今天不成立：
       接收方还没接进任何进程。**实测那条链路后果比原先记的更重**：schema 契约门是 segA 的第一句、
       裸 await、无 try/catch，跑在连接池与所有存储 init 之前；enforce 下抛出 → 进程 exit 1 →
       systemd 只有 `Restart=on-failure` / `RestartSec=5`、无 OnFailure、机器上无探针
       ⇒ **每 5 秒静默重启的崩溃循环、零告警**。且「behind」这一档**没有豁免通道**
       （`pass`/`waived` 在该分支写死 false；`AIDCP_ALLOW_SCHEMA_AHEAD` 只管「库比代码新」那一档）。
       **另一个部署陷阱**：`scripts/run-migration.ts` 执行 SQL 但**不写账本**（其文件头明写这条缺口，
       且用户 2026-07-25 裁定有意保留它）⇒ 用它补迁移，表建好了而门读的账本仍是旧版本、照样判 behind，
       现场看起来「表明明在」，最费时间。补迁移只能用 `npm run migrate up`。 -->
- [x] 1.5a0 **原清单（保留供追溯，其中「四处」已更正为五处）**。
  <!-- 2026-07-30 实测（六路勘察 + 逐条对抗核验，`aidcp-cloud@93d339b`）：
       ① **下一个可用迁移号是 0099，不是 0080**。migrations/ 现有 97 个 .sql，数字序最大
          `0098_facebook_group_join_daily_cap_50`；0079..0098 密集无空洞（0012 是永久保留空号）。
          裁定文档援引的 `0079_risk_command_outcome` 只是**判例**，不是队尾——它本身已被
          `0080_restricted_recovery_outcome` 扩过一次（+10 可空列、state 的 CHECK 从 3 值放宽到 5 值、
          6 条具名约束），**今天那张表的真实形状是 0079+0080**，照 0079 单独一份会低估形状。
       ② 耦合单元共**四处**，同一批做完：新迁移 + `src/schema/schema-contract.ts` 的
          `KNOWN_MAX_SCHEMA_VERSION`（现 `0098_...`，有测试断言它恒等于 migrations/ 最大版本，
          加了迁移不抬就红）+ 该常量上方那段**逐迁移追加式的裁定台账 JSDoc**（那是事实上的登记面，
          文件里没有任何表清单 / 版本清单数据结构）+ `boundaries/table-ownership.json` 追加一条
          `{table, owner:'automation', basis}`（现 112 条 = api 54 / automation 51 / content 7）。
          `REQUIRED_SCHEMA_VERSION`（现 `0097_...`）只在「缺了这条迁移链路就写不了」时才抬——
          接收方的台账写属于这一类，故**应当一并抬到 0099**，但那会给部署引入「先建表后上代码」的顺序约束。
       ③ **`AC-OWN-06`（跨属主表读）没有豁免通道，且这是有意的**。新台账表归 automation 后，
          api 侧若直接读它就是硬红、无处可登记——回读只能经内部 API。 -->
- [ ] 1.5b **⚠️ 逐条核对错误码的 status，别按 code 猜**（写还原用例时会用到）。
  <!-- 2026-07-30 实测：`prepareTarget` 钩子里 5 个码（`candidate_target_required` /
       `candidate_not_found_or_mismatch` / `candidate_not_pending` / `curated_content_unavailable` /
       `curated_target_unavailable`）全部被统一压成 409；`unsupported_action` 三处抛出**都是 422**、
       是 status-稳定的；真正 status 不稳定的那个码是 `account_name_required`。
       ⇒ **绝不可以在客户端按 code 查一张表反推 status**（那正是「补默认」的变形），
       status 只认服务端随附加位带过来的那个。 -->
- [x] 1.4d **`DataGateway` 与 paired command 二选一**（已裁定：是伪二选一，见下）：委托服务在 api 侧有**三个**消费者
  （飞书入站 `8316`、面板 `8615`、客户端 API `9157`），后两个走 `DataGateway`，
  而 `DataGateway` 在 `8539-8563` 已预留 remote thunk 位置。两条都建会出现
  「飞书走一条、面板与客户端 API 走另一条」的分叉，两者鉴权 / target 校验 / 错误归一都不同。
  <!-- 2026-07-30 调研 + 裁定建议已产出：本目录 `delegated-task-channel-adjudication.md`
       （pin 在 aidcp-cloud@1b36b74，含 1.3 / 1.5 落地步骤与 13 条与本节记载不符的实测事实）。
       结论摘要：**不是二选一**——两者方法集**零重叠**（既有 7 条是委托读写窄面，运营指令通道补的是
       第 8 个方法 + 三条与委托无关的指令，kernel 自己就把它们并成 `DelegatedTaskCommandPort`）。
       要收口的是**传输纪律**（统一到信封 + Bearer + 服务端注入 target）与**注入点**
       （四个接线点全部改指 `DataGateway`，飞书那两处今天绕开它，客户端 API 里还有第五处直连）。
       两个传输文件都保留、都不是重复实现。
       ⚠️ 最重要的一条：**1.7② 只完成了一半**——线格式只保 `code`+`message`，`name`/`status`
       在那一跳被丢，而结构化守卫判的是 `name`，故那 6 处迁移在真跨进程链路上**仍然恒 false**。
       修法在文档 §2.5（服务端把 name/status 塞进传输错误的 details，客户端按 kernel 已有的
       **补集判据** `OPERATOR_COMMAND_TRANSPORT_ERROR_CODES` 还原，该判据今天零消费）。 -->
  <!-- ⚠️ 另有一条**做 1.3 之前必须先解决**的真缺陷（文档 §3 步骤 0-a）：飞书分号批命令给子命令编的
       消息 id 是 `${messageId}:command:${n}`，而冒号正是 `commandId` 的分段分隔符、合法性检查明确拒绝它
       ⇒ `operatorCommandId()` 返回 null ⇒ 按契约必须拒发 ⇒ **每一条分号批里的委托 / 发帖 / 评论都会被拒发**。 -->
  <!-- 1.7③ 的范围要缩：**是三条不是四条**。调度启停改的是进程内布尔，给它持久台账会让重启后
       一次真实启动被判 duplicate 并回放陈旧的 `changed` —— 编造事实。4a 的 edge-resume receiver
       已有逐字同形的判例（状态是进程内的，台账就该是进程内的）。 -->
  <!-- 1.4a 的那条 ⚠️（「桩还在、行为逐位未变」）**已过时**：两个占位桩在 1b36b74 已删，
       `src/server.ts` 现写「调度启停两条句柄直接透传，不补占位桩」，两份同名动作面也已收成一份。 -->
- [ ] 1.5c 契约测试（**原文，范围与进度见上面的 1.5**）：鉴权、版本 / target 校验、幂等重放、
  **结果未知**（传输失败不得改写领域结局）。
- [ ] 1.6 `aidcp-automation` / `aidcp-api`：同步派生并各自跑 typecheck + 聚焦测试。

## 2. content 属主 authority（automation → content）

- [x] 2.1 `aidcp-content`：在既有内部 HTTP 服务端上注册四组写口——草稿精修 / FB 发帖素材 /
  概念池 / 精选库；每组独立注册，**一组初始化失败不得连带关闭其它组**（照 content 现有纪律）。
  <!-- ⚠️ 本条的「四组写口」两处不准，实装时按下面这版走：
       ① **草稿精修那条已被 0.6a 撤掉**（automation 方向现存 runtime 边为零，不开这个写口）；
       ② FB 发帖素材（2.1）与 token 用量（2.2）**今天在 kernel 里根本没有端口**，三件套无从写起，
          得先补端口面才谈得上注册；
       ③ 「写口」是误称：精选库两条**纯读**（0.6c 自己写的就是「补跨界读」），
          概念池 6 条里只有 2 条是写。名字不改没关系，但别照字面去找四组写。
       实际有契约的只有概念池 + 精选库这两条，且 2.3 的三件套已随 0.6h 落地。 -->
  <!-- aidcp-cloud 93d339b / aidcp-content 179d201。概念池 + 精选库两组已在 content 监听上**各自独立注册**。
       **投影已归位属主**：属主补了三字段召回方法，组装根那个 `.then(rows => rows.map(...))` 删掉改调属主。
       刻意**复用**全字段召回而不是另写一句 SQL——排序语义是两条召回共有的，抄成两份漂了不会报错，
       只会让选词看到的样本和创作看到的素材悄悄错位。
       另加一道机械闸：期望的方法名**从路由表现算**，逐条断言属主实例上确有该函数——
       防止将来端口加了方法而属主没跟上，被在场探针译成一句冒名的「对面不支持这个方法」。
       **单体行为逐位不变，且是断言出来的不是论证出来的**：注册函数只在 content 监听下跑，
       测试钉死单体与 core 两种模式都不启用它。 -->
  <!-- ⚠️ **2.1 那句「一组失败不连带关闭其它组」已做到，但同一个监听上还剩一处口径分裂**：
       老的裸形态精选路由（无鉴权、无信封、无目标校验）与新的精选召回路由**同进程并存**。
       路径不冲突，但同一个域两套鉴权口径，统一得单独一轮。 -->
- [x] 2.2 `aidcp-content`：token 用量记账写口。成本 MUST 由厂商账单反算，
  **禁止**在这一层硬编码价目表。
  <!-- aidcp-cloud c014393。**独立复核过：全仓没有任何硬编码价目表。**
       链路是「金额 ÷ token 数 × 1000」从厂商账单明细反算成单价快照落库，属主读时按最新可用历史价算出，
       无价即 null（不兜底 0）。已上线规格明文钉着这条。
       **端口面刻意不带任何单价 / 金额 / 币种字段。** -->
  <!-- **这是唯一一处刻意不照抄属主签名的端口**，理由值得记：属主入口是「发了就不管」的同步调用、
       纯内存缓冲。跨进程照抄只会得到一个**必然撒谎**的方法——无处报失败即静默假成功；
       而且一次模型调用一次 HTTP，会打掉属主自己列的「批量」不变量、把一条低频旁路挂上模型调用热路径。
       所以端口改成**提交已合并的增量行**，正是属主那个定时器今天真正落库的东西。
       属主今天没有这个方法，与精选库那条同形：content 接线时补方法或交适配对象，
       否则服务端在场探针答具名「不支持」，**绝不静默变成「记上了」**。 -->
- [x] 2.3 `aidcp-transport`：上述各口的三件套；`aidcp-kernel`：对应窄接口与失败原因联合类型。
  <!-- 四组全齐：概念池 + 精选库（0.6h）、FB 发帖素材 + token 用量（c014393）。
       后两组另析出一层共用的线上失败译码层——那 120 行映射表复制成两份会各自编译过、各自测试过，
       只在失败真发生那一刻才看得出对不上。 -->
  <!-- **一条关于「typecheck 能守什么」的实测，值得所有写传输三件套的人看**：
       把整条路由注册删掉，typecheck **会**红——但红的是「入参解析器成了孤儿」这个副产物，
       一旦解析器被两条路由共用，这个信号就消失。
       而**真实的滑手形态**（注册时手写一遍路径、不用共享常量）**typecheck 完全绿**，
       只有测试当场红。这就是「路由常量只有一份」的全部理由，也说明别高估 typecheck。 -->
- [x] 2.4 `aidcp-automation`：新增 content 客户端组与 `AIDCP_CONTENT_URL` /
  `AIDCP_CONTENT_INTERNAL_TOKEN`（本仓第一次有 content 方向的出边）。
  <!-- aidcp-automation 8c4ec84。形态照抄既有的 api 客户端组；两项配置走**必填**读取，
       **缺配置直接拒绝启动**——automation 起进程却够不着 content 就是那条缝断了，
       静默回落成「没有素材」正是本项目的红线形态。变异实测：把必填改成带默认值 → 用例当场红。 -->
  <!-- 刻意**没**碰 api 客户端清单与根表面：派生对账会逐条比对它们，混进 content 方向会当场对不上。
       也**没**撤台账里那两条 content 授权欠账——客户端建出来了，但本仓还没有生产消费者，
       撤掉是超额主张。 -->
  <!-- 📌 **2.4 需要第三个工作区**（automation 的手写组装根，cloud 里根本没有这个文件）。
       派生仓的手写组装根从不同步，只能手工改 + 手工 land。 -->
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
- [ ] 2.9 **`content-publish-rejection-evidence-authority` —— 14 条台账里唯一一条此前无人承接的**
  （2026-07-30 交接文档核验时发现：本 tasks.md 与 `specs/` 全文对「否决 / 驳回证据 / 候选装载」零命中，
  我原本误以为它属于 2.7 的传递性检查，实际不属于）。
  **后果是硬的**：96 条 task 全做完，台账也清不到零，第 4 段「清零 → 入口切真启动」直接卡住。
  内容见 automation 台账那条的注释：**草稿否决证据判定在委托执行器的候选装载路径上**。
  先坐实现状（属主是谁 / 判定读的是什么 / automation 侧调用点在哪，带 `文件:行`），
  再决定是补端口面还是**明写它由另一个 change 承接**——两条都可以，但**不能留空**。

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
  <!-- 2026-07-29 22:08 已部署第一批（aidcp-cloud@b66c022，单体形态）。
       快照来源：从 master 目标提交 `git archive` 出的干净快照，**不从任何 worktree 部署**。
       备份：/opt/aidcp/cloud.bak.20260729-220746.tar.gz + .env.bak.20260729。
       rsync 排除 .env / node_modules / .git；本批 package.json 零变更，故未动 node_modules。
       healthcheck 全过：active running；8787 与 127.0.0.1:8090 均在监听；PG 锚点缓存就绪；
       飞书长连接已建立（WSClient onReady）；重启后错误行数 0；config-mirror 正常 5s 一跳。
       同机 isales 四个服务重启前后均 active，全程未触碰。
       **这只证明单体现网零回归**（5.3 的口径），不证明三进程能跑。ol 未部署、用户未提。 -->
  <!-- b66c022 是本批的**最后一个**提交，所以 0.3f 的台账收窄与四条运营指令契约都在这次部署里；
       但它俩不改运行时行为（契约零接线、台账只活在测试面），现网真正变的只有
       错误族抬 kernel、文字转写能力二态、四个角色改判这三处。 -->
  <!-- 2026-07-29 22:52 已部署第二批（aidcp-cloud@9ae8e1d，仍是单体形态）。
       备份 /opt/aidcp/cloud.bak.20260729-225145.tar.gz；package.json 零变更故未动 node_modules。
       **这批是真运行时改动**（五个吞点 + Sink 三方法改必选 + 组装根断言收紧），所以部署验证有意义：
       重启后错误 0；PG / 飞书长连接 / 面板 API 8090 / 客户鉴权 8091 全部就绪；isales 四服务未受影响。
       **具名降级告警一条没出，这是对的**——dev 上精选库与概念池都接着线，本来就不该降级；
       那些告警只在真缺席时才响。另实测属主存储确实实现了改必选的那三个方法。 -->
  <!-- 六仓对齐：kernel `d4f451b` / transport `c07e9b5` / api `f42df86` /
       automation `686253d` / content `30a32c9` / cloud `9ae8e1d`。
       测试：cloud 3883 / api 470 / automation 1897 / content 436 / kernel 57 / transport 36，全 0 fail。 -->
  <!-- 2026-07-29 23:47 已部署第三批（aidcp-cloud@1b36b74，仍是单体形态）。
       备份 /opt/aidcp/cloud.bak.20260729-234657.tar.gz；package.json 零变更。
       重启后错误 0；PG / 飞书长连接 / 面板 8090 / 客户鉴权 8091 全就绪；isales 四服务未受影响。
       六仓对齐：kernel `c59172c` / transport `cb7423c` / api `6bde4db` /
       automation `f224070` / content `d1d8fe1` / cloud `1b36b74`。
       测试：cloud 3890 / api 470 / automation 1900 / content 436 / kernel 59 / transport 36，全 0 fail。 -->
  <!-- 2026-07-30 00:44 已部署第四批（aidcp-cloud@93d339b，仍是单体形态）。
       备份 /opt/aidcp/cloud.bak.20260730-004320.tar.gz；package.json 零变更。
       重启后错误 0；PG / 飞书长连接 / 面板 8090 / 客户鉴权 8091 / 评论调度器 / 发帖调度器全就绪；
       isales 四服务未受影响。
       六仓对齐：kernel `3e80194` / transport `cbb91b7` / api `d9c60cf` /
       automation `17c7712` / content `6ffa70b` / cloud `93d339b`。
       测试：cloud 3900 / api 470 / automation 1900 / content 439 / kernel 59 / transport 36，全 0 fail。
       本批现网真正变的只有一处：三字段窄投影从组装根移到属主存储（复用同一条召回，逐位等价）；
       四组路由注册在单体下**不启用**（只在 content 监听模式跑），已用断言钉死。 -->
  <!-- 2026-07-30 11:33 已部署第五批（aidcp-cloud@e790e47，仍是单体形态）。
       快照来源：从 canonical master 目标提交 `git archive` 出的干净快照，**不从任何 worktree 部署**。
       备份 /opt/aidcp/cloud.bak.20260730-113238.tar.gz + .env.bak.20260730；
       cloud 侧 package.json / package-lock.json **零变更**（pin 抬的是三个派生仓，不是 cloud），故未动 node_modules。
       rsync 排除 .env / .env.bak.* / node_modules / .git，事后逐条确认 .env 与 node_modules 仍在。
       healthcheck 全过：active running；8787 + 面板 8090 + 客户鉴权 8091 均在监听；
       **三个属主库各自 `select 1` 全通**（物理拆库后不再有单一连接串，逐库探的）；
       PG 锚点缓存就绪 / RiskControllerRegistry 就绪 / CommentScheduler 就绪 / 飞书长连接已建立（WSClient onReady）；
       重启后错误行数 0。isales 四服务（api / engine / scheduler / worker）重启前后均 running、全程未触碰。
       另在机器上逐条实证新代码真的上去了（还原函数在场、批命令分隔符已是 `-`、「结果未知」分支在场）——
       **不靠「rsync 没报错」推断**。
       **本批现网真正变的只有一处**：飞书委托异常的渲染分流（e790e47）。传输那半零消费、对现网零影响。
       仍是单体形态，**不证明三进程能跑**（5.3 的口径）。ol 未部署、用户未提。 -->
  <!-- 六仓对齐（2026-07-30）：kernel `65cf14e` / transport `8b3ab8f` / api `6997a74` /
       automation `018dc45` / content `5df122c` / cloud `e790e47`。
       同步按 §5.2 的顺序办：`--apply --prune`（src）+ `--apply --tests`（测试）全部落完，
       再按 kernel → transport → 三个业务仓抬 pin，逐仓 `npm install` + typecheck + 全量测试。
       测试：cloud 3913 / api 473 / automation 1910 / content 439 / kernel 59 / transport 36，全 0 fail。
       **新增用例落点是派生器自己判的、与预期一致**：飞书那 3 条进 api，委托传输那 10 条进 automation。
       复跑对账：六仓 `新增 0 · 内容不同 0 · 多出 0`、pin 全对齐，只剩设计上必然存在的组装根噪声。
       `npm install` **没有**用 `--userconfig /dev/null`：本机内网 registry 当前是通的（见 §5.3 那条更正）。 -->
  <!-- 2026-07-30 16:00 已部署第六批（aidcp-cloud@843bac6，仍是单体形态）。
       备份 /opt/aidcp/cloud.bak.20260730-155902.tar.gz + .env.bak.20260730；cloud 侧 package.json 零变更。
       **本批带迁移，故部署序列多一步、且顺序是硬的**：rsync → `npm run migrate status`（确认待应用
       **恰好 1 条**、其余属主 0，不盲目 apply）→ `npm run migrate up`（applied 0099，kind=expand，11ms）
       → 重启 → healthcheck。
       healthcheck 全过：active running；8787 + 8090 + 8091 在监听；重启后错误行数 0；
       PG 锚点缓存 / CommentScheduler / 面板 / 客户鉴权 / 飞书长连接（WSClient onReady）全就绪；
       三属主库各自 `select 1` 全通；isales 四服务重启前后均 running、全程未触碰。
       **schema 契约门的逐属主结论实证了「按属主收窄」这条机制**（不是推断）：
       automation「账本 0099 / 所需 0096 / 本构建认识 0099」、api「0098 / 0097 / 0098」、
       content「0069 / 0069 / 0069」，三条全通过——所以只抬 KNOWN_MAX 不抬 REQUIRED 确实不阻断启动。
       **属主隔离也实证了**：`operator_command_receipt` 只在 automation 库在场，api / content 两库都不在
       ⇒ 迁移归属从头声明 → 表归属 → 按属主分组 → 只在该属主库应用，全链走通。 -->
  <!-- **本批唯一无测试覆盖的那段（PG 台账 SQL）已在真库上逐分支证明**——单测只覆盖内存那份，
       所以这一步不是形式主义：init() 形状探测通过（表 + 8 列）；claim → claimed；
       二次 claim → existing/in_flight；落定后 → existing/applied；回执 JSONB 往返逐字无损；
       **「已落定的行绝不被第二次落定覆盖」那道闸生效**（第二次 settle 没改动载荷）；
       同键读回首次的 scope。用 VERIFY- 前缀键、跑完删净，事后本表 0 行。 -->
  <!-- 六仓对齐（2026-07-30 第二轮）：cloud `843bac6` / kernel `0a0a94e`（本批未变）/
       transport `c7db33e` / api `a28d134` / automation `70addd5` / content `747c128`。
       测试：cloud 3932 / api 473 / automation 1926 / content 439 / kernel 59 / transport 36，全 0 fail。
       **踩到两处派生仓手抄件**（0.7c 那个结构性问题第二次兑现）：automation 自己那份
       `boundaries/table-ownership.json` 缺新表 ⇒ 迁移属主检查当场红；`module-ownership.json` 缺 2 条
       ⇒ 边界普查红。三仓的 table-ownership 手抄件都停在 112 条，已按事实源逐份增量补齐。
       **一条值得记的区分**：这次漂移是**响亮的**（测试当场红），而上次 `ownership-rules.json`
       漂 88 行那次是**静默的**（检查读的是已生成的产物、把窟窿盖住了）。这影响 0.7c 的优先级判断。
       另：`sync-split-repos` 对迁移文件**只报不改**，0099 要手工拷进 automation 仓（对账会报「缺 1」）。 -->
  <!-- **dev 部署 sha 刻意停在 `e790e47`、未跟到 `730f910`**（如实记下，不是漏部署）：
       730f910 及其派生批次的 delta 只有**测试 + boundaries 生成物 + 一段 kernel 注释**，
       运行时行为逐位不变。为一批纯注释 / 纯测试改动重启在跑的 dev 车队没有收益，故不重启。
       下一批有真运行时改动时一并带上去。六仓 master 对齐基线：
       cloud `730f910` / kernel `0a0a94e` / transport `c8723bf` / api `af2aa5a` /
       automation `30a414b` / content `f75403b`；
       测试 cloud 3913 / api 473 / automation 1910 / content 439 / kernel 59 / transport 36，全 0 fail。 -->
  <!-- **同步顺序上踩到一次 pin 级联，记下来**：`--apply --tests` 会给 kernel 也派测试文件，
       而我是在**三个业务仓 pin 已经抬完之后**才跑的那一趟——kernel 头一动，
       transport 与三个业务仓的 pin 全部作废，只能整条链重抬一遍。
       **正确顺序**：先 `--apply --prune`（src）+ `--apply --tests`（测试）**全部落完**，
       再按 kernel → transport → 三个业务仓抬 pin。 -->
- [ ] 5.5 本地桩验不了的登记 `docs/real-machine-acceptance-backlog.md`（簇 60）。
- [x] 5.6 回写 `docs/cloud-composition-root-trisection.md` §0.0 与
  `docs/cloud-split-next-session-handoff.md` §0.1/§0.2 的实测现状。
- [ ] 5.7 `openspec validate split-cloud-automation-production-runtime --strict` 通过后归档；
  删除 worktree 与分支。
