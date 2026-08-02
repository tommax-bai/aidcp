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
  <!-- **2026-07-31 又发作一次，且这次证明上面那句「只在有人跑 boundaries:refresh 时才炸」在两个仓里连这条退路都没有。**
       - **发作**：另一路 change（add-configurable-facebook-consumption-mode，cloud 878e985）的迁移 0103 加了三张
         api 属主表。三份 `table-ownership.json` 手抄件全停在 121 条，且**迁移文件本身从没进过 aidcp-api**。
         **两个窟窿互相盖住**：属主侧的迁移属主检查读的是**本仓自己的** migrations 目录，
         迁移不在，就没有东西可以拿去跟一份同样缺了它的归属清单对；接口仓与内容仓压根没有读这份文件的测试。
         唯一报出来的是控制仓的跨仓对账，而它**只报迁移那一半**，对三份手抄件一个字不说。
         已修（api e9a40ad / automation 6f97602 / content 11b07ac）：整份忠实拷贝 + 迁移进属主仓，
         四份逐字一致（124 条）。**顺带更正上面记的一句**：`table-ownership.json` 现在已**不是**纯 additive 漂移——
         这次同时带了一条既有条目（`facebook_operation_policy`）的 basis 措辞更新，
         「共有条目零内容差异」那条实测结论已过期。
       - **比发作本身更要紧的结构事实**：`aidcp-api` 与 `aidcp-content` 的 `package.json` 里
         **声明了 `boundaries:refresh` / `boundaries:census`，但它们依赖的整个 `test/acceptance/helpers/` 目录
         在这两个仓里不存在**，一跑就是 `ERR_MODULE_NOT_FOUND`。也就是说：本条正文说的「只有跑刷新才会炸」，
         在三个派生仓里**只有 automation 那份是真的**，另外两个仓连这条退路都没有——
         那两个仓的手抄件漂移是**纯静默**的。⇒ 0.7c 拆成两半做时，这一半（把 helpers 补进去、或把这两条
         跑不起来的脚本从 package.json 删掉、不要留一条假装存在的检查）应当排在前面：它比同步机制便宜得多。 -->
  <!-- 优先级判断请按「静默 vs 响亮」读（本条正文上方那四次发作已按此分类）：静默那种才是真危险。 -->

- [x] 0.8 落实 A1：模型出口进 `aidcp-transport`。核对准入判据实跑一遍
  （`test/acceptance/module-boundary.test.ts` 的真正则，别凭记忆用「四条硬禁」），
  再按 kernel → transport → 三个业务仓的顺序快进 pin。
  <!-- 2026-07-29 完成：`src/llm/qwen.ts` + `src/llm/providers.ts` 进 aidcp-transport（08c4e81）。
       pin 按序快进：kernel 21cc10a → transport 21cc10a → 三个业务仓 21cc10a/08c4e81，
       每一步 `npm install --userconfig /dev/null` + typecheck + 全量测试。
       六仓全绿：cloud 全量 / api 470 / automation 1888 / content 436 / kernel 57 / transport 36。 -->
  <!-- 0.4 的裁决实质成立且已实跑核过：qwen.ts 548 行、SQL/池/存储引用零命中、import 只指 kernel。
       但 0.4 记的理由有一条是错的，见 0.8a。落点闭包见 0.8b/0.8c。 -->
- [x] 0.8a **更正 0.4 的密钥口径**：0.4 写的「密钥各自从 env 读」与生产事实不符——真实做法是
  **库内优先、env 回退**（`server.ts:2295-2297` / `:2337-2341` 走 `credentialStore.getSecretForRuntime`），
  content 手写 main 已改成经属主侧窄读口取（`aidcp-content/src/server.ts:421-428`）。
  **按字面实施会让后台「厂商密钥」页对 automation 进程彻底失效且无任何信号。**
  照 content 的做法接窄读口，**MUST NOT 复刻四层回落逻辑**（复刻正是两侧悄悄不一致的来源）。
  <!-- aidcp-automation c365b1a（A-1）：automation 侧也接上了同一条窄读口，两侧同形。
       四层回落一行都没复刻——角色 → 厂商/模型/温度/思考全查本地镜像，保守默认取 kernel 那个常量。
       变异实测：把保守默认改成本仓自写的字面量，当场红。
       **另一半同样重要、且容易只做一半**：读失败与「库里没配」分开记（前者说明属主侧那条 route
       不可达、本次走的是 env 回退）。变异：吞成 null → 那条用例当场红。 -->
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
- [x] 0.8g **活缺口已修（2026-07-31）：两条 route 补上了，且两处 catch 不再吞。**
  <!-- aidcp-api 3a75b0e / aidcp-cloud 072409f / aidcp-content 7284e05。
       **三处一起改才算修完**，只补 route 会留下同一个洞的下一次：
       ① api 手写 main 现在**无条件**注册 `role-model-selection/fetch` + `provider-secret/get-for-runtime`。
          代价是本 main 首次要建那四张属主表的 store（三张模型配置 + 凭据）——它们**不为本进程自己用**，
          纯粹是为了把答案算好送给 content。四层回落照单体逐字搬（送快照、不送表）。
          **未传 mirrorVersionBumper**：本进程只读这三张表；哪天面板配置写口搬进来 MUST 补上，
          否则跨进程失效通道会静默断掉（已写在代码注释里）。
       ② content 手写 main 的三处裸 catch 收进**唯一一个**包装：分开数「命中 / 读失败」，
          每次失败一行 warn，启动期再来一行自证（与上面两份模型镜像那行同形）。
          **读失败仍不拒绝启动**——属主域抖一下就停掉整个内容进程是过度反应；但绝不许静默。
       ③ `billing-price-refresh.ts`（cloud 属主源、派生进 content）里那个 `.catch(() => null)` 同样处置，
          logger 走注入、缺省 console。
       测试三条 + 两条：api 侧「往返 / 漏注册时传输层如实抛 / 组装根那两行必须还在」；
       cloud 侧「抛了必须每次都报」+ **反向那条「真没配必须安静」**——没有后者，前者什么都钉不住。
       变异实测：把那个 catch 改回吞 null，红的恰好是「读失败必须被报出来」那条，反向那条仍绿。
       cloud 4046 / api 499 / content 441，全 0 fail；acceptance 180/180；六仓零漂移。 -->
- [ ] 0.8g0 **原文（已处置，保留供追溯）：三进程形态下厂商密钥读必然失败，且失败被吞成「本来就没配」。**
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
- [x] 0.8i **automation 第一次真需要 `aidcp-transport` 依赖**：它今天没 pin
  （对账工具明确打「未 pin aidcp-transport（用得上它的仓才需要）」），因为它自己是 `src/transport/` 属主、
  一直用本地副本。而 `src/llm/*` **不是** automation 属主，只能走包。接线时要新增这条 pin。
  <!-- aidcp-automation c365b1a（A-1）。pin = transport master 头 40df6de；对账已从「未 pin」
       变成「pin 对齐」——**这条 pin 从此进棘轮**，以后 transport 一动它就要跟。
       **没有只加 pin**：只加 pin = 装了个本进程没有去处的东西，正好犯批 A 刚立的那条判据。
       同批做了消费者（见 0.8j）。
       **这道闸从今天起不再是前瞻的**（task 2.8 的 `transport-single-copy`）：当场验了一次
       「反正已经 pin 了，顺手从包里取个 HTTP 客户端」，闸当场红并点名说明符。
       ⚠️ **一条别记反的偶然**：那次 typecheck 也红了，但只因为 `InternalHttpClient` 恰好有 private
       字段（两份名义不兼容）。**换成没有 private 成员的类、或函数 / 错误类，typecheck 就是绿的**，
       只有那道闸会说话——闸的 docblock 说的仍然成立，别据此以为编译器能接住这类事。 -->
- [x] 0.8j **`qwen.ts` 有一个静默兜底，automation 的 main MUST 显式传 key 绕开它**：
  `this.apiKey = options.apiKey ?? process.env.DASHSCOPE_API_KEY ?? ''`——不传 key 时既不报错也不抛，
  直接落成空串；**更坏的是构造非 dashscope 厂商的出口时也会去读 `DASHSCOPE_API_KEY`**。
  content 的 main 是显式传的，automation 照抄。
  <!-- aidcp-automation c365b1a（A-1）。落在 `src/automation-model-exit.ts`：
       **不是写在 main() 里，而是抽成可单测的工厂**——写在 main() 里就只能等 task 3.1，
       而这几条纪律本身与 main() 无关。批 E 只剩「调它 + 把 client 注入角色调度器」。
       传的是**显式空串而不是省略**：空串不是 nullish ⇒ 那条 `??` 短路 ⇒ env 读根本不发生。
       变异实测：删掉那一行 → 2 条用例红。 -->
- [ ] 0.8j-剩余 **A-2 的另一半仍被 task 3.1 挡着**：批 E 的 `main()` 里
  `await createAutomationModelExit({ apiHttp })` 并把 `client` 注入角色调度器，关停路径调 `stop()`。
  <!-- 工厂已经把「怎么构造」全部封住了，剩下的纯粹是接线。两处别漏：
       ① `apiHttp` 传组装根**已有的那个**（再 new 一个不报错，只是多一份会漂的基址）；
       ② 用量记账挂 `onCall`（合并缓冲的家是 automation 自己的 main，见 2.4d-用量）——
          工厂只留了缝，没实现缓冲。 -->
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
- [x] 1.3 `aidcp-cloud`（事实源）：按 4a paired command 形态实现 route + receiver + api 侧 client；
  自由文本委托的**意图解析留在 automation**，api 侧 MUST NOT 自己拼 intent 调结构化入口。
  <!-- aidcp-cloud 319b0af / api 8e3d083 / automation 3de5121。**接线已落，且行为逐位不变**
       （全量 4022 pass / 0 fail，与接线前逐条相同）。意图解析一行都没搬——api 侧仍只把原文整体转发。
       ① segA 建台账 + 接收方。**台账单独一个 try**：它失败 MUST NOT 把整个委托控制面拖下水
          （既有 7 方法压根不用台账，各自有版本号乐观锁）。失败时换具名 fail-closed 台账：
          自由文本带原因拒收、7 方法照常。判据是不对称的——收下不判重意味着**一次重投就真发第二次**。
       ② automation 内部 API 挂：委托 7 条 + 自由文本 1 条 + 调度启停 2 条，逐组独立 + 具名 warn。
          **手动发帖 / 评论两组刻意不挂**（1.7b），理由写在注册处。
       ③ 取数聚合口的委托面放宽到 kernel 的 7+1。**这一步让编译器把此前只是「声称」的事钉死了**：
          本地服务不满足 7+1（`createFromText(text, opts)` vs `createFromText(input)`），
          所以本地分支只能喂接收方，忘不了。
       ④ remote 另起一条自己的条件 + **指向 automation 的客户端与令牌**。绝不搭既有那条 remote：
          它是按 content 的 base URL 走的，委托流量投过去会打到只服务 curated 路由的监听上、直接 404。
          两个客户端**逐方法显式转调**合成一个 7+1 对象，**不用对象展开**——展开拿不到类原型上的方法，
          那种错要真跑起来才现形。
       ⑤ 四个接线点全改指聚合口。最要紧的是发布队列视图：它此前握着本地实例 + `if (!x) return null`，
          拆完之后那个 null 会被渲染成「这个账号没有发布队列」，而真相是「问不到」。
       ⑥ 飞书自由文本闭包改说回执形态：`not_delivered` 明说这台机器没有处理器且**没有执行**；
          `rejected` 还原成既有业务错误再抛（渲染逐位不变）；传输失败照旧抛（渲染成「结果未知」，上一批已做）。
          幂等键取飞书消息 id，**拿不到就拒发、不造键**。 -->
  <!-- **两处顺带的结构改动，都是被逼出来的、不是顺手**：
       ① 网关块**上提到飞书入站之前**——入站 deps 需要那个端口，而网关原来声明在它之后，直接引用撞 TDZ。
          上提前核过：本块捕获的四个值在原位置与新位置之间**一次都没被重新赋值**。
          不上提只剩「让飞书继续握本地实例」这条退路，那正是本轮要消掉的两处绕过之一。
       ② `delegatedTaskService` **已从 segD 的解构里删掉**——它无人使用了。删掉它就是
          「四个接线点一个不留」的**机械证明**：segD 里再也拿不到那个本地实例。 -->
- [x] 1.3a **已接线（用户 2026-07-31 拍板取「显示未知 / 按钮仍可点 / 点了失败给明确提示」这一版）。**
  <!-- aidcp-cloud bc520ac / api 4dcb4b3 / console ad5006e。
       **卡点确实是签名**：面板那份读是同步布尔，表达不了「问不到」。已改成**异步三态**
       （复用 kernel 既有的 `AutomationDispatchActivity`，不另造第二个类型），
       三条路径一律落 `null` + 具名原因、**绝不落 false**：端口没注入 / 远端答 unavailable / 远端读抛错。
       面板上 false 的含义是「引擎正常停着」，运营看到它什么都不做——把这三种压成 false
       等于告诉运营一切正常，而真相是这条链根本不通。
       **api 模式读写两条一起接**：只接读会变成「灯亮着、按钮按下去没人接」，比两个都不接更糟。
       非成功回执各自带一句人话（`not_delivered` / `collision` 分开说），云端把人话放 `error`、
       机器码放 `reason`——console 的 api 客户端本来就按这个约定解析，前端直接上屏，
       不再是那句固定的「调度下发控制失败」。
       console 侧：徽标 `未知` 挂原因 tooltip（没接通道 / 对面没起来 / 令牌不对，三者处置不同），
       状态由 default 改 warning（default 读起来像「安静地停着」），按钮保持可点。
       变异实测：三条「读不到」任一压成 false → **typecheck 全绿**，只有新用例红。 -->
  <!-- 📌 **连带把 §4.1 点名的那处不诚实逼了出来**：类型一改，派生 api 仓手写入口里那句
       `dispatchActive: () => false` **当场编译不过**。按 §4.1 的建议改成**不传**——
       字段本来就是可选的（1.4a 改可选正是为了让「诚实地缺席」在类型层表达得出来），
       省略即回 null + 具名 `not_wired`，而不是自信地答一句「停着」。
       这也是本轮唯一一次**类型系统主动抓住一处已写下的不诚实**，值得记：
       把「不知道」建模成一个真实取值，比写多少注释都管用。 -->
- [ ] 1.3a0 **原文（前提已处置，保留供追溯）**：调度启停只接了服务端，api 侧客户端没接。
  已接：automation 内部 API 挂上了 `setDispatch` / `readDispatchActivity` 两条路由 + 接收方（进程内回执、无持久台账）。
  没接：api 侧仍走 `ctx.automationDispatchCommands` 那个**进程内闭包**（segC 设，api 模式下 segC 不跑 ⇒ 面板回 503）。
  **卡点是签名，不是接线**：面板那份 `dispatchActive()` 是**同步返回布尔**，而远端读是**异步且三态**
  （`unavailable` ≠ `active:false`）。要正确接线必须把面板那个签名改成异步 + 三态。
  **这正是派生 api 仓里 `dispatchActive: () => false` 那处不诚实的由来**——图省事就会再写一遍，
  把「读不到调度引擎」画成「调度引擎正常停着」。故本轮停手不硬接。
