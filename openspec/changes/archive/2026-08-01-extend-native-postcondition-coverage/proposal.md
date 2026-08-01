## Why

后置校验的逐面盘点已经做出来了（`aidcp-edge/native/page-engine/command-postconditions.json`，常驻门禁 `test/native-page-engine/command-postconditions.test.ts`）。**它给出的是一份工作量清单，不是一份完成报告**：42 条写命令里 **22 达标 / 3 不达标 / 1 结构上不适用 / 16 从没人逐条读过**。

规格对这份表的态度已经写死：**「未列出的面会被读成已覆盖」**，且 **「一个面在被记为达标之前，这条保证 MUST NOT 被用在它身上」**（`native-locating-gates`）。所以那 16 条 unread 不是「大概没问题」，是**全仓对它们是否会假成功一无所知**，且这个「一无所知」今天写在纸面上、没有人在推进它归零。unread 覆盖的是 7 条 Facebook 登录写动作、5 条通知面、以及 `plan_execute` / `profile_open` / `identity_read_self_profile` / `publish_navigate_entry`。

**盘点表自身还有一个会让它自我瓦解的洞。** 门禁强制了三件事：unread 条数 ≤ 预算、预算恰等于实际条数（不留空位）、below_bar 必须写清差在哪。**但 below_bar 没有任何数量约束。** 于是有一条完全合法的洗白路径：把一条 unread 改成 below_bar，附一句「差在哪」—— 预算依法下降、门禁全绿、**而那条命令的假成功风险一点没变**。棘轮只锁了一个方向的出口，另一个方向敞着。这不是假设：现存 3 条 below_bar 已经证明这个状态是可达终局，且其中没有一条带「什么时候、由谁消除」。

3 条已知不达标各有各的形态，都是本仓反复点名的老形态：搜索输入把「读不到」折成「读到了一个否」（失败方向诚实、**归因是错的**）；上传配图的判据认「那个序号位上有预览图」，**上一次残留的预览同样满足**；候选项添加只有话题一支达标，提及 / 地点 / 合集三支仍是「打进去再读回来」的自证。

## What Changes

- **16 条 unread 全部逐条读完并分类**，每条落到 confirmed / below_bar / not_applicable 三者之一并带证据；`unreadBudget` 归零。**读的结果不预判** —— 读出来是达标就记达标，读出来不达标就记不达标并修，不为了把数字做好看而调判据。
- **below_bar 补上棘轮与处置**：与 unread 同规格的单调预算（只许降、恰等于实际条数、不留空位），且每条 MUST 带具名处置（消除动作，或**具名例外 + 理由 + 谁来解**）。让「unread → below_bar」不再是一条能让门禁变绿而风险不变的路。
- **修 3 条已知 below_bar 中可修的两条**：上传配图的判据改为按本次上传的标识回读，不再接受残留预览；候选项添加的提及 / 地点 / 合集三支按各自结构信号确认。**第三条（搜索输入的归因折叠）先做属主核实**——它此前登记的两个去处，「并入会话守卫流」那个 change 已于 2026-08-01 归档，另一个属主是否仍在须当场查（本仓已因「等一个已经不在的属主」卡住过任务）。
- **门禁增两条断言**：`unreadBudget` 归零后不得被重新抬起；below_bar 预算同样只许降。
- 新分类中若有落到 below_bar 的，同样按上一条带处置登记，**不得只改数字**。

**不在本 change 范围内的一件事（对 handoff 表述的订正）**：这项工作在 handoff §13.4 里写成「三道闸推广到其余命令面」，读起来像是要把所有命令改走那套共享的 resolve–act–validate 编排。**规格明写不是这样**：「一个面是否合规是它自己后置条件的属性，不是它写在哪个模块里的属性；共享编排存在并已接第一条真实命令，但一条自带诚实后置条件的命令同样合规」。所以本 change 的判据是**每条写命令都有够强的后置条件**，改不改走共享编排是逐条的实现选择，不是目标。把它做成「全部改走共享编排」会是一次没有规格依据的大范围重写。

## Capabilities

### Modified Capabilities

- `native-locating-gates`: 补上 below_bar 的单调预算与具名处置（今天只有 unread 有棘轮，below_bar 无约束，构成一条让门禁变绿而风险不变的洗白路径）；并把「未读预算归零后不得再抬起」写成要求。

## Impact

- **aidcp-edge（唯一受影响仓）**
  - `native/page-engine/command-postconditions.json`：16 条 unread 重新分类；新增 below_bar 预算与逐条处置字段；`unreadBudget` 归零。
  - `test/native-page-engine/command-postconditions.test.ts`：新增 below_bar 预算断言、处置字段断言、unread 归零后不可抬起断言。
  - 视逐条阅读结果而定的实现点：Facebook 登录写动作（`native/page-engine/src/facebook/auth.rs`）、通知面与 `profile_open`（`native/page-engine/src/engine.rs`）、发布入口（发布相关分片）。**改动面在读完之前无法穷举，本 change 如实不预列。**
  - `publish_upload_image` / `publish_add_with_candidate` 的判据实现点（发布分片）。
- **串行约束**：`native/page-engine/src/engine.rs` 与 `facebook/auth.rs` 是并行开发点名的热点；本 change 期间与其他触碰这两个文件的流串行，不并行。
- **不涉及**：云端、console、Edge-Cloud 协议、Native IPC 协议版本。
- **依赖关系**：`publish_add_with_candidate` 三支的结构信号需真机标定（backlog 簇 123.34），该支在标定前只能记为**带具名处置的 below_bar**，不能记为达标。
