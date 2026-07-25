# Edge 仓拆分 · 下一 session 交接（可直接执行）

> 生成于 2026-07-25，**同日第二轮更新**（提案七处已改完 + 主进程归属已盘完）。
> **给接手 session 用**：从头读到尾，按本文执行。
> 对象 = openspec change `split-classic-client-edge-host`（把 `aidcp-edge` 拆成 `aidcp-classic-client` +
> `aidcp-edge-host`）。
> **本文里凡是写「已核实」的，都是对着代码/命令实跑出来的；凡是写「待定」的，必须先问用户。**
> ⚠️ **但第一轮里九条标着「已核实」的事实，第二轮执行时实测是错的或已过期——见 §2.5。
> 这不是打脸，是给接手者的告诫：「已核实」只代表写下那一刻，fleet 活跃，一律自己复核。**

---

## 0. 先核对现状（接手第一件事）

```bash
git -C /Users/baitianxing/codes/aidcp branch --show-current   # 必须是 main，不是就先停手（CLAUDE.md §7）
ls -d ../aidcp-edge ../aidcp-cloud ../aidcp-console            # 缺了就停手问用户
openspec list | head -5
```

**当前进度一句话**：提案七处缺陷已改完并推送；主进程归属台账已盘完（0.C.2/0.C.3/0.C.5 完成）；
**下一步是 0.C.0「让引擎发结构化事实」，但真正动 `main.cjs` 之前卡在一个未决的冻结窗口上**（§7.1）。

第二轮结束时的指针（fleet 活跃，接手时务必自己复核）：

| 位置 | 值 |
| --- | --- |
| 控制仓 `main` | `275f78d`（第一轮写的是 `234562d`，已推进） |
| 提案所在 worktree | `../aidcp.wt/split-classic-client-edge-host`，分支 `codex/split-classic-client-edge-host`，HEAD `fff7f1a` |
| **提案仍未合入 main** | change 目录只存在于那个 worktree 里，`openspec list` 在主 checkout 上看不到它 |
| edge `origin/master` | `cf10b0c`（两轮之间未动） |
| edge worktree 数 | 36（其中 35 个 linked，全部工作区干净） |
| 活跃 change 数 | 121 |

提案文件（**8 份**，全在那个 worktree 的 `openspec/changes/split-classic-client-edge-host/`）：
`proposal.md` / `design.md` / `tasks.md`（**88 条，3 完成**）/ `specs/` 下 **5 份**增量
（新增 `canonical-default-branch-guard/`，见 §3 B3）。

**另一份必读产出**（在主 checkout 上，已合入 main）：`docs/edge-split-ownership-inventory.md` ——
82 条通道 + 5 条传输 + 230 个行段的归属台账，`main.cjs` 动刀前的作业依据。

---

## 1. 用户已拍板（不要重新讨论，直接照做）

1. **未来第二个客户端 = 面向不同客户群的独立产品**（A 客户用 A 客户端，B 客户用 B 客户端），两者共用同一份
   Edge 引擎。⇒ 复用是真需求，拆仓收益 = **引擎不被复制成两份**。
   ⚠️ **收益不是「各发各的版」**——提案原来的立论必须整段改写，见 §3 B1。
2. **包分发走 tarball，不建私有 registry、不迁 GitHub 组织。** 引擎仓 CI `npm pack` 出 `.tgz` + manifest，
   经 GitHub Release 发（复用现有 `desktop-v<ver>` prerelease → ECS `/opt/aidcp/downloads/` 那条已跑通的链路）；
   客户端仓依赖精确 URL，**不可覆盖性由 lockfile 的 sha512 强制**。
   已实测：装 tarball URL 后 lockfile 带 `integrity: sha512-…`，篡改后 `npm ci` 直接 `EINTEGRITY` 非零失败——
   比 registry 的服务端「拒绝覆盖」策略更硬。**不要绑阿里云 OSS**（桶匿名读 403，已卡死两个 change 数周）。
3. **拒绝「先仓内边界、拆仓押后」的分 change 方案**——直接拆。但**仓内解耦这项工作不消失**，它从「独立 change」
   变成本 change 的**第 0 阶段**，见 §3 B5。
