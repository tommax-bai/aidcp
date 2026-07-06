# panel-curated-content Specification

## Purpose
TBD - created by archiving change curated-content-admin-page. Update Purpose after archive.
## Requirements
### Requirement: 按账号隔离的精选内容只读检索

面板 SHALL 提供按账号检索精选语料（`curated_content`）的只读接口：分页列表与筛选面（facets）。账号标识 MUST 必填；缺失时接口 MUST 以 400（`account_required`）拒绝，MUST NOT 默认某账号、MUST NOT 跨账号合并返回。所有读查询 MUST 以 `account_id` 过滤。列表 SHALL 支持按内容类型（笔记 / 评论）与纳入原因过滤，并支持参数化分页（limit/offset）；列表 MUST 一并返回与当前筛选一致的总条数（total），空结果集时 total MUST 为 0。前端 SHALL 默认选中第一个账号、账号未选时不发起查询，避免空账号被误判为功能损坏。

#### Scenario: 账号缺失被拒
- **WHEN** 调用列表或 facets 接口但未带账号标识
- **THEN** 接口返回 400（`account_required`），不返回任何行

#### Scenario: 仅返回本账号的行
- **WHEN** 带账号 A 调用列表
- **THEN** 只返回归属账号 A 的精选内容，绝不混入其他账号的行

#### Scenario: 类型与原因筛选 + 分页总数
- **WHEN** 带账号、内容类型=笔记、某纳入原因、limit/offset 调用列表
- **THEN** 返回符合该筛选的行（按更新时刻倒序）与一致的 total；当无任何行匹配时 total 为 0

#### Scenario: facets 驱动筛选项与影响预览
- **WHEN** 带账号调用 facets
- **THEN** 返回该账号实际出现的纳入原因去重列表及各自计数、其中携带机器人点赞 / 收藏标记的高权重行数、以及笔记 / 评论各自计数

### Requirement: 诚实置空地呈现精选内容

精选内容的展示 MUST 诚实置空：缺失的赞 / 藏 / 评计数 MUST 与真实为 0 可区分地呈现（缺失渲染为「未抓到」之类回落标识、0 渲染为 0），MUST NOT 把缺失伪造为 0。缺失来源链接时前端 MUST NOT 渲染死链，只渲染纯文本或「无链接」回落；存在外链时 MUST 以 `rel=noopener` 在新标签打开。正文在列表中 SHALL 默认折叠，完整正文在详情视图按需展开。

#### Scenario: 计数缺失与零可区分
- **WHEN** 某行的收藏数为缺失（NULL）、另一行的收藏数为 0
- **THEN** 前者渲染为「未抓到」回落标识、后者渲染为 0，二者可区分

#### Scenario: 缺来源链接不渲染死链
- **WHEN** 某行缺来源链接
- **THEN** 该行来源处显示「无链接」纯文本，MUST NOT 渲染一个打不开的链接

### Requirement: 删除单条精选内容——账号隔离、诚实回真态、语义如实

面板 SHALL 提供删除单条精选内容的接口。删除 MUST 经拥有 `curated_content` 表的进程内存储对象进行，MUST NOT 由面板层 raw SQL 绕过。账号标识 MUST 必填且 MUST 进入删除条件（`WHERE id=? AND account_id=?`），使仅凭全局自增 id 无法触及其他账号的行。接口 MUST 返回真实删除行数：删除 1 行与删除 0 行 MUST 可区分地呈现，MUST NOT 在未实际删除时报告乐观成功。由于准入判定不查历史，删除仅清除当前快照——界面 MUST 如实告知「之后再浏览到且仍达标会重新纳入，且历史点赞 / 收藏标记不会恢复」，MUST NOT 谎称永久移除。

#### Scenario: 删除本账号的行回真态
- **WHEN** 带账号 A 删除一条归属 A 的存在行
- **THEN** 接口删除该行并返回删除行数 1，界面提示已删除

#### Scenario: 凭别账号 id 删除被隔离
- **WHEN** 带账号 A 删除一条实际归属账号 B 的行 id
- **THEN** 不删除任何行，返回删除行数 0，账号 B 的行不受影响

