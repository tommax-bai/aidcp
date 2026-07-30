# Tasks

> 前置依赖：`facebook-rule-mode-cadence`、`facebook-global-group-regional-comment-templates` 与 `facebook-join-contact-first-post` 的能力规格尚未并入 `openspec/specs/`。本变更的 `facebook-rule-mode` delta MUST NOT 先于它们归档而生效。与 `environment-level-rule-mode-and-approval` 无功能耦合，可并行实装。

## 1. aidcp-cloud — 两道纯拦截闸的规则模式旁路

- [x] 1.1 会话启动闸增加规则模式豁免：平台为 Facebook 且权威规则模式配置为启用时，未绑人设不短路、不置 `needs_persona_setup`、不告警。
- [x] 1.2 豁免判据与启动闸同源现读权威配置；配置不可读、绑定不可解析或平台未确认为 Facebook 时 fail-closed 回到未豁免行为。
- [x] 1.3 模式裁决闸取消绑定人设入口闸，且 MUST 保持在慢启动绝对优先权与其 fail-closed 判据**之后**判定，顺序不得调换。
- [x] 1.4 补测：未绑人设 + 规则模式启用 → 正常起会话；未绑人设 + 规则模式关闭 → 仍短路；配置读失败 → 仍短路；慢启动激活 → 仍由慢启动接管而非规则模式。

## 2. aidcp-cloud — 评论段正文方案收窄

- [x] 2.1 规则批次在调用加群联系评论编排之前解析一次有效正文方案（账号显式模板 / 账号未显式选择的默认模板 / 账号显式生成）。
- [x] 2.2 有效方案为模板时评论段照常执行，正文继续按账号模板优先、区域模板兜底解析。
- [x] 2.3 有效方案为显式生成时，评论段以稳定具名原因收敛为不可执行；批次保留浏览与点赞结果并如实呈现为部分完成；MUST NOT 调用生成器、MUST NOT 以模板顶替该显式选择。
- [x] 2.4 评论触发口的人设闸改为按来源与有效正文方案分流：规则批次的模板正文放行，其余来源与生成式正文逐字保持既有拒绝行为。
- [x] 2.5 确认模板正文继续经过确定性正文校验、联系方式分离注入、审批策略、目标复核、平台确认与真实终态记录，逐条补回归测试。
- [x] 2.6 补测：区域模板缺失仍按既有具名停止收敛，MUST NOT 回落生成器或任意默认文本。

## 3. aidcp-cloud — 例外边界回归

- [x] 3.1 逐条回归：普通浏览、发布、飞书手工评论、排期评论、mandatory 评论对未绑人设账号仍以 `no_persona` 诚实拒绝，不受规则模式例外影响。
- [x] 3.2 回归人设解析器行为一字未变：仍返回明确的「无人设」信号，系统仍不存在默认或兜底人设。
- [x] 3.3 回归规则定义版本、风控、配额、去重、目标复核与平台确认未因本变更改变。

## 4. Console 与 Edge — 呈现口径

<!-- Edge 侧已交付（aidcp-edge ed2559e：27c2a9a 呈现 + e0471ac 事实过期时横幅不闪），含 ui-logic / persona-notice / fleet-console 测试。Console 侧未做。 -->

- [ ] 4.1 未绑人设且已启用规则模式的账号呈现为「按规则运行、未绑人设」，MUST NOT 呈现为待补人设，MUST NOT 呈现为已绑。
- [ ] 4.2 该态下不弹出人设向导、不发补人设引导，其它未绑人设账号的既有引导不受影响。
- [ ] 4.3 补对应前端与客户端测试。

## 5. 验证与集成

<!-- aidcp-cloud 8b31e97 / aidcp-edge ed2559e — land-change 跑完 acceptance+全量+typecheck 才 ff 推送 -->
<!-- 2026-07-28 deployed dev — schema 契约门 enforce 三属主全通过；飞书长连接已建立；8787/8090 在听 -->
<!-- 2026-07-30 Console 4.1-4.3 纳入本变更后重新打开 5.1-5.3；旧证据只覆盖 Cloud/Edge，不能替代本次 Console 验证与集成。 -->

- [ ] 5.1 各仓跑聚焦测试 → 全量测试 → typecheck，输出有界记录。
- [ ] 5.2 各 worktree rebase 到最新默认分支、重跑必需验证、fast-forward 集成并推送，回写本清单的 commit-sha。
- [ ] 5.3 `openspec validate facebook-rule-mode-without-persona --strict` 通过。

## 6. 交付边界

- [x] 6.1 Cloud 运行时变更验证后部署 DEV。
- [ ] 6.2 OL 部署、Edge 打包签名与真实账号 Facebook 写入验收不在本变更范围，分别作为独立事实报告。