4. **Windows 在范围内。**
5. **接受冻结窗口**（时间与负责人**待定**，见 §7）。
6. 发布分支回流债先清零——**已核实为 0**，见 §2。

---

## 2. 本 session 已做完的（不要重做）

| 提交 | 内容 |
| --- | --- |
| `8d15c60` | 关闭 4 个 change（`wechat-customer-api-contract` / `wechat-edge-runtime-honesty` / `edge-installer-oss-distribution` / `ol-client-auto-update`），关闭时留下的未修缺陷全部记进 `docs/real-machine-acceptance-backlog.md` 顶部 |
| `64eb3a9` | 归档 `wechat-read-controls-offline-toggle`（代码全在 edge master） |
| `3f10bf8` | 归档 `risk-state-cross-process-integrity`，**删掉被推翻的 `same-account-parallel-safety` 增量**；同步订正 `docs/risk-control.md` 与 backlog 110.1 / 110.8 |
| `692e855` | 砍掉 `self-contained-ads-runtime` 的席位上限 + 内核下载失败分类（用户决定，从未实装） |
| `234562d` | 新建 change `register-risk-target-follows-active-session`（补登 cloud `6b6b542` 那次无记录的设计反转） |

**回流债核实结果（用户要求「先清 0」，实测已满足）**：edge 6 条 release 分支上的 `+` 去重后 6 个 sha——
`e5a4d1d5` / `9867cdc2` / `6e64862a` 是纯版本号提交（发布态工件指针，按 CLAUDE.md §6 只对账不照搬，且 master
`0.3.24` 已高于最高的 `0.3.23`）；`210f3865` / `36fe38f3` 已被主干更强方案取代；`5ee9d2dd` 已回流。
**没有一条需要重新实现。** 唯一缺口是一条回归断言（手动打开的人设浮层收到「已绑」信号后不得被自动关掉）
主干没有等价用例。**那 3 条仍带 `+` 的 release 分支不要删**——它们是已上线包的构建基线。

---

## 2.5 §3 七处已全部改完（2026-07-25，提交 `a4d8458`，分支 `codex/split-classic-client-edge-host`）

七处逐条落地并跑过归档演练（五份增量全部 apply，无 abort）。**下面这几条本文原写「已核实」、
实测是错的，以此处为准**——它们改变了 B5 / B6 的改法，也改变了 §5 的判断：

| 本文原写 | 实测 | 影响 |
| --- | --- | --- |
| stdin 命令桥承载建号人设 / 稿件审批 / 浏览器停放**三对**请求-应答 | **只剩一对**（浏览器显示）。人设与稿件审批已迁到「客户端主进程直连云端 HTTPS」，客户端侧发送函数是**零调用点死代码**，且有测试断言禁止重新引入 | B5② 若照原文写，会把两条被有意拆掉的耦合**拉回 Host 合同**并当场撞红既有测试 |
| 跨边界的路是「日志流 + stdin 桥 + 第四路 Node IPC」 | **五条**：多出「启动时环境变量」（删除环境+擦凭证**只能**经它表达）与「POSIX 信号」（IPC 不可用时的权威兜底）。且 Node IPC **不只承载 lifecycle**，它还跑重绑请求-应答与两组协商 | 所有权盘点漏一条 = 拆完功能没了没人发现 |
| 主进程注册 **81 个** ipcMain 通道 | **82 个运行时通道**（81 个调用点，其中一个在循环里注册两条）；preload 82 个 invoke + 4 条推送，两侧零漂移 | 写 81 与 preload 对不上账 |
| 占用查询接口已有两个，**缺的是调用时机** | 两个都在，但**都答不出「是谁在用」**；其中一个必须由调用方传名册、无法枚举，对另一个实例的分身**结构性失明** | 不能假设「调用现成接口即可」，占用事实必须由 Host 自己的租约建立 |
| 同机双驱主入口 = 已活跃→附着**一道门** | **两道门**：另一道是「报告非活跃但孤儿调试端口存活→接管」。且附着方会在**自己退出时把对方的浏览器关掉** | 只加固一道等于没修；后果不是并驱而是对方浏览器被关 |
| `fs.openSync(path,'wx')` **仓内已有两处现成用法** | 两处只有**一处半**：一处是真竞争仲裁但属**一次性创建、非持有型锁**（无持有者身份 / 无存活探测 / 无释放），另一处只是临时文件防覆盖硬化 | 陈旧持有者回收必须现设计，不能靠引用先例带过 |
| §5 冻结清单三个 change | **35 个 edge worktree 里有 10 个**带未合并提交触及冻结集；其中恰好两个分支独占了桌面工作流与 mac 构建脚本的改动 | 本文自己说过「这份清单是下界」——确实是。判据改为 git 反查 |
| `self-contained-ads-runtime` 6/37 | 勾选滞后，代码 2026-07-10~18 已全量在 master；7.1/7.2 今日已被用户砍掉 | 别拿 6/37 当「这个 change 还早、冻结零成本」的论据 |
| `browser-slot-scheduling` 与排他前置冲突、不能并行 | 其 edge 分支**已全量并入 master**（ahead=0），worktree 是孤儿；剩余 15 项是云端 / 真机 / 明确不做 | §4.2 的「不能并行」约束实际已解除 |