- [ ] 1.3b **三条运营指令台账条目为什么没跟着清零**（如实记，免得下一手以为漏了）。
  它们的证据是**文案探针**，钉在 `automation_operator_command_unavailable:*` 这类守卫串上，
  而那些串**仍然合法存在**——接线之后它们的含义变了（从「压根没有这条通道」变成
  「这个进程没配置这条通道」），但探针分不出这两者。
  ⇒ 清零属**第 4 段**的判断（要不要认为这些串不再构成证据），需要与那一段的自熄断言一起做，
  **不在本轮偷偷带过**。
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
  <!-- 📌 **2026-07-31 第二次坐实（本条下面那两个注释块已部分过期，先读这一段）。**

       **B 半已全部了结**：2.4b 已落地，`content-role-factories` 已于 2026-07-31 撤条，
       同批还撤了 `content-textcard-transcription-authority`（2.4e）与 `content-reply-generation-authority`（2.6）。
       下面那句「B 半剩下的是一个新问题」**已过期**，别照它开工。

       **A 半：物理搬迁 0.8 已完整做完（qwen.ts + providers.ts 已在包里、pin 已抬），还剩 4 件：**
       - **A-1 ✅ 已做完（2026-08-01，automation `c365b1a`）**：pin 已加且对账已从「未 pin」变成
         「pin 对齐」。**没有只加 pin**——只加 pin 等于装了个本进程没有去处的东西，
         同批把 A-2 里不被 3.1 挡的那一半（构造）一起做了，见下。
         **实际不需要重抬 pin 链**：transport 本身没改，pin 直接等于它 master 头即可。
       - **A-2 一半已做完，另一半仍被 task 3.1 挡着**（0.8j）。
         三条硬约束**已全部落在 `automation-model-exit.ts` 这个可单测工厂里**、各有变异验过的用例：
         `import` 走 `aidcp-transport/llm/qwen.js`（不是桶文件）；`apiKey` 显式传（**空串而非省略**，
         空串让客户端那条 `??` 短路、env 读根本不发生）；密钥经属主侧窄读口取、四层回落一行没复刻。
         **剩下的纯接线**：批 E 的 `main()` 里调工厂、把 `client` 注入角色调度器、关停调 `stop()`，
         并把用量记账挂在 `onCall` 上（工厂只留了缝、没实现缓冲）。见 0.8j-剩余。
       - **A-3 ✅ 已做完（2026-07-31，见 0.8g 的 <!-- --> 记录）**：api 两条 route 已无条件注册，
         content 与 billing 两处裸 catch 已改成能区分「读失败」与「库内没配」。
         **一条比预期多出来的代价记在这里**：api 手写 main 为此首次构造了四张属主表的 store，
         而它们**在本进程里没有任何消费者**——纯粹是为了给 content 算答案。
         这正是 task 3.5 要在 automation 侧问的那个问题（「本进程里有没有去处」），
         在 api 侧的答案是「有去处，但去处在别的进程」。3.5 判据要能容下这一类，别一刀切成「没消费者就不该 new」。
       - **A-4 ✅ 已裁定（用户 2026-08-01）：走 ③ 的变体 —— 自动化侧随第 4 段正常撤，单体侧那条 binding 重述主张；
         ① 与 ② 明确不做。** 三条依据都是当场实测的，不是论证：
         **① 明确不做**：它要让单体去 pin 一个**从单体自己派生出来的包**。实测 `aidcp-cloud/package.json`
            今天既不 pin kernel 也不 pin transport —— 它是事实源，不依赖任何由自己派生的东西。
            走 ① 等于让事实源运行自己代码的一个陈旧快照（改了 qwen.ts 不抬 pin 就跑旧的），
            且同一进程里出现两份同名类 —— **正是自动化仓那道传输单份闸禁止的形态**。
         **② 明确不做（但它指出的缺口另案值得做）**：单体今天没有传输包名册的任何镜像，名册只活在
            控制仓脚本的 `TRANSPORT_MEMBERS` 里。在单体再抄一份就是**又一个手抄件**（本 change 已被
            手抄件咬过四次，见 §4.4）。真要补，正解是把名册挪进单体 `boundaries/` 并让控制仓脚本
            反过来读它 —— 那是个独立改造，不该被这一条绑架。
         **③ 的口径更正是有实测支撑的**：4.2 那句「三份 MUST 同批一致」**现实已经反驳过一次** ——
            2026-07-31 那批里单体侧 AST 台账 54 → 53、自动化侧刻意不动，两把尺**合法分叉**。
            真正成立的规则是：**自动化那两份（常量 + JSON 投影）必须一致**（已有 deepEqual 断言看着）；
            **单体那份问的是另一个问题，按自己的节奏自熄**。见 4.2 的更正。
         **而且自动化侧那条根本不需要特殊锚点**：它与其余内容条目同一条规则 —— 启动流程把模型出口
            喂进去之前它仍在阻止交付，喂进去之后（批 E，见 0.8j-剩余）随第 4 段一起撤。
         **单体侧那条要改的是主张、不是锚点**：探针永远命中是**正确的单体行为**（基础段本来就该构造它，
            实测单体里 14 个 content 属主文件 + 组装根都直接 import 模型出口）。
            该 binding 测的是「基础段有没有 new 一个内容属主类」，而它的主张是「自动化包拿不到模型出口」——
            后者已不成立（包里有），前者永远成立。**⇒ 重述这条 binding 的主张（或按 2.9 的先例判为
            属主/证据错配并撤条），MUST NOT 发明一个假锚点让它看起来自熄。**
       - **A-4 原文（保留供追溯）：⚠️ 这一条有一个真未决点，别当例行公事。**
         两个已有撤条判例都锚在「cloud 的自动化段不再点名任何 content 属主符号」这个可跑问题上，
         **这两种手法在这一条上都用不了**：三条探针**永远命中**（segA 恒跑必须 new、单体下 segC/segD 就是用它），
         而「qwen.ts 是 transport 成员」这个真正的理由**在 cloud 仓里没有任何可运行的锚**——
         kernel 有名册镜像 + 门禁（`kernel-non-members.json` + `AC-BOUND-03`），**transport 没有对等物**，
         名册只活在控制仓脚本里。三选一，需拍板：
         ① cloud 的 import 改指包（「segA 不再 new 一个 content 属主类」就成了可跑事实，与判例同形；
            代价是 cloud 要 pin transport，且那是最热的组装根）；
         ② 在 cloud 补一份 transport 名册镜像 + 门禁，撤条锚在它上面；
         ③ 只撤 automation 那份（它的判据是自己 docblock 写的「阻止本包交付完整生产进程」，
            A-1/A-2 做完即不再 prevent）——**但 4.2 明写三份 MUST 同批一致，走这条要先改 4.2 的口径**。

       **另一处已漂的记载**：design §5.5.8 引的行号（cloud `server.ts:2295-2297`/`:2337-2341`、
       content `server.ts:421-428`）**全部失效**，按符号名定位。§5.5.8 的结论本身仍成立。 -->

  <!-- 📌 **2026-07-31 坐实现状，下一手别再按交接文档那句「裁决早拍过了，是落地不是决策」通读本条**——
       那句话对 A 半成立，对 B 半**已经过期**。
       **B 半（四个角色工厂）：归属改判早已由 task 0.7 全部落地。** 实测：
       `concept-extractor-role` / `valuable-comment-archivist` / `curated-comment-evaluator` /
       `curated-note-evaluator` / `content-role`（基类）/ `curated-gate` 六个文件在
       `module-ownership.json` 里**已经是 automation**，且都已在 `aidcp-automation/src/` 里。
       design §2 里点名要一并修的「假消边残留」也已消：`curated-note-evaluator.ts` 不再从
       `cache/curated-content-store.js` 那个再导出壳取类型。
       ⇒ **B 半剩下的不是「落地既有裁决」，是一个新问题**：`CONTENT_ROLE_FACTORIES`
       （cloud `server.ts` 的模块级常量，也就是该台账条目的证据符号）今天**只剩一个 content 符号**——
       `curatedStore as CuratedContentStore` 那一步窄化里的 `CuratedContentStore` 类型。
       其余全部已归位：四个角色类与两个 Sink 类型属 automation，`TextCardTranscriber` 已取自 kernel。
       **而那一步窄化的目标类型，正是 2.4b 要造的精选写口。**
       ⇒ **`content-role-factories` 的前置是 2.4b，不是本条**；2.4b 落地后它才谈得上清。
       （形态与 task 2.9 那条**像但不同**：2.9 是属主记错了、纯撤条；这条是真依赖，只是缩到了一个类型上。）
       **A 半（模型调用出口进 transport）与 B 半互不依赖**，可单独开工；注意 §5.5.8 记着
       「裁决成立、但 0.4 记的理由有一条是错的」，动手前先读那一段。 -->
  <!-- ⚠️ **还有一层今天没人写下来的**：这套「opaque 句柄 + 注入工厂表」的存在理由是
       **当时四个角色属 content、automation 不能静态 import 它们**。0.7 改判之后那个前提没有了——
       角色调度器（automation）现在**可以**直接 import 这四个类。
       所以将来可能不是「把工厂表搬进 automation 组装根」，而是**整层拆掉**。
       但那会动掉 `RoleFactoryRegistry` 现在扛着的一道类型检查（工厂体 `new X(o)` 强制
       「构造契约 → 角色真实构造签名」可赋值，2026-07-23 审计坐实过一次回归）。
       **拆之前必须先想清楚那道检查搬去哪**，别顺手删。 -->
  <!-- 📌 **本条今天不做的理由（明写，不是遗漏）**：B 半的前置是 2.4b（一个还没造的写口），
       A 半是把模型出口整体搬进 `aidcp-transport` ——那是本仓最热的一条路径，
       且要动 transport 名册 + 三仓 pin。两半都不适合塞在本轮尾巴上做。 -->

  <!-- 以下两条为本轮实际落地的、2.5 之外的相邻工作，编号靠近以便追溯 -->

- [x] 2.4a **落地位置已坐实（2026-07-30，接线批次之后顺带勘的；下一手照此开工，不必重查）。**
  <!-- aidcp-cloud 3fe4b94。segC 新增 `contentReadAuthority`：仅 `seamMode === 'automation'` 建
       `ConceptPoolAuthorityHttpClient` / `CuratedSelectionAuthorityHttpClient`（共用一个 InternalHttpClient
       + `AIDCP_CONTENT_INTERNAL_TOKEN` + deploymentTarget），缺 URL 或缺 target **点名抛**
       `content_read_authority_unavailable:<缺的那项>`；其余四模式**一个客户端都不建**、逐位保持既有行为。
       选择写成三元不是 `??`：`??` 会在客户端字段意外 undefined 时静默取到本地属主实例，
       那正是本块要消灭的形态。
       改指端口的消费点共五处：dispatcher 的 `conceptStore`、scheduler 的 `conceptStore`、
       scheduler 的 `curatedStore`、发帖调度器的在场判定 `if (conceptPoolPort && likedNoteStore)`、
       评论搜索词那层薄适配（其具名 `not_configured` 原样保留，0.6f 的吞点①没退回去）。
       全量：typecheck 零错；acceptance 177/177；`npm test` 4023 pass / 0 fail（基线 4022，+1 为新用例）；
       `boundaries:refresh` 零漂移，crossBoundaryEdges / exemptionEntries 仍是 0。 -->
  <!-- ⚠️ **精选那条只做了一半，且是有意的**：`CuratedSelectionPort` 只有两条**读**方法
       （`selectForCreation` / `selectSamplesForSearchTerms`），覆盖不了 segC 里另外三处属主实例用法——
       ① dispatcher 的 `curatedStore`（opaque Sink 句柄，透传给 content 角色工厂、**含写**）；
       ② `markBotAction`（自有点赞/收藏并入精选语料，是一次真写）；
       ③ `curatedContentCapability` 的在场判定。
       ①归 **task 2.5**（角色工厂那个岔口）；②③今天**没有端口面可接**，要接得先补写口契约。
       所以 `content-curated-write-authority` 这条台账**不该只凭本条就撤**——它的名字里的 write 是真的。 -->
  <!-- 📌 **关于「门 12 → 10」这个预期，实读后的更正（2026-07-30）**：本条**没有**减门，且不该减。
       两把尺的关系比交接文档写的更细一层：
       ① automation 台账那条的撤条判据是它自己的 docblock 写死的——
          「only dependencies that prevent this package from supplying the complete production process」；
       ② 而 **task 3.1 写 `main()` 在 task 4.1 清台账之前**（§3 与 §4 的顺序，不是我的解读）。
          在 `main()` 真把 `contentClients.conceptPool` 喂进 RoleDispatcher / PublishScheduler 之前，
          这条依赖**仍然**在阻止本包交付完整进程。
       ⇒ 台账清零属**第 4 段**，第 2 段的交付物是「让每条依赖变得可满足」，不是「减门」。
       本条把概念池那条做到了「只差 main() 注入」：kernel 端口 ✓ / 传输三件套 ✓ / content 侧路由注册 ✓ /
       automation 根已建客户端 ✓（2.4）/ 消费面已是端口类型 ✓（0.6b、0.6g）/ **生产消费者已存在** ✓（本条）。
       **别据此改交接文档里那句「起手就能做的两条能减门」而不改理由**——减门的时机变了，工作量没变。 -->
  <!-- **变异实测（§6.5：要问哪条用例抓住的）**：六个变异，**typecheck 对每一个都是绿的**——
       属主实例结构上就满足那两个窄端口，编译器分不出「本地实例」与「HTTP 客户端」。
       六个全部只由新加的那一条 acceptance 用例抓住（`composition-root-4a-mode-wiring.test.ts`）。
       **其中一个变异逃过了这条用例的第一版**：在 `throw` 前面插一句 `return undefined;`，
       整条 fail-closed 就退化成静默回落本地实例，而「那句 throw 在文本里」的断言照样绿。
       用例已改断结构（本 IIFE 只许有一处提前返回，且就是模式守卫那处）。
       用例注释里写明了「别当冗余删掉」。 -->
  <!-- ⚠️ **踩到一次、记下来省别人一次**：跑变异用 `git checkout <file>` 还原会**从索引区**还原，
       未 staged 的本次改动当场没了；后续两个变异因此测的是「标记找不到」而不是变异本身、
       看着也是红的、**结论完全是假的**。变异还原一律用文件级备份（`cp` 出去再 `cp` 回来）。 -->
  <!-- **另一条实测**：`aidcp-automation` 里同名的 `composition-root-4a-mode-wiring.test.ts`
       是一份 `// aidcp:test-owner=derived` 的**派生私有文件**（7 条用例、断的是 automation 根），
       与 cloud 这份同名不同物、互不同步，本次改动对它零影响。 -->
  <!-- 2026-07-30 23:05 已部署第九批（aidcp-cloud@3fe4b94，**仍是单体形态**）。
       快照来源：从 master 目标提交 `git archive` 出的干净快照，不从任何 worktree 部署。
       备份 /opt/aidcp/cloud.bak.20260730-230507.tar.gz + .env.bak.20260730；package.json 零变更故未动 node_modules。
       **迁移：三属主逐一 `migrate status` 全部「待应用 0」**（content 0069 / automation 0102 / api 0100），
       本批零新增迁移，故未跑 `migrate up`（§4.6 那一步照查了，不是省了）。
       healthcheck 全过：active running、NRestarts=0；8787 + 面板 8090 + 客户鉴权 8091 全在监听；
       **三属主库各自 `select 1` 均回 1**；飞书长连接已建立（WSClient onReady）；
       ConceptStore / CuratedContentStore / PublishScheduler / CommentScheduler 均打「已就绪」；
       重启后错误行数 0，2 分钟 soak 后仍为 0。isales 四服务全程 active、未触碰。
       **启动日志确认跑的是 `monolith`**（「拆段传输已接线（monolith）」）⇒ 本批新代码在 dev 上走的是
       `contentReadAuthority === undefined` 的那一支，即**本地属主实例、逐位等价**。
       ⇒ 按 5.3 的口径：**这只证明单体现网零回归**，automation 分支在 dev 上一次都没被执行过，不声称。
       ol 未部署、用户未提。 -->
- [x] 2.4b **精选写口**：新建 kernel 端口 + 传输三件套 + content 侧注册 + 组装根按模式注入。
  <!-- aidcp-cloud 52272f4（写口）+ b7f24a0（撤条）；kernel dbd2cbd / transport 5e7c394 /
       api 5ee761e / automation 2fbb9eb / content ae7be94。
       **五个方法就是全部跨属主写面**，逐条对得上真实调用点：观测落库、图集刷新、
       转写读穿缓存（写侧唯一的读）、优质评论归档、自有点赞收藏并入语料。
       **与召回端口刻意分文件**：消费方不同（那边是发帖 / 评论调度器，这边是两个精选准入评估角色
       + 组装根），失败后果也不同（召回失败＝这一轮没素材，写失败＝这一条观测永久丢了）；
       合成一个端口会让只需要读的调用方结构上也拿到写能力。
       五个类型全部已在 kernel（`curated-content-types.ts`），端口零新类型。 -->
  <!-- **三条只对写侧成立的约束，每条都有用例钉着**：
       ① 返回 void 的三个方法跨线 MUST 回显式回执——`undefined` 编码后是空响应体，与「路由压根没跑」
          逐字节一样，写没做成会读起来像做成了。**变异实测：把回执去掉 → typecheck 全绿、
          三条传输用例红。**
       ② 属主失败 MUST NOT 被译成领域答案。0 行受影响＝库里没有这条源帖（调用方据此分支），
          坏回执兜底成 0 会让后续转写往一条不存在的行上写。
       ③ 两块增强负载（参照图集 / 文字卡转写）**属主是唯一规范化处**，这一层不写第二份校验——
          两份在写下来那天一致，此后任何单边调整都不报错，只会让某些今天写得进去的观测明天起被
          默默拒掉，**而丢一条观测没有任何人会发现**（语料只会少不会多）。 -->
  <!-- **组装根四处改指写口**：角色调度器那个 opaque 句柄、`markBotAction`、能力在场判定、
       以及角色工厂表两跳窄化的锚点。
       能力在场判定那处值得单记：原先判的是**本地属主实例在不在**，两者在单体里等价、
       在 automation 进程里不等价——那里本地实例必然缺席，判本地实例会把一条接得好好的
       跨进程写口读成「精选库没接上」，然后关掉自有收藏并入语料、并对客户端收回自动首作链的承诺。
       **变异实测：这四处任一改回属主实例 → typecheck 全绿**（属主实例结构上满足所有这些端口，
       编译器分不出本地实例与 HTTP 客户端），只有组装守卫那条用例红。 -->
  <!-- 全量：cloud 4029 pass / 0 fail（基线 4024，+5 新用例）；api 494 / content 439 /
       automation 1964 / kernel 59 / transport 36，全 0 fail；typecheck 六仓全绿；
       `boundaries:refresh` 只多一条新 kernel 文件的归属，跨域边与豁免仍是 0。 -->
- [x] 2.4b-1 **`content-role-factories` 已撤条——本 change 第一条真靠接线消掉的台账项。门 12 → 11。**
  <!-- aidcp-cloud b7f24a0 / automation 2fbb9eb。cloud 台账 55 → 54，automation 台账 12 → 11。
       **与前两条撤条不是同一种**（一条记错属主、一条重复计数），所以三处注释都先写明这一点。
       那条当初是准的：四个角色类属 content、本包 import 不到，只能由组装根递一张工厂函数表进来。
       两步把 content 那一面消掉了——**task 0.7** 把四个角色类 + 基类 + 精选闸改判 automation
       （六个文件今天就在 automation 仓 src/ 里）；**task 2.4b** 把两跳窄化的锚点从 content 属主的
       存储类换成 kernel 写口，那是那张表上**最后一个** content 符号。
       剩下的是组装根的活，而每个仓的组装根本来就各写各的。 -->
  <!-- ⚠️ **撤条不挂在探针上，挂在一条可跑的判据上**——因为那条探针**看不出这件事**：
       它只问「segC 里有没有提到那张表」，而一个要派角色的组装根必然有这张表，答案恒为真。
       新加的判据是 `contentOwnedSymbolsInRoleFactoryTable()`：把表里每个标识符解析到 import 来源、
       查归属表，**一个 content 都不许有**；返回具体符号名而非布尔，好让复活的人知道从哪查起。
       由 `composition-root-4a-inventory.test.ts` 的专门一条用例钉着。**它红 = 撤条失效 = 条目 MUST 复活。**
       表整个不见时那个函数**抛**而不是回空数组——否则撤条前提会凭空成立。 -->
  <!-- **没跟着撤的（有意）**：那些角色仍然写 content 属主的精选库
       （`content-curated-write-authority`），正文评估角色仍接一个 content 属主的转写器句柄
       （`content-textcard-transcription-authority`）。两条都还在。
       这条撤的是**第三次数**同样那两个依赖，且是按一个已经不成立的代码归属去数的。 -->
  <!-- 📌 **三份台账都要动，第三份没有任何机械信号**：cloud 那份是 AST 派生的（跑
       `composition-root:refresh-ledger` 重生成）；automation 那份是**手写常量 + 它自己的 JSON 投影**；
       automation 仓另有一条**写死 12** 的派生私有用例（`composition-root-4a-mode-wiring.test.ts`，
       带 `aidcp:test-owner=derived`）——它是这次唯一当场红的那个，**而它红是好事**：
       §4.7 说的「自动化那份拿不到中控侧任何机械信号」在这里第一次被具体验证到，
       只有这条写死的数字会拦住你。撤条理由已在三处各自完整重述，不靠互相引用。 -->
  <!-- 2026-07-31 16:41 已部署第十一批（aidcp-cloud@b7f24a0，仍是单体形态）。
       备份 /opt/aidcp/cloud.bak.20260731-b7f24a0.tar.gz；三属主 migrate status 均「待应用 0」，本批零迁移。
       上机器逐条确认新代码到了（kernel 写口文件在、注册函数 2 处、组装根端口 5 处）。
       healthcheck 全过：active running、NRestarts=0、三个监听全在、三属主库各回 1、飞书长连接已建、
       重启后错误 0、2 分钟 soak 仍 0；isales 四服务未触碰。
       **「精选灵感库能力不可用」一条没响，这是对的**——能力现在由写口派生，单体下写口就是本地实例、本来就该 wired。
       按 5.3 口径：只证明单体现网零回归，automation 分支在 dev 上仍一次没被执行过。ol 未部署。 -->
- [ ] 2.4b-2 **`markBotAction` 的失败仍是 best-effort + 具名 warn（既有行为，未改）**：
  跨进程后失败率会高得多，而这是一条真写、丢了就是这条自有动作永久没进语料。
  要么补可计数信号，要么明写接受丢失。**绝不能改成静默吞掉**（现在不是）。
  <!-- 📌 **2026-07-31 坐实：这一条同时是 `content-role-factories` 的前置**（见 2.5 的注释）。
       所需的写面已逐条数清（四个方法 + 一个在场判定）：
       `CuratedNoteSink` 的 `upsertObservation` / `refreshReferenceImages` / `getTextCardContext`
       （定义在 `src/agents/curated-note-evaluator.ts`，随 0.7 已归 automation）、
       `CuratedCommentSink` 的 `archiveComment`（`src/agents/curated-comment-evaluator.ts`，同上）、
       segC 的 `markBotAction`，外加 `curatedContentCapability` 那个在场判定。 -->
