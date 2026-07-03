## ADDED Requirements

### Requirement: 待审草稿编辑经拥有者对象一等单写、乐观 CAS、诚实非乐观

「待审正文草稿」的编辑 MUST 经拥有 `publish_log` 的进程内对象的一等单写方法完成，面板 MUST NOT 发任何裸 SQL。该方法 MUST 以乐观并发方式落库——`UPDATE … SET content_version = content_version + 1, … WHERE id = $id AND status = 'pending_approval' AND content_version = $expectedVersion RETURNING`，匹配 0 行时 MUST 经补充查询消歧为可区分拒因（`not_found` / `not_pending` / `version_conflict`），并在编辑前探测授权签名是否已存在（在途授权则拒 `already_decided`）。该方法 MUST NOT 乐观假成功、MUST 写后回读真态返回，且 MUST NOT 为不存在的记录 seed 行。审计以 `edited_by`（JWT 主体）/ `edited_at` 就地记录「谁 / 何时」。

#### Scenario: 并发编辑乐观拒绝
- **WHEN** 两个运营基于同一版本并发编辑同一草稿
- **THEN** 先到者版本自增成功，后到者匹配 0 行、得到可区分的 `version_conflict`，须刷新后重试，且无丢更新

#### Scenario: 授权在途拒绝编辑
- **WHEN** 编辑时该草稿的授权签名已存在（授权在途）
- **THEN** 编辑被拒 `already_decided`、不改动记录；该拦截为暂态——过期签名被下发兜底删除后草稿回可编辑

#### Scenario: 写后回读真态
- **WHEN** 编辑成功
- **THEN** 方法返回写回后的真实版本号与字段（非乐观回显），面板据此渲染，绝不假成功

### Requirement: 授权出口加写时活版本预检，共享逐字节写入函数保持不变

在共享的 Web + 飞书授权写回出口之上，系统 MUST 在**调用侧**（写签名之前）对 `publish-` 类 requestId 加一道活版本预检：读取记录当前版本与「人授权的版本」比对，不一致则 MUST 拒绝该授权、MUST NOT 写任何签名（O_EXCL 槽位留空、记录留待审可编辑）。该预检 MUST 保持既有唯一共享写入函数 `first-writer-wins`、逐字节契约不变——版本比对留在调用侧，`contentVersion` 仅作为字段随既有签名 payload 附带；同版本并发授权仍在 O_EXCL 上无害相撞（先到胜、后到 `alreadyDecided`）。

#### Scenario: 写时版本不符拒绝且不写签名
- **WHEN** 授权携带的版本与记录当前版本不一致（例如卡片上是旧版）
- **THEN** 授权被拒、不写任何签名，控制台回可区分的 `version_stale{currentVersion}`，飞书回一张就地替换卡「请到控制台重新审批」

#### Scenario: 共享出口字节不变
- **WHEN** 版本一致、授权写回
- **THEN** 仍经唯一共享函数写同一逐字节契约的签名（payload 多带一个 `contentVersion` 字段），Web 与飞书两路出口保持字节一致

#### Scenario: 同版本并发授权无害相撞
- **WHEN** 两路授权基于同一版本几乎同时写回
- **THEN** first-writer-wins：先到者写成功，后到者得 `alreadyDecided`，既有行为不变
