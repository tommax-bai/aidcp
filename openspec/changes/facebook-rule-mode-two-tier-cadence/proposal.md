## Why

Facebook 规则模式当前是单轴节奏：每 10 条确认浏览开一个批次，批次内串行做 1 次点赞 + 1 次加群联系评论。运营要求把互动密度与入群密度解耦——点赞要更密（每 5 条一次），入群密度维持不变（仍是每 10 条一次）。单轴节奏无法表达这个诉求：把阈值降到 5 会同时把加群频率翻倍，撞上加群日配额并显著抬高账号风险面。

需要的是两级节奏：浏览→点赞一级，点赞轮次→加群一级。两级都必须持久、可重启恢复、按部署目标隔离，并且「本轮不加群」这件事必须在数据与界面上被诚实表达，不能借用现有的失败态。

## What Changes

- **BREAKING（规则身份）**：固定规则定义号从 `facebook_browse_10_like_1_join_contact_1@1` 换为编码新两级节奏的新定义号，版本抬到 `@2`。定义号是 `facebook_rule_progress` / `facebook_rule_view_fact` / `facebook_rule_batch` 三表的主键与去重键组成部分，换号后旧进度、旧去重事实与旧批次在新定义下不可见；这是有意的语义（新节奏从零重新收集），MUST 在变更文档中具名登记而非静默发生。
- 一级节奏：每累计 **5** 条确认、身份稳定、当前轮次内未重复的浏览，创建一个规则轮次，轮次尝试 **1 次点赞**，目标绑定触发该轮次的第 5 条内容。
- 二级节奏：**每 2 个轮次**中的第 2 个轮次，在点赞到达终态后额外执行 **1 次加群 + 联系评论**。第 1 个轮次只做点赞。加群频率因此维持每 10 条浏览 1 次，与现节奏逐位相等。
- **轮次计数口径为「轮次序号」，不是「成功点赞数」**：点赞被风控抑制、结构性跳过、已赞、结果不明或失败，均照常推进轮次计数。这保留了现行「点赞被抑制仍独立尝试加群」的行为，并避免点赞日配额耗尽时静默停掉全部加群与联系评论。
- 新增「本轮不做加群」的诚实终态：动作状态枚举新增一个明确表示「按节奏本轮不适用」的取值，MUST NOT 复用 `not_started` / `structural_skip`（那两个表示「本该做却没起来」）。只点赞的轮次 MUST 走正常终结路径写入终态并释放账号单飞占用，MUST NOT 让轮次停在非终态。
- 进度投影新增二级节奏轴：除 `0..4/5` 的浏览进度外，暴露当前轮次在两轮周期中的位置与「本轮是否包含加群」，后台与客户端 MUST NOT 把「本轮不加群」渲染成加群/评论待处理或失败。
- 数据库以一版 expand 迁移放宽四张表对定义号与定义版本的 CHECK，并放宽批次三个动作状态列的 CHECK 以容纳新枚举值。**MUST NOT 编辑已入账本的既有迁移**；放宽既有 CHECK MUST 先按 `pg_constraint` 动态查名再 DROP，MUST NOT 用猜名 + `DROP CONSTRAINT IF EXISTS`（名字不符会静默 no-op，随后新旧 CHECK 取合取，迁移报成功而运行期写入仍被拒——迁移形态的静默假成功）。
- 联系评论的发布链**不变**：选群、正文来源、联系方式注入、审批模式、去重、风控记账与结果投影一律沿用现有实现，本变更 MUST NOT 触碰。变更仅改「何时触发加群联系评论」这一层。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `facebook-rule-mode`: 固定规则定义由单轴十浏览批次改为两级节奏（5 浏览→点赞轮次，2 轮次→加群联系评论）；新增「本轮不适用」动作终态与二级进度投影；明确轮次计数按轮次序号推进而非按成功点赞数。
- `content-schedule`: 统一账号自动化入口的规则模式进度投影由单轴改为两级，取消「十条确认浏览触发批次」的措辞。
- `client-facebook-rule-mode-toggle`: 客户端开关语义不变（仍只写 `enabled`），仅同步 Edge MUST NOT 自行累计浏览的条款中写死的条数措辞。

## Impact

- **前置依赖（硬）**：`facebook-rule-mode` 与 `client-facebook-rule-mode-toggle` 的能力规格尚未并入 `openspec/specs/`，仍活在未归档的 `facebook-rule-mode-cadence` 与 `client-facebook-rule-mode-toggle` 两个 change 里。本变更的对应 delta MUST NOT 先于它们归档生效；建议先归档 `facebook-rule-mode-cadence`，否则形成 delta 叠 delta、归档顺序会静默定死最终文本。
- **并行冲突（硬）**：另有两个在飞 change 同改 `facebook-rule-mode`——`environment-level-rule-mode-and-approval`（配置主键账号→环境）与 `facebook-rule-mode-without-persona`（取消人设闸 + 评论段收窄为模板）。后者与本变更同改规则模式判定与调度接线，按控制仓「热点文件单写者」纪律 MUST 串行、MUST NOT 并行开工。
- **Cloud**：规则定义常量、两级节奏判定、轮次终结路径、批次投影字段、动作状态枚举；规则运行时存储的必需列清单与 schema 版本常量。
- **Data**：一版 expand 迁移（放宽四表定义号/版本 CHECK + 批次三个状态列 CHECK）；`REQUIRED_SCHEMA_VERSION` 与 `KNOWN_MAX_SCHEMA_VERSION` 同步抬升，并同步其字面量断言测试。
- **Console**：规则模式列的进度展示、固定规则说明文案、动作状态中文映射与配色需容纳新枚举值（枚举漂移会整页白屏）。
- **Edge**：零代码改动。客户端只透传开关，渲染层对定义号只做类型校验、无字面量断言；边-云协议无阈值/进度字段。
- **DEV/OL 风险**：`facebook_rule_mode_config` 无 `execution_target` 且 DEV/OL 共库，而配置回读直接返回代码常量、不读库中定义号。若只部署一侧，同一批已开启账号会在两侧按不同定义各自维护进度且无任何机械手段暴露。部署策略 MUST 在实装期显式裁定。
- **Out of scope**：不改联系评论发布链、不改审批与风控闸、不改人设准入、不改配置主键归属、不改缺联系方式时的 fail-closed 行为（后者由另一变更承接）。
