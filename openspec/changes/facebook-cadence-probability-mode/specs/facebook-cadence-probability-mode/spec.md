# facebook-cadence-probability-mode Delta

## ADDED Requirements

### Requirement: 全局节奏解释模式开关覆盖全部 A→B 节奏数值

云端 SHALL 在 Facebook 全局运行数值单例策略上提供一个全局字段 `cadenceMode`,取值 `fixed`(既有精确计数)或 `probabilistic`,默认 `fixed`。该字段 SHALL 与其余全局数值同一条 PUT 原子写(revision 乐观锁、审计、镜像 bump),并 SHALL 统一作用于全部 11 个「N 次 A → 1 次 B」数值:Reel 观看节奏(persona / slow_start 的 viewsPerLike 与 viewsPerFollow、rule / consumption 的 viewsPerFollow)、规则模式(viewsPerLike、joinEveryNRounds)、消费模式(viewsPerLike、confirmedLikesPerJoin、confirmedJoinsPerComment)。`probabilistic` 模式下,每次合格 A 事件 SHALL 独立以 1/N 概率触发 B;`fixed` 模式行为 MUST 与本 change 之前逐字相同。环境级 rule/consumption 覆盖值(cadence_source='environment')的数值仍按环境取,但解释模式 SHALL 只认全局开关,环境路由 MUST NOT 接受模式覆盖。

#### Scenario: 固定模式零回归

- **WHEN** `cadenceMode='fixed'`(含存量库缺列 / 镜像载荷缺字段的回落)
- **THEN** 全部 11 个节奏的触发行为、计数器推进、审计与修订语义与本 change 之前逐字相同

#### Scenario: 概率模式长期均值一致

- **WHEN** `cadenceMode='probabilistic'` 且某节奏配置为 N
- **THEN** 每次合格 A 事件独立掷 1/N 判定,长期平均 B/A 比率趋近 1/N,但单次触发点不可预测(允许连续多次不中与相邻命中)

#### Scenario: 模式切换经策略修订生效

- **WHEN** 操作员经面板把 `cadenceMode` 从 `fixed` 改为 `probabilistic`(或反向)
- **THEN** 全局 revision +1、写审计,继承全局的环境行按既有级联机制获得新 policy_revision,进行中的批次 / 进度按既有快照失配机制重置,MUST NOT 出现「旧模式计数 + 新模式判定」混合推进

### Requirement: 概率判定是单点决策且不产生欠账

概率模式下每个触发判定 SHALL 只在对应事件的单一决策点掷一次(Reel 呈现时、确认 view / like / join 事件入账事务内);**会被反复读取的判定**(规则模式「本轮是否含加群」)SHALL 在轮次创建时掷一次并持久化,后续读取 MUST 返回持久化结果、MUST NOT 重掷。命中后既有的全部闸(预算、风控、冷却、作者/目标去重、单槽义务、平台确认后验)SHALL 原样生效;被闸拒绝 SHALL 结束本次机会且 MUST NOT 产生欠账或重试同一目标。计数器 SHALL 照常记录(可观测性),但 MUST NOT 在概率模式下驱动触发。随机源 SHALL 可注入(测试确定性),缺省 Math.random。

#### Scenario: 轮次含加群判定落库不漂移

- **WHEN** 概率模式下规则模式创建一个新轮次批,且同一批被多次读取(状态查询 / 恢复 / 对账)
- **THEN** 「本轮是否含加群」在创建时掷一次 1/joinEveryNRounds 并落库,所有后续读取返回同一结果

#### Scenario: 概率命中被风控闸拒绝不产生欠账

- **WHEN** 概率模式下某次 A 事件掷中触发 B,但风控 / 预算 / 冷却任一闸拒绝
- **THEN** 不下发命令、不计成功,本次机会结束;下一次机会来自后续 A 事件的独立掷骰,MUST NOT 对同一目标重试

### Requirement: 镜像下发版本偏斜安全

`cadenceMode` SHALL 随既有 facebook_operation_policy sync-read 镜像逐环境基线下发;载荷形状变更 SHALL 伴随 `config_mirror_version` 推进(防同游标不同载荷拒收)。共享校验器 SHALL 同时接受含与不含 `cadenceMode` 的基线键集;消费方读到缺字段 SHALL 回落 `fixed`。任何仓先于或后于其他仓部署 MUST NOT 导致信封拒收或行为错乱(最坏情况 = 暂时回落 fixed 现状)。

#### Scenario: 旧消费方遇新载荷

- **WHEN** automation 仍持旧 kernel 校验器而 api 已下发含 `cadenceMode` 的基线
- **THEN** 部署序内该窗口经镜像 version 推进触发全量重放,新校验器随 automation 部署一并到位;若消费方先行部署则对缺字段载荷回落 `fixed`,零行为回归

#### Scenario: 面板与镜像端到端

- **WHEN** 操作员在管理后台切到概率模式并保存成功
- **THEN** GET 回读带 `cadenceMode='probabilistic'` 与新 revision,automation 侧镜像在 bump 后的下一次同步读取到该字段并按概率模式判定
