# Tasks

> 全部工作落 `aidcp-edge` 一个仓。云端 / console / 协议均不涉及。
> 真机验收项**不进本文件**（2026-08-01 裁定），登记到 `docs/real-machine-acceptance-backlog.md`，见 §5。
> **§2 是「读」，§3 是「按读到的结果修」**。§3 的具体条目在 §2 完成前**故意不预列** —— 预列等于预判分类结果。

## 1. aidcp-edge — 盘点表的棘轮与处置（先做，防止后面一边读一边洗白）

- [x] 1.1 `native/page-engine/command-postconditions.json` 增 `belowBarBudget`，初值＝当前实际条数（3）
  <!-- aidcp-edge 72bc3d9 -->
- [x] 1.2 `test/native-page-engine/command-postconditions.test.ts` 增断言：below_bar 条数 ≤ `belowBarBudget`，且 `belowBarBudget` **恰等于**实际条数（不留空位，与 unread 同构）
  <!-- aidcp-edge 72bc3d9 -->
- [x] 1.3 盘点表增 below_bar 必填处置字段：消除动作，或具名例外（理由 + 前置 + 谁来解）；门禁断言缺失即失败
  <!-- aidcp-edge 72bc3d9：`disposition` 两形态——`kind:fix` 必填 `action` + `owner`，`kind:exception` 必填 `reason` + `blockedBy` + `owner`；字段规格同时写进表自己的 `invariants`，让读表的人不必去读门禁源码 -->
  - **多加了一条原任务没要求、但同族的断言**：`disposition` 只许出现在 below_bar 上。判据修达标后
    处置必须一并摘掉，否则表里会留下一条**永远等不到的待办**——那和「没有处置」是同一种失真的两面。
- [x] 1.4 给现存 3 条 below_bar 补处置：搜索输入＝属主待核（见 3.1）、上传配图＝可直接修（见 3.2）、候选项三支＝真机前置（指到 backlog 簇 123.34）
  <!-- aidcp-edge 72bc3d9 -->
  - 搜索输入按 `fix` 记，处置正文写明「**『实现点在单写区属主处』这句登记本身就是待核项，不得照抄**」——
    D5 点名的那个坑（等一个已经归档的属主）就藏在照抄里。
  - 候选项三支按 `exception` 记，`owner` 一栏同时钉住「标定前 MUST NOT 记 confirmed（无证据），
    也 MUST NOT 记 not_applicable（用『读不出来』冒充『本来就没有』是另一种假成功）」。
- [x] 1.5 门禁增断言：`unreadBudget` 归零后恒为 0，不得抬起（今天只断言「不许上调」，归零后语义更强）
  <!-- aidcp-edge 72bc3d9 -->
  - **实装形态：上限字面量 `UNREAD_BUDGET_CEILING = 16` 钉在门禁一侧。** 理由：单文件断言看不见历史，
    **一个被调高的预算和一个一直就是这么高的预算长得一模一样**；把上限放在测试里，调高预算就必须
    同时改这个字面量，那是一次会出现在 diff 里的显式动作。
  - **归零后的强语义是自动落地的、不需要再改一次门禁**：这个字面量降到 0 时，
    `<= 上限` 与既有的「预算恰等于实际条数」两条合起来即为 D4 要的硬断言。
  - <!-- aidcp-edge 9ecab93：§2 读完后该字面量已按棘轮规则降到 0，D4 的硬断言现已生效。
       同批把上限改成 `budgetProblems(registry, ceiling)` 的可传参数：合成样本必须带**自己的**上限跑，
       否则真上限一变（如这次 16→0），样本就不再触发那条规则、悄悄退化成装饰。 -->
