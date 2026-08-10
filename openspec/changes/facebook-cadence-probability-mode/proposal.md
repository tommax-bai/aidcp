# Proposal: facebook-cadence-probability-mode

## Why

「Facebook 全局运行数值」里所有「N 次 A 触发一次 B」的节奏(共 11 个数值:Reel 观看节奏 6 个、规则模式 2 个、消费模式 3 个)目前全部是**固定计数**触发——精确数到第 N 次必触发,行为节拍完全可预测,是机械指纹。用户要求增加一个全局开关:开启后同一批配置数 N 解读为「每次 A 有 1/N 概率触发 B」,长期均值不变、触发点不可预测,更接近真人。

## What Changes

- 全局策略单例(`facebook_operation_global_policy`)新增字段 `cadenceMode: 'fixed' | 'probabilistic'`(默认 `fixed`,零回归),经既有面板 PUT 原子写(revision 乐观锁 + 审计 + 级联传播 + 镜像 bump)与 sync-read 镜像下发。
- **一个开关统管全部 11 个数值**(用户裁定):
  - Reel 观看节奏(persona / slow_start 的 viewsPerLike+viewsPerFollow,rule / consumption 的 viewsPerFollow):会话内逐条判定从 `ordinal % N === 0` 变为每条 Bernoulli(1/N);
  - 规则模式 viewsPerLike(看 N 条起一批):每次确认 view 掷 1/N;joinEveryNRounds(每 N 轮含加群):**轮次(批)创建时掷一次 1/N 并落库**(该判定会被反复读取,不落库则不确定);
  - 消费模式 viewsPerLike / confirmedLikesPerJoin / confirmedJoinsPerComment:各自在确认事件到达的事务内掷 1/N。
- 概率命中后的所有既有闸(预算 / 风控 / 冷却 / 去重 / 单槽义务)原样生效;被闸拒绝不产生欠账——与固定模式的「无欠账」原则一致。
- 计数器照常记录(可观测性),但概率模式下不再驱动触发。
- 模式切换走既有策略修订机制:全局写 revision+1、级联 bump 继承环境的 policy_revision,运行时快照按既有 mismatch 机制重置。
- 版本偏斜兼容:镜像载荷缺 `cadenceMode` 时消费方回落 `fixed`(= 现状),kernel 校验器同时接受新旧两种键集,部署顺序无约束。

## Capabilities

### New Capabilities

- `facebook-cadence-probability-mode`: 全局节奏解释模式开关——fixed(精确计数)/ probabilistic(逐事件 1/N 概率),覆盖全部 11 个 A→B 节奏数值、单点决策落库规则、闸序不变、无欠账、版本偏斜回落。

### Modified Capabilities

- `facebook-reel-mode-cadence`: 「第 N 条 Reel 触发」的既有 requirement 加上模式限定——固定模式行为不变;概率模式下改为每条合格 Reel 独立 1/N 判定,其余(去重 / 无欠账 / 只认平台确认成功)不变。

## Impact

- **aidcp-kernel**(v0.1.4 → v0.1.5 新 tag):`FacebookCadenceMode` 类型 + 投影字段 + sync-read 基线校验器兼容新旧键集。
- **aidcp-api**:迁移 0118(全局表加列 + `config_mirror_version` bump,样板 0108)、store 读写/审计/传播/schema 探针、panel GET/PUT、kernel pin 抬 v0.1.5(从 v0.1.1 跨版本,typecheck 把关)。
- **aidcp-automation**:迁移 0119(规则批次表加 `includes_join` 持久列)、五处触发点接模式分支 + 随机源注入、schema 门 REQUIRED/KNOWN_MAX 抬到 0119、kernel pin 抬 v0.1.5。
- **aidcp-console**:全局策略编辑器加模式开关(Segmented)、类型、枚举单源、测试。
- **部署**:dev 上 api + automation(带各自 migrate --owner + 随包送新 kernel)+ console;无边缘/协议改动,不需要客户端发版。
