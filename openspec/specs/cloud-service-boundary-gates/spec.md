# cloud-service-boundary-gates Specification

## Purpose
TBD - created by archiving change cloud-service-boundary-gates. Update Purpose after archive.
## Requirements
### Requirement: 模块归属表覆盖全部云端源文件且不存在未分配态

云端仓库 SHALL 维护一份机器可读的模块归属表，为 `src/` 下每一个 TypeScript 源文件指定唯一归属层。层枚举 MUST 恰好为 `kernel` / `api` / `content` / `automation` / `composition` 五个取值，MUST NOT 提供「未分配」「待定」或等价取值。门禁 MUST 在扫描到的源文件数与归属表条目数不相等时失败，MUST 在归属表存在源码中已不存在的路径时失败。`composition` 的成员 MUST 来自测试源码里固定的白名单；白名单外的文件声明为 `composition` MUST 失败。

#### Scenario: 新增源文件未登记归属

- **WHEN** 开发者在 `src/` 下新增一个 TypeScript 文件而未在归属表中登记
- **THEN** 导入方向门禁失败并指名该文件路径，`npm run test:acceptance` 不通过

#### Scenario: 归属表残留已删除文件

- **WHEN** 某个源文件被删除但归属表条目仍在
- **THEN** 门禁失败并指名该条目，要求同批清理

#### Scenario: 靠声明 composition 绕过检查

- **WHEN** 开发者把一个新文件的归属声明为 `composition` 而它不在固定白名单里
- **THEN** 门禁失败，该文件不能获得「可导入任何层」的豁免

### Requirement: 导入方向门禁按归属层判定并阻断新增跨边界导入

门禁 SHALL 解析 `src/` 全量静态 `import` / `export ... from` 与动态 `import()`，把每条相对说明符解析到实际源文件，按两端归属层判定方向。任何层 MAY 导入 `kernel`；`composition` MAY 导入任何层；任何层 MUST NOT 导入 `composition`；其余跨层方向 MUST 在豁免清单中存在对应条目，否则门禁失败。允许方向的白名单 MUST 定义在测试源码中而非数据文件中。

#### Scenario: 新增一条未豁免的跨边界导入

- **WHEN** `content` 层的文件新增一条对 `automation` 层文件的 import，且豁免清单中没有对应条目
- **THEN** 门禁失败并输出该条 `from → to` 文件对与所属方向

#### Scenario: 导入共享内核层始终允许

- **WHEN** `api`、`content`、`automation` 任一层的文件导入 `kernel` 层文件
- **THEN** 门禁通过，且该条边不需要任何豁免条目

#### Scenario: 反向导入组合根被禁止

- **WHEN** 任一业务层文件导入被标记为 `composition` 的文件
- **THEN** 门禁失败，无论豁免清单中是否存在该条目

### Requirement: 表写入归属门禁覆盖 DML 与 DDL

门禁 SHALL 扫描 `src/` 下 SQL 字面量中的 `INSERT INTO` / `UPDATE` / `DELETE FROM`（DML）与 `CREATE TABLE` / `ALTER TABLE`（DDL），把每次写入或建表归到发生它的源文件所属层，对照表归属清单判定。非属主层的 DML 或 DDL MUST 在豁免清单中存在对应 `{表, 文件}` 条目，否则门禁失败。表归属清单 MUST 覆盖 `src/` 与 `migrations/` 中 `CREATE TABLE` 的表名并集，每张表 MUST 恰好有一个属主层。同层内多个文件写同一张表 MUST NOT 判为违规，但该表仍 MUST 有唯一属主层声明。

#### Scenario: 跨边界新增一条写入

- **WHEN** `api` 层的存储类新增一条对属主为 `automation` 的表的 `UPDATE`，且豁免清单无对应条目
- **THEN** 门禁失败并输出表名、文件路径与两侧归属层

#### Scenario: 非属主层新增自建表

- **WHEN** 某层文件新增 `CREATE TABLE IF NOT EXISTS` 语句而该表属主为另一层
- **THEN** 门禁失败，建表点被视为与写入同等的所有权违规

#### Scenario: 同层双写不被误判

- **WHEN** 同属 `automation` 层的两个存储类各自写入同一张 `automation` 属主的表
- **THEN** 门禁通过，不产生豁免条目

### Requirement: 豁免清单棘轮化，条数只减不增

两份豁免清单 SHALL 以具体条目（导入侧为 `{from, to}` 文件对，表写入侧为 `{表, 文件}` 对）而非通配模式记录违规，MUST NOT 用计数上限替代条目。门禁 MUST 同时断言三条：源码中每一条实际跨边界边存在于清单中；清单中每一条在源码中仍然存在；清单条目数不超过清单头部记录的 `frozenTotal`。削减违规时 MUST 在同一提交内删除对应条目并下调 `frozenTotal`。上调 `frozenTotal` MUST 在同一提交内写入 `raises` 条目（change 名、一句理由、日期），缺少该条目的上调 MUST 使门禁失败。

#### Scenario: 削减后不清理条目

- **WHEN** 开发者删除了一条跨边界 import，但未从豁免清单中删除对应条目
- **THEN** 门禁失败，防止清单留出空位供未来新违规静默回填

#### Scenario: 用旧条目换新违规

- **WHEN** 开发者删除一条旧豁免条目、同时新增一条不同的跨边界 import 并把它写进清单，总条数不变
- **THEN** 两条改动在同一次 diff 中逐条可见，且新条目 MUST 携带 `reason`；门禁 MUST NOT 因总条数未变而放行缺少 `reason` 的新条目