- [x] 2.4c **结清 `CONTENT_MEDIA_USAGE_WIRING_DEBT` 里三条已可结清的**（接线的前置卫生）。
  <!-- aidcp-cloud e9925f7 / transport 39b3c2c / automation 6da0e74 / api 9920ecd / content eb56863。
       **债①（真做的）**：`content-authority-http.ts` 里那份与 `content-authority-wire.ts` 逐字相同的
       私有译码副本已删、改指公共那一份，净减 141 行。
       **结清前逐条比过两份实现：语义一致、尚未漂移** ⇒ 这次是防患不是修 bug，
       而这恰恰说明为什么必须现在做——**行为测试永远发现不了它**（见下）。
       只活在被删那份里的几句解释已折进保留的那份，一句没丢（kernel 对未知 reason 的规定、
       在场探针为何只有属主侧有意义、`route_not_found` 为何是回落分支最现实的触发点、
       版本不符为何刻意不判成能力缺口）。
       **债⑧⑨（核对后发现早已做掉）**：两个 kernel 端口文件已在 `ownership-rules.json` 的
       fileOverrides 与 `kernel-non-members.json` 的 kernelRoster 里；两个传输文件已在控制仓
       `sync-split-repos` 的 TRANSPORT_MEMBERS 里。
       三条**移入新的 `CONTENT_MEDIA_USAGE_WIRING_DEBT_CLOSED` 而不是删掉**（形态照
       `operator-command-http.ts` 的同名清单）：删掉之后「做过了」与「从来没记过」长得一模一样，
       而这三条里有两条落在别的文件里，下一个人无从判断该不该再做一遍。 -->
  <!-- **变异实测，且这次的结论比用例本身更值得记**：在 `content-authority-http.ts` 里重新塞一份
       私有 `ownerHasMethod` 副本 → **typecheck 绿、同文件五条往返用例全绿**，只有新加的那条结构守卫红。
       ⇒ **复制出来的第二份在复制那一刻行为完全一致，行为测试原理上就看不见它**；
       它要等到某天有人只改了其中一份、且**恰好在失败真发生的那一刻**才现形，
       而失败路径正是最少被真跑到的那条。守卫按结构判（取用方 MUST import 公共模块 + MUST NOT
       自己定义同名函数），不按文本片段判——后者换个函数名就绕过去了。用例注释写了「别当冗余删掉」。 -->
  <!-- 六仓：cloud e9925f7 / kernel aa48c29（未动）/ transport 39b3c2c / api 9920ecd /
       automation 6da0e74 / content eb56863。同步顺序照 §6.2：先 src、再 tests、最后按
       kernel → transport → 业务仓抬 pin。测试：cloud 4024 / api 493 / automation 1961 /
       content 439 / kernel 59 / transport 36，全 0 fail；六仓对账零漂移。
       **content 仓这三个文件是零变更的**：它经 `aidcp-transport` **包**取注册函数，不自持副本；
       自动化仓才是自持的那个（§6.3 的设计）。所以 content 只需抬 pin。 -->
  <!-- 2026-07-31 15:28 已部署第十批（aidcp-cloud@e9925f7，仍是单体形态）。
       备份 /opt/aidcp/cloud.bak.20260731-0010.tar.gz；package.json 零变更故未动 node_modules；
       三属主 `migrate status` 均「待应用 0」，本批零新增迁移。
       上机器逐条确认新代码真的到了（`content-authority-wire.js` 的 import 在、私有 `ownerHasMethod` 已不在）。
       healthcheck 全过：active running、NRestarts=0；8787 / 8090 / 8091 三个监听全在；
       三属主库各自 `select 1` 均回 1；飞书长连接已建立；ConceptStore / CuratedContentStore /
       PublishScheduler / CommentScheduler / 面板 / 客户鉴权 全部打「已就绪」；
       重启后错误行数 0，2 分钟 soak 后仍为 0。isales 四服务全程 active、未触碰。
       **本批是纯结构收敛，现网行为逐位不变**（删的是一份与保留那份逐字相同的副本）。ol 未部署。 -->
- [x] 2.4d-媒体 **FB 发帖素材组已接线并结清债②③④**（`185cfb4` + `e703b66`）。
  <!-- cloud e703b66 / kernel ac98a30 / transport 259001b / api 8a67d1e / automation c2c6ff7 /
       content ad6eeed。content 监听独立注册那三条路由（起不来与精选库无关，各注册各的）；
       automation 侧客户端进 `contentAuthorityClients`、按模式取；**两个消费点都改指端口**。
       **第二个消费点是 kernel 端口注释点名「最容易漏」的那处**：审批驳回释放保留是组装根**直调**、
       不走下发器那个三方法窄口——只改窄口的话，被驳回的稿会永远攥着它那组素材。
       顺手删掉了下发器窄口与端口之间那层逐方法转发的箭头函数：两者**签名逐字相同**，
       那层没有任何窄化作用，只多一处会漂的地方（属主换实现时那三行要跟着改，漏改不报错）。 -->
  <!-- **债②（静默 return）**：`if (!reservation || !this.facebookPublishMedia) return;` 里挤着两件
       毫无关系的事——「这条稿本来就没有素材保留」（正常）与「本进程压根没配这条端口」（缺依赖，
       三个写全消失且一个字不留）。已拆两支：前者仍是正常返回，后者计入 `dropped` +
       具名 error，**且日志说的是后果**（这组素材会一直停在 reserved、无人回收），不是只报个事实。
       **债③（只有一句 warn、没人数）**：已补计数，**与 dropped 分开数**——一个要改配置、
       一个要查对面为什么写不进去，处置完全不同。
       ⚠️ **兜底回收扫描仍未做**：欠账原文是「补可计数信号 **or** 兜底回收扫描」，这里只取前一半。
       计数让「漏了多少」问得出来，但漏掉的那些素材今天仍然没有任何东西会把它们放回可用池。
       已在 `_CLOSED` 条目里明写这一点，别把它读成全做完了。 -->
  <!-- **变异实测五个，全部 typecheck 绿，且一一对应**（§6.5 要问「哪条用例抓住的」）：
       ① 两条件塞回同一个静默 return → 只红「缺端口那条」；
       ② 写失败那支去掉计数 → 只红「写失败那条」；
       ③ 把「没有素材保留」也弄响 → 只红「这一支不该响那条」；
       ④ 驳回直调改回属主实例 → 只红组装守卫；⑤ 下发器注入改回属主实例 → 只红组装守卫。
       **第三条用例最值得留意**：它钉的是「不该响的那次真的没响」。只断言「缺端口会响」的话，
       把所有分支一律弄响也算过——那不是修好，是制造噪声。 -->
  <!-- 全量：cloud 4037 pass / 0 fail；api 496 / content 439 / automation 1966 / kernel 59 /
       transport 36，全 0 fail；六仓对账零漂移；跨域边与豁免仍是 0。
       2026-07-31 18:03 已部署 dev 第十二批（e703b66，单体形态；上一批 878e985 是另一路 session 部的，
       e703b66 已确认包含它）。三属主 migrate status 均「待应用 0」；healthcheck 全过、
       2 分钟 soak 错误 0、三属主库各回 1、isales 未触碰。
       **`facebook_media_settle_dropped` 一条没出现，这是对的**——单体下端口恒在。 -->
- [x] 2.4d-用量 **属主那一半已做完（写口 + 路由）；调用方那一半改归第 3 段，理由在下。**
  <!-- aidcp-cloud 8848c56 / content 2d289d0 / automation 9ce3511（共享包未动 ⇒ 无 pin 变更）。

       **决定一（属主补方法 vs 交适配对象）：读完属主代码之后这根本不是二选一。**
       适配对象只有两条路，两条都违反端口写死的 MUST：复制一份 upsert SQL ⇒ 第二份落库实现
       （§8.4 点名那种「两侧各自编译通过、各自测试通过，只有真跑才发现对不上」）；
       或走 `add()`+`flush()` ⇒ `add` 用**自己的钟**重算桶起点、`flush` 回 `void`，
       前者违反「桶起点由调用方戳」、后者违反「回真落库行数」。**⇒ 只剩补方法一条路。**
       落法：把逐行落库那段从 `flush()` 里提成私有一段，两条路径共用；
       `flush()` **行为逐位不变**（仍逐行 try/catch、仍只计 droppedFlushes、仍不抛回调用方），
       `recordUsage` 只差两处——入参从私有 buffer 换成外部数组、返回从 void 换成成功行数，
       且**一行都没落上时抛**（回 0 会让「对面明确说一行没写」与「压根没问到对面」在调用方那里同形）。

       **决定二（合并缓冲落在哪）：本轮不用定，因为调用方今天不存在了。**
       ⚠️ **这是本条最要紧的一句，接手别按旧描述开工**：task 2.4e 把视觉调用搬出自动化段之后，
       `content-token-usage-authority` 在**自动化段一条证据都不剩**（重生成后只剩
       `segAApiFoundation:new:TokenUsageStore` 与 `segDApiServing:identifier-use:tokenUsageStore`）。
       用量记账的真实调用点是模型客户端的 `onCall`，而那个客户端建在 segA——segA 今天每个进程都跑，
       所以 automation 进程记账走的是本地属主实例、还自带一条 content 库的池。
       那条池要等 segA 三分才收得掉。**⇒ 合并缓冲的家就是 automation 自己的 `main()`（tasks 3.1）**，
       它在那里建自己的模型客户端、其 onCall 经本路由提交。写 3.1 时必须带上的两条硬约束：
       ① 提交前 swap 出快照，失败**丢弃 + 计数、绝不放回**（可交换累加计数器上重投即翻倍）；
       ② 占位值逐字沿用属主今天那四条（role→`untagged`、provider/model→`unknown`、无 accountId 直接丢），
       否则同一个未打标的调用在单体与拆分两种形态下会落成两行不同维度的账，**而这不会报错**。

       **路由「现在没人调也要注册」是有意的**：不注册的话，第 3 段写 `main()` 时才会发现对面根本没这条路由。
       同批补了三条单测并各做一次变异实测（都由**对应的那条**用例抓住，不是被别的用例连带）：
       桶起点逐字沿用调用方给的（变异成属主重算 → 该条红）、一行没落上时抛而非回 0（变异成回 0 → 该条红）、
       部分成功回真行数且失败行不重投。

       **E1（segD 那条无人承接的证据）**：api 侧的账单价格刷新与用量只读今天直接用属主实例，
       而 kernel 端口**刻意一个 api 侧方法都不开**（读侧 `usage()` / `upsertBillingPrices` /
       `billingPriceTargets` / `purgeOlderThan` 的消费方是 api 或属主自驱）。
       ⇒ **明写它由 segA/segD 三分承接，不由这条 content 端口承接**（照 2.9a「两条都行、不能留空」的口径）。
       成本红线（债⑦）自动满足：端口与传输层零单价字段，成本是属主侧读时 JOIN 账单快照反算的。 -->
- [x] 2.4d-用量-flaky **顺手修掉一条「看着是偶发、其实不是」的用例**（同批 `8848c56`）。
  <!-- `/task 前缀…` 那条在 2026-07-31 的两次全量里各红一次，单独跑与重跑都绿——**看着像并发偶发**。
       真因：它把同一句话解析**两次**再逐字段深比较，而解析器不传 now 时取 `Date.now()` 算截止时刻，
       两次调用之间跨过 1 毫秒就不等。单独跑几乎跨不过去，全量并发下就会。
       **诊断是实测坐实的**：强制在两次解析之间跨一毫秒 ⇒ 必红；喂固定时钟 ⇒ 必绿。
       ⚠️ 别把那个固定时钟删回 `{ source: 'feishu' }`，用例里已写明理由。 -->

- [x] 2.4d-回收 **不做了（用户裁定，2026-08-01）。计数面保留，回收扫描永不实装。**
  <!-- 无提交（本条是**裁定**，不是实装）。
       **裁定原文口径**：素材用过就不能再用；超时 / 发布失败带来的一点浪费可以接受。
       ⇒ 「停在 reserved 的素材组」**不是缺陷**，是可接受的损耗。本条就此关闭。
       **下一手别再把它当 bug 捡起来**——它长得非常像一个 bug，而且有很扎实的现场数据（见下），
       正因如此才要把裁定写在这里，否则下一个人一查库就会重新立案。
       **裁定当时的现场（dev，2026-08-01 实测，仅供理解裁定背景，不构成待办）**：
       23 组 reserved / 13 组 available（占用超过六成），最老 16 天、最新 4 天；
       其中一个账号独占 22 组。同账号的稿件状态里失败 26 条、待审批 3 条、待复核 5 条
       ⇒ 至少十几组确定不会再有人来还。**根因也已坐实**：占用发生在生成期、释放只有下发期一个出口，
       稿件在生成失败 / 被否决 / 从未下发时压根碰不到那个出口。
       **另记一条仍然有效的技术禁令**（万一将来裁定翻转，别踩这个坑）：
       **MUST NOT 做成按墙钟超时的回收。** 占用与释放之间隔着可以任意长的人工审批，
       按时间一刀切会把正在等审批的图放回可用池 ⇒ 同一组图被两条稿用掉，比停在 reserved 严重得多。
       安全判据必须反过来问属主侧「还有没有非终态稿件持有它」，而那两张表属主不同
       （素材表 content / 稿件表 api），要新增一条窄读端口才问得出来。 -->
- [ ] 2.4d-回收-原文 **FB 素材的兜底回收扫描**（债③剩下的那一半）：今天只有计数，
  漏掉的素材仍然停在 `reserved` 无人回收。计数面是 `getFacebookMediaSettleMisses()`。
  <!-- 📌 **2026-07-31 坐实：这条不能按「加个 TTL 扫描」做，那样会重复用图。先读完再动手。**
       **占用是怎么产生的**：`FacebookMediaSelectorRole` 在**生成期**调 `reserveNext`，
       把素材组置 `reserved` + 写 `reserved_by` / `reserved_at`；解除只有一个出口——
       `PublishDispatcher.settleFacebookMedia`，它在**下发期**按结局调 markUsed / quarantine /
       releaseReservation。调度器自己那 6 条路径覆盖得很全（含 draft 缺图、抢占、提交未确认）。
       **真正的洞在两头之外**：
         ① 稿件被**否决 / 取消 / 到期从未下发** ⇒ 压根不会走到调度器 ⇒ 永久停在 reserved。
            全仓 `releaseReservation` 只有调度器那一处调用点，没有第二条路。
         ② 进程在「已保留、尚未下发」之间死掉 ⇒ 同上。
       **为什么不能只按时间扫**：保留与结算之间**隔着审批等待**（人审 / 原生定时发布），
       这段可以任意长。按 `reserved_at` 超时就回收，等于把一组正在等审批的图重新放回可用池，
       于是同一组图被两条稿用掉——**这比停在 reserved 严重得多**。
       **也不能用一条 SQL 解决**：判「这个保留还活着吗」要问稿件状态，而
       `publish_log` 属 **api**、`account_facebook_publish_image_set` 属 **content**，
       跨域直连数据库是本 change 的红线之一。
       **三条候选（未拍板）**：
         ① 在稿件走向终态的那几处也调一次 settle。最便宜、覆盖 ①，但覆盖不了进程死。
            代价：保留信息藏在稿件的 `imageDirective` 里，终态路径在 api 侧，要多一跳取它。
         ② content 侧扫 `reserved` 且够老的行，**逐条向 api 问一次「还有非终态稿件持有它吗」**，
            答「没有」才回收。覆盖全，但要新增一条窄读端口。
         ③ 保留改成带到期时间的租约，下发链路续租。最稳、最动骨头。
       **倾向 ① + ②**：①先堵住绝大多数真实占用，②作兜底且**必须带那一问**，
       绝不做成只看墙钟的扫描。**在②落地前，MUST NOT 上任何 TTL 回收。** -->
  <!-- 现状事实供下一手直接用：状态全集 = available / reserved / used / disabled / deleted / quarantine；
       `releaseReservation` 只在 `status='reserved'` 且 reservationId 匹配时才动行、返回真态 rowCount。
       所以「回收」这个动作本身已经是幂等且安全的，缺的只是**谁在什么判据下调它**。 -->
  <!-- **消费面早就不是问题**：0.6c / 0.6e / 0.6g 那批已经把四个注入面全改成 kernel 端口类型
       （`ConceptStorePort` / `SchedulerConceptStore` / `CuratedSelectionPort`），
       所以剩下的**只是组装根按模式注入哪一个实现**——与刚做完的委托那条**同形**。
       传输三件套也齐了：`src/transport/content-authority-http.ts` 里
       `registerConceptPoolAuthorityRoutes` / `registerCuratedSelectionAuthorityRoutes` +
       `ConceptPoolAuthorityHttpClient` / `CuratedSelectionAuthorityHttpClient`（本步只用不改）。
       **两处注入点**（按符号定位，行号只作导航，pin 在 `aidcp-cloud@319b0af`）：
       ① `segCAutomation` 里 `new RoleDispatcher({...})` 的 `conceptStore` 与 `curatedStore: curatedContentStore`（约 :7090 / :7093）；
       ② 同段 `ctx.publishScheduler = new PublishScheduler({ conceptStore, ... })`（约 :7653），
          其精选面走 `curatedStore`（约 :7666）。
       **判例照人设生成器那处**（同段，约 :5615）：`seamMode === 'monolith'` 用本地实例；
       其余模式读 `AIDCP_CONTENT_URL` + `requireDirectInternalToken('AIDCP_CONTENT_INTERNAL_TOKEN')`
       + `deploymentTarget` 建 HTTP 客户端，**缺任一项直接抛**（`content_*_authority_unavailable`）——
       **fail-closed、绝不静默回落本地**。`seamMode` 取自 `serviceModeFromEnv()`（segC 顶部）。
       ⚠️ **别照搬「三元里塞一个 undefined」**：这两条今天的降级点已在 0.6f 收成具名抛出，
       接线时把那几处具名原因**原样保留**，不要因为换了实现就退回空数组 / 静默。 -->
