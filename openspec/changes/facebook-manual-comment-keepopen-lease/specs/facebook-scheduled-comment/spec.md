## ADDED Requirements

### Requirement: Facebook targeted comment holds a keep-open edge lease through human review

Facebook 定向评论（手动 `/comment` / `--join` 与自动排期两条触发路径同等生效）SHALL 在**一个持续持有的边端租约**内完成「站内搜索 → 打开目标帖 → 撰写 → 飞书人审 → 提交」整段，**贯穿人审等待窗口不释放边端**，直至提交或诚实终止。租约 `kind` MUST 为 `comment_prepare`，`leaseMs` MUST 覆盖搜索 + 读正文 + 人审超时 + 提交的最坏耗时。审批期间边端 MUST 停留在目标帖、MUST NOT 被同一会话并发的自治浏览闭环夺走浏览器或导航离开。

系统 MUST 给该路径下发给边端的**每一条评论命令**（`search.execute` / `note.open` / `interaction.comment`）透传该租约的 `taskId`。这是硬性要求而非可选：边端 FB 命令入口按 `canExecute(payload.taskId)` 无差别门控——持租约期内**无 taskId 的命令一律被挡**，故评论自身的命令若不带匹配 taskId 会被自己持有的租约一起挡死（自锁死锁）。透传后：本任务的评论命令（taskId 匹配）放行、并发自治浏览闭环的无标识命令（`page.scroll` / 返回等）被挡 → 页面钉死在目标帖。

租约 `priority` MUST 反映触发来源：手动操作员命令为 `'human'`、自动排期为 `'automatic'`（与小红书 keep-open 同口径）。

诚实边界不变：租约只负责「把浏览器钉在目标帖上」，MUST NOT 借此绕过或弱化任何既有闸——未授权 / 人审超时 / 被拒照样不提交（AC-PUB）；发布前就地核对目标帖身份、不评错帖、不重复评论照旧。**拿不到租约（获取超时）或提交前被更高优先级任务抢占**时，MUST 走诚实非提交终态（不打去重标记、可重试、不误计当日上限），MUST NOT 静默假成功。

边端不需改动：taskId 门控（`canExecute`）与租约接线为既有通道，本要求为 cloud 侧接线（申请租约 + 透传 taskId）。

#### Scenario: 手动 /comment --join 持锁贯穿人审、审批期停在目标帖
- **WHEN** 运营 `/comment <目标> --join` 触发 FB 定向评论，搜索命中候选并打开目标帖，进入飞书人审等待
- **THEN** 系统 MUST 在同一持有的 `comment_prepare` 租约内保持在目标帖贯穿撰写与人审等待，MUST NOT 在人审窗口释放边端使并发自治浏览闭环把页面导回首页；人审通过后 MUST 在**同一目标帖**上提交（不再复搜/换页）

#### Scenario: FB 评论命令透传 taskId、并发浏览命令被挡
- **WHEN** 该 keep-open 租约持有期间，边端同时收到本任务的评论命令（带匹配 taskId）与自治浏览闭环命令（无 taskId）
- **THEN** 带匹配 taskId 的评论命令 MUST 被 `canExecute` 放行执行；无 taskId 的浏览命令 MUST 被挡（不导航离开目标帖）

#### Scenario: 拿不到租约或提交前被抢占 → 诚实非提交
- **WHEN** 租约获取超时（边端无响应），或提交前被更高优先级任务抢占
- **THEN** MUST 记诚实非提交终态、MUST NOT 打每帖去重标记（可重试）、MUST NOT 误计当日评论上限，MUST NOT 静默假成功

#### Scenario: 红线反例——为省事不持锁或不透传 taskId（禁止）
- **WHEN** 有实现让 FB 定向评论在人审期不持锁（撒手等审批），或持锁却不给评论命令透传 taskId
- **THEN** MUST 视为违规、不予合入：前者会被自治浏览闭环滚回首页致 `editor_not_found`；后者会被自己的租约把评论命令挡死