**另外两条新发现（不在原七处内，但会咬人）**：

1. **`openspec archive` 中止时仍返回 exit 0。** 所以 `openspec archive … --yes && …` 这种脚本链会把
   中止当成功。唯一可靠判据是读 STDOUT 有没有 `failed for header` / `Aborted`。已写进 tasks 8.8。
2. **`edge-desktop-packaging` 有一处 spec 丢失风险**：`self-contained-ads-runtime` 在 proposal 里
   声称对它有增量，但它的 `specs/` 下根本没有这份 delta；真正持有该 delta 的是
   `native-page-engine-production-cutover`。两个都归档的话，ads-runtime 那条打包需求会**静默地
   永远到不了主 spec**。与拆仓无关，但该单独修。

---

## 2.6 主进程归属已盘完（第二轮，控制仓 `275f78d` + 分支 `fff7f1a`）

产出 `docs/edge-split-ownership-inventory.md`（540 行）。tasks **0.C.2 / 0.C.3 / 0.C.5 已勾**。

**覆盖度（可当事实用，因为是独立复核过的）**：82 条运行时通道全部有主，零重复、零归属冲突；
230 个行段块覆盖 1–7396 行**无空洞**。复核链路**自己重新从源码抽了一遍**通道清单（不是复用盘点结果），
得到同样的 82，并与渲染层预加载暴露的 82 个调用名**一一对应**——既无「渲染层调得到但主进程没实现」，
也无「主进程实现了但没人调」。

**两条改变计划的结论**：

1. **须切开的是 30 条，不是 10 条。** 多出来的 20 条是那批「直连云端 HTTPS」的产品通道。它们的
   HTTP 调用确实归产品侧，但**每一条都要先把环境 id 翻译成环境键，而那张表在引擎侧**。更要命的是
   那个解析函数在 id 认不出时**回落到「当前选中环境」**——所以 Classic 拿不到正确解析器时**不会报错**，
   而是把发布草稿编辑、发布队列取消这类**写操作静默打到另一个账号上**。
   ⇒ Classic 必须有自己的解析器，数据源是产品侧名册，不是引擎侧运行时注册表。
2. **0.C 自己有前置，顺序必须调（新增 0.C.0）。** 今天外壳**不是收到**引擎事实，而是**从引擎日志文本里
   正则猜**出来的：一张 22 条规则的表产生活动流，子串匹配产生状态徽标。后果三条——云边协议的
   **23 个命令名活在产品界面展示层里**（协议改名会随机弄坏 UI，而 CLAUDE.md §2 的协议同步铁律
   覆盖不到那个位置）；原始核心日志行**逐字**进产品界面；每次向执行侧写浏览器控制指令都以
   「日志里见没见过某一句话」为闸门。**这层不换掉，状态类通道哪边都拿不干净。**
   而且那个解析器**自己的文件头就写着**：它的测试只测自己、从不执行发出端 ⇒ 核心改一句日志措辞，
   **测试照样全绿而活动条目静默消失**。

