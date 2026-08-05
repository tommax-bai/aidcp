## 1. aidcp-edge — 观测层（Facebook auth 路由，`native/page-engine/src/facebook-router/06-auth.js`）

- [x] 1.1 给 `authObservation` 增加一个**只进摘要、不进返回值**的附加证据入参（返回对象结构必须一字不变——Rust 侧 `FacebookAuthObservation` 是 `deny_unknown_fields`，多一个字段就整条反序列化失败）
  <!-- aidcp-edge 313b2e1 authObservation 增加 extraEvidence 入参，只进摘要不进返回对象 -->
- [x] 1.2 `authLoginObservation` 在产出 `login_submit_ready` 时，把两个凭据框内容的**字符数**（形如 `emailLen:passwordLen`）经 1.1 的入参并入 signalId 摘要；MUST NOT 把字符内容并入摘要，MUST NOT 把长度写进返回对象、回执或日志
  <!-- aidcp-edge 313b2e1 并入 `fill:<邮箱长度>:<密码长度>`，只有长度 -->
- [x] 1.3 `authLoginObservation` 的「任一框为空」分支改为**恒回** `none` + `credential_fill_pending`，不再自行宣告 `manual_login_required` / `credential_fill_unavailable`（时间判断整体交给协调层，见 2.3）
  <!-- aidcp-edge 313b2e1 空框恒回 none + credential_fill_pending -->
- [x] 1.4 删除 `facebookAuthCredentialFillGraceMs` 常量与 `authWithinHydrationGrace` 在该处的唯一调用点——闸移走之后不留一个永不触发的死分支（其余三个 hydration grace 常量与调用点不动）
  <!-- aidcp-edge 313b2e1 facebookAuthCredentialFillGraceMs 常量与调用点已删 -->
- [x] 1.5 核对 `authPostcondition` 的 `login_submit_ready` 分支：它比对的是 `p.candidateKey`（按钮证据摘要）而非 signalId，指纹扩展后**不应**改变其行为；就地补一行注释写明这条边界，防止后续误以为两者同源
  <!-- aidcp-edge 313b2e1 已就地注释：postcondition 比 candidateKey，与 signalId 不同源 -->

## 2. aidcp-edge — 协调层（首登协调器，`src/native-page-engine/facebook-auth.ts`）

- [x] 2.1 新增三个具名常量并导出供用例按引用断言：`CREDENTIAL_SETTLE_MS = 1_500`、`CREDENTIAL_FILL_GRACE_MS = 45_000`、`MAX_STALE_LOGIN_SIGNAL_RETRIES = 5`
  <!-- aidcp-edge 313b2e1 三个常量已导出，用例按引用断言 -->
- [x] 2.2 安定窗口：协调器记住上一次 `login_submit_ready` 的 signalId 与首次观测时刻；signalId 变化即重置计时；跨度未达 `CREDENTIAL_SETTLE_MS` 时按节拍继续等待、**不下发**动作
  <!-- aidcp-edge 313b2e1 id 变即重置；未满窗等满剩余安定时长再复读 -->
- [x] 2.3 填充宽限期：记住第一次拿到 `credential_fill_pending` 的时刻作为锚点；`login_form_hydrating` / `login_fields_hydrating` 不启动也不推进该锚点；自锚点起超过 `CREDENTIAL_FILL_GRACE_MS` 仍未安定 → 返回 `manual_required` + `credential_fill_unavailable`（原因值与保活语义保持不变）
  <!-- aidcp-edge 313b2e1 锚点 = 首个 credential_fill_pending；hydrating 拍点不消耗 -->
- [x] 2.4 `stale_auth_signal` 有界恢复：`facebook_auth_submit_login` 回执为 `ok=false` 且 `reason=stale_auth_signal` 且 `effectPhase=not_started` 时，丢弃该观测、重新探测、在预算内继续，累计不超过 `MAX_STALE_LOGIN_SIGNAL_RETRIES` 次；MUST NOT 落终态、MUST NOT 关浏览器、MUST NOT 重放同一 signalId
  <!-- aidcp-edge 313b2e1 STALE_LOGIN_SIGNAL 符号出口 + 有界重来 -->
- [x] 2.5 划清恢复边界：`Ambiguous` 回执、任何**可能已发出输入**的回执、以及其它 refusal 原因（`auth_signal_already_consumed` / `auth_signal_budget_exhausted` / `auth_action_cancelled_or_expired`）一律维持既有终局语义，不得被 2.4 顺手放行
  <!-- aidcp-edge 313b2e1 恢复出口三条件缺一不可；ambiguous 与其它拒绝原因维持终局 -->
- [x] 2.6 恢复预算只由失败消费：安定等待与宽限期等待**不**计入 2.4 的重试计数；超出计数时给出可与「凭据被拒」区分的具名原因
  <!-- aidcp-edge 313b2e1 超限报 credential_fill_unsettled，与凭据被拒可区分 -->

## 3. aidcp-edge — 用例（守卫必须能被违规输入打红）

- [x] 3.1 `native/page-engine/tests/facebook_auth.rs`：新增用例断言同一登录表单在**凭据长度不同**的两次观测下产出**不同** signalId；并断言观测返回结构未新增字段（`deny_unknown_fields` 反向锁）
  <!-- aidcp-edge 313b2e1 偏离：指纹用例落在 TS jsdom 路由套件（Rust 用例桩住 CDP 求值、跑不到路由 JS）；结构反向锁同处。Rust 侧 assert_refused 已独立锁住 stale_auth_signal↔NotStarted -->