- [x] 2.4e **图内文字卡转写接线，并据此撤掉 `content-textcard-transcription-authority`（门 11 → 10）。**
  <!-- aidcp-cloud 7d921f6 / transport f7746bd / automation 26914d7 / api ac6789f / content 4ec2fa3。
       **本条与前三次接线（2.4a/2.4b/2.4d-媒体）形态不同，别照它们的结论读**：那三次是「保留本地构造 +
       加一条按模式取的替代路径」，证据符号原样留着、要等第 3/4 段才谈得上撤；本条把整条 OCR 子链
       **搬出了自动化段**，五个探针因此**全部自己停止匹配**，条目机械消失。

       **搬段不是洁癖，是它本来就在错的段**：转写器、两个视觉客户端、准入形态感知器原先全建在自动化段。
       那对两边都不对——自动化进程造不出它们（全是 content 属主、自动化包里根本没有这些模块），
       而**内容进程**（本该对外提供这条能力的那个）压根没有实例可供：它唯一的构造点长在一个内容模式不跑的段里，
       `startContentReadApi` 里那条转写路由**就算有人写了也永远注册不上**。
       现在建在 segB；segC 三条取用路径逐条显式：automation ⇒ content 的 HTTP 客户端；
       跑过内容段 ⇒ 经 `crossSegment` 取那个实例；两者皆非（今天只有 core）⇒ 响亮 `cross_segment_drop`、
       角色按 `unavailable` 如实留痕。**刻意没有本地兜底构造**——那需要视觉客户端与 content 模型解析，
       正是本块要消灭的耦合。

       **`enabled()` 具名不上线（用户 2026-07-31 拍板：读同一份开关）。** 它答的是「运营把旗标开着吗」，
       而旗标是部署配置、两个进程读同一份。开一条路由有两处坏：角色每评一篇笔记为一个布尔多走一次往返；
       且那一跳失败时这个**同步**方法无处报错、只能编一个答案，而角色会把它当三态里的一态如实打进日志。
       客户端本地读同一个旗标（取值闭包由组装根注入，不在传输层自己读 env），属主每次 transcribe 回显
       自己那侧的取值，不一致告警一次。**两个方向不对称，而不对称的方向恰好是无害的那个**：
       自动化关/属主开 ⇒ 压根不发起调用，角色报 `flag_off`，这就是正确行为；
       自动化开/属主关 ⇒ 调用发出、属主原样退回、一个字没转，角色却会报 `active` —— 这才是有害的那支，
       也正是回显能抓住的那支。

       **撤条的守卫刻意不是探针**（这条比上面的接线更要紧）：五个探针是自己停止匹配的，
       而「探针不再匹配」**分不出**「耦合真的没了」与「有人把接线删了」——两者在派生输出里都是安静地少一条。
       所以复活断言写成两半，缺一不可：① 自动化段 MUST NOT 再就地造转写链（三个构造类符号逐个查探针）；
       ② 自动化那条取用分支 MUST 还在。只断 ① 的话，把整条接线删干净反而「更绿」。
       同批下调 `composition-root-4a-inventory.test.ts` 里 content-owner 计数 8→7 并补撤条说明（census）。

       **两把尺仍然分开**：单体侧那份 AST 派生台账 54→53；**automation 侧那份（门）未动，仍 11**——
       它的判据是「阻止本包交付完整生产进程的依赖」，而 `main()`（tasks 3.1）排在清台账（4.1）之前。
       门要减到 10 在第 4 段。
       六仓零漂移；测试 cloud 4040 / api 496 / automation 1967 / content 439 / transport 36 / kernel 59，全 0 fail。
       ⚠️ 跑全量时撞到一次 `/task 前缀…` 用例偶发红：单独跑过、重跑过、基线同条件也跑过，判定为并发偶发，非本条引入。 -->
- [x] 2.6 处置 `ReplyWorkflow` 的 content 属主具体类实参（与模型出口是两件事，单独处置）。
  <!-- aidcp-cloud 2da39f6 / transport 40df6de / automation 7088c83 / api 3f2c6dd / content 9998290。
       **与 2.4e 同形同因**，落法逐字照它：构造搬进内容段（`ctx.replyAi`）→ 内容侧注册三条路由
       → 自动化段按模式取（automation ⇒ HTTP 客户端；跑过内容段 ⇒ 那个实例；两者皆非 ⇒ 响亮 drop）。
       **先记一句好消息**：编排层一直只持 kernel 的 `ReplyAiPort`，所以这从来不是工作流的耦合，
       只是组装根里一个 `new` 长错了段。搬完后那条唯一的探针自己停止匹配 ⇒ **第三条靠接线撤掉的**。

       **「缺席就不组装」这一支是编译器逼出来的，别改成非空断言绕过去**：工作流第三个实参必填，
       所以缺席时唯一诚实的处置就是不组装它（它本来就可选，下游两处内部 API 早有对应分支）。
       塞空壳是这里最坏的选项——每一次分类 / 润色 / 风险复核都会静静回一个结构上合法的结果。

       **回执守卫逐字校验 `fallback` 落在联合里，MUST NOT 只判 `typeof === 'string'`**：
       那个字段带的是「这一步为什么没得到正常答案」，而 `value` 那半无论如何都是合法取值 ⇒
       丢了它，一次超时会读成一次正常分类；任何默认值都会把它压成 `'none'`。

       顺带把互动 AI 单步超时收成一个解析函数：两段各读一次同一个 env 就是两个会各自漂的默认值，
       **漂了不报错**，只是两边对「多久算超时」看法不同。

       撤条按 2.4e 的纪律走全套：重生成（cloud 台账 53→52）+ census 撤条说明 + content-owner 计数 7→6
       + **两半复活断言**（自动化段 MUST NOT 再造 + 远端取用分支 MUST 还在）。
       **automation 侧那份（门）仍未动、仍 11**——减门是第 4 段的事。
       六仓零漂移；cloud 4044 / api 496 / automation 1967 / content 439 / transport 36，全 0 fail；acceptance 180/180。 -->

- [x] 2.7 **传递性检查已做完：四层逐层处置，两层本批修、两层此前已闭、一层校准样本。**
  <!-- aidcp-cloud f489e5e / aidcp-automation bf97e2e / aidcp-content f290a3c。
       **逐层结论（原文的四条描述有两条与代码不符，如实更正）**：
       ① 转写器句柄：**已闭，非本批**。组装根那一侧现在走响亮取用闸（2.4e），
          角色→评估器那一跳仍是条件展开、结构上静默，但缺席态由 AC-TCT-3 单独钉着
          （`test/acceptance/text-card-transcription-absence.test.ts`，缺席必须具名留痕、
          且不得改成抛出——那条链路是 fire-and-forget，抛出会打断浏览闭环）。不重复造。
       ② `CuratedNoteSink` 的「两个可选方法」——**原文已过期**：0.6d 早把三个方法的 `?` 全删了，
          今天一个可选都没有。本批只补一道**类型级**闸钉住它不许回来（比源码文本可靠：
          认的是「这个键在类型上可不可选」，不会被换行/重命名骗过）。
       ③ `CoverFormSensor.senseAt?` ——**本批修**。原文说的「降级成错误态、产出空、不抛不 warn」
          属实，但只说了一半：**同一个 `?` 在组装根那边是靠非空断言撑着的**，缺席在那里是
          运行时 TypeError。两种失败态、没有一种是设计出来的。按 0.6d 的同一条判据删 `?`
          （「提供不了」由实现方抛具名原因来说，不许靠不定义方法来说），两个调用点的兜底同时删。
          代价：两个测试桩要补这个方法——其中一个顺手改成两个方法记同一个计数器，
          这样哪天缓存短路失效，它会如实变成非 0，而不是因为「桩没实现」被悄悄跳过。
       ④ 人设两选一 ——**本批修**。检查从「第一次读」提到**构造期**（读点全在
          fire-and-forget + try/catch 里，拖到读 = 等于没有信号）。**零爆炸半径**：
          4046 条既有用例全绿，说明每个既有构造点本来就传了。
          `llmTimeoutMs?` ——**改判为「不是同一类问题」，本批不动**：它的缺省语义是文档写明的
          「沿用共享客户端构造默认」，不是能力消失；真需要更紧 deadline 的三个评论角色都显式传了。
          原文那句「per-role deadline 悄悄消失」在事实上成立，但那是**设计好的回落**、不是静默失败。
       ⑤（校准样本）`PublishDispatcher` 的素材端口：2.4d 已补计数 + 具名 error，
          `publish-dispatcher.test.ts` 里正反两条都在。本批不重复。
       新增 `AC-XOPT-1/2`（`test/acceptance/cross-owner-optional-args.test.ts`，读组装根 ⇒ 结构性留守 cloud）
       + `test/agents/content-role-soul-contract.test.ts`（只依赖 automation+kernel ⇒ 已派生进 automation）。
       **一条踩到的坑记下来**：源码文本扫描**连注释一起扫**。AC-XOPT-2 第一次跑就被组装根里
       一句复述被禁写法的注释判红——被禁的写法在整条链路上只许出现一次（就是断言的实参本身）。
       cloud 4050 / automation 1969 / content 441，全 0 fail；acceptance 182/182；六仓零漂移。 -->
- [ ] 2.7-原文 **传递性检查**：逐个构造点核对跨属主实参，**特别点名 optional 参数**
  （`PublishDispatcher` 的 `FacebookPublishMediaStore` 漏传不报错、三个写静默消失）。
  写一条会红的用例钉住它。**同形共四层，逐层都要处置**（见 design.md §5.5.6）：
  ① 转写器可选实参；② `CuratedNoteSink` 的两个可选方法（见 0.6d）；
  ③ `CoverFormSensor.senseAt?` 缺席时降级成错误态 → 转写产出空、不抛、不 warn；
  ④ `ContentRoleOptions` 的 `soul?`/`getSoul?` 皆缺时构造期不报、第一次读才抛，
  而读它的位置在 fire-and-forget + try/catch 里 → 静默不纳入；
  `llmTimeoutMs?` 缺席则 per-role deadline 悄悄消失（角色调度器公共选项本来就不传它）。
- [x] 2.7a **已被 2.4e 吸收：AC-TCT-3 早已落地，且落在一个单独文件里（不是原文说的那个）。**
  <!-- 无新提交。核实结果：`AC-TCT-3` 现住 `test/acceptance/text-card-transcription-absence.test.ts`，
       **不在**原文点名的 `text-card-transcription-honesty.test.ts` 里——后者文件头明写它「已移出」，
       理由是归属：这条守的失败态只可能发生在 automation 侧的角色上，
       必须跟着角色进 automation 仓才有意义，而 AC-TCT-1/2 依赖视觉客户端与生成提示（content），
       合在一个文件里就是跨属主、只能留守 cloud——那样这条断言永远到不了它要保护的那个仓。
       **另外原文的前提也已变**：转写器现在**不是**无条件构造无条件注入了（2.4e 改成按模式取），
       所以「false 分支生产上从未走过」这句只对 2.4e 之前的代码成立。下一手别照原文重做。 -->
- [ ] 2.7a-原文 **新用例落点已定**：转写器在今天的单体里是**无条件构造、无条件注入**
  （`server.ts:6493` / `:6761`），旗标只作回调传进去、在内部判——
  所以 `server.ts:116` 那个条件展开的 false 分支**生产上从未走过**，
  **「漏传」这个失败态只可能由本次拆仓引入**，现有测试不可能覆盖它。
  新用例作 `AC-TCT-3` 加进 `test/acceptance/text-card-transcription-honesty.test.ts`。
- [x] 2.8 **两条都已在前几批实装并有用例；本批只补了一道它们都依赖、却没人守的前提闸。**
  <!-- aidcp-automation 9d4c9a2（本批唯一新增）。**先说核实结果，别重做**：
       **（a）「写口只报真态行数」已成立。** 两条返回行数的写口都带具名守卫
       （`isNonNegativeInteger`），文件头明写「读不到 MUST 抛、MUST NOT 取 0——
       0 会被读成『对面明确说它一行都没写』，而真相是压根没问到对面」。
       用例已在：`content-authority-http.test.ts:285/497/554/566`（含「属主报错」与
       「属主答了但回执坏」两种**不同**的失败，刻意分开断言）、`content-media-usage-http.test.ts:286`。
       属主侧那一半是 2.4d-用量 做的（部分落库如实返回、绝不重投）。
       **（b）「用结构化守卫、不用 instanceof」已成立。** `isDelegatedTaskServiceError` 判的是
       `name` + 具名字段，正反三条用例齐全（`delegated-task-http.test.ts:268/282/296`，
       末一条钉「传输层自己的错误**不得**被还原成业务拒绝」）。
       仓里余下的 `instanceof` 绝大多数是 `err instanceof Error ? err.message : String(err)` 这类取值，
       且判别型的那些**全在客户端侧**——`InternalHttpClient` 收到线上错误后**在本地重新构造**
       `InternalHttpError`，对象从未以对象形态过线，所以那些 `instanceof` 结构上成立。

       **（c）本批新增的是上面那个「结构上成立」所依赖的前提**：它只在
       **本进程里那些类只有一份**时才成立。automation 是 `src/transport/` 的属主（50 个文件），
       同一批文件又被复制进 `aidcp-transport` 给另两家用；**两份行为逐字相同**，
       所以装错一份不会崩——只会让跨两份的 `instanceof` 恒 false，把鉴权 / 版本 / target 不匹配
       一起静默退化成兜底分支。故加一条闸：automation 的 `src/` MUST NOT 从
       `aidcp-transport/transport/*` 取任何东西（显式放行 `aidcp-transport/llm/*`）。
       **此刻是前瞻的**：今天一条都没有；但 A-1 马上要让本仓第一次 pin 这个包，
       危险的不是 A-1 本身（模型出口闭包实测不含传输原语），是它之后那句
       「反正已经依赖了，顺手也从包里取个 HTTP 客户端」——那一步零编译错误。
       变异实测：塞一个从包里 import 传输原语的探针文件，当场红并点名说明符。 -->
- [ ] 2.8-原文 失败语义测试：写口只报真态行数；跨进程错误识别用**结构化守卫**，不用 `instanceof`。
- [x] 2.9 **`content-publish-rejection-evidence-authority` 已撤条：它是**记错了属主**，不是没做。**
  <!-- aidcp-cloud 9df5210 / aidcp-automation 86ccf18。门 13 → 12（content-owner 9 → 8）。
       **每一环都机械核过，不是论证出来的**：
       ① 判定 `hasUserRejectionEvidence` 住在 `src/kernel/publish-pipeline-types.ts`——归属表判 kernel、
          且在 kernel 名册上；两行纯字段读、只 import kernel 类型、不构造任何东西。
          **而且它已经随 aidcp-kernel pin 存在于 automation 包里**（在装出来的 .d.ts 里，
          且已有 7 个 automation 文件从那个模块 import）。
       ② 数据来自 `apiDirectPorts.publishLog.loadForDispatch()`——**api** 属主的 4a 端口
          （表 publish_log owner=api），早已跨进程化，而自动化根**已经**构造着它的客户端
          （`new AutomationPublishLogHttpClient(...)`）。
       ③ 那个字段的唯一写入方是 `src/publish-agent/publish-log-store.ts`，属主 **api**。
       ⇒ 全链没有 content。**一个 kernel 纯谓词不可能是内容授权。**
       **错因**：组装根那条 import 走 `src/publish-agent/types.ts`（属主 content），
       而那文件对这个符号的全部内容是一句 `export * from '../kernel/...'`——kernel 那次 `git mv` 之后
       留下的六行残壳，**而那次搬迁（07-24）早于这条 binding（07-29）**。
       binding 的作者读到的是 import 路径，不是代码所在。
       **注意别把它叫「假消边」**（我一度这么写，核验时被纠正）：§8.3 的假消边指「把属主文件改成壳、
       却不 repoint 消费方，以此声称边消了」；这里是一次合法搬迁的残留，归属注释里有记录。 -->
  <!-- **一条结构性事实，比这条条目本身更值得记**：台账里 `owner` 字段是 binding 上**手写**的，
       `sweepReviewedProbes` 原样抄过去、**从不查 `module-ownership.json`**。只有「证据在场」是 AST 派生的。
       ⇒ **属主写错了，`--refresh-ledger` 跑一万次也纠不过来**，这类错只能靠人读出来。
       别把这份台账的 owner 列当派生事实读。 -->
  <!-- **动它之前先把另外 8 条 content 条目机械扫了一遍**（万一是同一个壳导致的系统性误记，
       那会实质改变门的大小）：其余 8 条的证据符号**全部定义在真 content 属主文件里**
       （ConceptStore / CuratedContentStore / FacebookPublishMediaStore / TokenUsageStore / QwenClient /
       ReplyAiService / OpenAiCompatVisionClient / 两个文字卡工厂）。**这条是孤例，不是模式**——
       对门的另外 8 条是好消息。
       **另标记一条不替它裁定的**：`content-role-factories` 的证据符号是 server.ts 里的一个**本地常量**，
       而它引用的四个角色类**已被 0.7 改判为 automation 属主**。那条现在还描述不描述一个真的内容依赖
       （写口），属 **task 2.5** 的问题。 -->
  <!-- **没被撤掉的那一半**（0.3d 的原始担心仍然成立）：若有人把那个谓词**打桩**而不是从 kernel import，
       被否决的稿件会读成「没被否决」，委托执行器会把它判成 `failed` 而不是 `cancelled`。
       那是**另一个**失败、另一种修法，自熄断言的失败消息里写明了「别拿它复活这条」。
       变异实测：把 binding 加回去，普查用例当场红。 -->
- [ ] 2.9a **原文（前提已被推翻，保留供追溯）**：14 条台账里唯一一条此前无人承接的
  （2026-07-30 交接文档核验时发现：本 tasks.md 与 `specs/` 全文对「否决 / 驳回证据 / 候选装载」零命中，
  我原本误以为它属于 2.7 的传递性检查，实际不属于）。
  **后果是硬的**：96 条 task 全做完，台账也清不到零，第 4 段「清零 → 入口切真启动」直接卡住。
  内容见 automation 台账那条的注释：**草稿否决证据判定在委托执行器的候选装载路径上**。
  先坐实现状（属主是谁 / 判定读的是什么 / automation 侧调用点在哪，带 `文件:行`），
  再决定是补端口面还是**明写它由另一个 change 承接**——两条都可以，但**不能留空**。

## 3. automation 生产运行时真接线

> 📌 **3.1 的体量已实测（2026-07-31），先读这段再排期。** 它读起来像「写一个 main()」，
> 实际是把 cloud 组装根的自动化段整段搬过来：`src/server.ts` 的 `segCAutomation`
> **4193 行**（去掉空行与注释 3377 行），**145 个构造点、99 个不同的类**，
> 读写 **54 个** 不同的 `ctx.*` 成员。这不是一次性能收尾的活，本身就该按批切。
>
> **已有的地基比想象中厚**：`createAutomationCompositionRoot`（1081 行）已经建好了
> 属主库连接池、16 个 api 客户端 + 2 个 content 客户端、3 个指令接收器、注销对账器、
> 同步读四件套（镜像 / 属主快照源 / 账号投影 / 变更中继）、内部 HTTP 服务端与 listen/close。
> 缺的是**运行时那一半**：边-云 WebSocket 服务端、事件总线 + 角色调度器、风控单写者、
> 各调度器与监测体 —— 也就是 `AutomationRuntimeHandles` 那个注入口今天还没有真实供给方。
>
> **排期含义**：3.1 不做完，前面已接线的 6 条 content 通道全都用不上（没有进程去消费它们），
> 第 4 段的清零与第 5 段的收尾也都排在它后面。**门停在 11 不是漏了，是它在等这一步。**
>
> 📌 **切批方案已出（2026-08-01，用户要求）：见 `HANDOFF.md` §9 —— 八批 A…H，按依赖排序，
> 每批带段落横幅定位、规模、依赖与踩点。别把 3.1 当一次性任务开工。**
> 三条贯穿判据也写在那里：每批结束必须可编译可测；搬之前先问「结果有没有去处」；
> 缺依赖 MUST 停在具名原因上。**自动化仓的 fail-closed 入口在批 H 之前一律不动**——
> 它是中间态的保护罩，让「组装根能构造」和「进程能启动」保持分离。
> **A-1（第一次依赖共享传输包）不属于任何一批，动的是版本链，必须单独一次做完**，建议排在 A 与 B 之间。