#### Scenario: 删 0 条不报乐观成功
- **WHEN** 删除一个已不存在（或已被淘汰 / 他人已删）的行
- **THEN** 接口返回删除行数 0，界面提示「该行已不存在」，MUST NOT 笼统提示「已删除」

#### Scenario: 删除语义如实告知
- **WHEN** 运营在界面发起删除前
- **THEN** 确认文案写明删除仅清当前快照、之后达标会重新纳入、历史标记不恢复

### Requirement: 按正文为空清理壳行——非按纳入原因

面板 SHALL 提供「清理空正文壳行」的接口，谓词为正文为空（NULL 或空串）且按 `account_id` 约束，MUST NOT 以「按纳入原因批量删除」实现。理由（写入约束）：`curated_content` 只存已纳入行，被拒原因从不入库；而最该清的空正文壳行恰带机器人收藏标记（高召回权重），任何「按原因 + 默认保护机器人动作行」的清理都会保护壳行、误删有正文的优质行。清理 MUST 返回真实清理条数，界面 MUST 呈现真实条数（可能因机器人并发写入而与事前预览不同），MUST NOT 回显预览数充当结果。

#### Scenario: 只清空正文壳行
- **WHEN** 带账号 A 执行清理空正文壳行
- **THEN** 仅删除账号 A 中正文为空（NULL 或空串）的行，所有带正文的行（含高共鸣观测行）保留

#### Scenario: 清理回真实条数
- **WHEN** 清理实际删除了 N 行
- **THEN** 接口返回 N，界面呈现真实的 N，而非事前 facets 预览的估计数

#### Scenario: 清理不跨账号
- **WHEN** 带账号 A 执行清理
- **THEN** 其他账号的空正文壳行不受影响

### Requirement: 精选存储缺失时优雅降级，不崩闭环

精选语料存储为可选依赖（其初始化可能失败而缺失）。当存储未注入时，所有精选内容面板接口 MUST 返回 503（如 `curated_unavailable`），MUST NOT 抛错连累边-云主闭环。当底层表尚不存在时，只读接口 MUST 回落为空结果而非 500。前端 MUST 将「加载中 / 暂无数据 / 服务不可用」三态可区分地呈现。

#### Scenario: 存储未注入回 503
- **WHEN** 精选存储未注入而调用任一精选面板接口
- **THEN** 接口返回 503，且不影响边-云主链路运行

#### Scenario: 表不存在回空而非报错
- **WHEN** 底层精选表尚未建立而调用只读列表
- **THEN** 接口返回空列表（total 0），MUST NOT 返回 500

#### Scenario: 前端三态可区分
- **WHEN** 处于加载中 / 无数据 / 服务不可用任一状态
- **THEN** 界面分别呈现可区分的提示，空数据不被误读为功能损坏

### Requirement: 精选内容池参考图 SHALL 站内浮层预览

精选内容池中的参考图点击 SHALL 打开站内图片预览浮层，并支持在同一组参考图内切换预览；前端 MUST NOT 将列表图片、查看笔记详情图片或参考创作弹窗图片点击实现为原图链接导航或下载入口。缺少可用图片 URL 时 SHALL 维持现有空态，MUST NOT 构造虚假图片。

#### Scenario: 查看笔记详情点击参考图
- **WHEN** 运营打开精选内容池的「查看笔记」详情并点击其中一张参考图
- **THEN** console 打开站内图片预览浮层，首张预览为被点击的图片，不跳转原图 URL、不触发下载

#### Scenario: 多图切换预览
- **WHEN** 同一精选笔记存在多张可用参考图并已打开预览浮层
- **THEN** 预览浮层显示当前位置，并提供上一张 / 下一张切换；切换只在该笔记的可用参考图集合内循环

#### Scenario: 无可用图片维持空态
- **WHEN** 精选行没有可用 `ossUrl` 或 `sourceUrl`
- **THEN** 列表图片列显示空态，查看笔记详情显示暂无参考图，MUST NOT 提供会打开死链或下载的图片点击目标