- [x] 3.2 `test/native-page-engine/facebook-auth.test.ts`：喂「密码逐拍变长」的探测序列，断言在安定窗口未满前**一次动作都不下发**；把序列改成「长度稳定」后断言恰好下发一次
  <!-- aidcp-edge 313b2e1 a growing password never authorizes submission… -->
- [x] 3.3 同文件：喂「首个 `credential_fill_pending` 之后长期为空」的序列，断言恰好在 `CREDENTIAL_FILL_GRACE_MS` 之后才出 `credential_fill_unavailable`，且 `login_form_hydrating` / `login_fields_hydrating` 拍点不消耗预算
  <!-- aidcp-edge 313b2e1 the fill grace is anchored on both fields appearing… -->
- [x] 3.4 同文件：喂 `stale_auth_signal` + `not_started` 回执，断言协调器继续而非终局；喂 `Ambiguous` 回执，断言仍然终局；喂第 6 次连续 stale，断言如实失败且原因可与凭据被拒区分
  <!-- aidcp-edge 313b2e1 三条：re-probes / bounded budget / ambiguous 不被搭救 -->
- [x] 3.5 反向锁：断言观测层在**任何文档年龄**下都不再产出 `credential_fill_unavailable`（这条判据已整体搬到协调层，观测层再产它就是两处实现漂移）
  <!-- aidcp-edge 313b2e1 empty credentials stay pending at any document age（0/24999/25000/600000 四个文档年龄） -->
- [x] 3.6 变异确认：对 2.2 / 2.3 / 2.4 各做一次就地变异（安定窗口置 0、宽限锚点改回文档年龄、stale 分支删掉），确认每一处都有**具名用例**打红，并记下是哪一条抓住的
  <!-- aidcp-edge 313b2e1 四处变异全部被具名用例打红：安定窗=0→growing password；锚点改回任意拍→fill grace anchored；删恢复分支→superseded 两条；去掉指纹证据→still-typing password -->

## 4. aidcp-edge — 门禁、产物与部署

- [x] 4.1 `npm run gate:native`（fmt / clippy / test 三段；注意 cargo 不在 PATH，需指 rustup toolchain bin）
  <!-- aidcp-edge 313b2e1 fmt/clippy/test 全过，toolchain 1.97.1 -->
- [x] 4.2 `npm run build:native-page-engine` 重建引擎产物——路由 JS 是编进二进制的，不重建等于改动没生效；确认 `manifest.json` 的 `capabilityDigest` 随之更新
  <!-- aidcp-edge 313b2e1 capabilityDigest 已更新为 89c8488c… -->
- [x] 4.3 `npm run test:acceptance` → `npm test` → `npm run typecheck`（按本仓回归纪律的顺序）
  <!-- aidcp-edge 313b2e1 acceptance 39/39；全量 3145 pass（一次 flaky 命中无关的传输重建用例，复跑全绿）；typecheck 干净 -->
- [x] 4.4 提交并推送 `master`；控制仓 tasks.md 按 `<!-- <repo> <commit-sha> 备注 -->` 回写 sha（sha 必须取自**已推送**的提交）
  <!-- aidcp-edge 313b2e1 经 scripts/land-change ff 推送 origin/master -->
- [x] 4.5 本改动只落边缘、不改协议、不改云端——确认无需 dev 部署；若需随桌面客户端出包，按用户显式触发再打包（默认不打）
  <!-- aidcp-edge 313b2e1 只落边缘、不改协议、无需 dev 部署；**未打安装包**——运营机行为要换包才变 -->

## 5. 真机验收（共享真机环境，解耦登记）

- [x] 5.1 **【按用户裁定清账 2026-08-05：真机验收 / 出包类不再登记、不再统计，直接归档。此勾表示「按裁定清账」，MUST NOT 读成「已验证」】** 在一个 `password` 命名的环境上重跑完整首登流程，断言：判定就绪时密码字符数等于存储值长度、提交一次即通过、不再出现「The password you entered is incorrect」
- [x] 5.2 **【按用户裁定清账 2026-08-05：真机验收 / 出包类不再登记、不再统计，直接归档。此勾表示「按裁定清账」，MUST NOT 读成「已验证」】** 在一个「填充中途被页面重绘清空」的环境上验证：45s 宽限期到点后进入人工登录等待，浏览器与 CDP 保活、未被杀
- [x] 5.3 验收项按共享真机环境归簇登记到 `docs/real-machine-acceptance-backlog.md`，不阻塞归档
  <!-- aidcp-edge 313b2e1 docs/real-machine-acceptance-backlog.md 新增簇 133，并更正簇 131.7 里「password 那批只能人工」的旧口径 -->
- [x] 5.4 **【按用户裁定清账 2026-08-05：真机验收 / 出包类不再登记、不再统计，直接归档。此勾表示「按裁定清账」，MUST NOT 读成「已验证」】** 运营侧回填：验收通过后，把被本缺陷改名的环境（9 个 `password`）名称按实际登录态还原；`checkpoint` / `locked` 两类的解除不在本变更范围，单独登记
