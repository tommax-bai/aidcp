## MODIFIED Requirements

### Requirement: 评估→撰写→去AI味→审批四段单职责角色

系统 SHALL 以四个独立角色实现评论支线，**评估与撰写 MUST NOT 合并**：`CommentAppraiser`（只判定要不要评、产判定不产文本）→
`CommentComposer`（产评论文本）→ `CommentDeAiFlavor`（去 AI 味 + 合规声明判定：**检测步**确定性无 LLM；**改写步**在命中 AI 味信号或与参考语料撞车时按**该账号人设口吻**做至多一次 LLM 改写，改写失败 / 超时 MUST 回退原文、不抛异常）→
`CommentApprovalGate`（循环内飞书人审）。任一段失败 / 不通过 MUST emit `comment.skipped` 并带如实原因，MUST NOT 伪造文本或伪造通过。
`CommentComposer` 作为浏览闭环首个自由文本角色，MUST 自己保证：空 / 超长文本如实跳过、做跨笔记近似去重、撰写时避开裸 `@`（编辑器带 `data-tribute` 提及）；并 SHALL 提供**语义弃权出口**——对着笔记确实写不出有真实内容的话时，MUST 返回弃权（`nothing_genuine`）走 `comment.skipped` 分支，MUST NOT 硬凑客套话（客套敷衍正是评论体裁的 AI 味主形态）。

评论撰写前的外部语料召回属于可选 prompt 增强，MUST 设独立短超时；异常、超时或空结果 MUST 按“无参考语料”继续撰写，不得让该 Promise 无界占住评论支线，也不得把可选增强失败伪装成评论成功。

评论评估、撰写与去 AI 味改写的每次 LLM 调用 MUST 使用独立于全局 thinking 天花板的评论短 deadline，生产默认 30 秒并允许正数 env 覆盖。底层 fetch 即使忽略 Abort 也 MUST 按该 deadline reject。评估/撰写超时 MUST 诚实 `comment.skipped`，去 AI 味超时 MUST 回退原草稿；网络/超时错误 MUST NOT 自动重试同一模型调用，内容已返回但为空、过长或语言不符的既有有限补写除外。

#### Scenario: 评估为是才进入撰写

- **WHEN** `CommentAppraiser` 判定该笔记值得评论且配额/门槛通过
- **THEN** emit `comment.appraised` 触发 `CommentComposer` 产文本 → `CommentDeAiFlavor` 去 AI 味 / 合规 → `CommentApprovalGate`；评估为否则 emit `comment.skipped`，不进入撰写（不付 LLM 撰写成本）

#### Scenario: 可选语料召回悬空时按空参考继续

- **WHEN** `CommentComposer` 的参考语料召回在短超时内未 resolve / reject
- **THEN** 系统 MUST 记录稳定超时原因并按空参考继续调用评论撰写模型；MUST NOT 永久停在 `comment.appraised`，MUST NOT 因可选语料缺失伪造模板评论

#### Scenario: 评论撰写 fetch 忽略 Abort 时短 deadline 收敛

- **WHEN** `CommentComposer` 的底层 fetch 永不 settle 且忽略 Abort
- **THEN** 本次模型调用 MUST 在评论短 deadline 到达时失败，`CommentComposer` MUST emit `comment.skipped{reason:'llm_error'}` 且不得为同一网络错误自动重试；浏览经既有终局出口继续

#### Scenario: 去AI味检测步确定性、改写步失败回退

- **WHEN** `CommentComposer` 产出草稿文本
- **THEN** `CommentDeAiFlavor` 的 AI 味检测 MUST 为确定性规则（无 LLM、可独立单测）；命中信号触发的人设口吻改写走评论短 deadline，改写失败 / 超时 MUST 回退检测前原文并继续流程，MUST NOT 抛异常中断评论支线

#### Scenario: 撰写诚实弃权不硬凑

