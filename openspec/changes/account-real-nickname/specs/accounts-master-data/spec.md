## ADDED Requirements

### Requirement: 账号平台真实昵称由云端角色驱动本人主页访问采集(edge 纯执行)

系统 SHALL 采集**当前登录账号自身**的小红书真实昵称用于后台展示,且**采集由云端角色驱动、edge 仅执行**:云端角色决定何时采、命令 edge 打开本人主页、解析上报的主页 DOM、单写持久化;**edge MUST NOT 做任何昵称相关决策**(不判定、不挑选、不门控)。该昵称只在账号**本人主页**可读(feed 页不含),故采集 SHALL 经一次「访问本人主页」完成。

- **触发与幂等(云端)**:当某连接的账号是真实平台 userid(非占位 `default`)**且** `accounts.nickname` 为 NULL 时,云端角色 SHALL 在会话开始时驱动**恰好一次**本人主页访问;`nickname` 已非空则 MUST NOT 再绕路(无写放大)。
- **执行(edge,纯操作)**:edge SHALL 按云端命令打开指定主页 id(`/user/profile/<id>`)、原样上报主页 DOM(含昵称;读不到则诚实置空,亦可由页面标题兜底),**MUST NOT** 含「这是不是自己」之类判定。
- **隔离(红线:本人绝不进社交管线)**:本人主页访问 MUST NOT 触发关注决策 / 关注命令、MUST NOT 产生 `interaction_feed` / 关注 / 去重记录、MUST NOT 被当作「被浏览作者」进入作者评估管线。判据为「上报主页的 author id == 该连接已认证账号」。
- **持久化(云端,单写、诚实)**:云端 SHALL **仅当**上报昵称非空时经单写接口 upsert 到该账号行;空(诚实失败)MUST NOT 覆盖已有真名、DB 保持 NULL 以便下次重试(有界)。
- **风控中性**:本人主页采集 MUST NOT 消耗风控配额 / 单场预算,MUST NOT 计为互动动作。
- **有界回 feed**:采集(成功或 edge 静默)后云端 SHALL 在有界时间内恢复正常浏览、绝不困死会话。
- **展示**:面板 API SHALL 暴露 `nickname`;console 账号名 SHALL 按 `nickname → label → accountId` 回落(无真名回落运营标识,MUST NOT 展示假名)。

该要求 MUST NOT 改变 `account_id` 作为主键,MUST NOT 影响已按账号 keyed 的风控/发布/概念表,MUST NOT 新增协议消息类型(经已有 `profile.open` 命令的可选字段 + 已有 `profile.detail` 上报);**废止**初版「昵称随握手由 edge 判定带回」的行为。

#### Scenario: 真实账号且昵称未知 → 云端角色驱动一次本人主页采集并持久化

- **WHEN** 某连接账号是真实 userid(非 default)且 `accounts.nickname` 为 NULL,会话开始
- **THEN** 云端角色命令 edge 打开本人主页(`profile.open{authorId=accountId, direct}`),读上报的主页昵称,经单写接口持久化,并让节点返回 feed

#### Scenario: 昵称已知 → 不再绕路

- **WHEN** `accounts.nickname` 已非空,会话开始
- **THEN** 云端不驱动本人主页访问(无写放大)

#### Scenario: 占位账号不采

- **WHEN** 账号为 `default`(占位、非 userid),会话开始
- **THEN** 云端不尝试昵称采集

#### Scenario: 本人绝不进社交管线

- **WHEN** 发生本人主页访问
- **THEN** 本账号 MUST NOT 产生 `profile.browsed`、MUST NOT 触发关注决策或关注命令、MUST NOT 生成 `interaction_feed`/关注/去重行、MUST NOT 消耗风控配额或单场预算

#### Scenario: 诚实空不覆盖真名

- **WHEN** edge 上报空昵称(诚实失败)
- **THEN** 云端 MUST NOT 写入,`accounts.nickname` 保持原值(NULL 则下次会话有界重试)

#### Scenario: edge 静默 → 有界恢复浏览

- **WHEN** 本人主页采集中 edge 在超时内未上报(如 CDP 断)
- **THEN** 云端在有界时间(~20s)内恢复浏览、返回 feed,绝不困死会话

#### Scenario: edge 保持纯执行

- **WHEN** 昵称采集链路运行
- **THEN** edge 仅打开云端指定的主页 id 并原样上报主页 DOM(含标题兜底),不含任何昵称判定 / 自身识别;采集不新增协议消息类型
