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

- [ ] 2.1 `facebook_auth_submit_login`
- [ ] 2.2 `facebook_auth_enter_totp`
- [ ] 2.3 `facebook_auth_submit_totp`
- [ ] 2.4 `facebook_auth_clear_totp`
- [ ] 2.5 `facebook_auth_dismiss_warning`
- [ ] 2.6 `facebook_auth_close_push_blocker`
- [ ] 2.7 `facebook_auth_confirm_remember_password`
- [ ] 2.8 `plan_execute`
- [ ] 2.9 `profile_open`
- [ ] 2.10 `notification_open`
- [ ] 2.11 `notification_browse_comments`
- [ ] 2.12 `notification_browse_likes`
- [ ] 2.13 `notification_browse_follows`
- [ ] 2.14 `notification_back_home`
- [ ] 2.15 `identity_read_self_profile`
- [ ] 2.16 `publish_navigate_entry`
- [ ] 2.17 `unreadBudget` 归零；分类结果单独成一次提交，**不与 §3 的判据修复混在一起**（便于事后分辨哪些是读出来的、哪些是改出来的）
- [ ] 2.18 统计落 below_bar 的比例。**若过半**，说明建表时的 confirmed 标准与实读标准有系统性差异 → 回头复核已记 confirmed 的 22 条，并在此记录结论（design Open Questions）

## 3. aidcp-edge — 已知不达标项的修复

- [ ] 3.1 `search_execute`（判据把「读不到」折成「读到了一个否」）：**先核属主**——此前登记的「并入会话守卫流」那条路已断（该 change 2026-08-01 归档），「实现点在单写区属主处」的那个属主是否仍活着须当场查。属主仍在 → 交还并登记；属主已不在 → 本 change 直接修（design D5）
- [ ] 3.2 `publish_upload_image`：判据由「该序号位有预览图」改为按**本次上传**的标识回读，须能区分「本次产生的」与「之前就在的」；残留预览不得再满足判据（design D6）
- [ ] 3.3 `publish_add_with_candidate` 的 mention / location / collection 三支：结构接受信号需真机标定（backlog 簇 123.34）。标定前保持 below_bar 带具名处置，**不得记 confirmed**（无证据）、**也不得记 not_applicable**（它们结构上有可读回的业务结果，用「读不出来」冒充「本来就没有」是另一种假成功）（design D7）
- [ ] 3.4 §2 读出的新增 below_bar 项：逐条排修复或具名例外。**Facebook 登录面若修复面过大**，按 design 风险条转成带具名处置的 below_bar 并单独立项，不在本 change 里硬做

## 4. aidcp-edge — 验证

- [ ] 4.1 每条改动过判据的命令补 / 改脱机用例：断言「读不到」与「读到否」两态可分、断言证据与本次动作绑定
- [ ] 4.2 变异检验：对 3.2 的「绑定本次」判据做一次变异（退回成「有预览图即可」），确认有用例红，并记下**是哪一条**抓住的
- [ ] 4.3 门禁自检回归：1.6 的两条负样本保留为常驻用例，防止棘轮日后被改松
- [ ] 4.4 全量闸：`cargo test --locked` / `cargo fmt --check` / `clippy -D warnings` / `npm run gate:native` / `npm run typecheck` / `npm run test:acceptance` / `npm test`

## 5. aidcp-edge — 收口

- [ ] 5.1 提交 + 推送 `aidcp-edge` master；本仓 tasks.md 按 `<!-- <repo> <sha> 备注 -->` 回写（sha 取自**已推送**提交）
- [ ] 5.2 真机项登记到 `docs/real-machine-acceptance-backlog.md`：候选项三支的结构接受信号标定（并入簇 123.34，不新开簇）
- [ ] 5.3 真机项登记：§2 读出的、只有真机能判定的判据（若有），按面归入既有簇
- [ ] 5.4 归档前按 handoff §12.1 逐条对读 delta 与实装，**至少读两遍、第二遍在修完之后**
- [ ] 5.5 开工前与收口前各跑一次 `openspec list`，核对 `engine.rs` / `facebook/auth.rs` 有无并行流压着（这两个是点名热点，须串行）
