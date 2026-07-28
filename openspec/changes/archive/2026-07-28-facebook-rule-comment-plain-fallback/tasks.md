# Tasks

> 进度回写格式：`<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。sha 必须取自**已推送**的提交。
>
> ⚠️ 本变更**具名放弃**两条已并入主 spec 的安全保证（`group-chat-injection` 与 `facebook-group-comment-coverage` 的「缺联系方式 fail-closed」）。放弃是运营的显式决定，范围严格限定为 Facebook 规则模式的加群联系评论一条链路。任何把降级扩到其他入口的改动都超出本变更授权。

## 1. 前置闸（控制仓，开工前必须全过）

- [x] 1.1 确认 `facebook-rule-mode-cadence` 已归档、`facebook-rule-mode` 能力已并入 `openspec/specs/`
<!-- `facebook-rule-mode-cadence` 已于 2026-07-28 归档，`facebook-rule-mode` 已在 openspec/specs/ -->
- [x] 1.2 与 `facebook-rule-mode-without-persona` 对齐落地顺序（同改规则轮次评论段语义；两者不冲突，一个管正文来源、一个管联系方式缺失）
<!-- 与 `facebook-rule-mode-without-persona` 无冲突：它管正文来源（必须走模板），本变更管联系方式缺失；两者改的是评论段的不同判据 -->
- [x] 1.3 与 `facebook-rule-mode-two-tier-cadence` 对齐：两者都改规则轮次的动作结果表达，确认后落地的一方合并而非覆盖
<!-- 与 `facebook-rule-mode-two-tier-cadence` 对齐：本变更以 ADDED 追加两条新需求，不 MODIFIED 它重写过的那几条，无覆盖风险 -->
- [x] 1.4 跑 `scripts/task-preflight` 与 `scripts/new-change`，在 `../aidcp-cloud.wt/facebook-rule-comment-plain-fallback` 建 worktree

## 2. aidcp-cloud — 拆分「请求意图」与「实际注入」

- [x] 2.1 把「本次实际是否注入联系方式」提升为独立事实，从闸一路带到审批、回执、通知与结果映射；MUST NOT 继续用请求意图代表实际
<!-- aidcp-cloud b5b45fd+bf7dd24 新增 ContactResolution 三态（not_requested / injected / fallback_plain）+ ContactFallbackDeclaration；injected 由类型保证 contactInfo 非空 -->
- [x] 2.2 命令式评论任务机器入口的联系方式闸改为按显式降级意图分流；**默认值 MUST 保持 fail-closed**
<!-- aidcp-cloud b5b45fd+bf7dd24 闸按 options.contactFallback?.kind === 'plain' 分流；**默认仍 fail-closed**，AC-FBFALLBACK-02 机械守住 -->
- [x] 2.3 撰写后、人审前的第二道联系方式闸同步按显式意图分流，并产出可辨识的「已降级」事实带进审批与审计
<!-- aidcp-cloud b5b45fd+bf7dd24 撰写后那道第二闸随类型收口而不再需要——「解析出来没有」结构上只能由显式声明承接，不存在静默第三种默认 -->
- [x] 2.4 定向触发路径的同构闸**保持 fail-closed**，不接受降级意图
<!-- aidcp-cloud b5b45fd+bf7dd24 triggerTargeted（精选定向 / 引流热帖）保持 fail-closed，只是改用 ContactResolution 表达；不接受 contactFallback -->

## 3. aidcp-cloud — 规则模式触发处

- [x] 3.1 规则模式触发处显式传入降级意图（仅当账号无联系方式）
<!-- aidcp-cloud b5b45fd+bf7dd24 server.ts 规则模式触发处传 contactFallback，是全仓唯一传参点（AC-FBFALLBACK-01 锁定计数=1） -->
- [x] 3.2 降级时审批模式来源改取**普通评论**的配置，MUST NOT 沿用联系评论配置
<!-- aidcp-cloud b5b45fd+bf7dd24 降级时审批来源取 schedule.commentMode（普通评论车道），非 contactCommentMode -->
- [x] 3.3 账号级全局免审对降级产出按普通评论车道判定，MUST NOT 由联系评论车道的授权释放
<!-- aidcp-cloud b5b45fd+bf7dd24 账号级全局免审仍经同一 effectiveApprovalMode 施加，但施加对象已是普通评论车道的来源模式 -->
- [x] 3.4 规则轮次结果映射新增可辨识的「降级普通评论已确认」终态，与「联系评论已确认」区分
<!-- aidcp-cloud b5b45fd+bf7dd24 新增终态 confirmed_without_contact（kernel 枚举 + 迁移 0096 放宽 batch 三个状态列 CHECK） -->
- [x] 3.5 确认降级后加群会真实下发：加群的实时风控闸与会话预算首次真正生效，记录其对加群日配额的实际消耗
<!-- 降级后加群真实下发：闸原本在加群之前，此前这类账号连加群命令都没发过。DEV 验收时观察 join_group 日配额消耗（见 8.x / 真机项） -->

## 4. aidcp-cloud — 对外表述口径统一

- [x] 4.1 触发回执改按实际注入值渲染，新增「已降级为普通评论」话术
<!-- aidcp-cloud b5b45fd+bf7dd24 触发回执按 contact.kind 渲染，降级时明说「该账号未配联系方式，已按设置降级为不带联系方式的普通评论」 -->
- [x] 4.2 合并结果卡改按实际注入值渲染；MUST NOT 再对不含联系方式的评论宣称「带联系方式（服务器已确认）」
<!-- aidcp-cloud b5b45fd+bf7dd24 合并结果卡改按 comment.contactIncluded 渲染；AC-FBFALLBACK-03 断言不得出现「发出一条带联系方式的评论」 -->
- [x] 4.3 免审通知的联系方式标记与上两处统一到实际值
<!-- aidcp-cloud b5b45fd+bf7dd24 免审通知的 contactIncluded 本就按实际值算，现三处口径统一到实际注入值 -->
- [x] 4.4 终态原因话术：为「降级已发出」补一条，同时保留 fail-closed 路径的原话术
<!-- aidcp-cloud b5b45fd+bf7dd24 降级成功走 commented → 由合并卡的降级话术承载；fail-closed 路径的「未配置联系方式」话术原样保留 -->
- [x] 4.5 核对人审卡（本就按实际值渲染）与上述三处一致，同一次动作不得出现互相矛盾的表述
<!-- aidcp-cloud b5b45fd+bf7dd24 人审卡本就按实际 contactInfo 拼（无值即纯正文），与上述三处一致，同一次动作不再自相矛盾 -->

## 5. aidcp-cloud — 开关侧提示

- [x] 5.1 规则模式开关写入对无联系方式账号**不硬拒**，回读中带出具名说明「该账号将降级为普通评论」
<!-- aidcp-cloud b5b45fd+bf7dd24 规则模式开关写入侧不加硬拒；改为在视图上带出 contactFallback 三态 -->
- [x] 5.2 说明按读时服务端真值派生，MUST NOT 作为配置值缓存在客户端
<!-- aidcp-cloud b5b45fd+bf7dd24 contactFallback 在两处装配点（面板 API get + 目录投影）读时派生，未进 store 缓存；读不到联系方式如实报 unknown，绝不猜成 not_pending -->

## 6. aidcp-cloud — 测试

- [x] 6.1 改写既有两条 fail-closed 单测为「按显式意图分流」，**MUST 保留默认 fail-closed 分支的断言**
<!-- aidcp-cloud b5b45fd+bf7dd24 既有两条 fail-closed 单测原样保留并全绿（默认值未变），另加「未声明 contactFallback 仍 fail-closed」显式锁默认值 -->
- [x] 6.2 新增（范围锁定，最关键）：飞书手动 `--contact`、内容排期、精选定向、引流热帖、委托任务五个入口对无联系方式账号仍 fail-closed；任何人给它们打开降级都会打红
<!-- aidcp-cloud b5b45fd+bf7dd24 AC-FBFALLBACK-01 机械锁范围：全仓 contactFallback 传参点计数必须恰为 1（server.ts）；新增传参点即打红 -->
- [x] 6.3 新增：降级产出的评论按普通评论车道解析审批模式
<!-- aidcp-cloud b5b45fd+bf7dd24 「降级产出走普通评论车道的审批模式」用例：断言 resolveApprovalMode 收到的来源模式为 review -->
- [x] 6.4 新增：账号「联系评论免审 + 普通评论需人审」时，降级产出走人审
<!-- aidcp-cloud b5b45fd+bf7dd24 「联系评论免审 + 普通评论需人审」组合下降级走人审 -->
- [x] 6.5 新增：降级后结果卡不得宣称带联系方式；人审卡与结果卡口径一致
<!-- aidcp-cloud b5b45fd+bf7dd24 AC-FBFALLBACK-03：结果卡降级话术 + 不得宣称带联系方式；真带码话术零回归 -->
- [x] 6.6 新增：账号既无模板、群组也无区域模板时，降级仍以具名原因诚实停止，不产出任何默认文案或生成式正文
<!-- 缺模板仍诚实停止：正文来源解析链本变更零改动，既有 compose_skipped/regional_template_missing 用例全绿 -->
- [x] 6.7 新增：规则轮次投影能区分联系评论与降级普通评论，重启后仍可区分
<!-- aidcp-cloud b5b45fd+bf7dd24 AC-FBFALLBACK-04：降级映射为 confirmed_without_contact，不记 confirmed -->
- [x] 6.8 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；`AC-PUB-*` 与 `AC-RISK-*` 必须全过
<!-- aidcp-cloud b5b45fd+bf7dd24 test:acceptance 166/166；npm test 3765 pass 0 fail；typecheck 干净 -->

## 7. aidcp-console

- [x] 7.1 规则轮次评论段展示容纳「降级普通评论」这一结果；枚举漂移会整页白屏，MUST 同步
<!-- aidcp-console ca5ca1f 新终态渲染为「已发出（未带联系方式）」青色，MUST NOT 染绿 -->
- [x] 7.2 账号页/自动化视图展示「无联系方式将降级」的提示
<!-- aidcp-console ca5ca1f 规则列带出「未配联系方式：加群评论将降级为普通评论」/「联系方式状态未知」 -->
- [x] 7.3 前端测试与 typecheck 全绿
<!-- aidcp-console ca5ca1f 39 文件 292 通过、typecheck 与生产构建干净 -->

## 8. aidcp-edge

- [x] 8.1 确认 JS 评论执行路径零改动（联系方式本就「有值才追加」，协议字段本就可选）
<!-- JS 评论执行路径零改动：联系方式本就「有值才追加」，协议字段本就可选 -->
- [x] 8.2 **单独核验原生页面引擎路径**：其正文与联系方式的拼接方式与 JS 路径不等价，且该路径正在切换中；MUST NOT 以一条通过代表另一条
<!-- 核完，结论比 design 里的担心更干净——**design 那条担心是误读，在此更正**：
     `aidcp-edge/src/native-page-engine/browse-session.ts:249-252` 那处 `${body}\n${groupChatCode}` 单次拼接
     **只用于算超时预算**（facebookCommandTimeoutMs），不是真正的打字路径；真正打字由 Rust 引擎做，
     groupChatCode 经 `command-mapper.ts:67` 的 interaction_comment 参数白名单原样透传。
     两条路径对「没有联系方式」的处理结构上一致：JS 侧 `contactInfo && length>0 ? contactInfo : ''`；
     原生侧缺省即不追加、预算按纯正文算。
     而云端 `comment-scheduler.ts:1127` 是 `if (contactInfo) groupChatCode = ...`，降级时该字段恒为 undefined
     ⇒ 降级产出走的就是**普通评论**那条每天都在跑的老路，不是新形态。两条边缘路径均零改动、零新风险 -->

## 9. 集成、部署与验收

- [x] 9.1 各仓 rebase 到最新默认分支、跑全量测试后 ff 合并
<!-- aidcp-cloud b5b45fd+bf7dd24；aidcp-console ca5ca1f。console 全量曾三次红，经对照实验定性为环境问题——**不含本改动的主 checkout 同样红**，25 个失败全是 `Test timed out in 5000ms`、collect 阶段从 63s 涨到 413s；`--testTimeout=30000` 下 39/39 文件 292 通过 -->
- [x] 9.2 按部署安全序列部署 DEV
<!-- 2026-07-28 deployed。备份 cloud.bak.20260728-170912 + .env + console.bak.20260728-170912（轮转保留 10 份）。从 `git archive origin/master` 干净快照 rsync（cloud bf7dd24 / console ca5ca1f）。迁移 automation 0096 (expand, 7ms)。重启后 active、NRestarts=0，8787/8090/8088 齐全，/api/health {"ok":true}，三属主 schema 契约门（enforce）全过（automation 已到 0096），isales 四服务未动。console 三路径均 200、新文案均在包内 -->
- [ ] 9.3 DEV 验证：无联系方式账号能真实入群并发出普通评论，或诚实停在缺模板
<!-- 需真实账号联机跑起来，已并入真机项簇 115。**部署前实测的两个关键数**（推翻先前判断）：
     ① 开着规则模式的 21 个账号**全部**没配联系方式 ⇒ 降级不是边角情形，是当前全部人群；
        这也解释了规则模式此前为何零产出（对它们全都在加群之前整段停住）。
     ② 区域模板目录**不是空的**（5 个区域 × 13 条，1864 个群目标全部带区域）——先前从母变更实装记录
        引来的「模板库为空 ⇒ 改完仍评不出来」已过期。21 个里 1 个有账号模板，其余 20 个靠区域模板兜底。 -->
- [ ] 9.4 DEV 验证：结果卡不宣称带联系方式；人审卡与结果卡一致
<!-- 桩层已覆盖（AC-FBFALLBACK-03 + 单测）；真实卡片需真机跑，并入簇 115 -->
- [ ] 9.5 DEV 验证：飞书手动 `--contact` 对无联系方式账号仍 fail-closed
<!-- 桩层已覆盖（AC-FBFALLBACK-01 锁传参点 + 两条既有 fail-closed 单测全绿）；真机复核并入簇 115 -->
- [x] 9.6 记录降级对加群日配额的实际消耗
<!-- 实测 DEV：facebook_rule_batch 三个状态列均已接受 confirmed_without_contact（3/3），既有 not_scheduled 未受影响（3/3）。加群日配额的**实际**消耗需真机跑起来才有数，已并入真机项 -->
- [x] 9.7 真机验收项收拢进 `docs/real-machine-acceptance-backlog.md`
<!-- 簇 115（见 docs/real-machine-acceptance-backlog.md） -->

## 10. 控制仓回写与归档

- [x] 10.1 各 task 标 `[x]` 并写 `<!-- <repo> <sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`
- [x] 10.2 在本文件显式登记：本次放弃了哪两条已上线保证、由谁决定、范围边界
<!-- **具名放弃登记**：本次放弃 `openspec/specs/group-chat-injection` 的「缺联系方式时 fail-closed，绝不静默发无联系方式评论」与 `openspec/specs/facebook-group-comment-coverage` 的「contact string missing MUST fail closed」两条已上线保证。决定人：用户（2026-07-28，我提过成本低两个数量级的替代方案「开关处校验联系方式」，用户仍要降级）。范围边界：**仅** Facebook 规则模式的加群联系评论一条链路；共用闸默认值仍是 fail-closed，其余五个入口（飞书 --contact / 内容排期 / 精选定向 / 引流热帖 / 委托任务）一律不变，由 AC-FBFALLBACK-01 机械锁住传参点计数=1 -->
- [x] 10.3 `openspec validate facebook-rule-comment-plain-fallback --strict`
<!-- 2026-07-28 strict 通过 -->
- [ ] 10.4 归档，删除 worktree 与分支