**第二轮又推翻的三条「实测事实」**（第一轮喂下去的前提，逐条订正）：

| 原说法 | 实测 |
| --- | --- |
| 只有两条非生命周期通道能命令运行中的执行侧 | **至少四条**。改环境昵称、人设落库都经「更新状态」那个函数连锁写到执行侧标准输入。**真正的接缝是那个函数的扇出，不是通道清单**——任何未来调用它的产品侧通道都自动继承这条路径。按通道清单画边界必然漏 |
| 删除环境走云端 HTTPS、完全绕过执行侧 | **两处都错**。用的不是那条云端封装函数；且只有视频号走云端，其余平台终局直接调指纹浏览器本机删除，删前还触发注册表 reconcile（会停执行侧、释放槽位）。整块判产品侧 ⇒ 删一个正在跑的环境会「云端撤销 + 名册移除成功，但它的执行侧还活着、还占着槽位」 |
| 人设落库到不了执行侧 | 错，见上 |

**还有四条推送通道原先完全无主**（状态更新 / 活动流 / 名册更新 / 批量代理进度）。只路由那 82 条
请求-应答通道，界面会**没有状态、没有名册、没有活动流、没有进度**。已补 0.C.0b。

**七处双方共读写的模块级状态**见 inventory §5。其中两条**两个方向都是坏的**，必须显式设计而不是二选一：
- **退出中标志**：归 Host 则产品侧关窗永远收不到、**应用永远退不掉**；归 Classic 则退出时每个核心的
  退出都判为异常、**收尾过程中反复重启核心**并弹「已停止运行」。
- **环境注册表**：见上面第 1 条。

---

## 3. 提案必须先改的 7 处（改完才谈开工）

> **状态：全部完成**，见 §2.5。以下保留原文供回查评审口径。

编号沿用评审口径，方便回查。

### B1 立论不成立，且提案自己已自相矛盾
`proposal.md` Why 段把痛点定为「必须同仓、同版本、同节奏发布」，但同一份文档的 Impact 段又写「已安装 Host 不
独立热更新、版本由当前 Classic 安装包固定」，`design.md` 也规定「Host 仓不产出面向客户的 dmg/zip/nsis」。
⇒ 引擎侧的修复照样要等客户端改 pin、重打包、重签名、重公证，**节奏一天都没解耦**。
**改法**：删掉「发布节奏」这条理由，换成 §1.1 那条（两个独立客户端产品共用一份引擎、避免引擎被复制成两份），
并显式写明代价：引擎修一次，从发一个安装包变成发两个。

### B2 引用了不存在的仓 `aidcp-automation`
4 处：`design.md` §11、`tasks.md` 1.2 与 2.5、`proposal.md` Impact。该仓不存在；云端拆仓是另一条 6 步串行链的
第 5 步、**尚未开始**（见 `docs/cloud-decomposition-execution-plan.md`），且云端评审文档明确反对预建。
**改法**：4 处全改回 `aidcp-cloud`，并加一句「本 change 既不依赖也不预设云端拆仓结果」。
⚠️ 这条不改会把 CLAUDE.md §2 的协议同步铁律指向空仓——那条规矩历史上已因遗漏造成两次静默丢命令。

### B3 fleet 顺序错 + 唯一硬门禁会静默失效
`tasks.md` 2.1（改远端名）排在 2.4（改 helper）**之前**。而 `scripts/task-preflight` 的仓名单硬编码四个仓，
且**仓缺失时只 `continue`（SKIP），不是 FAIL**，只有四个全缺才 `exit 1`。
⇒ 改名瞬间，旧路径消失 = 静默 SKIP，门禁对新两仓完全无感——CLAUDE.md §7 记的「canonical edge 停在 OL 发布分支
24 小时」正是这道闸要防的事故。
**改法**：① 2.4 提到 2.1 之前；② `scripts/lib.sh` / `task-preflight` / `fleet-status` / `release-desktop-macos`
在过渡窗口内**同时接受新旧仓名**；③ 把 preflight 改成「名单内该存在的仓缺失即 FAIL」；
④ 补一份 `canonical-default-branch-guard` 的 spec 增量（接受两个新仓名）——该能力现在逐仓点名，本 change 零增量。