- [x] 1.6 **让门禁先抓一次自己**：造一条「unread 改 below_bar 但不抬 belowBarBudget」的样本，确认门禁当场红；再造一条「below_bar 无处置」的样本，确认同样红。**首跑不红就说明断言写虚了**
  <!-- aidcp-edge 72bc3d9：门禁 6 例 → 10 例 -->
  - **做成了常驻自测，不是一次性变异。** 判据提成纯函数（`budgetProblems` / `dispositionProblems`），
    每条新断言配一个会触发它的合成样本 + 一个「健康样本必须零问题」的正对照
    （否则样本红了也说明不了什么）。一次性变异做完就没了，下一个人重构判据时不会再触发。
  - **断言的是「恰好由哪条判据报错」，不是「有没有红」**：洗白样本断言 `problems.length === 2`
    且两条都指名 `belowBarBudget`；上限样本断言 `length === 1`。**「有红」不等于「是这条抓住的」。**
  - **另跑了一次真表变异证明接线是活的**（纯函数全对不等于真表那条线接通了）：把真表里一条 unread
    改成 below_bar、附处置、并把 `unreadBudget` 16→15，**只有棘轮那条测试红，处置那条仍绿**——
    与设计预期的洗白形态完全吻合。事后按备份拷回并核 sha 一致（`git checkout <file>` 会连未提交改动一起冲掉，不用）。
- **本节验证**：验收 38/38、全量 2955 例（2954 通过 / 1 跳过 / 0 失败）、`typecheck` 干净、
  `land-change` 的 Native 门禁（fmt + clippy -D warnings + Rust 测试）全过。已 ff 推 `origin/master`。

## 2. aidcp-edge — 16 条 unread 逐条读并分类

> 每条产出：状态（confirmed / below_bar / not_applicable）+ **可复核证据**（指向具体判据代码的 `文件:行`）。
> 只给结论词不给证据的不算读过。读的结果**不预判**，不为了数字好看放松判据（design D1）。

- [x] 2.1 `facebook_auth_submit_login` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.2 `facebook_auth_enter_totp` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.3 `facebook_auth_submit_totp` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.4 `facebook_auth_clear_totp` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.5 `facebook_auth_dismiss_warning` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.6 `facebook_auth_close_push_blocker` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.7 `facebook_auth_confirm_remember_password` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.8 `plan_execute` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.9 `profile_open` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.10 `notification_open` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.11 `notification_browse_comments` <!-- aidcp-edge 7355bb1 → below_bar；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.12 `notification_browse_likes` <!-- aidcp-edge 7355bb1 → below_bar；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.13 `notification_browse_follows` <!-- aidcp-edge 7355bb1 → below_bar；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.14 `notification_back_home` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.15 `identity_read_self_profile` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.16 `publish_navigate_entry` <!-- aidcp-edge 7355bb1 → confirmed；证据逐条写在盘点表该条的 evidence 里（带 `文件:行`） -->
- [x] 2.17 `unreadBudget` 归零；分类结果单独成一次提交，**不与 §3 的判据修复混在一起**（便于事后分辨哪些是读出来的、哪些是改出来的）
  <!-- aidcp-edge 7355bb1（纯分类，零判据改动）→ `unreadBudget` 16→0；`belowBarBudget` 3→6。
       §3 的两处更正另成一次提交 9ecab93，两次分开正是为了事后分得清「读出来的」与「改出来的」 -->
- [x] 2.18 统计落 below_bar 的比例。**若过半**，说明建表时的 confirmed 标准与实读标准有系统性差异 → 回头复核已记 confirmed 的 22 条，并在此记录结论（design Open Questions）
  <!-- aidcp-edge 7355bb1 -->
  - **结论：3 / 16 落 below_bar，远未过半，回头复核那 22 条的触发条件不成立。** 而且这 3 条是**同一处**
    （通知分类浏览的三支共用一段代码），不是三处独立判断 —— 按「独立判断」算只有 1 / 14。
  - **但读出了另一件同族的事，比比例更该记**：建表时的分类**有一条是错的**（`search_execute` 记 below_bar，
    而那条折叠早在建表前两天就被另一条流修掉了，见 3.1）。**系统性差异确实存在，方向却与 Open Question 猜的相反**——
    不是判据标准偏松，是**照抄旧登记、没回头读代码**。这类错误比标准偏差更难被发现：它长得跟一条正常的
    待办一模一样。**下次建这种表，「证据」一栏必须写成当场读出来的 `文件:行`，不许引用另一份登记的结论。**

## 3. aidcp-edge — 已知不达标项的修复

