## ADDED Requirements

### Requirement: 内容排期写入经一等单写通道，UPSERT 前校验账号存在，默认 fail-closed

内容排期的写入——每账号 `PUT /api/content-schedule/:accountId` 与全局 `PUT /api/content-schedule/global`——SHALL 经受 JWT 保护的一等单写通道（内容排期存储的专属方法），MUST NOT 用 raw SQL UPDATE 绕过，MUST NOT 报告乐观成功。每账号写为 UPSERT，且写前 SHALL 先校验 `accounts` 中确有该账号行（无行 → 具名拒 `unknown_account`，绝不为不存在 / 退役账号造幽灵排期行），退役保留账号 `default` SHALL 拒。非法值（掩码非 168 位 '0'/'1'、日上限非非负整数、坏结构）SHALL **整块拒**、绝不部分落库。写后 SHALL 回读真态返回，且拒绝与成功 MUST **可区分**呈现。缺省与非法一律 fail-closed（归「不自动」）。此与本 spec「写只经拥有者对象、诚实非乐观」核心不变量同构。

#### Scenario: 写后回真态
- **WHEN** 运营经面板保存某账号或全局的内容排期
- **THEN** 接口返回从内容排期存储读回的写后真实状态，而非提交即返回的乐观「ok」

#### Scenario: 未知账号拒、不造幽灵行
- **WHEN** 对一个 `accounts` 中不存在或已退役的账号 PUT 内容排期
- **THEN** 接口具名拒绝（如 `unknown_account` / 退役拒），绝不 UPSERT 出一条孤儿排期行

#### Scenario: 非法值整块拒
- **WHEN** 提交的内容掩码非 168 位 '0'/'1'、或日上限为负 / 非整数
- **THEN** 整块拒绝、绝不部分落库，接口以可区分于成功的方式呈现拒绝