- **WHEN** `CommentComposer` 面对已判值得评的笔记仍写不出有真实内容的评论（LLM 返回弃权）
- **THEN** MUST emit `comment.skipped{reason:'nothing_genuine'}`，不进入去 AI 味与审批；评论支线照常收敛（下游进主页评估不受影响）

#### Scenario: 红线反例——撰写失败伪造文本（禁止）

- **WHEN** `CommentComposer` LLM 失败 / 产空文本，但实现回退到模板/占位文本照常提交
- **THEN** MUST 视为违规、不予合入；MUST emit `comment.skipped{reason}`，绝不发出无法落地的伪造评论

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

普通评论因必须在详情页打开时发出，审批 SHALL **循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经飞书人审授权。评论支线从 `comment.appraising` 起 MUST 进入被命令统一出口和看门狗识别的 `commentInflight` 暂停态，扣住会离开当前帖的滚动、换帖和刷新；`session.end` 仍可达。审批本身 MUST 设硬性短超时；超时 / 拒绝 MUST 记审计并 `comment.skipped`。审批使用评论专属 requestId，未获授权 MUST NOT 下发评论命令。

除各阶段局部超时外，`commentInflight` 暂停态 MUST 具有不可被重复事件续期的有界总 deadline，生产安全默认 SHALL 不超过 5 分钟，合法正数 env 覆盖仍优先。到期 MUST 只结算一次 `comment.skipped{reason:'comment_subline_timeout'}`、先释放暂停并恢复看门狗，再经既有终局出口继续浏览。该 note 的迟到 `comment.appraised` / `comment.approved` MUST 失效：不得重新进入暂停态，不得下发旧评论。

唯一免逐条审批路径是：本篇携详情确认的结构化 mandatory context，规则 actions 含 comment，且规则显式 `comment_approval: auto_approve`。此时该规则保存本身构成账号级站立授权；`CommentApprovalGate` MUST 在提交前把账号、目标和清洗后的终稿发送到免审通知口，**通知成功后**才 emit `comment.approved`。通知口未接线或发送失败 MUST fail-closed 为 `comment.skipped{reason:'auto_approve_notice_failed'}`，MUST NOT 下发。未配置规则、规则为 `review`、或非规则命中评论继续逐条人审。

#### Scenario: 普通评论授权后下发、超时则跳过
- **WHEN** 普通评论的飞书人审在超时窗口内写入授权信号
- **THEN** gate 下发；若未授权 / 被拒则 skip、退出暂停态

#### Scenario: 评论支线任一阶段悬空时在默认五分钟内恢复浏览
- **WHEN** 评论评估、撰写、去 AI 味或审批阶段未在评论支线总 deadline 内产生终局，且未配置合法 env 覆盖
- **THEN** 系统 MUST 在不超过 5 分钟内先解除 `commentInflight` 并恢复看门狗，再 emit 一次 `comment.skipped{reason:'comment_subline_timeout'}`；后续 idle nudge MUST 能继续下发浏览滚动

#### Scenario: 超时后的迟到授权不得提交
- **WHEN** 某 note 已因 `comment_subline_timeout` 恢复浏览，随后旧异步调用迟到 emit `comment.appraised` 或 `comment.approved`
- **THEN** 系统 MUST 忽略该迟到事件、MUST NOT 重开暂停窗、MUST NOT 下发评论或报告成功

#### Scenario: 强制规则免审先通知后授权
- **WHEN** mandatory comment 的规则显式 `auto_approve` 且免审通知成功
- **THEN** gate 不等待逐条点击，直接 emit approved；通知内容必须是即将提交的终稿

#### Scenario: 强制规则免审通知失败不裸发
- **WHEN** 免审通知口未接线或发送失败
- **THEN** MUST emit `comment.skipped{reason:'auto_approve_notice_failed'}`，不下发 edge 评论

#### Scenario: XHS 与普通 FB 评论仍需逐条审批
- **WHEN** 评论没有有效的 auto-approved mandatory context
- **THEN** 它仍走既有人审；MUST NOT 因本功能全局自动直发
