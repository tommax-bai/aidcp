# 交接：第八轮（2026-08-01）

> **这份是入口，短。** 细节在 `docs/native-migration-repair-handoff-2026-08-01.md`
> —— 那份 800+ 行、按时间顺序保留了 §1–§15，**只在需要追溯某条结论的来龙去脉时去翻**。
> 本轮的完整记录是它的 **§14 / §15**。
>
> ⚠️ **本文里所有数字都是 2026-08-01 的快照。fleet 高度活跃，一律以 CLI live 为准**：
> `openspec list` / `openspec list --specs`。别引用本文的计数做决策。

---

## 0. 起手三件事

1. `scripts/task-preflight` —— 四个 canonical checkout 必须都停在默认分支（aidcp=`main`，其余=`master`）。
   它是**唯一会 exit 1 拦停**的门禁，且是 fleet 全局的：任一仓漂移会拦下全部四仓的新任务。
2. `openspec list` 看活跃 change 与真实进度。
3. 要动 edge/cloud 前先 `ls -d ../aidcp-edge ../aidcp-cloud` 确认在本机。

**Rust 工具链不在默认 PATH**：
`export PATH="$HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/bin:$PATH"`

---

## 1. 现状（2026-08-01 快照）

| | 值 |
| --- | --- |
| 活跃 change | 29（其中 ✓ Complete 待归档 **1**：`native-page-engine-production-cutover`） |
| 已合并 spec | 182 |
| 未勾任务合计 | 465 |
| 真机验收待验 | 936（`docs/real-machine-acceptance-backlog.md`） |

三仓 head：控制仓 `b4ee0cd8` / edge `a65a28d` / cloud `534af19`。
全库 `openspec validate --all` 本轮实测 211 项 0 失败。

---

## 2. 本轮做了什么（三件）

### 2.1 立项四条 change（零开工，文档齐备、`validate --strict` 全过）

| change | 项数 | 一句话 |
| --- | --- | --- |
| `surface-native-engine-diagnostics` | 35 | 诊断通路本体（解锁 E12 + 逐字输入降级记账） |
| `extend-native-postcondition-coverage` | 37 | 后置校验盘点的 16 条未读 + 3 条不达标 |
| `bound-facebook-comment-migration-latch` | 31 | 云端编排 A：Facebook 迁移闩生命周期 |
| `unify-facebook-comment-budget-source` | 31 | 云端编排 B：评论预算单一事实源（跨仓） |

**立项时坐实的、与上一轮 handoff 表述不同的三件**（照旧表述开工会走偏）：

- **引擎已经在写诊断了，只是没人收得到。** 不是"要加记账"——`native/page-engine/src/` 下
  **15 处 `eprintln!`、11 类具名标签**，一批就写在成功路径上（含逐字输入的降级记账，早写好了）。
  宿主把它收进 2048 字符尾缓冲、**只在构造进程级失败对象时**挂出 ⇒ 命令正常返回的行随进程丢弃。
  **而"到人眼前"的末端已经存在**（Electron 逐行读核心 stdout/stderr → UI 活动流 + `edge.log`），
  **断点只有"引擎子进程 → 核心进程"这一跳**。所以走"宿主转发"比预想便宜得多，
  且不必碰就绪握手（未就绪时任何非就绪记录都会判协议非法并终止引擎）。
- **"三道闸推广到其余命令面"会把范围放大一倍。** 规格明写：一条命令合不合规是**它自己后置条件**的属性，
  不是它写在哪个模块的属性。要做的是把 16 条未读读完、3 条不达标补上，**不是**把命令统一改走共享编排。
- **云端评论预算那条缺陷已经修了。** 摘出文档说"云端只把正文传给预算函数"——那是
  `aidcp-cloud 9013a5f`（2026-07-29）修的，**比那份文档还早两天**。立论因此从"修一个正在发生的缺陷"
  变成"消除一个只能靠人记住的约束"，优先级相应下调。

### 2.2 清账：16 条归档

+22 条 requirement 并进主 spec、3 条改名、零删除。活跃 change 41 → 29。

**归档顺序不是按日期排的**，是按读出来的依赖排的（见 §5 的坑）。

### 2.3 生产切换线收口：45/49 → **49/49**