### B4 发布链三处断头
- **registry**：已由用户决定改走 tarball（§1.2）。要改的位置：`design.md` §8 与风险表、`tasks.md` 4.6 / 8.1 / 8.4、
  `specs/classic-client-edge-host-assembly/spec.md` 的「精确锁定」那条（现文禁止 tarball 作正式发行物）。
  `design.md` 的 Open Question #1 可直接关掉。
- **签名/公证 CI**：6 个 Apple secret + 运行时密钥全在 `tommax-bai/aidcp-edge` 仓上，分发走该仓 prerelease；
  控制仓 `scripts/release-desktop-macos` 硬编码仓名。`tasks.md` 全文没提迁移，反而 2.3 要求「两仓都无 secret」，
  把唯一解法禁掉了。**改法**：新增任务迁移 `build-desktop.yml` / `build-desktop-macos.sh` / 公证脚本 /
  entitlements 到 Classic 仓，重建 secret（标 `[需用户操作]`），2.3 改为「源码内无 secret；发布 secret 只存在于
  Classic 仓 CI」。
- **Windows**：见 §4.1。

### B5 契约与代码现实脱节，且没有「先就地拆开」这一步
现实：`src/electron/main.cjs` **7396 行**、注册 **81 个** ipcMain 通道、preload 暴露 82 个 invoke；
跨边界的路**不止日志流一条**——还有一条 stdin 命令桥（承载建号人设 / 稿件审批 / 浏览器停放的**请求-应答**）
和第四路 Node IPC（承载生命周期）。而 `design.md` §3 只给了 9 个生命周期动词，指纹环境建号/改代理/删除、
浏览器开关与显示、重新登录、重启等**属执行侧却无处安放**。
`tasks.md` 里**没有任何一条**是「先就地把这个文件拆开」，两条「Move」指向同一个文件。
**改法**：① `tasks.md` 最前面新增「第 0 节：主进程就地拆分（在现 aidcp-edge 完成，不建新仓）」，
准入判据写死——`main.cjs` < 1500 行、归属引擎的模块零 renderer/window/navigation import（加边界测试）、
81 个通道全部有归属标注无「待定」、三套测试全绿，不满足不得进建仓阶段；
② `design.md` §3 增补「非 lifecycle 的产品↔执行通道」一节，把那三对请求-应答写成**具名 request/response**
（不是通用 execute），禁令措辞改为「不得暴露平台原子动作」以免误伤已上线的应用内稿件审批；
③ 所有权表从「按类别」改成「按文件/行段」清单。

### B6 排他机制：三层已存在，真空在别处
`design.md` §7（v2 已扩成 MachineRuntimeCoordinator）方向对，但**没指名任何跨进程原语**，且遗漏了真正的入口。
已核实的现实：
- 指纹浏览器自身的「占用拒启」**只覆盖跨账号/跨设备**；同机第二个实例走的是另一条路——先查分身是否 active，
  是就直接拿调试端口**附着上去**（`src/cdp/browser-provider.ts` 的 active 分支）。**这才是同机双驱的主入口**，
  只加固孤儿收养那条分支等于没修。
- 每个客户端实例首次准备运行时会**无条件停掉已在跑的守护进程再重启**（`ads-runtime.cjs` 的 `resetExisting`）。
  第二个实例启动 = 掐掉第一个实例正在用的守护进程。
