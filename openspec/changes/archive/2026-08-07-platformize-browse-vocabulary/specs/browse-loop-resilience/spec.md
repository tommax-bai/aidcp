## MODIFIED Requirements

### Requirement: 浏览循环因结束命令停止后须可被云端浏览类命令唤醒重启

边端浏览循环在收到会话结束命令（`session.end`）停止后（循环退出、不再上报），若随后收到云端**浏览类推进命令**（如 `xiaohongshu.feed.scroll` / `facebook.feed.scroll`、`navigation.back` 等），MUST 能**重启浏览循环**并重新上报 `page.cards`，使云端决策环得以继续；MUST NOT 把这类命令静默堆进**无人消费**的命令队列致其永久堆积（既有缺陷：循环停止后命令被入队但无消费者）。重启 MUST 幂等（循环已在跑时为安全空操作），且重启语义 MUST 与自动续场配套——云端续场重开会话后下发的引导命令必须能让已停的边端循环复活。重启 MUST NOT 在边端**主动诚实下线/关闭**流程中误触（关闭中收到的迟到命令不得复活循环）。

#### Scenario: 结束后收到浏览类命令重启已停循环

- **WHEN** 边端浏览循环已因 `session.end` 停止，随后收到云端一条浏览类推进命令（如续场引导的 `xiaohongshu.feed.scroll` / `facebook.feed.scroll`）
- **THEN** 边端重启浏览循环、重新评估当前页并上报 `page.cards`，云端据此续驱决策环

#### Scenario: 浏览类命令 MUST NOT 静默堆积无人消费

- **WHEN** 浏览循环未在运行时收到云端浏览类命令
- **THEN** 命令 MUST 触发循环重启被消费，MUST NOT 仅入队后无任何消费者而永久静默堆积

#### Scenario: 关闭流程中迟到命令不复活循环

- **WHEN** 边端正在主动诚实下线/关闭，期间收到一条迟到的云端浏览类命令
- **THEN** 边端 MUST NOT 因该命令重启浏览循环（关闭语义优先），干净退出

### Requirement: Facebook deep-read failures retain canonical recovery semantics

When a Facebook browse session receives a cloud-dispatchable deep-read, interaction, refresh, or notification command that it cannot execute, it SHALL return `action.completed` with the canonical orchestration action name and `ok:false` with an honest reason. The cloud ingress SHALL normalize legacy protocol-message action names before publishing the completion to session roles. A failed `browse_images` or `scroll_comments` completion SHALL advance the corresponding reader stage rather than being treated as an unknown failure. After the platform-scoped rename, the deep-read commands `xiaohongshu.note.browse_images` / `xiaohongshu.note.scroll_comments` are structurally xiaohongshu-only, and a Facebook session's platform-segment gate rejects them at the edge entrance before dispatch; the honest-failure completion contract above governs whichever layer refuses the command.

#### Scenario: Unsupported image browse exits the detail flow
- **WHEN** the cloud sends `xiaohongshu.note.browse_images` to a Facebook edge that does not implement image browsing
- **THEN** the edge reports `action.completed { action: 'browse_images', ok: false, reason: 'capability_unsupported' }`
- **AND** DeepReader advances with zero images browsed so the normal return-to-list path can run

#### Scenario: Legacy dotted completion remains safe
- **WHEN** an edge layer mistakenly reports the protocol message name instead of the action key: `action.completed { action: 'xiaohongshu.note.scroll_comments', ok: false }`（直接切换后旧客户端执行不了新名命令，旧点号形态 `note.scroll_comments` 结构性不再出现；归一表键随词汇批 4 同批换新）
- **THEN** cloud normalizes the action to `scroll_comments` before session roles consume it
- **AND** the dispatcher does not issue a fallback feed scroll from the current detail page

### Requirement: Facebook scroll verifies the active list context

Before Facebook edge executes a feed scroll, it SHALL ensure the currently remembered list context is active. The remembered context SHALL be the main feed after normal entry/return and the search-results URL after a browse search. If it cannot restore that context, it SHALL report an honest failed scroll and SHALL NOT report page cards from a detail page.