`native-page-engine-production-cutover` 现为 ✓ Complete。落地四件：文件输入原语（实读已成立）、
Rust 全量闸（350 例 0 失败 + release）、契约测试覆盖盘点 + 补三条、发布安全夹具提到验收层（31 → 38 例）。

edge 三个提交：`1ea3cb1` / `8bafe28` / `a65a28d`。

---

## 3. 下一步（按价值排序）

### ① `native-page-engine-production-cutover` 归档 —— **但 MUST NOT 直接归档**

它满了，但它是**迁移主线**、中途有过**显式弃守裁定**，其 tasks.md 里自带一条归档红线警告：
照原文归档 = 主规格声称系统具备"从未实现"那一列的能力。

**归档前置两项，缺一不可**：

- **整份 delta 通读**（不是只读"具名偏离"那几条）。判据见细节文档 §12.1；
  本仓实测：有弃守裁定的 change 命中率极高（三条有裁定的线分别命中 13 / 2 / 1 条），
  没裁定的线零命中。**弃守/收窄裁定是 delta 漂移的主要来源。**
- **跨 delta 对账**（见 §5 第 1 条）。

### ② 其余四条线收口

`restore-native-facebook-residual-parity` 43/61 · `restore-native-xiaohongshu-action-honesty` 40/56 ·
`enforce-native-engine-artifact-gates` 43/54 · `harden-native-engine-runtime-contracts` 40/48。

**唯一硬依赖**：FB 残余对齐的收口需要 `bound-facebook-comment-migration-latch` 先落
（那条线的 delta 里"迁移闩生命周期"两段已被摘出，等它承接）。

### ③ 新立的四条 change 择一开工

四条都零开工、互不阻塞。若要挑一条最划算的：`extend-native-postcondition-coverage`
——它的第 1 节（给盘点表补 below_bar 棘轮）是纯本地改动、当天可完成，且**做完之后才安全**：
不补的话，后面读 16 条未读时，把 unread 改成 below_bar 就能让门禁变绿而风险不变。

### ④ 出包 → 一次真机 session（**只有用户能做**）

backlog 簇 122 / 123 / 124 / 125 / 126 合计 75 条共用同一个前置：重打一次客户端安装包。
本轮新立的四条 change 又各自往 backlog 加了真机项。
**小红书真机验收自 2026-07-22 迁移以来一次都没做过。**

最该盯的三条：**123.29**（评论提交后平台清不清空输入框——不确认的话全量评论回执降级）、
**123.32**（话题选择器是否还成立——漂了会全线贴不上且零报警）、
**123.26**（多帧指针轨迹会不会划走反应浮层，这批唯一有理由怀疑会新增失败的路径）。

---

## 4. 别再重新讨论的裁定

- **统一自动化运行模型已撤出计划**（2026-07-30 用户裁定）。它不再是任何工作的前置，
  设计稿移到 `docs/design/managed-automation-runtime/`。**已上线规格重新是唯一权威。**
  重新立项时别重做 §24 那张约 60 份能力的逐条处置映射表（成本很高且已修正过一轮）。
- **真机验收项一律只活在 backlog**，不进 tasks.md（2026-08-01 用户裁定）。
- **不为这批工作专门打包**——但包在持续更新，需要新包的真机项会随下一次出包自然可验。
- **跨平台打包那批弃守已成终局**（簇 127 废弃，复核不会发生）。
- **`browse_next` / `browse_scroll` / `plan_execute` 在活路径上已死**：判据不是文档写了 `@deprecated`，
  是 `aidcp-cloud/src/comm/command-bridge.ts` 的 `createEnvelope` 出口里**根本没有它们**。
  别给它们补测、别在那条路上改代码。

---

## 5. 坑（★ 是本轮新踩的）

### ★ 攒批归档的真正风险是「delta 对不上 delta」，不是「delta 对不上实装」

**两件事，别合并记忆。** 16 条里 **7 个能力被不止一条待归档 change 改**，
而**每条 delta 都是照当时的主 spec 写的** —— 同批另一条尚未归档，它的修改对写作者**不可见**。
三处撞车，两类后果：

- **有意取代**（2 处）⇒ 只需定归档顺序。**顺序反了会静默留下旧文本**
  （实例：先归档 `simplify-active-browser-takeover` 会让主 spec 停在"要求分别展示浏览器出口与本机出口"——那个界面已经不存在了）。