- 占用查询接口**已经有两个**（核心侧 `browser-profile/active`、外壳侧 `listActiveProfiles()`），缺的是调用时机。
- 「被占用」的终局语义已固化进 `openspec/specs/edge-companion-ui/spec.md`，新错误码应复用它、不要另起一套。
**改法**：机制选型写死为**文件的原子独占创建（`fs.openSync(path,'wx')`）**——仓内已有两处现成用法、零新依赖、
macOS/Windows 语义一致。**明确不用操作系统锁**：被保护的不是客户端进程的内存，而是守护进程持有的浏览器；
客户端死了浏览器不死，锁自动释放反而会让第二个客户端「合法」拿到锁去附着一个半驱动状态的浏览器。
回收租约必须**同时**满足「持有者已死」**且**「浏览器侧证明那个浏览器已不在」；只满足前者判定为孤儿、不许接管。
全局限频用短临界区 + 时间戳文件（此处超时接管是安全的，因为它只保护一个数字——**判据必须与租约不同、
绝不可复制粘贴**）。⚠️ **不得引入常驻协调进程、锁服务或任何 broker**（对齐 2026-07-25「不引入 Redis」决策）。

### B7 归档会当场硬中止
`specs/edge-multi-instance-isolation/spec.md` 声明 `## MODIFIED Requirements` + 标题
「并存实例的机器级执行资源 MUST 由 Host 强制排他」，但主 spec 里**只有三条**：实例级 userData 隔离开关 /
同机多监督者并存 / 并存的运营前置约束。**已实测复现**：`openspec archive` 报
`MODIFIED failed for header ... - not found` / `Aborted. No files were changed.`；`validate --strict` **查不出来**。
**改法**：把「并存的运营前置约束」放进 `## REMOVED Requirements`，新的机器级排他走 `## ADDED`；
或把 MODIFIED 标题改成主 spec 里逐字存在的那条。**改完必须在 scratchpad 拷贝上实跑一次 archive 验证**。

---

## 4. 两件真前置（都不是「押后拆仓」的变体，修的是今天就在漏的洞）

### 4.1 Windows 自包含出包 —— 单独一个小 change，做完并真出一次包
**今天不是「打包会失败」，是「会绿灯出假包」**：CI 的 Windows 任务不 stage 指纹浏览器运行时、不还原烘焙密钥，
而 electron-builder 对缺失 extraResources **只警告不报错**，打包后置检查也没有自包含运行时的闸
⇒ 产出一个能装、装完起不了浏览器的安装包。工作流注释与 `docs/release-desktop.md` 写的「会因缺资源失败」是**错的**。
另外从 2026-07-22 接入原生页面引擎起，**在 mac 上交叉打 Windows 包已结构性死亡**（会把 mac 二进制拷进 win 包、
后置检查抛错），但文档还写着「Windows 本机可打」。
**⚠️ 现网事实（已复核）**：dev 下载页最新 Windows 包是 `AIDCP Setup 0.3.5.exe`，mac 已到 0.3.18、主干 0.3.24。
而 **0.3.5 正是「打包版子进程工作目录落进 asar」那一版**（修复 `3f578b9` 是 2026-07-10 15:00，在 0.3.5 之后），
之后 Windows 再没出过包。**Windows 客户装上去大概率起不了核心。**
**为什么必须排在拆仓之前**：拆仓设计里最没验证的一块，恰恰是「引擎包携带 win32-x64 预编译二进制、客户端消费
它出安装包」；今天连单仓单流水线的 Windows 自包含都没跑通过一次。先弄绿，拆仓才有机械验收口径——
**拆前拆后同一条命令都出 mac×2 + win×1**；否则验收事实上只剩「mac 还能打」。

### 4.2 机器级排他 —— 落在现 aidcp-edge（拆仓时整块随引擎搬走，零返工）
按 §3 B6 的选型实装：守护进程引用计数（有健康且版本兼容的就 **MUST NOT** stop）、分身租约（**必须接进那条
active 直连分支**，不是只加固孤儿收养）、跨进程限频闸（叠在现有两条本地队列之后，本地队列不删）。
⚠️ 与在飞的 `browser-slot-scheduling` 碰同一批代码，**不能并行**——要么让它先落地，要么两件合并。

---

## 5. 冻结清单（按文件冻，不是按仓冻）