- [ ] 3.1 `aidcp-automation`：在 `createAutomationCompositionRoot` 之上写真 `main()`——
  边-云 WebSocket 服务端、事件总线 + 角色调度器、风控单写者、各调度器与监测体。
- [ ] 3.1e **批 E 后半（每连接角色调度器工厂）撞到一个必须先裁定的归属问题 —— 与 3.1c 同形，
  <!-- **步骤 1 已落**（cloud bc690ce / kernel ac02b74 / transport 8f88509 / api 6b00006 /
       automation 76aded7 / content f99f3a7）：前三个业务配置（排期 / 热帖阈值 / FB 评论配置）
       的「快照 + 账号 → 生效值」析出 kernel，存储残壳留 api 并等值再导出，既有消费方一行未改。
       新增 kernel 成员 `content-schedule-resolution.ts`（另三段补进既有 kernel 契约文件）。
       六仓对账零漂移；跨域边仍 0；cloud acceptance 184/184、全量 4077 pass / 0 fail；
       api 501 / automation 2040 / content 441 / kernel 70 / transport 36，全 0 fail。

       **顺带结清三处已经存在的第二份实现**（都不是新写的，是本来就在那儿的）：
       ① 面板目录投影里就地展开的掩码解析 —— 它的注释自称「与 automation 侧现读同一个解析函数」，
          实际是另一份等价写法，注释与事实早就分了家；
       ② 同步读发布方自带的热帖逐项回落（与属主存储各一份，语义碰巧还一致）；
       ③ 同步读发布方自带的评论模式映射。

       **实读发现一个不会报错的坑，已钉住**：同步读快照上的评论模式是**复数 `templates`**，
       领域类型是**单数 `template`**，两套字面量，而快照字段类型是裸 `string`、typecheck 抓不到。
       跨进程消费方顺手写 `mode === 'template'` 恒 false —— 后果不是崩溃，
       是**运营配好的模板被静静换成 AI 生成正文**。今天零消费方，而**批 E-2 步骤 3 正是第一个**。
       已收成两个具名出口（`facebookCommentModeToWire` / `FromWire`），
       并把快照字段类型从裸 `string` 收窄到线缆联合，让编译器接住误用。

       **结构断言写法上纠正了一次，下一手照新写法办**：第一版按「文件里没有同名的本地定义」判
       （抄的是 content-authority-wire 那条判例），**当场被变异绕过** —— 第二份改名成
       `localResolveEffectiveContentActiveMask` 就躲开了同名检查，8 条用例与 typecheck 全绿。
       改成**正向判据**「每个取数口的方法体 MUST 调到 kernel 那个符号（按词边界）」后才抓得住。
       ⇒ 「MUST NOT 自己定义同名函数」是弱判据，凡新配这类断言一律写成正向委托判据。
       变异四个，逐条给出是哪条抓住的：改名的第二份解析 → 结构断言红；发布方改回就地写线缆
       字面量 → 结构断言红；未配模式时改用列值 → 那条行为用例红；把内容掩码「统一」成按合法性
       校验 → 那条口径用例红。

       **步骤 2 已落**（cloud f12181b / kernel 9cfd1c9 / transport a2ffe05 / api 8c0ba78 /
       automation ed2d32b / content f060706）：Facebook 运营基线判定析出 kernel
       （`facebook-operation-policy-resolution.ts`）**并补上了它缺的那条同步读流**
       `facebook_operation_policy`（api → automation）。cloud acceptance 184/184、
       全量 4084 pass / 0 fail；automation 2040 pass / 0 fail；六仓对账零漂移。

       **一个与原计划不同、且更省事的形状（下一手照这个读）**：载荷发的是属主
       **已合成好的逐环境基线投影**，不是那 8 张原始表。原勘察设想的是「补一条流把输入运过去」，
       实读后发现那样等于逼消费方在本进程里把「全局默认 ← 环境覆盖 ← legacy 回落」再实现一遍——
       正是本 change 反复被咬的形态。发成品之后，kernel 里的纯段就只剩「未就绪 / 绑不到环境 /
       没配浏览面 → 三条具名 blocker，否则给基线」，automation 侧一行判断都不用写。
       顺带把属主侧两处就地展开的合成收口到同一个合成口。

       **三处刻意做成「缺了就响亮失败」**：① 发布方的基线取用口必填无默认（回落空表 =
       告诉自动化进程「这台机器没有任何 FB 环境」，每个 FB 账号被**错误原因**永久拦住浏览）；
       ② 组装根经 `requireSegment` 取句柄且**在快照期才解**（装配期那个句柄必然还没赋值）；
       ③ 自动化侧副本没到 / 陈旧时如实报未就绪。

       **发布顺序：游标先读、基线后取**，并在取之前按库回读一次。反过来会发出
       「新游标 + 旧基线」，消费方存下就再也不会重取——那是会一直错下去的静默陈旧。

       **staleness 仍由既有的 `content_schedule` 闸覆盖**：四个策略写事务同批推进两个键，
       所以新键留在参数档（不入 `AUTOMATION_GATE_MIRROR_KEYS`）不减少停手保护。

       **⚠️ 留了一条明账**：`aidcp-api` 的手写入口**还没构造** Facebook 运营策略存储，
       故它今天供的是一个当场抛具名错误的实现。三进程真跑之前必须补上，
       否则 automation 拉这条流会拿到 502 而不是基线。**MUST NOT 改成回落空表。**

       变异五个，逐条给出是哪条抓住的：未就绪回落默认基线 / 没配浏览面给个默认 feed /
       交出属主对象本身不深拷贝 / 自动化侧就地展开等价判断 / 校验器放过残缺节奏字段。

       **六处机械检查当场红，全部按它们记的位置改（无一放宽）**：同步读清单、镜像注册表条数、
       流注册表条数、策略存储的两处 bump 期望、api 手写入口（必填口）、
       automation 两份派生私有夹具 + 一处写死的存盘条数。
       最后那处改成**由消费流清单算出来**——紧邻已有一条 deepEqual 钉住真实集合，
       再写个手打数字只会在每次新增流时红在一个看不出所以然的地方。
       **§4.2c 那条又应验一次**：两份派生私有分叉都靠 typecheck「碰巧」接住，没有任何机制提醒。

       **⚠️ 步骤 2 上 dev 时连挂三次，三处不同源，都是「同一份名单的第 N 个手抄副本」。
       后续任何新增同步读流，把这四处一起改，别指望编译器。**
       修复后 dev 已部署到 `c0de08b` 并健康（三口在听、启动失败 0、错误 0、
       重启计数 0、飞书长连接已建立、三属主库待应用 0、面板 API 经 nginx 回 200、isales 四服务未触碰）。

       | 第几次 | 哪份副本漏了 | 谁本该抓住 | 实际后果 |
       | --- | --- | --- | --- |
       | ① | 组装根的**自举流名单**（`API_SYNC_READ_OWNER_STREAMS`） | 没有人 | 就绪闸 `not_ready` → 起不来 |
       | ② | 基线投影用两个 spread 合成，**多带两个键** | 没有人 | 载荷校验 `invalid_envelope` → 起不来 |
       | ③ | 迁移里 CHECK 约束的**流名清单**（0083 写死） | 没有人 | 写检查点被约束拒 → 起不来 |

       **三次都是 typecheck 绿 + 全量测试绿**，各自的原因不同、值得分开记：
       - ①：那份名单写的是 `[...] as const satisfies readonly SyncReadStream[]` ——
         **`satisfies` 只校验写下的每条合法，不校验有没有写全**；
       - ②：**TS 对 spread 结果不做多余属性检查**，返回类型标注拦不住多余键；
         而 kernel 那边的夹具是**照类型手写**的，恰好只有 11 个键，
         它证明的是「契约自洽」，不是「真产出物符合契约」；
       - ③：**只有真连库才现形**。进程起得来、快照也拉到了，写检查点那一跳才炸。

       三处都已改成**从唯一定义处派生 / 逐字段构造 / 按定义算出集合去比对**，
       并各配一条变异实测过的闸（`monolith-sync-read-bootstrap.test.ts`、
       策略存储那条「真产出物过真校验器」、迁移那条「约束覆盖全部消费流」）。

       **另一条只关流程、但代价很大的**：`rsync` 退出码为 0 **不等于文件到了** ——
       中途我据此判定「已部署」，实际机器上还是旧树，白排查了一轮。
       CLAUDE §6.7 早写着「上机器逐条确认新代码真的到了」，这次是照着字面踩的。
       现在的做法是部署后逐个 marker `grep` 验内容。

       **步骤 3 已落**（automation `72373f4`，落点 `src/automation-connection-dispatcher.ts`）：
       每连接角色调度器工厂，交付批 E-1 留下的那个必填口。
       typecheck 干净；automation 2048 pass / 0 fail；边界普查 forbidden=0；六仓对账零漂移。

       **保护线刻意画在本文件的依赖面上，不在调度器的选项面上** ——
       `RoleDispatcherOptions` 200 余个字段几乎全可选（实测必填的只有 `llm` / `sendCommand` 等寥寥几个），
       漏传不报错、只是能力安静消失。故 B 组 10 个口一律**必填字段或能力二态**，
       `unavailable` MUST 带具名理由（用 `undefined` 会让「没接线」与「接了但今天不可用」同形）。

       **两段析出成可单测纯函数**（都不是为了好看，是因为它们承载最容易被"顺手简化"掉的口径）：
       - `mapRuleBatchTerminalStates`：降级正文 MUST 投影成 `confirmed_without_contact`
         （投成 `confirmed` 是对人谎报「联系方式已发出」）；`no_targets` / `no_strong_candidate`
         是**没开始**不是失败（记成失败会让重试与告警都走错分支）；
       - `ruleBatchContactCommentOptions`：`contactFallback` 的审批模式与主审批模式是**两个独立字段**。

       变异四个，逐条给出是哪条抓住的：免审外溢 → 两条行为用例红；「没有目标」记成失败 → 一条红；
       降级投成 confirmed → 一条红；**动作闸里另算一遍浏览模式 → 只有那条结构断言红**。

       **收尾补了一个真空白**（automation `4abbf45`）：原先只测了析出的两段纯函数，
       **工厂本体那 46 项映射一条覆盖都没有** —— 而今晚栽的三次共同点正是「映射类代码没人真跑过」。
       为此给构造点开一条注入缝（`createDispatcher`），**唯一理由就是让选项面可断言**（注释已写明别删）。
       四条新用例各自变异验过：二态未接时 MUST 整组缺席（塞 `undefined` 即红）／
       接上后逐项接线／调度器没接 MUST 具名不启动（静默报「已触发」即红）／
       下行指令按 edgeId 定向（改广播即红，广播会串号）。

       **批 G 开工面**：`AutomationCommentPorts`（7 项）+ `AutomationFacebookRuntimePorts`（3 项），
       签名都在该文件里，照着填即可；填不上的必须给 `unavailable` + 具名理由，别塞空实现。
       **上面那组用例同时也是批 G 的验收夹具**：填完口把 `state` 从 `unavailable` 改成 `wired`，
       「逐项接线」那条会立刻告诉你有没有真接上。

       **批 G 第一片已落**（automation `806c0fa`，落点 `src/automation-facebook-runtime.ts`）：
       Facebook 规则 / 消费两套运行时存储，填掉 10 个口里的 2 个（`rule` / `consumption`）。
       它们自洽——只要自动化属主池 + 部署目标 + schema 探针。两条红线各有会真触发的用例：
       **缺部署目标即整片不构造并具名 unavailable**（task 3.4；两张表 target-scoped，
       没有目标只会往共享库写没有归属的行）；**init 失败 MUST 具名（带原始错因）**，
       绝不吞成「本来就没这个能力」。另钉住关停只关自己建的（批 D 那条共享池坑）。
       变异三个逐条验过。

       **批 G 第二片已落**（automation `c8172bf`，落点 `src/automation-comment-approval.ts`）：
       评论域审批与通知五个口 + 语料口 ⇒ **10 个口累计已填 7 个**，剩 3 个
       （评论调度器 / 联系评论安全闸 / 消费协调器）。四条红线各有会真触发的用例：
       审批口径读不到一律 fail-closed 为 review（端口没接线 / 抛错都算，MUST NOT 沿用来源模式扩权）；
       人审端口按 env 整体二态且 `unavailable` 必须具名；「已批准」的状态迁移是 best-effort、
       失败绝不影响放行判定；语料库缺失是具名降级。语料库**复用批 B 底座已建实例、不另建**。
       变异五个逐条验过。

       **⚠️ 本片顺带修了步骤 3 的一处真漏，记下形态**：免审通知在单体里由调用点按
       `approvalSource` **现推来源**，步骤 3 搬运时直接透传端口、把来源丢了 ⇒
       mandatory 人设免审与账号级免审会发出**同一种卡**，运营再也分不出这条评论
       是被哪条授权放行的。**是 typecheck 顶出来的**（端口签名对不上）——
       也就是说：**搬运时"直接透传"看着最保险，其实最容易丢掉调用点现推的那一层**。
       已按单体逐字补回并配结构断言钉住「来源不许写死」。

       **批 G 第三片已落**（automation `2a8b614`，落点 `src/automation-comment-scheduler.ts`）：
       评论调度器 + 加群调度器 + 联系评论统一安全闸 ⇒ **10 个口累计已填 9 个**。
       两个调度器必须同片：安全闸的触发闭包**就是**评论调度器的定向触发口，切开会造出
       「闸建好了但没有可触发的东西」的中间态，而它与「今天没有热帖」完全同形。
       **三个 api 属主事实今天没有通道**（群评论时序策略 / 账号暂停 / 排期名额回程），
       做成必填能力二态并各自具名，缺席后果逐条写在字段注释里 —— 缺席都不是报错：
       覆盖评论一条不发 / 加群到顶不暂停账号 / 排期名额不归还。
       五条红线各有会真触发的用例，五个变异逐条验过：
       **关停路径 MUST NOT 调那三个群存储的 `close()`**（其内部是 `pool.end()`，而池是注入的
       共享属主池 —— 与批 D 记的锚点缓存同形；**批 G 第一片那两个关的是自建池，别照抄那的写法**）；
       精选召回缺席抛具名 `not_configured` 绝不回空数组；时序策略拿不到即回「本轮无可评群」
       且连候选都不查；免审通知来源现推恒为评论调度器；写作语言连试两次不匹配即拒发。
       顺带修掉一处手抄窄形状：两条触发口的回执类型改取契约那一份（原先手抄成三字段，
       漏掉的 `level` 恰是「不染绿」那条判据要用的）。

       **批 G 第四片已落**（automation `55e7892` + `33934fe`，落点
       `src/automation-facebook-coordinator.ts`）：Facebook 消费模式协调器 ⇒ **10 个口全满**。
       前置是 cloud `7517307` / kernel `d274199`：把「基线 + 慢启动 → 账号最终模式」析出成公共判定。

       **⚠️ 下面这条判断已于 2026-08-02 实读推翻并作废，保留供追溯**：
       ~~消费协调器要的运营策略决策是 api 属主的 `resolveForAccount`（异步、含慢启动解析），
       与步骤 2 给自动化侧的同步基线口不是同一个东西，自动化进程今天拿不到它，
       要么补一条跨进程口、要么把慢启动那段也析出~~。
       **真实情况**：两样输入本进程都已具备 —— 基线走同步读镜像那条流（步骤 2 已落）；
       慢启动走**本进程自己的**风控投影（`slowStartView()`，而自动化进程本来就是风控的单写者）。
       缺的只是把两样拼成最终模式的那一小段纯判断。⇒ **用户 2026-08-02 重新拍板走就地组合**
       （与 08-01 已定的路线①同一条），**08-02 早先那条「同意补跨进程口」随之作废**。
       补口的话，等于让自动化进程绕一圈去问接口进程要一件本来就在自己这一侧的事实。
       **「MUST NOT 用同步基线口顶替」这句仍然成立**——顶替会丢掉慢启动档位；
       正解是**基线口 + 本进程慢启动投影 + kernel 那一份合成判定**，三样缺一不可。
       析出的两段（都零 import / 零 SQL / 零活状态）：风控慢启动投影 → 慢启动解析
       （原在组装根闭包里）；基线 + 慢启动 → 账号最终决策（原在 api 属主存储 `resolveForAccount` 尾部）。
       两条结构断言按**正向委托**写（按「没有本地同名定义」写会被改名绕过），各配变异实测。
       协调器片四条红线同样各有用例、五个变异验过：陈旧具名拒绝且记账 /
       决策前必须先物化风控控制器（否则随后那道同步终闸恒不可用 = 永远不发）/
       终闸拿不到控制器一律 fail-closed 绝不就地补建 / 时序策略拿不到让协调器自己报 blocker。
       恢复扫描只交付入口、**定时器不在构造期起**，并配源码级断言钉住。

       **本轮部署**：cloud `7517307` 已部署 dev（2026-08-02 深夜，健康检查全过，
       三属主库无待应用迁移）。批 G 第三 / 第四片只动 automation 派生仓，**没有上机**——
       dev 上跑的仍是单体，与它们无关。

       **批 H 第一片已落**（automation `1de0876`，落点 `src/automation-business-config.ts`；
       前置 cloud `66c88f8` / kernel `b4cc9a2` / transport `cca7fff`）：
       四个业务配置取值口的实现。本文件**零解析逻辑** —— 判定全在 kernel（步骤 1/2 已析出），
       这里只做「取快照 → 喂判定」，并配结构断言钉住五个判定符号真被调到、
       反向禁掉「就地做账号覆盖回落」与「手比正文模式字面量」两种第二份实现的形状。

       **⚠️ 顺带补掉一处真缺口**：那条环境流**此前不带环境键**，而基线解析的第一跳
       就是「账号 → 环境键」—— 也就是说在补上之前，自动化进程**根本解析不出 FB 基线**
       （下游即「这个账号永远不开始浏览」）。生产端的查询里本来就有这一列，只是没进载荷。
       三处同批：kernel 载荷类型 + 校验器 + 生产端投影；**绑定歧义时环境键恒 null**
       （挑一个发过去等于替下游做了个它复核不了的选择），校验器把这条写成硬约束。
       生产端那段投影**析成了纯函数**，好让「真产出物过真校验器」这条能真的写出来
       —— 手写夹具证明的是契约自洽，这一条本 change 已经栽过一次。

       **⚠️ 两条由变异实测改过来的判断，后面几片照办**：
       ① 热帖阈值原先写「陈旧回落写死默认」，变异跑出来没人抓；细想**方向正好反了** ——
          它是参数档不是闸门档，而写死默认很可能比运营配的更松，一陈旧就悄悄把闸放宽。
          改成保留上一份，只有一次都没收到过快照才用默认。
       ② 桩把镜像陈旧态的值置了空，而**真镜像陈旧时会保留上一份** ——
          于是「陈旧要不要沿用」那条用例是空的（把变异放进去 11 条全绿）。
          ⇒ **写镜像类桩之前先读一眼真实现的回落形状**，别按「陈旧＝没有」想当然。

       **批 H 第二片已落**（cloud `f7e9043` / kernel `12154e1` / transport `2e08ec6` /
       api `f622d12` / automation `697823c` / content `b156714`）：
       **用户 2026-08-02 拍板「先修两件小的」** —— 三件今天没有通道的 api 属主事实里，
       接掉**暂停账号**与**退还排期名额**两条；**群评论时序策略那条留到真要切三程序时再做**
       （它最大、改动面最广，且缺席后果已写明并具名）。

       两条都按 4a 既有形态落：契约 + 传输三件套 + 属主实现 + **消费方改指端口**。
       **最后那一步不是可选的**：只加口不改消费方，普查会当场报「建好零消费方」——
       而它报得对，那种口在单体里一次都不会被走到。

       **排期名额回程的三条形状**（都因为「小时格账本是属主进程内的」）：
       ① 端口只能是「报告一次事实、由属主自己决定归不归还」，
          MUST NOT 把小时格搬到自动化侧重算 —— 两本账一定会漂，漂开的现形方式是
          某一小时被归还两次或一次都不还；
       ② 回调签名放宽到可异步，**抛错即视作没接管**（既有的 catch 就是这条判据的落点）：
          不抑制只是多发一张结果卡，而把「问不到」当成「已接管」会吞掉一张本该发出去的失败卡；
       ③ 注册的是**晚绑定转发器** —— 排期器要到自动化段末尾才构造，而路由在更早一段就注册完了；
          缺席时**响亮抛错**而不是回 false（回 false 读作「排期器看过了、没接管」，
          与「这个进程里根本没有排期器」完全同形，而后者是配置问题、必须有人去修）。

       **api 手写入口里那条刻意未注册**：本进程还没有内容排期调度器，
       注册一条背后没有调度器的路由就是新造一处「看着接好了、其实永不触发」，已写明理由。

       **⚠️ 两处手抄件这次各咬一口，都不是自动同步范围**：
       ① 机械普查那套计数散在 **5 处**（中控 2 份清单 + 消费方绑定表 + transport 手写分叉 +
          automation 手写分叉），20 组 55 槽 → 21 组 57 槽要逐处改；
       ② `aidcp-transport` 与 `aidcp-automation` 的 `test/transport/` 是**手写分叉**
          （import 路径与断言都与中控侧不同），同步脚本只管 `src/` ——
          中控侧动 4a 清单时这两边要手工跟，这次一处靠红、一处靠 typecheck 才想起来。

       **批 G / H 尚未做的那一件**：把这些工厂接进组装根（`createAutomationCompositionRoot` 那一处）
       —— 10 个口现已全满，但最后一跳属批 H 的 `main()`。今天仍是**编译期可见的缺口**。

       下面是逐项供给方分类（2026-08-02 实读 `buildDispatcher`
       全 439 行得出），照它开工即可，不必重查。** 工厂本体 = cloud `src/server.ts` 的
       `buildDispatcher`（约 439 行、46 个顶层选项 + 8 个条件展开块）。

       **A. 供给方今天就在本仓 —— 直接接（照批 D/F 的写法）**
       - **每连接上下文 `ctx`（E-1 已给）**：`eventBus` / `accountPlatform` /
         五个 `has*` 能力闸 / `getRiskStatus` / `getQuotaLevel` / `canInteract` /
         `explainInteract` / `explainSearch` / `explainView` / `explainRuleJoin` /
         `getCommentDailyRemaining` / `getCommentLikeDailyRemaining`；
       - **批 D**：`pacingFloors`（节奏兜底）/ `edgeTaskLeases` / `sendCommand`
         （`edgeCommandToEnvelope` + 服务端 `pushToEdges`，**按 edgeId 定向、不广播**）/
         `isHardPaused`（服务端 `isEdgePaused`）；
       - **批 E-1**：`interactionGuard`（按账号取）/ `cooldownGate`（**单例共享**，内部按账号分桶）；
       - **批 B/C**：`configMirrorGate` / `hasCommentedForLead`（风控去重账本）/
         `recordRiskFact` / `resolveController` / `ownership`（归属跟随 + 切换后驱逐控制器）；
       - **A-1**：`llm`；
       - **内容客户端（已接线）**：`conceptStore` / `curatedStore` / `textCardTranscriber`；
       - **api 客户端**：`notifyComments`（结构化通知）/ 联系人名册 /
         `automationConfigCommands`（联系评论尝试台账两条）/ `onSessionRejected`；
       - **本仓自有**：`sessionLimitProvider`（单场）/ `resumeConfigProvider`（续场）/
         `roleFactories`（`CONTENT_ROLE_FACTORIES`，0.7 已改判 automation）；
       - **同步读镜像 / 账号窄口**：`personaBinding`（三态）/ `getNickname` / `setNickname`；
       - **步骤 1 刚补上的**：`hotLeadGateConfig` / `isAutoContactEnabled` /
         `activeWeekMaskFor` / 联系评论日上限 / `facebookRuleCommentBodyScheme`；
       - **步骤 2 刚补上的**：`facebookRuleModeDecision`
         （= 基线取用 + `decideFacebookBrowseMode` 纯函数 + 人设三态 + `ctx.controller.slowStartView()`）。

       **B. 批 G 才有 —— 一律做成必填注入口或能力二态，让编译器逼批 G 面对**
       | 口 | 单体里是谁 | 缺了会怎样（**都不是报错**） |
       | --- | --- | --- |
       | 评论调度器（`triggerManual` / `triggerTargeted`） | `commentScheduler` | 规则批次的加群+联系评论整段不发；热帖引流评论不触发 |
       | 评论人审端口（**能力二态**） | `commentApproval` + `commentApprovalEnabled` | 单体里 env 未开就整体不注入、评论**诚实跳过**；用 `undefined` 会与「接了但今天不可用」同形 |
       | 免审通知 | `notifyAutoApprovedComment` | 免审评论发出去但没人知道 |
       | 评论审批口径 | `resolveEffectiveCommentApprovalMode` | 审批模式判定缺失 |
       | 强制评论结果通知 | `notifyMandatoryCommentOutcome` | 同上 |
       | 联系评论统一安全闸 | `triggerGatedAutoComment` | 子上限 / 尝试审计 / `record('comment')` 时机三件一起没了 |
       | FB 规则模式运行时 | `facebookRuleModeRuntimeStore` | 规则批次视图与批次推进落不了账 |
       | FB 消费模式运行时 | `facebookConsumptionModeRuntimeStore`（5 方法） | 消费模式认领 / 下发 / 结算全断 |
       | FB 消费协调器 | `facebookConsumptionCoordinator` | 单体里缺它是**具名 throw**，照抄这个形状 |
       | 优质评论语料（**能力二态**） | `valuableCommentStore` | 缺则不接线（单体即如此），别做成静默空实现 |

       **三处开工即会撞上的踩点**：
       ① **角色人设注入 MUST 走取值口而不是快照**（构造期检查已在，漏传当场抛）；
       ② `facebookRuleModeDecision` 与规则批次的 `actionGate` **共用同一个决策闭包** ——
          MUST 按引用共用，别在 `actionGate` 里再算一遍（那是本 change 反复被咬的第二份实现形态）；
       ③ 规则模式那条降级（没配联系方式发普通评论）**放弃了两份已上线规格的 fail-closed 保证**、
          由运营显式裁定，且 `contactFallback` 与主审批模式是**两个独立字段**
          （沿用同一个等于把联系评论的免审外溢到普通评论正文）——搬运时逐字保留，别"顺手统一"。 -->

  别当例行搬运开工。** 勘察已做完（2026-08-01，源 `aidcp-cloud@534af19` 实读），下面是结论。
  <!-- **勘察结果（省下一手一次全量重查）**：
       工厂本体 = `src/server.ts` 的 `buildDispatcher`，**约 400 行**、向调度器传 **41 个顶层选项**
       （另有两组按条件展开：FB 规则模式 6 项、FB 消费模式 6 项）。
       调度器选项面本身有 **70 余个字段、几乎全是可选** —— 这正是 task 2.7 点名的
       「optional 参数是静默缺席的主要来源」的最大一处：漏传任何一项都不报错。

       **能直接接的（供给方今天就在本仓 / 组装根）**：停手闸（批 C）、模型出口（A-1）、
       节奏兜底与租约客户端与对边出口（批 D）、互动守卫与冷却闸（批 E 前半）、
       风控闸与当日剩余与去重账本（批 B/C）、概念池 / 精选写口 / 图内文字转写（内容客户端，已接线）、
       通知投递与联系人名册与联系评论台账（api 客户端）、单场与续场配置（本仓自有）、
       人设绑定三态与账号昵称（同步读镜像 / 账号主数据窄口）。

       **⚠️ 真正的坎：四个业务配置存储是 api 属主、且不在本仓**
       （`content-schedule-store` / `hot-lead-config-store` / `facebook-comment-config-store` /
       `facebook-operation-policy-store`，归属表逐条可查）。自动化段对它们有 **32 处引用**
       （排期 11 / FB 运营策略 13 / FB 评论配置 5 / 热帖阈值 3），**全部是同步热路径读**
       （`effectiveScheduleFor` / `resolveBaseForAccount` / `effectiveConfigFor` / `getGateConfig`）。

       **前三个有事实源、缺的是「有效值」那一段**：本仓同步读镜像已带 `content_schedule` /
       `hot_lead_config` / `facebook_comment_config` 三条消费流，但镜像给的是**快照**，
       而调度器要的是**按账号解析后的有效值**（含全局回落与就绪判定），那段逻辑住在 api 属主的存储里。

       **第四个连事实源都没有**：`facebook_operation_policy` **不在本仓的同步读消费流清单里**，
       而它读 8 张 api 属主表（accounts / client_environments / client_env_scope /
       facebook_operation_policy / facebook_operation_global_policy /
       facebook_primary_browse_surface_policy / facebook_rule_mode_environment_config /
       facebook_environment_slow_start_completion）**并写其中两张**
       （慢启动完成、全局策略审计）。它驱动的 `resolveFacebookOperationDecision`
       **决定整个 Facebook 浏览模式**——没有它，FB 账号会安静地永远不浏览。

       **✅ 用户 2026-08-01 已拍板：走路线 ①（析出纯判定段进 kernel）。裁定已落控制仓事实源
       `docs/cloud-service-decomposition-proposal.md` §4.7（与停手闸那条裁决并列）。**
       落地顺序：
       1. 前三个（排期 / 热帖阈值 / FB 评论配置）——事实源已在，析出「给定快照 + 账号 → 有效值」
          那一段进 kernel，api 侧存储改为调它、行为逐位不变、既有消费方一行不改；
       2. FB 运营策略——**析出之后仍要补一条同步读流**，否则本进程拿不到输入。这一件尚未开工；
       3. 工厂本体照批 D/F 的办法写，四个业务配置与评论域一律必填注入口 / 能力二态。

       **原三条路（保留供追溯）**：
       ① **析出纯判定段进 kernel**（3.1c 已走通的那条）：把「给定快照 + 账号 → 有效值」做成无状态函数，
          存储残壳留 api。对前三个成立；对第四个还要先解决事实源。
       ② **本仓按镜像自己再实现一遍解析** —— **MUST NOT**：这正是本 change 反复被咬的形态，
          第二份在写出来那一刻行为完全一致，要等两份漂开、且恰好在该拦住的那一刻才现形。
       ③ **跨进程问 api** —— 与 3.1c 的结论同理：同步热路径读，改成一次 HTTP 要动每个调用点的签名
          并给热路径加一跳网络；真要跨进程只能是「异步取源 + 本地镜像」，
          也就是给 `facebook_operation_policy` 补一条同步读流。

       **MUST NOT 做的**：给 FB 运营决策一个恒 `unsupported` / `blocked` 的实现把编译过掉。
       那不报错、只是让 Facebook 账号在本进程里永远不开始浏览 —— 本 change 红线点名的那种假成功。

       **不被这条挡住、可以先做的**：工厂本体照批 D/F 的办法写出来，把四个业务配置
       与评论域（评论调度器 / 人审端口 / 免审通知 / 联系评论闸，均属批 G）一律做成**必填注入口**
       或**能力二态**，让编译器逼后面那批面对。裁定只决定「谁来喂这个口」，不阻塞工厂本身交付。 -->
  <!-- **批 E 前半已落**（aidcp-automation ac09a7f）：每连接运行时。落点
       `src/automation-connection-runtime.ts` —— 连接运行时注册表（握手准入 → 建私有总线 →
       解析可写控制器 → welcome 提交 → 断连拆除）、互动去重守卫注册表、动作冷却兜底闸。
       **为什么切两半**：注册表是自洽的一块；而每连接角色调度器工厂是整段最密的一处
       （一个函数 400 余行、读写二十来个存储与策略，其中相当一部分供给方要到批 G 才有）。
       一次搬完必然停在编不过的中间态，**而这一批恰恰是批 D 与批 F 都在等的那个口**。
       调度器工厂做成**必填注入口**，后半缺席是编译期可见的 —— 与批 B 留给批 C 的办法一致。
       三条红线各有会真触发它的用例，变异三个逐条给出是哪条抓住的：
       缺账号标识必须拒绝握手（放过 = 一台配错的机器拿别人的账号动真实平台）；
       配置错误必须发得出去，且通知挂了不能连带把「握手被拒」一起吞掉（2 条红）；
       归属切换后 MUST 驱逐缓存控制器 —— 只重放计数会漏掉状态，陈旧的 normal 会盖回
       接管方刚写的 restricted，而那时归属谓词已通过、最后一道保护不再触发。
       **另有一条结构断言**：调度器工厂不许退化成可选。退化后 7 条行为用例全绿、只有它红 ——
       「后半还没接」与「这个账号今天没排期」在行为上完全同形。
       **仍未做（批 E 后半）**：每连接角色调度器工厂本身。
       验收：typecheck 干净；acceptance 145/145；全量 2040 pass / 0 fail；六仓对账零漂移。 -->
  <!-- **批 F 已落**（aidcp-automation 613338a）：发布下发与陪伴界面。落点
       `src/automation-publish-dispatch.ts` —— 界面快照层、当日用量装配、浏览器待机提示、
       发布下发器、定时发布对账器、下发触发受理口，外加驳回 / 前置检查 / 预览刷新三个闭包。
       定时器不在本批起：`start()` 留给进程入口在就绪闸之后调。
       **一个必填口交给批 E**（本轮会话用量 / 续场闸裁决）。单体那句 `ctx.runtimes?.… ?? null`
       在单体里走不到、拆开之后是常态：读不到就把「本轮会话」整段静静抹掉，日志一行没有。
       它**挂在批 D 那个端口上、不另立第二个接口** —— 批 E 供的本来就是同一个注册表实例，
       拆成两个接口的唯一后果是它可能供出两个不同实例，那种错不报错、只是数字对不上。
       四条红线各有会真触发它的用例，变异六个逐条给出是哪条抓住的：
       素材端口做成能力二态（类型上可选、漏传不报错，代价是三个写静默消失）；
       驳回路径直调素材端口（不走下发器那个窄口，只改窄口会漏掉它）；
       平台投影永远是最后一步（顺序颠倒算出「0/0 今日计划已完成」）；
       兜底扫描只认已批准的发布稿（评论授权混进来会把窗口永久占满）。
       **另有一条结构断言：本模块不许整体类型逃逸。** 本批实测踩过一次 ——
       手抄的存储契约漏四个字段、返回类型宽一档，全靠去掉 `as never` 才现形；
       现在存储契约直接取下发器自己那一份，本文件零强转。
       **四样刻意不构造**（构造条件在单体里就写着「非自动化模式」）：草稿精修工作器、
       发布授权 outbox 中继、待下发看门狗、客户端内审批与删图处理器 —— 后两样在本进程里的
       调用点已按模式改指接口进程的远程口（批 D 的消息处理器），本进程零读者。
       顺带：批 B 的底座暴露 `riskStore`（本批按窗口读计数，取注册表用的那一个实例、不另建）。
       验收：typecheck 干净（零强转）；acceptance 137/137；全量 2032 pass / 0 fail；六仓对账零漂移。 -->
  <!-- **批 D 已落**（aidcp-automation ff44774）：边缘接入。落点 `src/automation-edge-access.ts`
       ——验证码协助与协调、指令定序器、边缘任务租约客户端、消息处理器、边-云 WebSocket 服务端，
       外加成对指令接收器要的那份依赖（`edgeResumeDeps`）。**监听不在本批起**：`start()` 留给
       进程入口在就绪闸之后调（批 H），fail-closed 入口一个字没动。
       **三个必填端口逼后面的批次面对**：每连接运行时（批 E）/ 陪伴界面快照（批 F）/
       互动能力（批 B/G，做成**二态**——`unavailable` MUST 带具名理由，
       用 `undefined` 表示会与「接了但今天不可用」同形）。
       四条红线各有会真触发它的用例，变异五个逐条给出是哪条抓住的：
       出口闸把 unknown 当 blocked → 3 条红（其中租约归还那条是承重的：扣住它槽位永不释放）；
       暂停态漏接 → 1 条；断连不失效在途发布指令 → 1 条；互动缺席不吭声 → 1 条。
       **另有一条结构断言**：`unknown` 档的豁免名单只许有一份（按引用取 kernel）。
       塞第二份进去时**7 条行为用例全绿、typecheck 也绿**，只有它红——§4.2b 那条原理在本批复现。
       **两件本批实读得到的事实**：
       ① 锚点缓存的 `close()` 内部是 `pool.end()`，而池是注入进来的共享属主池 ⇒
          关停路径 MUST NOT 调它（会连带打死本进程其余十几个存储）。与批 B 启动期告警池同一条坑。
       ② 本批**零新增消息类型**，故 CLAUDE §2 第 4 处同步（边缘侧主动命令路由白名单）
          本批无新增项；`AC-PROTO-*` 全过（消息类型总数仍 94）。
       验收：typecheck 干净；acceptance 129/129；全量 2024 pass / 0 fail；六仓对账零漂移。 -->
  <!-- **批 D 顺带改判一条批 A 的裁定**（aidcp-automation ff44774）：
       判据清单里 `accountPersonaService` 由 `construct` 改 `skip`。
       实读证据：生成器只在 monolith / core 两种模式下建，自动化模式下它恒 undefined，
       人设端口取的是接口进程那个 HTTP 客户端；原判写的「构造后立刻喂进本段的人设端口表」
       描述的是单体那一支，而那一支在自动化进程里根本不执行。与 `personaAutoFill` 同形。
       **不是能力消失**：人设读写照常，只是走跨进程通道。分组统计由用例算出，无手打计数要跟。 -->
  <!-- **批 B 已落**（aidcp-automation 4d3fb89）：风控单写者与告警底座
       （`src/automation-risk-foundation.ts`——写者锁 → 风控存储 → 注册表 → 三个互动存储 + 告警存储）。
       **形态定了：每一批都写成可单测的工厂，不写进 `main()`。** 写进 main() 就只能等本条做完，
       而这些装配本身与 main() 无关。批 E/F/G 照此办，最后 main() 只是把它们串起来。
       两个刻意必填、无默认的口留给批 C（配置副本陈旧 / 记账断链）；
       抢不到写者锁的具名错误留给批 H 映射成非零码退出。 -->
  <!-- aidcp-automation 6035fa4 批 A 已落**外壳**（`src/automation-service-entry.ts`）：
       读配置 → 建根 → 先监听 → 就绪闸 → 放行业务 → 优雅关停 → 信号处理。
       **本条仍未完成**：外壳里一行业务代码都没有，运行时依赖与业务入口是必填参数、
       今天只有测试在喂。批 B…G 逐批补真实供给方（切批方案见 HANDOFF §9）。
       可执行入口 `runAutomationEntry()` 一个字没动，照旧 fail-closed —— 保护罩留到批 H。 -->