- [x] 3.1 `search_execute`（判据把「读不到」折成「读到了一个否」）：**先核属主**——此前登记的「并入会话守卫流」那条路已断（该 change 2026-08-01 归档），「实现点在单写区属主处」的那个属主是否仍活着须当场查。属主仍在 → 交还并登记；属主已不在 → 本 change 直接修（design D5）
  <!-- aidcp-edge 9ecab93 → 改判 confirmed。**两条去处都不用走了：这条缺陷已经不存在。** -->
  - **核出来的事实**：修它的正是那条「会话守卫流」（`restore-native-xiaohongshu-session-guards`），
    落在 `aidcp-edge bfaa33d`（2026-07-29），该 change 2026-08-01 归档。提交说明与新增注释**逐字点名**
    这条折叠的机制（`unwrap_or(false)` 把「探针自炸」读成「页面上确实没有搜索框」），
    并在 `execute_search` 的几何探针（`engine.rs:1026`）与状态探针（`:2688`）两处都加了 `evaluated_value` 守卫。
  - **时间线是这条的关键**：守卫 07-29 落地，而本盘点表建表是 08-01（`fcb1fd2`）——**登记比修复晚两天，
    却写着它还坏着**。原登记（那条 change 的 §9.5-1）自己就写了「另一条流可能正压着这块」，那条流已经压完了。
  - **剩下的一处不改，如实记**：`unwrap_or(false)` 本身还在，但只有「页内脚本返回结构漂移」这一**假想态**
    才折叠，而该脚本（`xhs-search-input-geometry.js:28/41`）每条返回分支都带齐 found / focused / value。
    为一个假想态去动 `engine.rs`（并行开发点名的热点文件）不划算。
- [x] 3.2 `publish_upload_image`：判据由「该序号位有预览图」改为按**本次上传**的标识回读，须能区分「本次产生的」与「之前就在的」；残留预览不得再满足判据（design D6）
  <!-- aidcp-edge 20fc70a -->
  - **改法**：写文件**之前**先取一份预览位身份基线，写之后有界轮询（5s / 250ms）等目标序号位出现
    **基线里没有的**身份。身份 = 图片地址的长度 + FNV-1a 摘要，在页内算好，**地址本身不过 IPC**
    （调用方只需要判等）。摘要碰撞会把新图读成旧图 —— 悲观方向，造不出假成功。
  - **四种终局四个原因码，一条都不压成另一条**：基线读不到（**在写文件之前**停手，回 not_started）/
    那一位一直没出现 / 出现了但身份读不出来 / 出现了但还是基线里那张（后三者 ambiguous）。
    身份标志缺席时按「读不出来」算，绝不当成新图。
  - **⚠️ 这条不是原任务假设的「纯本地小改」，实读之后换了落法。** 判据原文在
    `xhs-command-router.js:985-988`，而那是 `restore-native-xiaohongshu-action-honesty` 的**单写区**，
    且属主已经改过**同一个 `if` 块**的设封面那半（`52a2110`）。所以走本仓现成的第三条路
    ——**引擎特化**：`engine.rs` 截走这条命令，共享读数落在特化支撑分片 `xhs-input-targets.js`
    （其属主 change 已归档、无活写者），**属主文件一行没碰**。与评论提交 / 正文填写 / 话题三条同族。
  - **交给属主的待办（本轮没删，也没加任何注释标记）**：路由里
    `if(kind==='publish_upload_image')return done(action('upload_image',true));` 这一行现已不可达。
    **只删这一行** —— 同一个 `if` 块里 `publish_set_cover` 那半仍然活着，整块删掉会把设封面一起删没。
- [x] 3.3 `publish_add_with_candidate` 的 mention / location / collection 三支：结构接受信号需真机标定（backlog 簇 123.34）。标定前保持 below_bar 带具名处置，**不得记 confirmed**（无证据）、**也不得记 not_applicable**（它们结构上有可读回的业务结果，用「读不出来」冒充「本来就没有」是另一种假成功）（design D7）
  <!-- aidcp-edge 72bc3d9（处置落表）+ 控制仓 backlog 123.34 补了反向指针 -->
  - 处置按 `kind:exception` 记，`blockedBy` 直指 backlog 簇 123.34；`owner` 一栏把「两个都不许记」那句
    钉进表里，不靠人记住。**反向也补了**：123.34 那条现在写着「标定完成后去把盘点记录一并改掉」，
    否则处置会变成一条永远等不到的待办。
