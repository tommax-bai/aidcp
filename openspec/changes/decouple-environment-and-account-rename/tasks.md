## 1. aidcp-edge — 改名两路解耦

- [x] 1.1 加聚焦回归：云端别名写失败时本地名字保留不回滚，且回执分别标注本地与云端两路结果。<!-- aidcp-edge 690eb70 变异验证：回滚突变与「云端没成也报已保存」文案突变各被预期用例抓红 -->
- [x] 1.2 拆开改名处理：本地写入与云端写入各自成败，取消「云端失败即回滚本地」。<!-- aidcp-edge 690eb70 同时删掉「本地确认失败就回滚云端」那条路径——两路独立后它不再成立 -->
- [x] 1.3 本地一路同时改指纹浏览器分身名，失败只如实报告、不阻塞其余两路；非 AdsPower 环境跳过该步。<!-- aidcp-edge 690eb70 清空人工名不动分身名（命名权交回系统跟随） -->
- [x] 1.4 回执按两路结果分别成文，并把云端「环境尚未绑定账号」译成运营可读文案。<!-- aidcp-edge 690eb70 文案组装析出为 ui-logic 纯函数以便按行为断言；未收录原因原样带出 -->

## 2. 验证与交付

- [x] 2.1 跑聚焦测试与 `npm run typecheck`。<!-- aidcp-edge 690eb70 -->
- [x] 2.2 跑 `npm run test:acceptance` 与全量测试，跑 `openspec validate decouple-environment-and-account-rename --strict`。<!-- aidcp-edge 690eb70 -->
- [x] 2.3 提交、推送、回写交付证据（不打安装包）。<!-- aidcp-edge 690eb70 pushed to origin/master -->

## Evidence

- Edge 实装：`aidcp-edge` commit `690eb70`（land 时 rebase 到 `origin/master`），已 ff 推送。
- 聚焦验证：`test/electron/*.test.ts` 1074 passed / 0 failed / 1 skipped；`npm run typecheck` 通过；`git diff --check` 干净。
- 发布前验证：`npm run test:acceptance` 39 passed（AC-PROTO / AC-PUB / AC-RISK 全过）；全量 `test/**/*.test.ts` exit 0；`land-change` 内的 `gate:native`（fmt / clippy / test）通过。
- 变异验证（确认用例承重而非仅仅变红）：① 把云端失败分支改回 `saveSettings({ environments: previousEnvironments })` → 「云端别名失败绝不回滚本地名字」当场红；② 把回执文案改成任何情况都返回「已保存人工昵称…」→ 逐路点名的四条用例当场红。两处突变均已还原。
- 控制仓：`openspec validate decouple-environment-and-account-rename --strict` 通过。
- 交付边界：仅源码与 OpenSpec。**未打安装包、未部署**——本变更纯客户端，运营机要拿到它需要另行出包（按 CLAUDE.md §6 打包属用户显式触发）。renderer 不热加载，本机验证也需重启客户端。

## 真机验收（未做，登记待办）

- 未绑定账号的环境（实测样本 `k1fd37qr`，云端 `client_environments.account_id` 为空）双击改名：应当左栏名字留住、指纹浏览器分身名同步改掉、提示明说云端昵称未改且原因为「尚未完成首次登录」。
- 已登录环境改名：三路全成，提示为「已保存人工昵称…后续系统更新不会覆盖」，云端后台与飞书卡片显示新名。