- [x] 3.2 启动 readiness gate 与 api 同形：同步读镜像首次装载完成、readiness 到 `ready` 之前
  **不放行业务入口**。
  <!-- aidcp-automation 6035fa4 批 A。四个要点全落 + 各有用例：三条早退条件（正在关闭 /
       已经启过 / readiness 不是 ready）、**在途 promise 去重**、周期表 unref、先 listen 再放行。
       探活路由 `internal/automation/sync-read/readiness` 把「业务入口放行了没有」与就绪度**分开报**——
       「监听着但没放行业务」这个中间态必须可观测，否则运维只看到端口通。
       变异实测（哪条抓住的，不只是会不会红）：删就绪闸 → 2 条红；探活不报放行状态 → 2 条红；
       **删在途去重只留布尔 → 只有专为它写的那条红**；**关停不等在途放行落地 → 一开始 6 条全绿**，
       补了会真触发的那条才显形（注释里写明「别当冗余删掉」）。
       **口径**：闸的形状与行为已交付并验过，被闸住的那个业务入口今天是注入进去的；
       真业务入口到批 B…G 才有，届时不必重做本条，但要确认没被绕过。 -->
- [ ] 3.3 缺依赖时**停在具名原因上**：MUST NOT 用空数组 / `false` / 未绑定 / 代码默认放行。
  现在那个 fail-closed 壳守的东西，接线后必须仍然守得住——为此写回归用例。
  <!-- 批 A 只做了「让编译器逼你面对」那一半：外壳的运行时依赖与业务入口都是必填参数、无缺省，
       配置缺项照旧具名抛错。真正的回归用例（台账非空时仍拒绝启动）属批 H，见 4.3。 -->