- [x] 3.4 §2 读出的新增 below_bar 项：逐条排修复或具名例外。**Facebook 登录面若修复面过大**，按 design 风险条转成带具名处置的 below_bar 并单独立项，不在本 change 里硬做
  <!-- aidcp-edge 9ecab93（处置改指真属主）+ 控制仓 E14 登记 -->
  - **Facebook 登录面那条风险没有发生**：7 条全部读下来是 confirmed，一条都不用修。
  - **新增的 3 条（通知分类浏览）按具名例外交给单写区属主，不在本 change 里改。**
    它们落在 `xhs-command-router.js:649-676`，该文件的单写区属主是
    `restore-native-xiaohongshu-action-honesty`（2026-08-01 复核仍活跃 40/56，且当前**没有 worktree
    压着**）。与 E13 同一个文件、同一种形态、同一处置 —— 发现方无权改属主的热点文件。
  - **已登记为 `docs/edge-honesty-gap-inventory.md` 的 E14**（判据现成：同文件 `:398` 的 `tabBadgeCount`
    已在读每类未读角标，取切栏前后两次读数即可）。顺手修正了该文件头部滞后的计数（12 → 14，E13 加入时漏改）。

## 4. aidcp-edge — 验证

- [x] 4.1 每条改动过判据的命令补 / 改脱机用例：断言「读不到」与「读到否」两态可分、断言证据与本次动作绑定
  <!-- aidcp-edge 20fc70a：新增 `native/page-engine/tests/xhs_publish_upload_binding.rs`，5 例 -->
  - 两态可分那条钉了**三个**终局而不是两个：显式「身份读不出来」/ 身份标志**缺席** / 那一位确实没有，
    三者原因码互不相同。绑定那条同时断言**附件确实写下去了**——否则「不确定」会被误读成「没开始」。
- **本节口径说明**：§2 是只读通读、没改任何命令的判据，§3.1 判定不改，§3.3 / §3.4 转交属主，
  所以「改动过判据的命令」实际只有 3.2 一条。**写出来是为了让下一个人知道这不是漏了。**
- [x] 4.2 变异检验：对 3.2 的「绑定本次」判据做一次变异（退回成「有预览图即可」），确认有用例红，并记下**是哪一条**抓住的
  <!-- aidcp-edge 20fc70a：做了三次，逐条归因；源码事后按备份拷回并核 sha 一致 -->
  - ① 删掉「与基线比对」那一支（退回成「有预览图即可」）→ 残留预览那条红。
  - ② 身份标志缺席时的默认由悲观改成乐观 → 两态那条红。
  - ③ 基线读不到时不停手、继续用空基线写下去 → 「写之前停手」那条红。
  - **② 第一次跑是绿的，这件事比三条都红更值得记**：那个悲观默认当时**一处都不承重**——
    所有夹具都显式给了标志，缺省分支根本走不到。补了「标志缺席」那条用例之后它才咬住。
    **变异要问「哪条用例抓住的」，不能只问「有没有红」**；而「没红」的正确读法是
    **判据没被覆盖**，不是「判据没问题」。
  - Rust 侧每次都确认输出里出现 `Compiling`，否则测的是编辑之前的旧二进制。
- [x] 4.3 门禁自检回归：1.6 的两条负样本保留为常驻用例，防止棘轮日后被改松
  <!-- aidcp-edge 72bc3d9 立、9ecab93 加固：4 条常驻自测（1 正对照 + 3 负样本），且负样本带**自己的**上限，
       真上限 16→0 之后仍然承重。原任务要求两条，实装 3 条负样本（多的那条：判据修达标后处置没摘掉） -->
