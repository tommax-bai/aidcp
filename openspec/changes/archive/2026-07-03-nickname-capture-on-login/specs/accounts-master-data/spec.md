## MODIFIED Requirements

### Requirement: 账号平台真实昵称由云端角色驱动本人主页访问采集(edge 纯执行)

系统 SHALL 采集**当前登录账号自身**的小红书真实昵称用于后台展示,且**采集由云端角色驱动、edge 仅执行**:云端角色决定何时采、命令 edge 打开本人主页、解析上报的主页 DOM、单写持久化;**edge MUST NOT 做任何昵称相关决策**(不判定、不挑选、不门控)。该昵称只在账号**本人主页**可读(feed 页不含),故采集 SHALL 经一次「访问本人主页」完成。

采真名是**登录后的固定引导步骤**,与浏览会话/人设解耦:

- **触发与幂等(云端)**:当某连接的账号是真实平台 userid(非占位 `default`)**且** `accounts.nickname` 为 NULL 时,云端角色 SHALL 在**该账号登录后(edge hello)**驱动**恰好一次**本人主页访问;`nickname` 已非空则 MUST NOT 再绕路(无写放大)。该触发 **MUST NOT 被诚实人设启动闸阻断**——未绑人设、被启动闸拦下不开浏览会话的账号,登录后**仍** SHALL 采一次真名。绑了人设的账号经会话开始(`session_start`)触发同一采集体,行为不变。
- **红线:采集不等于浏览**。登录引导采集路径 **MUST** 只驱动「访问本人主页」这一个动作(经 `profile.open{direct}` + 读 `profile.detail` + 单写),**MUST NOT** 接入浏览反应链;未绑人设的账号采完真名后 **MUST** 闲置,**MUST NOT** 在默认人设上浏览/点赞/关注/评论/搜索。
- **执行(edge,纯操作)**:edge SHALL 按云端命令打开指定主页 id(`/user/profile/<id>`)、原样上报主页 DOM(含昵称;读不到则诚实置空,亦可由页面标题兜底),**MUST NOT** 含「这是不是自己」之类判定。
- **持久化(云端,单写、诚实)**:云端 SHALL **仅当**上报昵称非空时经单写接口 upsert 到该账号行;空(诚实失败)MUST NOT 覆盖已有真名、DB 保持 NULL 以便下次有界重试。
- **有界**:~20s 兜底超时(edge 静默/未登录不困死会话/连接);采空 K 次后退避,不永绕。`profile.open` 采集 MUST NOT 触发风控/预算/节奏。
- **调度开关**:全局调度关闭时 MUST NOT 驱动边端(连登录引导采集也不动)。
- **展示**:面板 API SHALL 暴露 `nickname`;console 一切展示账号名处 SHALL 按 `nickname → label → accountId` 回落(无真名回落运营标识,MUST NOT 展示假名)。

该要求 MUST NOT 改变 `account_id` 作为主键,MUST NOT 影响已按账号 keyed 的风控/发布/概念表,MUST NOT 新增协议消息类型(经已有 `profile.open` 命令的可选字段 + 已有 `profile.detail` 上报)。

#### Scenario: 真实账号且昵称未知 → 登录后(不经人设闸)驱动一次本人主页采集并持久化

- **WHEN** 某连接账号是真实 userid(非 `default`)且 `accounts.nickname` 为 NULL,该账号登录(edge hello)
- **THEN** 云端角色在**登录引导**(不要求开浏览会话、不要求绑人设)命令 edge 打开本人主页(`profile.open{authorId=accountId, direct}`),读上报的主页昵称,经单写接口持久化,且全程不浏览

#### Scenario: 未绑人设账号登录 → 仍采真名但绝不浏览(红线)

- **WHEN** 账号未绑人设、被诚实人设启动闸拦下(不开浏览会话),但库内昵称为 NULL 且全局调度开着,该账号登录
- **THEN** 云端**仅**驱动一次本人主页采集(恰一次 `profile.open{direct}`),采到非空昵称即持久化;**MUST NOT** 产生任何浏览指令(open_note/like/collect/follow/comment),采完即闲置

#### Scenario: 昵称已知 → 不再绕路

- **WHEN** `accounts.nickname` 已非空,该账号登录或会话开始
- **THEN** 云端不尝试昵称采集(无写放大、零扰动)

#### Scenario: 全局调度关闭 → 不驱动边端

- **WHEN** 全局调度开关关闭(运营显式暂停),未绑人设账号登录
- **THEN** 云端 MUST NOT 驱动任何命令(连登录引导采集也不动)

#### Scenario: 上报空昵称(诚实失败)→ 不写、有界重试

- **WHEN** edge 上报空昵称(未登录/读不到)
- **THEN** 云端 MUST NOT 写入,`accounts.nickname` 保持原值(NULL 则下次有界重试),采集经 ~20s 超时兜底干净收尾

#### Scenario: edge 纯执行,不新增协议

- **WHEN** 昵称采集链路运行(无论经会话开始还是登录引导)
- **THEN** edge 仅打开云端指定的主页 id 并原样上报主页 DOM(含标题兜底),不含任何昵称判定/自身识别;采集不新增协议消息类型