- [ ] 3.1c-裁定 **用户 2026-08-01 选定路线 A（改判归属 / 析出纯判断段）。⚠️ 实读后只有「析出纯段」那一支成立，
  「整文件改判」被证据否掉，开工前必读这段。**
  <!-- **整文件改判不成立的证据**：新鲜度查询口在单体里有 **7 个 api 属主消费方**直接 import
       （账号状态、客户身份存储、镜像刷新器、镜像描述表等）。整份挪走会当场造出 7 条跨域边，
       而棘轮只许下降。⇒ 那三份文件**留 api 是对的**。

       **真正的形状（这才是路线 A 的可行支）**，三条实测支撑它：
       ① **契约早已在 kernel**：`ConfigMirrorKey` / `MirrorReadState` / `ConfigMirrorFreshnessSource` /
          `ConfigMirrorGatePort` 全在 kernel，那三份 api 文件只是等值再导出 + 实现。
          自动化仓的四个消费方（消息处理器 / 角色调度器 / 风控控制器与注册表）**已经只持端口**，形态本来就对。
       ② **api 属主那一判是「临时」的，不是定论**：归属表里那条 basis 逐字写着「【待定稿裁决】…
          按配置域默认落 api…**请求回写 §4.7 见 docpatch R1**」。也就是说它**从没在事实源里裁定过**。
          ⇒ 这不是推翻一条深思熟虑的裁定，是**把一条一直挂着的临时判做完**。
       ③ **可析出的纯段确实存在**：新鲜度模块 77 行里，真正是判定的只有两条 fail-safe 策略
          （未安装事实源 → fresh；事实源抛了 → 按 stale 收敛）。**挡住它进 kernel 的只有一样东西**：
          模块级可变单例 `installedSource`（那条 basis 自己也点名了这一点）。
          把「给定一个 source → 四个方法」做成**无状态工厂**进 kernel，那个 ambient 槽位留 api，
          两边都不动消费方 —— 与本 change 反复用的「析出纯段、残壳留原处」判例同形。

       **落地顺序（第 1 / 2 / 4 步已完成，2026-08-01；第 3 步留给批 C）**：
       1. ✅ 控制仓事实源 §4.7 已落这条裁定（含挡住整份进 kernel 的两条具体理由、
          镜像键清单按进程各自给的理由、以及刷新器不动的理由与它带出的记账缺口）；
       2. ✅ kernel 加无状态工厂（cloud `391f77d` → kernel `6599b80`）；单体那两份改为调它，
          **行为逐位不变、7 个 api 消费方一行未改**。两条 fail-safe 策略从此只有一份定义，
          变异逐条验过：抛错兜成 fresh → 1 条红；未装当 stale → 2 条红；
          只读裁决顺手记账 → 1 条红；事实源构造期取快照（秒级回滚开关失效）→ 1 条红。
       3. ✅ **已做（automation `089e2cc`）——但先读这条更正**：
          上面那句「它缺的不是工厂，是事实源」**是错的**。本仓的同步读镜像早就带了一个
          按进程的事实源（`AutomationSyncReadMirrors#configFreshnessRuntime`，实现 kernel 的
          `ConfigMirrorFreshnessSource`）。真实状况是**它建好了却零消费方**——
          全仓只有定义它的那个文件提到它。**⇒ 根本不需要把 api 的刷新器搬过来。**
          单体那套（版本表 + 轮询刷新器）解决的是「一个进程里的 15 份内存副本何时过期」；
          三等分之后，本进程持有的配置副本**就是**那几条同步读消费流，它们各自带
          `freshUntil` 与就绪态。实测吻合：闸门档的键与本进程的消费流几乎一一对应
          （两个环境类键共用环境流；参数档不参与停手）。
          落点 `src/automation-config-mirror-gate.ts`，只做两件属于本进程的事，各有变异验过的用例：
          **闸门键清单**（混进本进程没有的键 → 镜像对认不出的键一律答 stale ⇒ 本进程被永久停手；
          混进参数档 → 把「只告警」升级成「停手」）、**拒绝落账**（没有落账口时具名留痕 + 自己计数，
          MUST NOT 静默 no-op —— 镜像自带的那个默认参数正是一个静默 no-op，已显式接管）。
          **仍未接线的最后一跳**：把 `gate.isStale` 喂给批 B 那个必填口，属批 H 的 `main()`。
       4. ✅ pin 链已按 kernel → transport → 三个业务仓的顺序抬完，六仓对账零漂移。
          **api / content / automation 三份 `ownership-rules.json` 无需改动**：
          kernel 文件不派生进业务仓，它们的生成器按本仓实际文件收窄。
          （automation 那份 `kernel-non-members.json` 是 57 条 vs 单体 106 条的**既有分叉**，
          与本次无关、已登记在 0.7c，MUST NOT 顺手"对齐"——那正是 §8.2 禁的整体重序列化。）
       **仍然 MUST NOT**：给自动化侧的 `mirrorStale` 一个恒 false 的实现把编译过掉。 -->
- [x] 3.1c ~~**⚠️ 批 C 的一半被归属挡住了**~~ **—— 归属问题已消解，不需要裁定（2026-08-02 复核）。**
  <!-- **这条不是"选了三条路之一"，是前提本身错了。** 原判据说「自动化侧缺新鲜度事实源」——
       实读发现本仓的同步读镜像**早就带了一个按进程的事实源**（`configFreshnessRuntime`，
       实现 kernel 的 `ConfigMirrorFreshnessSource`），只是**建好了零消费方**。
       ⇒ 不需要改判归属、不需要再加一条镜像、也不需要接口进程推结论：把已有的那套接到停手闸上即可。
       落点 `src/automation-config-mirror-gate.ts`（批 C 停手闸，automation `089e2cc`）。
       判定逻辑一个字都不在本仓：两条 fail-safe 策略单写在 kernel 工厂里，与 api 侧那两份同源；
       本模块只负责「哪些键在本进程算闸门档」与「因陈旧而拒绝记到哪去」。
       与其余各批同形：已交付、**未接进 `main()`**（那属批 H）。
       **这正是那条通用教训的又一例**：下「缺一个机制」的判断前先 grep ——
       在这个项目里「建好没人用」比「缺东西」更常见。 -->
  配置副本停手闸的**契约在 kernel**（`ConfigMirrorGatePort`），本仓的三个消费方
  （消息处理器 / 角色调度器 / 风控控制器与注册表）都已经只持这个端口，形态是对的。
  **但它的实现三件套全是 api 属主、且不在本仓**：`src/config-mirror-freshness.ts`、
  `src/config/mirror-stop-work.ts`、`src/config/mirror-refresher.ts`（三份在 cloud 的归属表里都是 api）。
  <!-- **为什么这不是「搬过来就行」**：
       ① `isStale` 是**同步**读、且在每次动作准入的热路径上 —— 跨进程要一次 HTTP 就得改掉每个调用点的
          签名，还给热路径加一跳网络。真要跨进程只能是「异步取源 + 本地镜像」（与角色模型解析同形）。
       ② **本进程恰恰是 `automation_config_mirror_health` 这条属主流的发布方**
          （见 `AUTOMATION_SYNC_READ_OWNER_STREAMS` 与 `AutomationRuntimeHandles.syncReadSources`）。
          「健康报告的发布者拿不到新鲜度事实源」这件事本身就说明归属需要重判，不是接线不够。
       ③ **今天的缺省正是批 B 拒绝接受的那种**：本仓消息处理器上写着
          「未注入 = 恒不陈旧」。也就是说，不裁定就接线的话，自动化进程会静静地宣称
          「配置副本永远新鲜」——不报错、只是把该停手的动作放过去。
          批 B 已经把这条口做成**必填、无默认**（`mirrorStale`），所以这个洞今天是**编译期可见**的，
          不会被悄悄跳过。
       **三条路，需拍板（与 A-4 同一类问题：归属裁定，不是编码）**：
       ① 把这三份（或其中的纯判定段）改判 / 析出到 automation 或 kernel；
       ② 保留 api 属主，本仓按「异步取源 + 本地镜像」再加一条同步读镜像（形态照角色模型那条）；
       ③ 由接口进程把停手结论随已有的某条通道推过来。
       **MUST NOT 做的**：给 `mirrorStale` 一个恒 false 的实现把编译过掉。 -->
- [x] 3.1d 批 C 的**另一半可以先做**（不被 3.1c 挡）：记账 outbox 与对账器、风控指令消费者、
  `event_outbox` 保留期剪裁、面板事件投递、配置面审计中继。
  <!-- aidcp-automation 6958e55。落点 `src/automation-risk-accounting.ts`。
       **批 B 那两个必填口至此都有真实现了**（配置副本陈旧 ← 3.1c 第 3 步；记账断链 ← 本条）。
       三条不许降级的各有会真触发它的用例，变异五个逐条给出是哪条抓住的：
       起不来时不告警 / 漏斗活着仍落回 controller（会记两次账）/ 记账起不来连剪裁一起不启。
       **两条结构断言**，因为它们守的东西行为测试原理上看不见：
       ① outbox 与风控存储 MUST 同一个池——exactly-once 靠计数表那条唯一索引 + 单事务，
          分居两库时索引管不到对方，**零报错、只是不再 exactly-once**；
       ② 承重命令主题 MUST NOT 设兜底强删——要断的是某个字段**不在**配置里，
          而「不在」在行为上什么都不表现，直到某天一条没被应用的命令被删掉。
       **一处刻意的不对称**：记账不过归属闸（计数表是既成事实账本，归属刚变更时飞在半路的回执
       仍要记进同一本账——分裂的是写权限，不分裂的是事实）。
       **仍未做**：面板事件投递客户端与配置面审计中继（后者写的是接口属主表，
       跨进程后 MUST 走已有通道、别直连），以及风控指令消费者的接线。 -->
  <!-- 这半边的料本仓都有（`src/risk/risk-accounting.ts`、`src/transport/event-outbox.ts`、
       `risk-command-outbox.ts`、`eventbus-outbox-bridge.ts`、`outbox-health.ts`、`outbox-notify-listener.ts`）。
       它供的是批 B 留下的另一个必填口 `accountingBlocked`。
       **两个踩点照抄 §9.2**：`event_outbox` 是队列不是账本，剪裁不接就只进不出；
       配置面审计中继写的是**接口属主表**，跨进程后必须走已有的那条通道，别直连。 -->
- [ ] 3.4 持久任务仍按 `AIDCP_DEPLOY_ENV` 写 `execution_target`；target 缺失或非法时
  **不启动那个 worker**。
- [x] 3.5 逐段对着 cloud `segCAutomation` 核对装配清单，确认没有「本进程里根本没有消费者」的对象
  被顺带 new 出来（判据：先问它的结果在本进程有没有去处）。
  <!-- aidcp-automation 6035fa4 + aidcp-cloud f83e266 批 A。
       清单落在 `aidcp-automation/src/automation-segc-export-disposition.ts`，**41 条逐条判**，
       源 `aidcp-cloud@f489e5e` 实读。结论：**construct 34 / skip 2 / open 5**。
       预排批次：B 5 / C 1 / D 6 / E 2 / F 16 / G 6 / H 5。

       **判据被拆成两个字段，不是一个**：「本进程内有消费者」与「构造只为答别的进程」。
       后者 MUST 显式声明（`servesOtherProcess`），因为这两者不等价 —— A-3 已出过反例
       （接口进程为答内容进程建了四个自己没消费者的读取器，那是对的）。
       今天唯一走这条例外的是 `dispatchActivityForPanel`：本进程是那个布尔的唯一持有者，
       接口进程只能问过来，通道（运营指令读写）已接线。

       **skip 2 条不是省事，是照抄既有裁定**：`personaAutoFill` 与 `publishUiUpdateCommand`
       在单体里的构造条件逐字写着「非自动化模式」，自动化进程从来就没有它们。改成构造
       等于悄悄改变了模式行为。

       **另记两条没人写下来的**：`resolveController` 与 `triggerPublishDispatchOnApprove`
       的**导出面今天没有任何读者**（接口服务段各有自己的本地实现）⇒ 本包只要本地函数，
       不必再导出一遍。

       **机械信号刻意放在 cloud 侧**：`aidcp-cloud/test/acceptance/segc-export-face.test.ts`
       （AC-SEGC-FACE）现场解析自动化段导出面并与钉死名单比对。理由是 §4.7 那条教训——
       派生仓的手抄件拿不到中控侧任何信号；判据的来源只在 cloud 存在，闸就该在那边。
       本包侧另有四条自洽不变量（construct 必须有去处 / skip 必须真没消费者 /
       例外必须显式 / open 一律排批 H），变异逐条验过、各由对应那条抓住。
       **两侧都证明不了那 41 条裁定本身对不对** —— 裁定是人读出来的，AC-SEGC-FACE 红的时候
       要做的是重判那条句柄的去处，不是改名单让它变绿。 -->
- [ ] 3.5a **批 H 的现成工作清单**：判据清单里 5 条 `open` 逐条裁定，一条都不许留空。
  **✅ 裁定已由用户 2026-08-02 拍板：五条全部走路 ②（装配移到接口进程），自动化侧一律记
  `skip`**，措辞照抄 `accountPersonaService` 判例（不是能力消失，是属主在接口进程）。
  <!-- ⚠️ **先更正原注释里一条贯穿全清单、而且是错的前提**：原文写「通道今天不存在」——
       **不成立**。两个方向的跨进程通道都早已存在且部署参数都配好了：
       api → automation 见 `aidcp-cloud/src/server.ts:1888` `startAutomationInternalApi()`
       （已注册约 15 组路由），客户端侧 `src/server.ts:8712`；automation → api 见
       `src/server.ts:4404-4434` 的 15 个 HTTP 客户端。**真正缺的只是各自那一条 route。**
       这条更正直接改变了两条路的成本对比 —— 而它正是「文档里的现状判断没有任何机械手段
       会复核它」那条教训的第二次应验（第一次是协调器那条，见 HANDOFF 已作废段）。

       **逐条依据（实读，`aidcp-cloud` 侧行号）**：

       | 条目 | 读谁的数据 | 消费方 | 要不要本进程运行时状态 | 裁定 |
       | --- | --- | --- | --- | --- |
       | `interactionCustomerApi`（`server.ts:6272`） | automation 互动表 **+ api 的 `client_users`/`client_environments`** | 只有 `server.ts:10258` → client-auth（**目录只存在于 api 仓**） | 要（边-云服务端 + 风控 registry） | ② |
       | `interactionInternalApi`（`server.ts:6264`） | 10 条路由里 8 条纯 api 属主配置表 | 只有 `server.ts:9516` → panel（**只在 api 仓**） | 只有一条运行控制下发 | ② |
       | `interactionPermissionOverview`（`server.ts:6228`） | **零张表**（两个输入都是 env 纯解析） | 只有 `server.ts:9521` → panel | **完全不要** | ② |
       | `listAccountAutomationCatalog`（`server.ts:4937`） | 混：5 张 api 属主表 + 4 类 automation 事实 | 只有 `server.ts:9688` → panel | 要三样，**其中两样已有端口** | ② |
       | `rolePromptProvider`（`server.ts:8437`） | 几乎不读表；角色实例来自 automation、发布预览表在 **content** | 只有 `server.ts:9895` → panel | 要（但只是**预览专用**的独立实例，无副作用） | ②+① 混合 |

       **三条是结构性不可行、不只是成本高**：`interactionCustomerApi` / `interactionInternalApi` /
       `listAccountAutomationCatalog` 若留在自动化侧算，就要读 api 属主表 ⇒ 撞 `AC-OWN-06`，
       而那条**没有豁免通道**（`import-exemptions.frozenTotal` 现为 0）。

       **两条已有的现成判例，别重新发明**：`server.ts:9695-9706` 的 `setJoinGroupAutomation`
       已经在接口段**纯用端口**算出了目录的单账号形态（批量形态就是它）；`server.ts:9458-9460`
       已经写着「面板用户名单在 segB/segC 才解析 ⇒ api 模式就地按同一 env 重解析」，
       与权限总览那条逐字同构。

       **`interactionPermissionOverview` 零成本、可立刻清**：零表、零运行时状态，两个输入
       （`AIDCP_PANEL_USERS` / `AIDCP_INTERACTION_PANEL_GRANTS`）都是三服务共用的同一份 `.env`。
       **别跟互动那两条捆在一起**，捆了就被最重的那条拖住。

       **`rolePromptProvider` 必须混合，纯 ② 会造成真能力消失**：角色目录 40 条里 20 条是浏览类，
       其中**只有 1 条**在 api 侧有静态预览，另 19 条要真实角色实例去渲染，而那 48 个角色类
       **只存在于 `aidcp-automation/src/agents/`**（api 仓 `agents/` 下只有一个文件）。
       ⇒ 壳在接口进程，浏览那一支向自动化进程要「已渲染的预览」。**还有一个原清单没记的
       第三方**：发布预览的两张 builder 表只存在于 `aidcp-content/src/` —— 这条句柄实际横跨
       三个属主，接口进程要么再向 content 取一条 route，要么把那两张表另行归属。
       与 `server.ts:8606-8607` 已写下的裁定一致（「它们构造时真依赖预览调度器 / 风控控制器 /
       边缘服务端 —— 那些要走端口，不是搬家」）。

       **两个附带的归属动作，别漏**：
       ① `decideFacebookBrowseMode`（`src/orchestrator/facebook-rule-mode.ts:44`）判 automation
          但是纯函数（入参全普通值、无 IO、无定时器）⇒ 按 §8.4 应析出 kernel，目录那条才算干净；
       ② `prompts-preview.ts` 的两张 builder 表在 content（P4-7 只把它做成「组合根注入」，
          单体里够用，拆进程后注入源没了）。

       **⚠️ 落地时会当场变红的机械检查**：五条改判 `skip` 后，新加到自动化段导出面的那几个
       端口句柄会让导出面从 41 条变化 ⇒ `aidcp-cloud/test/acceptance/segc-export-face.test.ts`
       （AC-SEGC-FACE）当场红。**那时要做的是同步名单并重判新句柄的去处，不是改名单让它变绿。** -->