- **不是取代，是底稿旧了**（1 处）⇒ **必须改 delta**。判据：**撞车的那条 requirement 根本不在后写 change 的 proposal 范围里**。
  实例：`simplify-` 会把 `refresh-proxy-preflight-on-manual-start` 的整段规则连同 4 条 scenario 静默删掉。

**还有一类：顺序对了也不够。** `recover-facebook-scroll-after-no-movement` 上一轮已登记"前一条必须先归档"，
但 delta 仍写作 `ADDED` 且**新旧要求名不同** ⇒ 归档结果不是取代，而是**两条互相矛盾的 MUST 并存**。

**攒批前扫两条，很便宜，`validate --strict` 一条都抓不到**：
① 建"capability → 哪些待归档 change 改了它"的表，>1 的逐对比对正文；
② 每条 `MODIFIED` 的 requirement 名必须在主 spec 里**逐行精确存在**（`grep -qxF "### Requirement: X"`），
不存在的只能由**同批的 ADDED / RENAMED** 解释。
⚠️ 写这个 grep 时注意 `### Requirement:` 后面**那个空格**——少算一格会让全部条目误报。

### ★ RENAMED 的写法有个会让归档中止的坑

FROM/TO 的反引号里必须带**完整 `### Requirement: ` 前缀**。写成裸名字会报
`MODIFIED failed for header … not found` + `Aborted`，**而 exit code 仍是 0**。
**在树的 change 里就有写错的**（`configure-facebook-mode-numeric-policies`）——
也就是说它此前根本 archive 不了，只是没人试过。**照抄它会把 bug 复制走。**

### 归档必须先在 scratchpad 演练

`cp -R openspec $S/openspec && cd $S && openspec archive <name> -y`，grep 输出里的
`failed for header|Aborted`。几秒钟，真仓不脏。**判据是输出，不是退出码。**

### 归档提交必须路径限定 `git add -A <路径>`

否则只提交新增、删除永远挂在工作区。**验收判据**：`git diff --cached --name-status` 应大量是 `R`（重命名）；
一堆孤立 `A` 就是漏了。本轮 98 R / 19 M / 2 A。

### 控制仓有 5–8 个 session 并发

暂存会被别人的全量提交带走（上一轮中过一次，内容没坏但提交说明全丢）。
**唯一救得回来的做法是把"为什么"写进文件本身**，别只写在提交信息里。
提交一律路径限定，**绝不仓根裸 `git add -A`**。

### 卡在「等某方」的任务，要回头查那一方还在不在

上一轮有条任务等的属主 change 早已归档、单写区主张失效、根本无人可等。
本轮交出 E13 前先查了属主仍活跃——**这一步要成为习惯**。

### ★ 变异检验要问「哪条用例抓住的」，不只问「有没有红」

本轮做了 9 次变异，全部命中预期用例。**Rust 侧要确认输出里出现 `Compiling`**，
否则测的是编辑不是新二进制。**还原源码用备份拷回、按 sha 核对，别用 `git checkout <file>`**
（会连未提交的修复一起冲掉）。

### ★ 夹具不真实会让用例测的是夹具

给小红书笔记 id 用 `note-a` 这种占位，路由的 `[A-Za-z0-9]+` 正则在连字符处截断、
两张卡被去重成一张。**是红着发现的，不是读代码想到的。**

### ★ 门禁 / 测试写完，先让它抓一次自己

上一轮那道后置校验盘点门禁首跑就抓到自己表里一条理由写虚了。本轮的做法同理：
每条新断言都用一次变异证明它承重。

### 别信任何文档里的计数（含本文）

`openspec list` 才是。

---

## 6. 本轮新登记的缺陷

**E13**（`docs/edge-honesty-gap-inventory.md`）：小红书 feed 刷新**点完无条件回确认**，
不取批次基线、不校验换没换（`native/page-engine/src/xhs-command-router.js:456-460`）。
三种情况会静默兑现成假成功：点到别的元素 / 点了但没重载 / 重载了但内容没变。
后果是**浏览闭环空转且看不出来**——每条日志都是成功。

**属主** `restore-native-xiaohongshu-action-honesty`（该文件的单写区，已复核仍活跃）。
**判据现成**：`cards()` 已带 `noteId`，取点击前后两次 id 集合比较即可。

**它为什么没被补测**：唯一写得出的用例是"点了就成功"，那等于把缺陷锁进测试。
所以走登记，不走补测——**这个判断本身值得记住**。
