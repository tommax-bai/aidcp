# curated-note-actions Specification

## Purpose
TBD - created by archiving change curated-note-actions. Update Purpose after archive.
## Requirements
### Requirement: 精选笔记行内定向动作入口——仅笔记行、按行归属账号执行

面板 API SHALL 提供两个精选行级写动作端点（参照创作、定向评论），请求 MUST 携带该行归属账号 accountId 且行加载 SHALL 以 id 与 account_id 双条件命中（防跨账号越权）。动作 SHALL 仅对 content_type='note' 的行开放；评论行（content_type='comment'，未持久化源笔记 noteId）MUST 拒绝。执行账号固定为行归属账号，MUST NOT 支持指定其他账号执行。动作依赖（发布/评论调度器或精选存储）未注入时 SHALL 以 503 诚实降级，MUST NOT 假装受理。

#### Scenario: 笔记行触发动作按行归属账号执行

- **WHEN** 管理员对某账号的精选笔记行触发参照创作或定向评论
- **THEN** 动作以该行归属账号为执行账号受理，请求中的 accountId 与行归属不一致或行不存在时返回 404，不发生任何跨账号执行

#### Scenario: 评论行动作不可用

- **WHEN** 对 content_type='comment' 的行调用任一动作端点
- **THEN** 以机器原因码 note_only 拒绝；console 对评论行禁用动作按钮

#### Scenario: 依赖缺失诚实降级

- **WHEN** 发布/评论调度器或精选存储未注入（如启动期 PG 不可用）
- **THEN** 端点返回 503 与稳定错误码，MUST NOT 返回成功或吞错

### Requirement: 参照洗稿创作——参照注入完整发布链、人审闸不短路

参照创作 SHALL 将该行的标题、正文（截断至有界长度）与话题装配为参照笔记注入创作输入，并走完整既有发布链路（生成→配图→人审→下发），MUST NOT 绕过或简化任何一环（含 AC-PUB 三重人审闸）。创作提示中参照笔记 SHALL 使用独立条件块，MUST NOT 混入既有抽样素材块；参照块 SHALL 要求借选题/结构/要点、以账号人设口吻重新创作，MUST 禁止逐句照抄或近似同义替换。正文为空的壳行 MUST 以 empty_body 拒绝，MUST NOT 以空参照触发。发布链路占用中 SHALL 诚实返回未触发（原因如 publish_busy/skipped），MUST NOT 排队假装成功。

参照创作触发时还 SHALL 把该精选行的展示/审计血缘随 `referenceNote` 传入发布链，至少包括精选行 id、行归属账号、sourceId、sourceUrl、标题、正文、作者、话题和触发时刻。该血缘用于发布记录持久化与内容页「来稿件」展示；MUST 以触发时快照为准，MUST NOT 在历史展示时要求当前精选行仍存在。

#### Scenario: 参照创作生成草稿并送人审

- **WHEN** 对一条正文非空的精选笔记触发参照创作且发布链空闲
- **THEN** 以该笔记为参照生成草稿、落待审状态并发送人审卡；审核通过前绝不发布

#### Scenario: 参照块独立于素材块且带非照抄红线

- **WHEN** 装配含参照笔记的创作提示
- **THEN** 参照笔记以独立条件块注入（含禁止逐句照抄、须有可辨识表达差异的红线），既有抽样素材块及其「仅作灵感、严禁照抄」护栏原样保留

#### Scenario: 空正文壳行诚实拒绝

- **WHEN** 对 admit_reason 为 bot_collect(content_missing) 等正文为空的行触发参照创作
- **THEN** 触发即以 empty_body 拒绝，不进入发布链

#### Scenario: 发布占用中诚实返回未触发

- **WHEN** 发布链路正在为任一账号生成草稿时触发参照创作
- **THEN** 返回未触发与占用原因，MUST NOT 静默排队或谎报已触发

#### Scenario: 触发时携带来稿展示血缘

- **WHEN** 管理员从精选页触发参照洗稿
- **THEN** 发布链输入携带该精选行触发时的展示血缘，后续发布记录可据此展示来稿件，即使当前精选行之后被删除

### Requirement: 定向评论目标定位——搜索驱动精确匹配、绝不导航存量链接

定向评论 SHALL 以该笔记标题（截断至有界长度以守单步时限）为搜索词、以综合排序且不限时间窗发起平台搜索，并 SHALL 在返回卡片中按 noteId 精确匹配目标；命中后 SHALL 打开该卡片并以详情上报的 noteId 校验一致后方可评论。MUST NOT 导航存量 source_url（xsec_token 过期风险）、MUST NOT 由裸 noteId 伪造链接、MUST NOT 在未命中时退而评论「相似」笔记。搜索定位 SHALL 有界重试（不超过 2 次搜索尝试），用尽未命中 SHALL 以 note_not_found 诚实结束。

#### Scenario: 精确命中后才开笔记评论

- **WHEN** 搜索结果卡片中存在与目标 noteId 精确相等的卡片
- **THEN** 打开该卡片、校验详情 noteId 一致后进入撰写；校验不一致则不评论