#### Scenario: Detail-page recovery returns to search results
- **WHEN** a browse search opened a detail page and cloud subsequently asks for `facebook.search.scroll`
- **THEN** the edge restores that search-results URL before scanning or scrolling
- **AND** it does not redirect the search browse session to the homepage

### Requirement: 越南语 Feed 恢复控件必须由 Native 通过 CDP 可信点击

当无可用卡片的 Facebook 页面出现唯一、可见且规范化文案精确等于 `Đi đến Bảng feed` 的恢复控件时，Edge SHALL 把它识别为 Feed 恢复目标。页面脚本只可返回当前视口内的唯一坐标，MUST NOT 调用 DOM `click()` 或把“发现控件”当作已恢复。

Native MUST NOT merely because this recovery control exists activate the browser. It SHALL immediately re-locate the same semantic target before sending exactly one CDP `mouseMoved → mousePressed → mouseReleased` sequence. If the containing `facebook.feed.scroll` is the watchdog-authorized `idle_recover_nudge`, the common scroll entry MAY already have activated the exact target once; the recovery-control path MUST NOT activate it a second time. Only when the control disappears and the page is reclassified as the home surface may browsing continue. Ambiguous, offscreen, stale, or postcondition-missing controls SHALL return an honest not-started or indeterminate result.

#### Scenario: 唯一越南语恢复控件被可信点击

- **WHEN** 空卡片页面存在唯一可见的 `Đi đến Bảng feed` 控件
- **THEN** JavaScript 只返回坐标，Native 重新定位后发送一组 CDP 指针事件
- **AND** 控件消失且 home surface 被确认后才继续既有 Feed 浏览

#### Scenario: 恢复控件不独立触发前台化

- **WHEN** 非看门狗 `facebook.feed.scroll` 命中唯一可见的恢复控件
- **THEN** Native 重新定位并执行既有可信点击，但不调用 `Page.bringToFront`

#### Scenario: 看门狗恢复命令最多前台化一次

- **WHEN** `idle_recover_nudge` 已在公共滚动入口激活精确 target，随后命中 Feed 恢复控件
- **THEN** 恢复控件路径不再次激活 target
- **AND** it still re-locates the control before pointer input

#### Scenario: DOM click 不得冒充恢复

- **WHEN** 页面脚本识别到该控件
- **THEN** 页面脚本不调用 `HTMLElement.click()`
- **AND** 单纯取得坐标或完成 CDP 发包都不被记录为恢复成功

#### Scenario: 不唯一或后置状态缺失时失败关闭

- **WHEN** 同文案目标不唯一、目标在视口外、点击前已移动消失，或点击后未确认 home surface
- **THEN** Edge 不重复点击、不改点其他控件
- **AND** 按是否已经发出 CDP 点击分别报告未开始或结果不明

### Requirement: Reels keyboard-probe learning advances only through normal continuation
The Edge Reels key preference SHALL affect only which single key a normally admitted `facebook.reels.scroll` dispatches. An unconfirmed or identity-unresolved key delivery MAY select the alternate key for the next command, and canonical progress MAY retain the successful key, but neither result SHALL create an immediate retry, bypass dwell or risk admission, consume a view, or disable later commands. Cloud SHALL continue to own whether and when another command is admitted.

#### Scenario: Unconfirmed probe waits for normal admission
- **WHEN** Edge emits `reels_navigation_unconfirmed` after delivering one preferred key
- **THEN** no second key SHALL run in that command and the alternate key SHALL run only if Cloud later admits another scroll normally

#### Scenario: Identity-unresolved probe waits for normal admission
- **WHEN** Edge emits `reels_identity_unresolved` after delivering one preferred key
- **THEN** Edge SHALL emit no card or view and SHALL wait for Cloud's ordinary continuation path before trying the alternate key

#### Scenario: Confirmed key remains a soft preference
- **WHEN** one probe produces a canonical Reel and its key is retained
- **THEN** the retained key SHALL still run only after the next command passes existing session, quota, soft-pause, interaction-hold, dedupe, dwell, cancellation, and deadline gates

#### Scenario: Admission suppression performs no new input
- **WHEN** quota, pause, hold, session end, command dedupe, cancellation, or deadline suppresses the next command
- **THEN** the key preference SHALL create no timer, retry debt, bypass command, or trusted input
