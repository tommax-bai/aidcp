## MODIFIED Requirements

### Requirement: 手动解决必须与边缘自动清除并存且幂等无冲突

按 id 手动解决与既有「按 edge 自动清除」SHALL 共用同一个 `resolved_at IS NULL` 守卫。两条入口对同一行的并发/重复解决 MUST 靠数据库行锁串行——先提交者命中并置 `resolved_at`、后到者重估 `WHERE` 命中 0 行——从而幂等、诚实回真实行数、不二次解决、不报错。手动解决 MUST NOT 改动验证码事件的按 edge 自动清除与暂停/恢复语义。

#### Scenario: 手动解决后边缘配对清除命中 0 行

- **WHEN** 一条 `block` 告警已被人工按 id 解决，随后该 edge 才送来配对的 `captcha.cleared`
- **THEN** 按 edge 自动清除对该行命中 0 行、不二次解决、不报错（按 edge 恢复 edge 下发的既有语义照常）

#### Scenario: 两入口共用同一未解决守卫

- **WHEN** 检视按 id 解决与按 edge 解决的 SQL
- **THEN** 二者都带 `AND resolved_at IS NULL` 守卫，保证并发下行锁串行、后者命中 0 行
