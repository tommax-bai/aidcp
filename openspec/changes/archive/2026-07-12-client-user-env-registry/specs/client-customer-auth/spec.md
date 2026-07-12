# client-customer-auth Specification

## ADDED Requirements

### Requirement: Standalone environment registry decoupled from assignment

系统 SHALL 维护一张**独立于归属**的环境注册表 `client_environments`（env_key 主键 + label/platform/source），使环境可以「只登记、不归属任何客户」。管理侧的全局环境全集 MUST 为「注册表 ∪ 归属表」的并集——**未分配给任何客户的环境（assigneeCount=0）也 MUST 被列出**，供后台「待分配」池呈现。label/platform MUST 优先取归属行最新非空值、回落注册表登记值。该表 MUST 由 `init()` 的 `CREATE TABLE IF NOT EXISTS` 自建（无迁移器），MUST NOT 加 FK 到 accounts 热点表。

该全集读为**跨用户聚合**，MUST 只接入受内部 JWT 的面板端点，MUST NOT 注入客户鉴权服务（N2 结构性无泄漏不变）。缺表（首启竞态）MUST fail-closed 回落空数组。

#### Scenario: 未分配环境出现在待分配池

- **WHEN** 一个环境已登记进注册表但尚未归属任何客户
- **THEN** 全局环境全集读 MUST 列出该环境，其 assigneeCount 为 0（后台呈现为「待分配」）

#### Scenario: 已归属但不在注册表的环境不丢

- **WHEN** 某 env_key 只在归属表出现（如历史客户端自建 attach）、注册表尚无
- **THEN** 并集读 MUST 仍列出该环境，并带其真实归属客户与人数

#### Scenario: 跨用户聚合不越权

- **WHEN** 持客户令牌的请求试图取得全局环境全集
- **THEN** 客户侧 MUST 无此能力（只有吃 userId 的 scoped 读），全集读只经内部面板端点

### Requirement: Environment registration is assignment-free and idempotent

系统 SHALL 提供批量登记能力 `registerEnvironments(items, source)`，把环境写入注册表而**不产生任何归属**（MUST NOT 写归属表）。登记 MUST 幂等：冲突时只用**非空**新值补 label/platform（COALESCE，绝不拿 null 覆盖既有非空值），`source` 仅首次插入时定、冲突不降级。空 / 全空白 env_key MUST 跳过；MUST 按 env_key 去重。env_key MUST 为裸 profileId（不带 `ads-` 前缀），与边缘 attach / `/my-environments` 过滤口径逐字一致。

登记来源分三类：一次性导入存量环境（`import`）、边缘握手自动登记（`auto`）、后台手动登记（`admin`）。**任何自动路径 MUST NOT 推断归属**——绝不把环境塞给某个客户（fail-closed 归属边界不破）。

#### Scenario: 边缘连上自动进池但不归属

- **WHEN** 一个 AdsPower 环境（edgeId=`ads-<分身id>`）完成握手注册
- **THEN** 系统 MUST 以裸 profileId 登记该环境进注册表（source=auto），且 MUST NOT 为其创建任何客户归属

#### Scenario: 非分身兜底 edge 不登记

- **WHEN** 握手 edge 的 edgeId 非 `ads-` 前缀（self-/host- 兜底）
- **THEN** 系统 MUST NOT 把它登记为可分配环境

#### Scenario: 幂等登记不覆盖既有好值

- **WHEN** 对已登记环境再次登记、但新值 label 为空
- **THEN** MUST 保留既有非空 label，MUST NOT 用空值覆盖
