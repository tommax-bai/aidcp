## MODIFIED Requirements

### Requirement: 发布审批写回经唯一共享函数、first-writer-wins、共享逐字节契约

Web 发布审批 SHALL 与飞书审批、客户端内审批、委托任务审批调用**同一个**授权写出口，写入同一张持久授权记录，用卡铸造时的同一个 `requestId`。写 MUST 是 first-writer-wins 的原子写，其原子性 MUST 由数据库的活跃行唯一约束承担，MUST NOT 依赖文件系统的排他创建或任何进程内互斥：第二个决定（Web vs 飞书 vs 客户端 vs 重复点击）MUST 快速失败、接口返回 `{alreadyDecided:<首个决定值>}`。接口 SHALL 返回 `{written:true}` 或 `{alreadyDecided}`，MUST NOT 返回 `{published:true}`（平台真实回执才是发布是否发生的真相）。

每次写入 MUST 携带真实的决策人与决策渠道，MUST NOT 用常量占位；`executionTarget` MUST 由服务端注入。系统 MUST NOT 接 `publish-executor.ts` 那条缺 `requestId`、属未激活 `activate-publish-pipeline` 的审批分支。

过渡窗口内该出口 MAY 在持久写成功后 best-effort 影子写一份同格式本机文件；影子写失败 MUST NOT 改变接口返回值、MUST NOT 向审批人报错、MUST NOT 回滚授权。

#### Scenario: 已决定的 requestId 第二路写快速失败
- **WHEN** 一个 `requestId` 已被飞书审批写定，随后 Web 又对同一 `requestId` 提交一个决定
- **THEN** 第二次写快速失败，接口返回 `{alreadyDecided}` 携首个决定值，该 `requestId` 的活跃授权行仍恰好一条且未被覆盖

#### Scenario: 写回不冒充发布成功
- **WHEN** Web 审批成功写入授权
- **THEN** 接口返回 `{written:true}`，绝不返回 `{published:true}`

#### Scenario: 影子写失败不影响授权成立
- **WHEN** 持久授权写入成功但影子文件写入失败
- **THEN** 接口仍返回 `{written:true}`，失败只记日志

#### Scenario: 红线反例——用文件排他创建做互斥（禁止）
- **WHEN** 有实现继续以本机文件的排他创建作为多入口审批的互斥手段
- **THEN** MUST 视为违规、不予合入；写方与执行侧分进程后该互斥会静默消失

### Requirement: 授权出口加写时活版本预检，共享逐字节写入函数保持不变

在共享的多入口授权写回出口之上，系统 MUST 在**调用侧**（写授权之前）对 `publish-` 类 requestId 加一道活版本预检：读取记录当前版本与「人授权的版本」比对，不一致则 MUST 拒绝该授权、MUST NOT 写入任何授权行（活跃槽位留空、记录留待审可编辑）。该预检 MUST 保持既有唯一共享写出口的 `first-writer-wins` 语义不变——版本比对留在调用侧，`contentVersion` 作为授权记录的真列随之落库；同版本并发授权仍在活跃行唯一约束上无害相撞（先到胜、后到 `alreadyDecided`）。

`contentVersion` MUST 是授权记录上的独立字段而非嵌在冻结载荷里的可选项，使下发前版本闸成为一个原子的查询谓词。

#### Scenario: 写时版本不符拒绝且不写授权
- **WHEN** 授权携带的版本与记录当前版本不一致（例如卡片上是旧版）
- **THEN** 授权被拒、不写入任何授权行，控制台回可区分的 `version_stale{currentVersion}`，飞书回一张就地替换卡「请到控制台重新审批」

#### Scenario: 版本随授权落库为真列
- **WHEN** 版本一致、授权写回
- **THEN** 授权行的 `contentVersion` 等于人所审的那一版，下发前版本闸可直接以其为谓词判定

#### Scenario: 同版本并发授权无害相撞
- **WHEN** 两路授权基于同一版本几乎同时写回
- **THEN** first-writer-wins：先到者写成功，后到者得 `alreadyDecided`，既有行为不变