#### Scenario: 静默上调冻结总数

- **WHEN** 提交把 `frozenTotal` 调高但未写入对应的 `raises` 条目
- **THEN** 门禁失败并指出缺失的 `raises` 记录

### Requirement: 门禁自身不得静默假通过

扫描器 SHALL 对任何无法完成的解析显式失败并报出原因，MUST NOT 以跳过、忽略或按通过处理的方式掩盖漏检。至少下列情况 MUST 判定失败：相对 import 说明符解析不到实际源文件；SQL 扫描命中一个既不在表归属清单也不在已知表全集内的标识符；归属表条目数与扫描到的源文件数不一致。扫描 MUST 覆盖动态 `import()`，MUST 在 SQL 扫描前剥离行注释与块注释，MUST 以显式排除规则处理已知误命中形态而非以「不在白名单即跳过」兜底。

#### Scenario: 导入说明符解析失败

- **WHEN** 某条相对 import 因改名或路径错误解析不到实际源文件
- **THEN** 门禁失败并列出该说明符与所在文件，而不是把这条边当作不存在

#### Scenario: 出现未登记的表

- **WHEN** 源码中出现一条写入语句，其表名不在表归属清单也不在 `migrations/` 已知表全集中
- **THEN** 门禁失败并要求先登记该表归属

#### Scenario: 动态导入不得逃逸

- **WHEN** 跨边界依赖以动态 `import()` 形式书写
- **THEN** 门禁按与静态 import 相同的规则判定方向，不因书写形式不同而放行

### Requirement: 共享内核层有准入条件与单写者纪律

系统 SHALL 承认一个名为 `kernel` 的共享内核层，用于承载被多个边界共同依赖的协议、事件与角色名类型、平台能力声明和无状态工具，替代「按边界复制三份」的做法。`kernel` 成员 MUST NOT 包含 SQL 字面量、MUST NOT 注册 HTTP 路由、MUST NOT 发起 LLM 或供应商 HTTP 调用、MUST NOT 持有进程内活状态（模块级可变单例、定时器、连接池）、MUST NOT 导入 `api` / `content` / `automation` / `composition` 任一层。门禁 MUST 对每个 `kernel` 成员逐条断言上述条件。`kernel` MUST 登记为热点文件单写者范围，改动需串行；拆仓后 `kernel` MUST 由单一仓库拥有并以版本化包发布，消费方 MUST 固定版本而非经 Git 路径引用源码。

#### Scenario: 带 SQL 的存储类被塞进内核层

- **WHEN** 开发者把一个含 `INSERT` 语句的存储类标记为 `kernel`
- **THEN** 门禁失败并指出违反的准入条件，该文件必须留在原业务层并进豁免清单

#### Scenario: 内核层反向依赖业务层

- **WHEN** 某个 `kernel` 成员新增一条对 `automation` 层文件的 import
- **THEN** 门禁失败，内核层不得获得任何反向依赖豁免

#### Scenario: 角色名联合类型保持单一来源

- **WHEN** 新增或删除一个角色名成员
- **THEN** 该联合类型只存在于 `kernel` 的单一定义中，全部消费方经类型检查一次性暴露不一致，MUST NOT 出现按边界复制的多份定义

### Requirement: 门禁挂在既有验收闸上且零新增依赖

门禁 SHALL 以仓内既有的「读源码做结构断言」验收测试范式实现，只使用运行时内置的文件与路径能力，MUST NOT 引入新的运行时或开发依赖，MUST NOT 依赖持续集成服务存在。门禁用例 MUST 位于验收测试目录，从而由既有的验收测试脚本与集成脚本在每次合并前执行。门禁 MUST 在每次运行时输出机器可读的计数：按方向分解的跨边界条数、总条数、`frozenTotal` 及其差值。

#### Scenario: 集成前自动执行

- **WHEN** 任一 change 走既有集成脚本合并回默认分支
- **THEN** 两道门禁随验收测试一并执行，违规即拒绝合并，无需任何持续集成配置

#### Scenario: 依赖清单保持不变

- **WHEN** 门禁落地
- **THEN** 云端运行时依赖与开发依赖数量不变，门禁只依赖运行时内置能力

### Requirement: 门禁先于任何边界重构落地

拆分迁移的第一阶段 SHALL 把模块导入检查与数据所有权检查排在首位，且这两项 MUST 在建立模块边界、收口跨领域调用、迁移持久消息等任何边界重构动作之前完成并生效。

#### Scenario: 先做重构后补门禁

- **WHEN** 有人主张先重构模块边界、稍后再补门禁
- **THEN** 该顺序不被接受；未生效的门禁期间产生的新跨边界依赖没有任何机械手段发现，重构成果会被同期提交打穿

### Requirement: 豁免清单剩余条数作为拆仓就绪度的准入度量

拆分迁移中提取独立 Git 仓库的阶段 SHALL 以两份豁免清单的剩余条数作为可判定准入条件，MUST 写成具体阈值而非「边界已足够清晰」这类形容词。门禁输出的计数 MUST 是该准入判定的唯一取值来源。

#### Scenario: 条数未降至阈值即申请提取仓库

- **WHEN** 跨边界导入豁免条数仍高于约定阈值而有人申请进入仓库提取阶段
- **THEN** 准入判定为不通过，剩余条数即为待偿还的跨仓耦合，提取只会把它们原样翻译成跨仓调用

#### Scenario: 条数达标即可进入提取阶段

- **WHEN** 两份豁免清单的 `frozenTotal` 均已降至约定阈值以下且门禁持续通过
- **THEN** 该项准入条件判定通过，无需额外的主观评估