- [ ] 3.5b **五条裁定的落地**（3.5a 只是裁定，这条是干活）：接口侧装配 + 四条新窄 route
  + 两个附带归属动作。**权限总览那条零成本、可单独先清**，其余四条按上表分组。
- [x] 3.5c **启动前置三件之二**（与裁定无关，先落）：关停真空 + 属主池透传。
  <!-- aidcp-automation fc99d52。
       ① **关停真空**：`stop()` 按约定只在业务放行过之后才跑，但三样东西在**工厂构造期**
          就已占住资源——风控写者锁（靠会话保活）、记账漏斗三张周期表、模型出口的角色模型轮询。
          「同步读一直不就绪 → 收到终止信号」这条路径上它们全部泄漏。写者锁最重：
          下一个自动化进程等锁超时会**直接拒绝启动**，现象出在新进程、根因在上一个进程的
          关停路径。业务入口因此加**必填** `dispose()`，无条件调用一次，排在 `stop()` 之后、
          `root.close()` 之前（那三样用的是本进程的属主池与连接，晚于根关停就没得还了）。
          必填无缺省的价值当场兑现：改完编译器点名三处内联夹具。
       ② **属主池透传**：外壳此前不转发 `ownerPool` ⇒ 组装根必然自建一个池，而业务入口那
          十几个工厂要的是**同一个**属主池。两条各自建池都能跑、都不报错、本仓零断言。
          透传后关停责任随之转移（`ownsPool === false` ⇒ 根不再关它）。
       变异逐条给出是哪条抓住的：归还改成「只在放行过之后才做」→ 3 条红（含新写的专用用例）；
       去掉属主池透传 → **只有**新写的那条红，**typecheck 全程绿**（该参数可选，编译器对此
       完全沉默）——这正是它必须配行为用例的理由。
       typecheck 干净；全量 2118 pass / 0 fail（基线 2116）。 -->
- [ ] 3.5d **启动前置三件之三：schema 契约门**。⚠️ **自动化仓今天一个调用点都没有**
  （`src/schema/schema-gate.ts:258` 有完整实现，两个测试文件在用，**`src/` 下零调用点**，已实测复核）。
  <!-- **照 content 办，MUST NOT 照 api 办**：
       - content `aidcp-content/src/server.ts:307-314` 把门放在**建池之前**，裸 await、无 try/catch，
         失败 → `process.exit(1)` → systemd 重启语义成立；
       - api **没有这道门**，改用逐存储 schemaEnsurer，且在建池**之后**；更坏的是
         `buildApiCompositionRoot()` 在 `:1531` 被裸 await 而 try/catch 从 `:1611` 才开始
         ⇒ 关停不可达 ⇒ `:998` 建的池永不 `end()`，入口又只设 `exitCode` 不调 `exit`
         ⇒ **进程很可能不退出**，systemd 看到的是 `active (running)` 的僵尸，既不服务也不重启。
       落点：`main()` 第一句、建池之前。`runSchemaContractGate({ owners: ['automation'] })`
       —— 本进程只连 automation 库，就没有立场声称别的库的 schema 对不对（`schema-gate.ts:274-276`）。
       **不需要**像 content 那样显式传路径：本仓有自己的 `migrations/`（57 个）与
       `boundaries/table-ownership.json`，默认基准 `src/schema/../..` 正好是仓根。
       **MUST NOT 包 try/catch**（文件头 :256 明写）。
       小坑：这份派生副本的日志前缀仍是 `[aidcp-cloud] schema 契约门…`（:284 / :316）。 -->
- [ ] 3.5e **Facebook 慢启动参数进同步读流**（**用户 2026-08-02 拍板：加进数据流，不走回落默认**）。
  <!-- 现状：风控的养号事实口有四项，前三项（平台 / 建号时间 / 慢启动起点与毕业时间）
       同步读镜像**已有现成取用口**（`transport/automation-sync-read-mirrors.ts` 的
       `accountFor()` 与 `slowStartForAccount()`）；**第四项 `facebookSlowStartPolicy`
       （爬坡总天数 + 逐日上限）不在任何流的载荷里**——`facebook_operation_policy` 流发的是
       逐环境基线投影，`reels.slowStart` 只有 `viewsPerFollow`。
       属主侧有现成合成口 `facebook-operation-policy-store.ts:943` `slowStartRuntimePolicy()`，
       符合「发成品不发原始表」的既有口径。
       ⚠️ **形状要先想清楚**：那个合成口是**全局**的，而基线投影是**逐环境**的——
       别顺手往每个环境行里塞一份重复值，先定它落在信封的哪一层。
       ✅ **改动面已查清（2026-08-03 实读，`aidcp-cloud` 相对路径），比预想干净**：

       | # | 文件:符号 | 改什么 |
       | --- | --- | --- |
       | 1 | `src/kernel/sync-read-facts.ts:171` `FacebookOperationPolicySnapshot` | 顶层加 `slowStart` 兄弟字段。**它是全局的、不是逐环境的** —— MUST NOT 往每个环境行里塞重复值 |
       | 2 | 同上 `:409` 的 `hasExactKeys(value, ['environments'])` | 改成两个键 + 给 `slowStart` 写形状校验。**这道精确键集闸正是当初炸出「载荷不合法」那次的机制**，它会替你抓住漏改 |
       | 3 | `src/config/api-sync-read-source.ts:59` `FacebookOperationPolicyBaselineStore` | 加 `slowStartRuntimePolicy()`；`:85` 的合成处一并带出成品 |
       | 4 | `src/transport/automation-sync-read-mirrors.ts` | 加取用口（消费侧） |
       | 5 | kernel 那份**手写夹具** | 照类型手写的、键数写死 ⇒ 必红。见下 |

       **两条让这次比前三次省事的事实**（别按旧经验高估风险）：
       - 配额类型 `ActionQuota` **已经在 kernel**（`src/kernel/risk-contract.ts:17`），
         载荷类型直接用它即可，不必搬运也不必手抄第二份；
       - 本次**不新增同步读流、只在既有流的载荷里加一个字段** ⇒ HANDOFF 那张「连挂三次」表里的
         三处（组装根自举流名单 / 迁移 CHECK 约束的流名清单 / 流注册表条数）**本次都不涉及**。
       ⚠️ **仍会咬人的是第 2 类**：手写夹具证明的是「契约自洽」不是「真产出物符合契约」。
       ⇒ 键集不变量 MUST 用**生产者的真输出**过**真校验器**，别只改夹具让它变绿。

       **属主侧现成合成口**：`src/config/facebook-operation-policy-store.ts:943`
       `slowStartRuntimePolicy()`（读进程内 `globalPolicy`，缺配置时回落 `defaultGlobalPolicy`）。
       ⚠️ 它**缺配置时会回落编译默认而不是抛** —— 发布前想清楚：这条回落在单进程里无害
       （属主自己就是那份配置的家），跨进程后会变成「自动化侧收到一份看着正常的默认曲线」。
       与「MUST NOT 回落空表」那条同源，处置方向要一致。
       ⚠️ **另一条方向性红线（与本条同一个口，别忘）**：镜像没到位 / 陈旧时，
       养号事实 **MUST NOT 喂空**。喂空 = 告诉风控「这个号没在慢启动」，一个还在爬坡的
       新号会直接按满档跑且不报错。单体里的正解是接到停手闸上、取**最保守的第 1 天**
       （`risk-controller.ts:428,455`）。 -->
- [ ] 3.5f **互动能力二态口接通**（**用户 2026-08-02 拍板：这一批就接通，不走具名缺席**）。
  <!-- 它是批 D 留在 `AutomationEdgeAccessOptions` 上的第三个必填口，二态：
       `wired` 带 port / `unavailable` 带具名理由。三个子件在单体里的锚点：
       收件箱 `server.ts:5372-5388`、运行时开关 `server.ts:6044-6055`、
       握手后恢复编排 `server.ts:6156-6180`（边缘注册回调内的那段）。
       表基本都在 automation 属主（`interaction_feed` / `_reply_jobs` / `_offboards` /
       `_runtime_controls` 等），照 `server.ts:5310-5388` + `6212-6224` 的顺序在本进程建。

       **接通那一支要新建两样今天不存在的东西**：
       ① `hasPendingRevocationHold` 读 `client_env_revocation_holds`（**api 属主**），
          而 4a 端口清单里没有它 ⇒ 要新开一条 api 窄端口。**MUST NOT 直调属主存储**，
          也 MUST NOT 吞成 false（`client-user-store.ts:3401-3405` 明写失败方向必须是抛）；
       ② 回复生成能力只能从 content 客户端取，取不到则**整条不组装**
          （单体 `server.ts:5345-5362` 就是这么写的，注释明写「塞空壳进去才是灾难」）。

       **`unavailable` 分支仍必须保留且理由具名**，至少五个：schema 缺失 / schema 半迁移 /
       回复配置解析器不可用 / 回复生成不可用 / 新端口缺席。
       **红线：整体缺席，不得半截可用** —— 单体回落处（`server.ts:5455-5471`）是把八个变量
       **一起**置空的；半截可用会让下游能力位发得不一致。 -->
- [ ] 3.5g **批 H 主体接线**：12 个工厂接进组装根，写 `main()`。
  <!-- 实读得到的三件事，开工前必读（`aidcp-automation/src/` 相对路径）：

       **① 14 个口今天还空着**（编译器点名 / 或必须由 `main()` 现造）：
       组装根的 `runtime.facebookScope` 与 `runtime.syncReadSources`（无任何工厂供给）、
       边缘接入的 `interaction`（→ 3.5f）、发布下发的 `media`、调度器的 `textCardTranscriber` /
       `roleFactories` / `sessionLimitProvider` / `resumeConfigProvider` / `isDispatchActive` /
       `onSessionRejected`、业务配置的 `globalActiveWeekMask`、模型出口的 `apiHttp`
       （组装根内部建了两个但都没暴露）、评论调度器的 `facebookStores` 四件与
       `scheduledTaskFeedback`（**签名不匹配**：口要同步、客户端是异步 ⇒ 要写转接）、
       两处的 `groupCommentPolicy`（**用户已裁定暂不接**，必须显式传具名缺席）。

       **② 三处真环，不是排序能解决的**，一律用晚绑定薄壳破：
       风控底座 ↔ 记账漏斗；边缘接入 ↔ 每连接运行时 ↔ 调度器工厂；组装根 ↔ 边缘/发布。
       第三处尤其要注意：`syncReadSources` 是组装根的**构造入参**不是事后注入，
       而它的五个供给方里有三个（发布在途 / 验证码可用性 / 配置副本健康）住在工厂身上。

       **③ 两个工厂在构造期就起定时器**（与本 change「定时器不在构造期起」的约定不一致，
       不是缺陷但必须知道）：记账漏斗三张、模型出口一张。它们的归还靠 3.5c 那个 `dispose()`。

       **⚠️ 一个会静默吃掉能力的形状**：调度器那张依赖表里有 8~11 个字段写成裸
       `RoleDispatcherOptions['x']`（不带 `NonNullable`）—— **编译器只逼你写出字段名、
       不逼你给真值**，塞 `undefined` 全程绿灯，跑起来就是那条能力无声消失。逐条对着供需表核。

       **⚠️ 两处重复实例风险**：发布下发工厂内部**私建**了一个会话配置存储且不对外暴露
       （`automation-publish-dispatch.ts:365`），而 `sessionLimitProvider` 与
       `globalActiveWeekMask` 要的是同一个实例；照现状接会让进程里存在两份、各持一套缓存，
       **两边都不报错**。

       **⚠️ 关停时逐条对着 close 语义表写**，关错打死整个进程：裸 `pool.end()` 那一族
       （锚点缓存 / 群目标 / 群成员 / 加群审计 / 告警 / 点赞 / 有价值评论 / 互动 feed /
       群路由 / 委托任务存储）**禁止调**；`ownsPool` / `ownedPool?` 守卫那一族安全。

       **⚠️ 别照抄单体自动化模式的启动顺序**：单体是**先开边缘口、后装同步读**
       （`server.ts:7628` vs `:1906`），与本 change 要求的顺序正好相反。这一段是**新写**，不是搬运。

       **⚠️ 部署形态 MUST 是 stop→start，禁止滚动 / 蓝绿**：风控写者锁是会话级 advisory lock，
       构造期就抢，两个进程重叠期间后起的那个会抢不到锁并拒绝启动。 -->
- [ ] 3.6 `aidcp-automation`：`npm run typecheck` + 全量 `npm test` 全绿。
  <!-- 批 A 当批实测：typecheck 干净；acceptance 89/89；全量 1983 pass / 0 fail。
       本条是第 3 段的收尾闸，八批做完再勾。 -->

## 4. 台账清零与门禁

- [ ] 4.1 `aidcp-automation/src/automation-composition-root.ts` 的
  `AUTOMATION_ROOT_READINESS_BLOCKERS` 逐条删除并同批下调；**只许下降，不留空位**。
- [ ] 4.2 `aidcp-cloud/boundaries/composition-root-independent-blockers.json` 同批收缩；
  **实为三份**（见 0.3a）：还有 `aidcp-automation/boundaries/composition-root-independent-blockers.json`
  那份已漂到 20 条的陈旧快照。
  <!-- ⚠️ **口径更正（用户 2026-08-01 随 A-4 裁定；原文那句「三份 MUST 在同一批次内一致」是错的）**：
       现实已经反驳过它一次 —— 2026-07-31 那批里单体侧 AST 台账 54 → 53、自动化侧刻意不动，
       **两把尺合法分叉**，因为它们问的是不同的问题（「自动化段还碰不碰内容符号」
       vs「还有什么阻止本包交付完整生产进程」）。
       **真正成立的规则是**：
       ① **自动化那两份（常量 + JSON 投影）MUST 一致** —— 已有 deepEqual 断言看着，这条不变；
       ② **单体那份问的是另一个问题，按自己的节奏自熄**，MUST NOT 为了「凑齐三份」去手改它，
          也 MUST NOT 因为它没减而拖住自动化那两份。
       照原文办的具体危害：会逼人给单体那份发明假锚点（A-4 差点就走上这条路）。 -->
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
  <!-- 2026-07-30 19:28 已部署第七批（aidcp-cloud@9df5210，仍是单体形态）。**本批合了主干**，
       所以带上了另一路 change（可配置 Facebook 消费模式，`f58c2d2`）——用户 2026-07-30 明确要求合并主干重部。
       备份 /opt/aidcp/cloud.bak.20260730-192622.tar.gz + .env.bak.20260730；
       cloud 侧 package.json / package-lock.json 相对已部署的 843bac6 **零变更**，故未动 node_modules。
       **顺序是硬的，本批真用上了**：rsync → `migrate status`（确认待应用恰好 3 条：automation 2 / api 1 /
       content 0，且三条 kind 都是 expand、不会被 `--allow-contract` 闸拦）→ `migrate up`
       （applied 0101 33ms / 0102 53ms / 0100 48ms）→ 重启 → healthcheck。
       **顺序倒过来会怎样是实测过的链路，不是推测**：那批把 REQUIRED_SCHEMA_VERSION 抬到 0102，
       先重启则 schema 门 enforce 下抛出 → 进程 exit 1 → systemd 每 5 秒静默重启、零告警（见 0.x 那条注释）。
       healthcheck 全过：active running；8787 + 8090 + 8091 在监听；重启后错误行数 0；
       **schema 门逐属主全通过**（content 0069/0069、automation 0102/0102、api 0100/0100）；
       PG 锚点缓存 / CommentScheduler / 面板 / 客户鉴权 / 飞书长连接（WSClient onReady）全就绪；
       三属主库各自 `select 1` 全通；isales 四服务重启前后均 running、全程未触碰。
       **另跑了 2 分钟 soak**（启动那一刻绿不等于跑起来绿）：ActiveEnterTimestamp 停在 19:28:09 未前移
       ⇒ 没有崩溃循环；6 分钟窗口内错误 0；日志里的 warn 只有既有的「view 配额暂不可用 → 休眠浏览」，
       不是本批带来的新形态。 -->
  <!-- **属主隔离实测**（这批一次加了三张表所属的两个属主，值得逐库验）：
       api 库有 facebook_operation_policy / facebook_group_comment_policy、无 automation 那三张；
       automation 库有 facebook_consumption_progress / facebook_consumption_action /
       operator_command_receipt、无 api 那两张；content 库五张都没有。
       ⇒ 迁移归属从头声明 → 表归属 → 按属主分组 → 只在该属主库应用，全链再次走通。
       另上机器逐条确认两批的新代码都真到了（对方那批的 facebook-consumption-mode.ts、
       我这批的 operator-command-receiver.ts）——不靠「rsync 没报错」推断。 -->
  <!-- **现网真正变的是对方那批**（可配置消费模式：新配置权威 + 运行时 + 面板）。
       我这两批（撤两条台账 + 接收方与幂等台账）对现网**行为逐位不变**：接收方未接线、台账无消费者。
       仍是单体形态，**不证明三进程能跑**（5.3 的口径）。ol 未部署、用户未提。 -->
  <!-- ⚠️ **一条只报不动的运维观察**：/opt/aidcp 下 cloud 备份 tar 已累积 **139 个**（约 930MB）。
       console 那侧有「只留最近 10 个」的纪律，cloud 这侧似乎没有。删备份是破坏性动作，未擅自做。 -->
  <!-- 2026-07-30 20:42 已部署第八批（aidcp-cloud@319b0af，仍是单体形态）。
       备份 /opt/aidcp/cloud.bak.20260730-204207.tar.gz；package.json 零变更；三属主待应用迁移均为 0。
       **本批是真运行时改动**（飞书自由文本委托现在经接收方 + 幂等台账），所以部署验证有意义。
       healthcheck 全过；**本批的新就绪信号在**：「运营指令幂等台账已就绪（executionTarget=dev）」
       ——PG 台账对着真表初始化成功，等于接线在启动期自证了一次。
       另跑 75s soak：启动时刻未前移（无崩溃循环）、5 分钟内错误 0、
       「台账不可用」告警 0、「委托未送达 / 键冲突」0、内部 API 未注册告警 0（monolith 不起该监听，本来就不该有）。
       isales 四服务未触碰。 -->
  <!-- ⚠️ **有一件本批没能证明的，如实说**：飞书自由文本委托那条链**没有在 dev 上真跑过一次**
       （要真发一条飞书消息才触发）。启动期只证明了台账可用、接收方构造成功、单体行为零回归。
       「一条飞书 `/delegate` 端到端跑通、台账里落下一行、重投拿回同一结果」属真机验收项，
       已按 5.5 登记 backlog 簇 60。 -->
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