> ⚠️ **本节的表格已被第二轮实测超越，别单独读它。** 实际触及冻结集的是 **35 个 linked worktree 里的
> 10 个**，不是表里那三个 change；且 `browser-slot-scheduling` 的 edge 分支**已全量并入 master**
> （ahead=0，worktree 是孤儿），§4.2 说的「不能并行」约束**实际已解除**。权威判据见 §2.5 表与
> change 的 design.md Phase 0：**用 git 反查，不要在 change 文档里搜文件名**。

全组停工不可行也没必要（120 个活跃 change、36 个 edge worktree）。**只冻这 5 个位置**：

1. `src/electron/main.cjs`
2. `src/electron/ads-runtime.cjs`
3. `src/cdp/browser-provider.ts`
4. `.github/workflows/build-desktop.yml`
5. `package.json` 的 `build` 段 + 配套 `scripts/after-pack.cjs`、`scripts/stage-ads-runtime.mjs`、`scripts/build-desktop-macos.sh`

**打基线前必须清空的（生成时状态，接手复核）**：

| change | 进度 | 碰哪个 | 有 edge worktree |
| --- | --- | --- | --- |
| `self-contained-ads-runtime` | 6/37 | ①②③ 三个全碰 | 无 |
| `native-page-engine-production-cutover` | 38/47 | ⑤ | **有** |
| `browser-slot-scheduling` | 47/62 | ① | **有** |

- `self-contained-ads-runtime` 的代码**已全量在 edge master**（`git cherry` 15 条全 `-`），台账滞后而已；
  但它与 §4 两件前置**高度重叠**，应合并处置、不要三边同改。
- `native-page-engine-production-cutover` 跟拆仓是**帮忙不是添乱**——它正在建的「原生二进制随包分发 + 哈希校验 +
  签名」正是拆仓要用的机制，应优先做完。（用户已说这个交给原 session、不用管，它其实已干完、只是忘了删 worktree。）
- `browser-slot-scheduling` 见 §4.2，与排他前置冲突。
- 还有一条判据：建 split-base 前，`git -C ../aidcp-edge worktree list` 里触及上述文件的 worktree 必须为 0。

⚠️ **这份清单是下界**：判定方式是在 change 文档里搜文件名，一个 change 完全可能改了主进程却没在文档里写文件名。
真正打基线前应改成 `git log --since=<冻结起点> -- <这5个位置>` 反查。

---

## 6. 会咬人的坑（每条都已经咬过）

1. **`openspec validate --strict` 通过 ≠ `archive` 会成功**。MODIFIED 标题不在主 spec 里就当场 abort，
   本仓已中三次。**改完 spec 增量一律先在 scratchpad 拷贝上跑一次 archive 演练再动真格**：
   ```bash
   S=<scratchpad>/probe; rm -rf $S; mkdir -p $S; cp -R openspec $S/openspec; cd $S
   openspec archive <change> --yes
   ```
2. **`scripts/task-preflight` 仓缺失是 SKIP 不是 FAIL** —— 改名瞬间静默 fail-open。见 §3 B3。
3. **`scripts/release-desktop-macos` 里有一道 asar/cwd 断言**：从安装包抠出主进程文件、检查子进程工作目录不是
   那个归档文件。这正是 CLAUDE.md §5 那条打包红线的机械化形式，而那个回归**原样发到过运营机一次**。
   执行侧一搬进包，这条正则永远匹配不到——要么每次打包硬失败，要么被人「修」成删掉断言、红线随即失效。
   **必须在第一次 Classic 打包之前把它移植过去，不能并入事后清理。**
4. **发布分支上的改动必须回流主干**（CLAUDE.md §6 铁律）。拆仓之后 `git cherry` 这个机械检查**永久失效**——
   所以切下一个 release 分支前是最后一次有意义的对账时机。当前债已为 0（§2）。
5. **canonical checkout 永远停默认分支**（CLAUDE.md §7）。要分支隔离就另开 worktree；
   切 `release/*` 发布分支**必须在 linked worktree 里做**。
6. **别碰 dev 同机的 isales**（不同 systemd 服务 / 目录 / 端口）。

---

## 7. 仍需用户拍板