- [x] 4.4 全量闸：`cargo test --locked` / `cargo fmt --check` / `clippy -D warnings` / `npm run gate:native` / `npm run typecheck` / `npm run test:acceptance` / `npm test`
  <!-- aidcp-edge 20fc70a：Rust 355 例 0 失败（`RUST_TEST_THREADS=1 cargo test --locked`）、
       `cargo fmt --check` 通过、`clippy --all-targets -- -D warnings` 无告警、
       验收 38/38、全量 2955 例（2954 通过 / 1 跳过 / 0 失败）、`typecheck` 干净；
       `land-change` 的 `gate:native` 同批全过。工具链 1.97.1-aarch64-apple-darwin（不在默认 PATH） -->

## 5. aidcp-edge — 收口

- [x] 5.1 提交 + 推送 `aidcp-edge` master；本仓 tasks.md 按 `<!-- <repo> <sha> 备注 -->` 回写（sha 取自**已推送**提交）
  <!-- 四次落地，均已 ff 推 origin/master：72bc3d9（§1 棘轮与处置）/ 7355bb1（§2 分类，纯读）/
       9ecab93（§3.1 改判 + §3.4 转交）/ 20fc70a（§3.2 绑定本次上传）。四个 sha 都取自已推送提交 -->
- [x] 5.2 真机项登记到 `docs/real-machine-acceptance-backlog.md`：候选项三支的结构接受信号标定（并入簇 123.34，不新开簇）
  <!-- 控制仓：123.34 已存在且覆盖这三支，按要求**未新开簇**，只补了指回盘点表的反向指针 -->
- [x] 5.3 真机项登记：§2 读出的、只有真机能判定的判据（若有），按面归入既有簇
  <!-- 无新增真机项：§2 的 16 条全部在代码上判得出来（13 条判据够强、3 条判据缺失且判据所需读数已在同文件内）。
       **「没有」也要写出来**，否则下一个人无从分辨是「查过了没有」还是「忘了查」 -->
- [x] 5.4 归档前按 handoff §12.1 逐条对读 delta 与实装，**至少读两遍、第二遍在修完之后**
  <!-- aidcp-edge 24131eb（对读发现的那处缺口的修复）+ 本次回写 -->
  - **对读抓到一处实装没跟上，已补**：delta 那条 scenario 写的是「把 unread 改成 below_bar 时，
    **抬 below_bar 预算这个动作本身会被拒**」，而实装只给 unread 加了上限字面量。
    后果是：真按规矩同时把 below_bar 预算加一，两个预算都还等于各自实际条数、门禁全绿，
    而那条命令的风险一点没变 —— **正是这条要求要堵的那条路，换了个更体面的走法**。
    已补上 below_bar 的上限字面量（与 unread 同构，design D2 要的就是同构），
    并加了一条「按规矩抬预算」的负样本，由上限那条单独抓住。
  - **其余逐条对得上**：机械覆盖全部写命令（恰好相等）/ 四态之分 / 两个预算都不留空位 /
    处置必填与两种形态 / 具名例外指向**具体**真机条目（簇 123.34，不是泛指真机）/
    未读归零后恒零。三条 scenario 各有常驻样本承重。
  - **MODIFIED 目标名按 §5 的判据逐行精确核过**：
    `grep -qxF "### Requirement: Native page writes MUST be validated against the acted-upon target"`
    在主 spec 命中（注意 `### Requirement:` 后面那个空格，少算一格会全体误报）。
- [x] 5.5 开工前与收口前各跑一次 `openspec list`，核对 `engine.rs` / `facebook/auth.rs` 有无并行流压着（这两个是点名热点，须串行）
  <!-- 开工前 + 收口前各跑一次（2026-08-01） -->
  - `facebook/auth.rs`：**一行未改**（§2 对那 7 条只做通读）。
  - `engine.rs`：§3.2 改了（新增上传特化 + 两个辅助函数，替掉原 `verify_uploaded_preview`）。
    落地前核过：点名共写它的两条活跃 change（`restore-native-facebook-residual-parity` /
    `harden-native-engine-runtime-contracts`）改的是 Facebook 与运行时契约两块，与小红书发布分支不重叠；
    `land-change` 的 rebase 也无冲突。
  - **`xhs-command-router.js` 才是本轮真正的串行约束**（原任务没点名它）：它是
    `restore-native-xiaohongshu-action-honesty` 的单写区，本 change **一行未碰**，见 3.2 与 3.4。