#### Scenario: 定向搜索使用综合排序与不限时间窗

- **WHEN** 定向评论发起目标搜索
- **THEN** 搜索携带综合排序与不限时间窗（不沿用按需评论命令的「最多收藏+一天内」默认），保证非当日老笔记可被检索

#### Scenario: 有界重试后诚实失败

- **WHEN** 两次搜索尝试的返回卡片均无目标 noteId
- **THEN** 任务以 note_not_found 终态结束并如实上报，MUST NOT 换目标补发

#### Scenario: 红线反例——导航存量笔记链接（禁止）

- **WHEN** 有实现以精选行存量 source_url 直接导航、或以裸 noteId 拼详情链接打开笔记
- **THEN** MUST 视为违规不予合入；目标定位只允许搜索驱动+卡片点击路径

### Requirement: 定向评论两型——内容评论与带群评论共用撰写链

内容评论 SHALL 复用既有按需评论撰写链（读笔记现场与在场评论→人设撰写→去 AI 味→人审）。带群评论 SHALL 在相同撰写链之上追加该账号配置的群聊口令（审核卡展示合并后最终文本，审=发；边端以既有整段插入方式追加）。两型的评论正文均 SHALL 基于笔记信息自动生成，MUST NOT 要求额外人工文案输入。账号未配置群聊口令时带群评论 MUST 触发即以 group_code_missing 拒绝（fail-closed），MUST NOT 退化为内容评论静默发出。

#### Scenario: 内容评论走既有撰写与人审

- **WHEN** 触发内容评论且目标定位命中
- **THEN** 评论正文由既有撰写链基于笔记现场自动生成，经人审通过后发布

#### Scenario: 带群评论追加群口令且审=发

- **WHEN** 触发带群评论且账号已配置群聊口令
- **THEN** 审核卡展示「正文+群口令」合并文本，审核通过后按同一合并文本发布

#### Scenario: 未配群口令触发即诚实拒绝

- **WHEN** 对未配置群聊口令的账号触发带群评论
- **THEN** 触发即以 group_code_missing 拒绝，MUST NOT 降级为内容评论发出

### Requirement: 定向评论受控独占与记账——单飞、让位、去重、跳配额保人审

定向评论任务 SHALL 按账号单飞（同账号在跑中再次触发即拒绝）；SHALL 以既有评论接管语义让位（任务前结束该账号浏览会话、任务后恢复）。触发前 SHALL 查询该账号对目标笔记的评论去重记录，已评论过 MUST 以 already_commented 拒绝；发布成功后 SHALL 记入去重账本（只记真实回执）。人工触发 SHALL 跳过风控配额闸（人是刹车）但 MUST 保留人审；人审未接线时 MUST NOT 裸发。边端离线 SHALL 触发即诚实拒绝。

#### Scenario: 已评论过的笔记诚实拒绝

- **WHEN** 对去重账本已有该账号评论记录的笔记触发定向评论
- **THEN** 触发即以 already_commented 拒绝，不发起边端任务

#### Scenario: 任务期间让位并恢复

- **WHEN** 定向评论任务启动与结束
- **THEN** 启动时结束该账号自治浏览会话取得独占，结束（无论成败）后恢复浏览

#### Scenario: 同账号并发触发被拒

- **WHEN** 某账号定向评论任务在跑中再次触发任一评论动作
- **THEN** 第二次触发以在跑原因拒绝，不产生并发边端任务

#### Scenario: 人审未接线绝不发布

- **WHEN** 评论人审开关未启用或审批端口未注入
- **THEN** 撰写完成也不发布，任务以未发出的诚实终态结束

### Requirement: 触发态回执与终态结果分离——诚实三态

动作端点的响应为触发态回执（triggered 与机器原因码），MUST NOT 把域内拒绝或未触发表达为成功。终态结果沿既有渠道呈现：参照创作=内容页待审草稿+飞书人审卡；定向评论=飞书人审卡+既有三态终态结果卡（成功绿/未产出黄/失败红），终态卡 SHALL 可辨识为定向来源。console SHALL 按 triggered 真值分支提示（成功=引导去飞书审核；拒绝=中文原因；异常=错误提示），MUST NOT 对拒绝染绿。

#### Scenario: 触发成功提示走飞书人审

- **WHEN** 动作端点返回 triggered=true
- **THEN** console 提示任务已触发并引导到飞书完成人审；不宣称动作已完成

#### Scenario: 域内拒绝以原因码透传

- **WHEN** 动作因 empty_body/note_only/already_commented/group_code_missing/publish_busy/边端离线等被拒
- **THEN** 端点返回 triggered=false 与稳定机器原因码，console 映射为中文提示且不染绿

#### Scenario: 终态不由触发回执谎报

- **WHEN** 任务触发成功但终态失败（如 note_not_found、发布失败）
- **THEN** 终态经既有渠道如实呈现（黄/红），触发回执不被追溯性当作成功依据