1. **⚠️ 唯一仍未决、且正在挡路的：冻结窗口开在什么时候、谁负责。**（用户已同意冻结原则，日期与
   负责人未定。）**它挡的是 0.C.1「切文件」这一步**——`main.cjs` 是冻结集里最热的文件：35 个 edge
   linked worktree 里**有 8 个带着未合并提交压在它上面**，master 在 2026-07-24 还被一个无关改动
   （小红书面板）碰过。CLAUDE.md §7 明写热点文件单写者。
   **注意 0.C.0（让引擎发结构化事实）主要动的是核心侧发出端与解析层，不是 `main.cjs` 本体，
   可以先开工**；真正要改 `main.cjs` 结构时再需要这个窗口。
2. ~~Windows 那个坏包先撤入口还是等新包替换~~ —— **已定（2026-07-25）：等新包替换，不撤入口。**
   已接受的风险写进 tasks 0.A.3：替换落地之前新装 Windows 的客户大概率起不了核心。
3. ~~Windows 要不要买代码签名证书~~ —— **已定（2026-07-25）：暂缓**，先把 0.A 自包含出包打通、
   真出一次包，再按实际安装体验决定。当前 Windows 包本来就配置为不签名。
4. ~~两个 wechat 现网缺陷还修不修~~ —— **已定（2026-07-25）：都先不修，留 backlog。**
   决定与三条别被误读的说明已写进 `docs/real-machine-acceptance-backlog.md` 顶部第 24–41 行那段。

---

## 8. 操作命令

```bash
# 看提案（它在 worktree 里，主 checkout 上看不到）
cd ../aidcp.wt/split-classic-client-edge-host
openspec list && openspec validate split-classic-client-edge-host --strict

# 改提案：就在那个 worktree 的 openspec/changes/split-classic-client-edge-host/ 下改，改完提交推分支
# 归档演练（每次改完 spec 增量都要跑；change 目录不在主 checkout，必须显式拷进去）
S=/private/tmp/claude-501/.../scratchpad/probe; rm -rf $S; mkdir -p $S
cp -R openspec $S/openspec
cp -R ../aidcp.wt/split-classic-client-edge-host/openspec/changes/split-classic-client-edge-host $S/openspec/changes/
cd $S && openspec archive split-classic-client-edge-host --yes 2>&1 | grep -E "failed for header|Aborted|Totals|archived as"
# ⚠️ 读输出，别看退出码——中止时它照样返回 0（§6 坑 1）

# 子仓验证四连（改 edge 代码时）
cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck

# 部署（只从主 checkout 的 eligible ref 走，绝不从 worktree 部署）
scripts/deploy-target dev --check
```

**默认授权**（CLAUDE.md §6，不必逐次问）：提交、推送、部署 dev。
**必须先问**：force-push、非 fast-forward、`ol` 部署、打桌面安装包。

---

## 9. 下一步（接手直接从这里开始）

**做 0.C.0：让引擎发结构化事实。** 依据是 `docs/edge-split-ownership-inventory.md` §1 与 §4。
这一步**不需要等冻结窗口**——它动的是核心侧的事件发出端与外壳的解析层，不是 `main.cjs` 的结构。

顺序建议：

1. 先把 inventory §4 那份「由传输推导出的 Host 公开面」当作目标形状（它已经取代 design.md §3 里
   那份 9 个动词的草稿）。
2. 从**活动流**下手而不是状态徽标：活动流的结构化通道**已经存在**（有一条结构化事件行的旁路，
   Facebook 已经在独占使用它），把其余平台迁过去即可，那张 22 条正则表随后整表删掉。
   **正则回退表绝不能带进 Classic**。
3. 再做状态徽标：把子串推断换成引擎侧的 typed 状态文档（快照 + 增量）。这一步会顺带解决
   「浏览器控制就绪」靠 grep 日志当闸门的问题。
4. 全程守住一条：**拆后标准输出必须降级为纯诊断**，任何产品行为都不得再依赖解析它——
   这条要有测试，写进 0.C.6 准入判据了。

**动 `main.cjs` 结构之前先回来问冻结窗口（§7.1）。**
