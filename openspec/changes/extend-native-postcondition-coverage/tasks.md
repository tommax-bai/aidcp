# Tasks

> 全部工作落 `aidcp-edge` 一个仓。云端 / console / 协议均不涉及。
> 真机验收项**不进本文件**（2026-08-01 裁定），登记到 `docs/real-machine-acceptance-backlog.md`，见 §5。
> **§2 是「读」，§3 是「按读到的结果修」**。§3 的具体条目在 §2 完成前**故意不预列** —— 预列等于预判分类结果。

## 1. aidcp-edge — 盘点表的棘轮与处置（先做，防止后面一边读一边洗白）

- [ ] 1.1 `native/page-engine/command-postconditions.json` 增 `belowBarBudget`，初值＝当前实际条数（3）
- [ ] 1.2 `test/native-page-engine/command-postconditions.test.ts` 增断言：below_bar 条数 ≤ `belowBarBudget`，且 `belowBarBudget` **恰等于**实际条数（不留空位，与 unread 同构）
- [ ] 1.3 盘点表增 below_bar 必填处置字段：消除动作，或具名例外（理由 + 前置 + 谁来解）；门禁断言缺失即失败
- [ ] 1.4 给现存 3 条 below_bar 补处置：搜索输入＝属主待核（见 3.1）、上传配图＝可直接修（见 3.2）、候选项三支＝真机前置（指到 backlog 簇 123.34）
- [ ] 1.5 门禁增断言：`unreadBudget` 归零后恒为 0，不得抬起（今天只断言「不许上调」，归零后语义更强）
- [ ] 1.6 **让门禁先抓一次自己**：造一条「unread 改 below_bar 但不抬 belowBarBudget」的样本，确认门禁当场红；再造一条「below_bar 无处置」的样本，确认同样红。**首跑不红就说明断言写虚了**

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
