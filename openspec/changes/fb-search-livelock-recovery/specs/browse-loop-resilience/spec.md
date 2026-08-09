# browse-loop-resilience — delta (fb-search-livelock-recovery)

## ADDED Requirements

### Requirement: 搜索失败必须回滚搜索行程页型

Cloud 在搜索命令下发时将会话页型标为 `search`(搜索行程开始);当该搜索以失败终态(`action=search, ok=false`)返回时,Cloud SHALL 立即把 `sourcePageType` 回滚为 `feed` 并清空搜索行程计数(已浏览搜索卡数、连续滚动数)。MUST NOT 让失败的搜索把会话钉死在「搜索行程」状态——那会使后续一切恢复滚动都声明错误的面、被 Edge 诚实拒绝,形成活锁。回滚 SHALL 先于任何失败兜底处置执行,保证兜底命令解析到正确的面。

#### Scenario: 搜索失败后页型立即回滚

- **WHEN** 已下发的搜索以 `ok=false` 终态返回(含 `not_submitted` 与 `failed_after_submit`)
- **THEN** `sourcePageType` 回滚为 `feed`,搜索行程计数清零
- **AND** 随后的失败兜底与看门狗恢复滚动不再声明 `search` 面

#### Scenario: 搜索成功不受回滚影响

- **WHEN** 搜索以 `ok=true` 终态返回并送达搜索结果卡片
- **THEN** 页型保持 `search`,搜索行程按既有有界退出规则(攒卡回首页)继续

### Requirement: 面错位失败回执必须被消费

Edge 按面声明闸拒绝滚动时回报 `reason` 以 `surface_mismatch_observed_` 开头的失败终态,回执名携带实际观测面。Cloud SHALL 消费该回执:按观测面重同步面认知(`observed_reels` → 最近列表形态记为 `reels`;`observed_list` → 记为 `feed`),且当 `sourcePageType='search'` 时一并回滚为 `feed`(观测已证明不在搜索页);随后进入统一失败恢复处置。MUST NOT 让该回执落入零处置——诚实拒绝被读成「什么都没发生」正是活锁的形成机制。

#### Scenario: 声明搜索面实测 Reels 的拒绝被纠正

- **WHEN** Cloud 收到 `action=scroll, ok=false, reason=surface_mismatch_observed_reels` 且会话页型为 `search`
- **THEN** 面认知更新为 `reels`、页型回滚为 `feed`,并触发统一失败恢复处置
- **AND** 下一条恢复命令按纠正后的面下发,不再重复同一错位

#### Scenario: 声明 Reels 面实测列表的拒绝被纠正

- **WHEN** Cloud 收到 `reason=surface_mismatch_observed_list` 的滚动失败终态
- **THEN** 面认知更新为 `feed`,并触发统一失败恢复处置

### Requirement: 导航类失败的默认恢复是有界 redrive 回主浏览入口

导航类动作(搜索、开帖、返回、刷新、主页打开等非互动类)失败后,Cloud 的默认兜底 SHALL 从「按当前面认知原地滚动」改为 redrive 回本场钉住的主浏览入口(复用既有 `resume_redrive` 语义:主入口为 Reels 的账号重驱 Reels 入口,其余回首页 feed),并在 redrive 前把 `sourcePageType` 标回 `feed`——回主路径与页型账本 MUST 同步翻转。互动类失败(点赞/评论/收藏/关注/加群等)保持既有各自重试逻辑,MUST NOT 走本兜底。

失败恢复 SHALL 受统一恢复预算约束:凡「失败→redrive」消耗 1 次预算,任何成功动作回执将预算清零;预算耗尽(连续 3 次失败恢复未见任何成功)时 Cloud SHALL 以具名原因诚实结束本场会话,MUST NOT 继续无限重驱。恢复预算 MUST 只由失败消费——准备性动作不扣减。会话结束后由续场闸与排程正常接管,浏览器槽位随会话结束参与轮转。

#### Scenario: 搜索失败兜底 redrive 回主入口

- **WHEN** Facebook 主入口为 Reels 的账号搜索失败,页型已回滚
- **THEN** 兜底命令是 redrive 重驱 Reels 入口,不是在搜索面上原地滚动

#### Scenario: 恢复预算耗尽时诚实结束会话

- **WHEN** 连续 3 次失败触发的 redrive 之间没有出现任何成功动作回执
- **THEN** Cloud 以具名原因(如 `recovery_exhausted`)结束本场会话
- **AND** 结束不是静默假失败:原因落日志与会话终局,续场闸照常评估下一场

#### Scenario: 成功回执重置恢复预算

- **WHEN** 一次失败恢复后收到任意成功动作回执
- **THEN** 恢复预算清零,后续偶发失败重新拥有完整恢复窗口

#### Scenario: 互动类失败不走 redrive 兜底

- **WHEN** 点赞或评论动作失败
- **THEN** 走各自既有的原地重试/终局逻辑,不触发回主入口的 redrive
