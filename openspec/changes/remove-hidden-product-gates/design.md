## Context

历史 rollout 采用“先代码、后环境开闸”，随后产品又增加了账号级配置、渠道开关、周历、审批模式和运行控制。旧开关没有随产品控制面收敛，形成两套授权：后台写入成功只是必要条件，运维还必须知道并修改 `.env`。这会制造不可解释的人工审核降级、能力恒 false、排期不运行或某环境永久不执行。

本 change 跨 Cloud/Edge/Console。约束包括：Cloud `RiskController` 仍是最终风险状态单写者；不可逆写必须校验身份、能力、作用域、限速、幂等和结果；Edge 已安装客户端不会因源码合并自动升级；dev/ol 数据与 worker 必须按 `execution_target` 隔离。

## Goals / Non-Goals

**Goals:**

- 常规产品行为只有一套可解释的业务授权：后台账号/渠道/排期/审批配置。
- 删除会把可见“开启”静默改成“不执行”的环境变量。
- 让 Cloud 与 Edge 的能力原因来自真实身份、只读探针、端点健康和运行控制，不来自本机人工白名单。
- 保持全局紧急停写、风险、限速、熔断、幂等、平台确认等安全边界。
- 用测试锁死已删除变量即使重新出现在进程环境中也不能改变产品行为。

**Non-Goals:**

- 不删除超时、并发、阈值等可观测调优参数。
- 不删除诊断、mock、真机 probe 等只在显式测试入口消费且不会覆盖后台产品配置的变量。
- 不把尚未形成后台产品承诺的实验能力强行常开。
- 不在本 change 构建或发布 Edge 安装包。

## Decisions

### 1. 用“是否覆盖显式产品配置”而不是变量命名判定

删除清单：

| 领域 | 删除的隐藏授权 | 新事实源 |
|---|---|---|
| 视频号自动回复 | `AIDCP_INTERACTION_AUTO_ACCOUNT_ALLOWLIST` | published auto-safe policy + channel/rule + runtime controls |
| 视频号私信 AI | `AIDCP_INTERACTION_DM_AI_ENABLED` | channel `aiPolishEnabled` 与规则策略 |
| 视频号 Edge | 本地 interaction/write/account/channel gates 与 write-probe-approved gates | scoped Cloud controls + active identity + successful read probe + endpoint breaker |
| 内容排期 | `AIDCP_CONTENT_SCHEDULE_AUTO`, legacy `AIDCP_PUBLISH_AUTO` | deploy target + account schedule/action settings |
| FB 评论 | `AIDCP_FB_COMMENT_AUTO/SHADOW/REVIEW_ALL` | account schedule/manual command + structured approval policy |
| FB 加群 | `AIDCP_FB_GROUP_JOIN_AUTO/SHADOW` | account join automation config + schedule + risk |
| FB 浏览 | `AIDCP_FB_BROWSE_AUTO` dev-only injection | platform/account lifecycle and normal risk controls |
| 评论点赞 | `AIDCP_COMMENT_LIKE` | configured quota + stochastic/content/risk gates |

保留 `AIDCP_INTERACTION_WRITE_ENABLED`，因为它是环境级不可逆写紧急刹车，Cloud 会把 effective 状态投影到运行控制；它不是账号白名单。保留部署目标、schema compatibility、auth/capability、熔断、风控、限速、CAS/幂等和 post-check。

替代方案是把每个环境变量都暴露到后台。拒绝：这仍然保留重复授权和组合爆炸，用户必须理解实现细节才能让配置生效。

### 2. 视频号写能力使用只读链路证据，不要求“写过一次才允许写”

评论写能力要求：Cloud 控制允许评论读/写、身份 active 且匹配、评论只读探针成功、相关端点未熔断。私信同理。第一次真实写仍走严格目标、幂等 key、单飞、限速与结果确认；结构错误会打开对应端点熔断。

替代方案是保留 `*_WRITE_PROBE_VERIFIED`。拒绝：正常安装包没有安全途径生成这些本机环境变量，导致产品配置永远无法生效；它证明的是运维手工改过环境，而不是当前账号/当前会话/当前端点健康。

### 3. 调度器常驻，动作默认关闭

合法 `AIDCP_DEPLOY_ENV=dev|ol` 下始终构造 `ContentScheduler`。空配置和默认关闭的账号不会触发动作；执行目标不合法仍不启动。删除 legacy `PublishScheduler` interval，避免第二套触发器。

### 4. 删除影子模式的生产环境入口

Facebook 评论/加群的 shadow 环境变量是 rollout 工具，不是产品状态。现有测试可通过显式依赖/fixture 验证只读阶段，但生产装配不再读取 shadow 变量。需要未来灰度时应建立可见、可审计、作用域化的产品配置，而不是恢复进程级隐藏变量。

### 5. 跨仓能力声明同步

Cloud 与 Edge 的 platform registry 镜像同时移除 `runtimeGate` 字段和值；Console 删除“还需开启环境变量”的说明。协议字段不新增，避免无必要的 v2 漂移。

## Risks / Trade-offs

- [删除默认关闭开关会扩大动作可达性] → 账号/动作默认配置保持关闭；测试覆盖空配置不触发、暂停/风险/限速/身份/能力拒绝。
- [评论写能力不再要求预先真写探针] → 仍要求相邻只读链路成功、精确目标、幂等、单飞、端点熔断与发送后确认；错误不转成功。
- [Facebook 旧运维 shadow 流程消失] → 保留单测 fixture 和只读 probe 脚本；生产灰度必须以后走可见配置。
- [Edge 源码修复未立即进入 V11] → closeout 明确区分 Cloud/Console dev 部署与 Edge 包可用性，不声称已安装客户端已修复。
- [并行分支改变相同热点] → 集成前 fetch/rebase 最新默认分支，逐仓重跑验证，只做 fast-forward。

## Migration Plan

1. 先合并/部署 Cloud，使白名单、DM AI、内容排期和 Facebook Cloud 门禁消失；保留全局互动紧急停写。
2. 部署 Console 文案，确保界面不再指导运维开隐藏变量。
3. 合并 Edge 源码；不构建安装包。后续显式发布新客户端后，正常安装包才获得写能力收敛与 FB 浏览策略修复。
4. dev 验证启动日志、health、interaction runtime controls、Feishu、PostgreSQL和错误日志；本次不主动创建真实回复或平台写入。
5. 回滚 Cloud/Console 使用部署备份与前一提交；Edge 若尚未发包无需客户端回滚。

## Open Questions

- 无。若真实测试暴露平台写端点缺少足够的只读能力证据，新增的必须是身份绑定且可观测的能力证据，不得回退到账号/环境白名单。
