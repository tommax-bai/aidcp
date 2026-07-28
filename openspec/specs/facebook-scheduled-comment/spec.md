# facebook-scheduled-comment Specification

## Purpose
TBD - created by archiving change facebook-scheduled-comment. Update Purpose after archive.
## Requirements
### Requirement: Facebook comments trigger through existing comment entry points routed by account platform

Facebook automatic comments SHALL be triggered through the existing schedule-driven comment entry point (per-account comment schedule with its daily cap) and the existing Feishu `/comment` command entry point; a separate Facebook-specific cron MUST NOT be added. Both entry points SHALL resolve the account platform through the account store (`accounts.platform`) and route Facebook accounts to the Facebook targeted-comment pipeline. For each account the pipeline SHALL read an operator-configured keyword list, pick a keyword at random, select a concrete group URL from that account's own joined-group membership ledger, and search ONLY within that selected group, then pick a candidate post from the in-container results (bounded extraction). It MUST NOT perform whole-site Facebook search and MUST NOT comment on posts outside the selected joined group. Missing keywords OR missing eligible joined groups produce an honest no-op result.

#### Scenario: Schedule trigger routes by platform
- **WHEN** the content schedule fires a comment action for an account with `accounts.platform='facebook'`
- **THEN** the comment pipeline uses the Facebook platform profile and the targeted pipeline, not the xhs search loop

#### Scenario: No configured keywords or joined groups yields no-op
- **WHEN** a Facebook account is active but has no configured keywords, or no joined group can be selected for the account
- **THEN** the trigger records/returns a no-targets outcome and does not search whole-site or browse random Facebook surfaces

#### Scenario: Search stays within a selected joined group
- **WHEN** the pipeline picks a random keyword for a Facebook account
- **THEN** it searches only inside one concrete group URL selected from that account's joined-group ledger and never performs a whole-site search

### Requirement: Shadow mode runs to validation without posting or recording

Shadow mode SHALL execute target selection, composition, and deterministic validation, but MUST NOT submit the comment, mark cooldown, record risk, dedupe as posted, or report `commented`. Shadow output SHALL be logged/auditable without secrets.

#### Scenario: Shadow candidate does not post
- **WHEN** shadow mode produces a valid candidate comment
- **THEN** the system logs the target/text/validator result safely and does not call the edge submit capability or record risk

### Requirement: Unattended Facebook composition uses hard validators

Facebook scheduled comments SHALL run deterministic validators after LLM composition and before any submit attempt. Validators MUST reject URLs/bare domains, phone/email/WeChat-like contact info, `@mention`, platform-specific length violations, spammy English phrases, empty/low-signal text, and weak target relevance. Rejected text MUST produce `compose_skipped`; the system MUST NOT auto-fix then post.

**Operator `--force` override (change manual-comment-force-flag)**: only when the Feishu manual command carries `--force`, the **relevance** check (`weak_relevance`) SHALL be skipped for that run (implemented by passing an empty relevance context so the relevance branch is a no-op). The `--force` override MUST NOT relax any **content-safety** validator: URLs/bare domains, contact info, `@mention`, length violations, spam phrases, and empty/low-signal text MUST still reject with `compose_skipped`, and the system MUST still not auto-fix then post. `--force` is carried only from the manual command entry point; automatic/scheduled/shadow paths MUST keep enforcing `weak_relevance`.

#### Scenario: URL is rejected
- **WHEN** the composed Facebook comment contains a URL or bare domain
- **THEN** validators reject it with `compose_skipped`, and no submit occurs

#### Scenario: Validator reject is not repaired into post
- **WHEN** a validator rejects the LLM output
- **THEN** the system does not call another fixer that can still post in the same attempt

#### Scenario: `--force` skips relevance but not content-safety
- **WHEN** an operator runs `/comment <acct> --force` for a Facebook account and the composed comment has zero keyword overlap with the target post but contains a URL or contact info
- **THEN** the `weak_relevance` check is skipped, but the comment MUST still be rejected with `compose_skipped` for the URL/contact violation (content-safety validators are not overridden)

#### Scenario: Automatic path still enforces relevance
- **WHEN** the automatic/scheduled Facebook comment path composes a comment with zero relevance overlap (no `--force` present)
- **THEN** validators MUST reject it with `weak_relevance` → `compose_skipped` (the override signal is absent on automatic paths)

### Requirement: Facebook post success requires server-confirmed verification

Facebook comment execution SHALL report success only when it can verify a server-confirmed comment on the intended target post, scoped by own identity and text fragment. Acceptable confirmation includes a comment permalink/id or delayed reload/requery proof that the comment remains on the target post. Editor clearing, local optimistic row insertion, or comment-count changes alone MUST NOT count as success. Ambiguous or missing confirmation returns a non-success reason.

#### Scenario: Optimistic DOM alone is not success
- **WHEN** Facebook locally renders a new comment row immediately after submit but no server-confirmed id/permalink or delayed persistence is verified
- **THEN** edge MUST NOT report `ok:true`; it reports an honest non-success outcome such as `state_unchanged` or `verification_ambiguous`

#### Scenario: Verified server comment reports success
- **WHEN** the submitted comment is confirmed by permalink/id or delayed requery on the target post matching own identity and text
- **THEN** edge reports `ok:true` and cloud may record risk/cooldown

### Requirement: Every Facebook failure point has an honest non-commented outcome

Facebook scheduled commenting SHALL distinguish and surface non-success outcomes including kill switch off, account paused, platform mismatch, no targets, login required, checkpoint/blocked, no strong candidate, validator rejection, quota denied, cooldown denied, submit no target, and verification ambiguous. None of these outcomes may be recorded as `commented`.

#### Scenario: Login required is not no candidate
- **WHEN** a Facebook profile is logged out when a scheduled comment attempt runs
- **THEN** the result is login-required/blocking, not `no_strong_candidate` or `commented`

#### Scenario: Verification ambiguous is not success
- **WHEN** the comment submit cannot be verified after bounded attempts
- **THEN** the result is non-success and no risk/cooldown success record is written

### Requirement: Facebook comment containers are identified to humans by group name, never by id

A Facebook comment container SHALL store a functional key (the group/page URL, which contains the numeric id) AND a human-readable name. The name SHALL be the container's real group/page name, auto-resolved by the edge from the container page (reported back to cloud, which persists it against the matching URL). Every human-facing surface (management console, audit rows, Feishu receipts) SHALL display the group name; when a name has not yet been resolved it SHALL show a neutral placeholder (e.g. "待识别"). Surfaces MUST NOT display the raw group id / URL to humans. When the edge cannot read a name it MUST return no name (honest), and cloud MUST NOT fabricate a name from the id. Legacy bare-URL container configuration MUST be accepted (coerced to a URL with an unresolved name) for backward compatibility.

#### Scenario: Group id is never shown to humans
- **WHEN** an operator views a configured Facebook container in the console (or an audit row / Feishu receipt references it) and the container's real name has been resolved
- **THEN** the surface shows the group name (e.g. "Puerto Rico Y Sus Encantos e Historia") and never the raw group id or URL

#### Scenario: Name auto-resolves from the container page
- **WHEN** a Facebook comment run searches inside a configured container and the edge reads the container's real name from the group page
- **THEN** the edge reports the name with its `page.cards`, and cloud persists it against the matching container URL so subsequent human-facing surfaces show the group name

#### Scenario: Unresolved name shows a placeholder, never the id
- **WHEN** a container has been configured (URL pasted) but its real name has not yet been resolved
- **THEN** human-facing surfaces show a neutral placeholder ("待识别"), not the group id / URL

#### Scenario: Unreadable name is honest, never fabricated
- **WHEN** the edge cannot read a container's real name from the page
- **THEN** it returns no name and cloud leaves the stored name unresolved (never derives a display name from the id)

### Requirement: Facebook comments are composed after reading the target post and its discussion

Facebook generated-comment composition SHALL happen AFTER the target post is opened, using the post's caption (when present) and a bounded sample of other people's comments as context. The generated composer MUST write in the same language as the post/comment content (the local content language), and MUST NOT default to the interface language when it differs. The generated comment SHALL respond to the actual discussion rather than being written blind from a keyword alone. Template-comment mode SHALL still open the target post and read the caption/comment sample before choosing and validating the template body, but it MUST NOT call the generated composer or rewrite the template based on the post content. The edge MUST report the caption and comment samples honestly (empty when a photo post has no caption; never fabricated). The deterministic relevance check SHALL treat the keyword plus the post caption and comments as the relevance context when relevance validation is enabled.

#### Scenario: Generated comment matches the content language, not the UI language
- **WHEN** a target post and its comments are in a non-Chinese language (e.g. Spanish) while the account's Facebook interface language is Chinese
- **THEN** the generated comment is written in the content language (Spanish), not Chinese

#### Scenario: Generated compose reads the post before writing
- **WHEN** an automatic Facebook comment is composed in generated mode
- **THEN** the post is opened and its caption + other-people comments are read first, and the composer receives them as context (it is not written blind from the keyword alone)

#### Scenario: Photo post with no caption still composes from the discussion
- **WHEN** the target is a photo post with no text caption
- **THEN** the edge reports an empty caption (never fabricated) and the generated composer grounds the comment in the other-people comments and persona

#### Scenario: Template mode reads target context but skips composer
- **WHEN** an automatic Facebook comment is prepared in template mode
- **THEN** the post is opened and context is read for validation/review/audit, but the body comes from a configured template rather than LLM generation

### Requirement: Shadow mode is a read-only browse that never submits

Shadow mode SHALL perform the read-only steps needed to compose (search and open the target post to read its caption and comments) and run composition + validators, but MUST NOT submit a comment, record risk/cooldown, dedupe as posted, or report `commented`. It MUST NOT dispatch the comment-submit command.

#### Scenario: Shadow browses read-only but never submits
- **WHEN** shadow mode runs for a Facebook account
- **THEN** it may dispatch search and open (read-only) to read the post, composes and validates a candidate, and audits `shadow_ok` — but never dispatches the comment-submit command and never records success

### Requirement: A pinned just-joined group is a valid comment container with keywords from account config

The Facebook comment pipeline SHALL accept, for a human-authorized manual join-then-comment, a container PINNED to a single just-joined group URL supplied by the caller, in place of choosing from the operator-configured container list or the LRU coverage window. Keywords SHALL still come from the account's Facebook comment configuration; if the account has no configured keywords the pinned path MUST fail closed with an honest no-targets outcome (never whole-site search, never a blind post). The pinned path SHALL update the membership ledger's coverage bookkeeping for that group (mark-commented on verified success; the existing left/inaccessible signal on the relevant failures), exactly as the coverage loop does.

#### Scenario: Pinned container overrides config selection
- **WHEN** a manual join-then-comment supplies just-joined group G as the pinned container
- **THEN** the pipeline searches inside G (not a config-listed or LRU-selected container) and runs the unchanged compose/validate/server-verify path

#### Scenario: Pinned path with no keywords is an honest no-op
- **WHEN** the account has no configured Facebook keywords
- **THEN** the pinned comment step returns an honest no-targets outcome and does not search whole-site or post a blind comment

#### Scenario: Verified pinned comment updates the ledger
- **WHEN** a pinned comment on group G is server-confirmed as posted
- **THEN** the membership row for (account, G) records the coverage timestamp/count, consistent with the background coverage loop

### Requirement: Coverage-mode comment target selection relaxes timing as a review-gated fallback

When the Facebook comment pipeline selects a joined group for an account, it SHALL first attempt to pick a joined group under the normal timing constraints — warmup (minimum join age) AND cooldown (minimum time since last comment) — from a least-recently-commented window, at random. When NO joined group satisfies these timing constraints, the pipeline SHALL, by default, fall back to a RELAXED selection that ignores the warmup and cooldown timing (still restricted to `status='joined'` groups, still ordered least-recently-commented, still random within the window) instead of skipping the account. A relaxed pick MUST be flagged so the human-review approval card visibly marks that the timing window was not met, for the operator to confirm or reject. The relaxed fallback MUST still enforce the per-account daily cap and every other gate — it relaxes ONLY the per-group timing, never the per-account comment volume, and never the always-on human review. The relaxed fallback MUST be reversible via an environment kill switch that restores the strict behavior (no eligible group → honest no-op skip). When the account has zero joined groups at all, the result MUST still be an honest no-op, relaxed or not.

#### Scenario: All joined groups within cooldown fall back to a flagged relaxed pick
- **WHEN** a Facebook account's every joined group is still inside warmup or cooldown, and the relaxed fallback is enabled (default)
- **THEN** the pipeline picks the least-recently-commented joined group anyway and the resulting Feishu human-review card is annotated that the timing constraints were not met, so the operator decides

#### Scenario: Relaxed fallback still respects the daily cap
- **WHEN** an account has already reached its Facebook comment daily cap
- **THEN** no relaxed pick is submitted — the daily cap denies the run exactly as it does for a normal pick (the relaxed fallback never raises per-account volume)

#### Scenario: Kill switch restores strict skip
- **WHEN** the relaxed-fallback kill switch is disabled and no joined group satisfies the timing constraints
- **THEN** the pipeline produces an honest no-targets no-op and does not comment, exactly as before this change

#### Scenario: Zero joined groups is still an honest no-op
- **WHEN** a Facebook account has no joined groups at all
- **THEN** both the normal and the relaxed selection return empty and the pipeline records an honest no-op — it never fabricates a target or blindly posts

### Requirement: Operator search keywords preserve internal whitespace as a single term

An operator-configured Facebook comment search keyword that contains internal whitespace (a multi-word phrase) SHALL be stored and used as ONE keyword/search term end-to-end. The console keyword input MUST NOT split a term on spaces into multiple keywords; only leading/trailing whitespace is trimmed. Comma-separation between distinct keywords SHALL still be supported.

#### Scenario: Multi-word phrase stays one keyword
- **WHEN** an operator enters the search term `手冲 咖啡` in the console keyword field
- **THEN** it is stored and searched as the single keyword `手冲 咖啡`, not as two keywords `手冲` and `咖啡`

#### Scenario: Comma still separates keywords
- **WHEN** an operator enters `手冲 咖啡, 烘焙`
- **THEN** it is stored as two keywords, `手冲 咖啡` and `烘焙`

### Requirement: Facebook account config supports generated or template comment bodies

Each Facebook account's comment configuration SHALL include a comment-body mode. `generated` mode SHALL use the existing Facebook composer after the target post is opened and read. `template` mode SHALL choose from operator-configured account templates and MUST skip LLM comment generation for the body. Both modes SHALL still require configured search keywords, target selection from the account joined-group ledger, deterministic validation, human review when configured/required, edge submit, server-confirmed verification, and honest audit outcomes.

Template mode MUST fail closed when the account has no valid templates; it MUST NOT silently fall back to generated mode. Generated mode MUST NOT require templates. Templates MUST be stored per account, may contain multiple entries, and SHALL be sanitized for empties/duplicates while preserving meaningful internal whitespace.

**A template is a block, not a line.** Operator editors SHALL separate templates by a line containing only `------` (six or more hyphens), so a single template may span multiple lines and keep its own line breaks. The same separator SHALL be used when rendering stored templates back into the editor. Line breaks inside a block are part of that template's body and MUST NOT split it into separate templates. This applies to both the per-account template editor and the region-wide template editor.

#### Scenario: Generated mode uses the composer
- **WHEN** a Facebook account is configured for `generated` mode and a target post is opened
- **THEN** the pipeline calls the Facebook composer with the keyword, group label, post text, and discussion sample before validating and reviewing the produced body

#### Scenario: Template mode skips generation
- **WHEN** a Facebook account is configured for `template` mode and has valid templates
- **THEN** the pipeline selects a template body and does not call the Facebook composer for that comment attempt

#### Scenario: Template mode without templates fails closed
- **WHEN** a Facebook account is configured for `template` mode but has no valid templates
- **THEN** the pipeline records/returns an honest no-op or compose-skipped outcome and MUST NOT fall back to generated comments

#### Scenario: A multi-line block is one template
- **WHEN** an operator enters several lines of text with no `------` separator line
- **THEN** the editor stores exactly one template whose body keeps those line breaks

#### Scenario: Separator lines split templates
- **WHEN** an operator enters two blocks of text separated by a line containing only `------`
- **THEN** the editor stores exactly two templates, and neither body contains the separator line

### Requirement: Template comments use the same safety and contact lanes as generated comments

Template comment bodies SHALL pass the **structural** deterministic validators before any submit attempt: empty, low-signal, minimum length, and maximum length. A rejected template MUST NOT be repaired and posted.

Template bodies SHALL NOT be subject to the **content-policy** validators (URL/bare-domain, contact-info text, `@mention`, spam phrase, relevance). Those validators exist because an unattended generated body has no human author to answer for it; a template's author is the operator, who owns its content. Applying them to operator-written campaign copy rejects legitimate material — real-machine evidence 2026-07-28: a recruitment template carrying its own phone number is rejected as `contains_contact` and never posts. The operator's decision of record (2026-07-28) is that template content is their responsibility and that a template carrying contact details alongside the account contact string is intended, not a conflict.

The maximum-length validator is retained for templates because it is a physical constraint rather than a policy one: the edge types a comment character by character at human cadence inside a bounded platform step budget, so an over-long body ends as a typing-deadline failure instead of a posted comment.

Contact-info comments SHALL keep the template/generated body separate from the account contact string: the body is sent as `text`, and the contact string is injected through the existing contact-info lane after human review.

#### Scenario: Operator template with contact text is accepted
- **WHEN** a template body contains a phone number or other contact text
- **THEN** the body validator does not reject it, and the comment proceeds to the existing review and submit lanes

#### Scenario: Generated body with contact text is still rejected
- **WHEN** an unattended generated (non-template) body contains a phone number, email, WeChat-like contact phrase, bare domain, `@mention`, or spam phrase
- **THEN** the body validator rejects it before submit, exactly as before

#### Scenario: Over-long template is still rejected
- **WHEN** a template body exceeds the platform body length limit
- **THEN** the validator rejects it, because the edge cannot finish typing it inside the platform step budget

#### Scenario: Contact template comment appends account contact info separately
- **WHEN** a contact comment uses template mode and the account has configured contact info
- **THEN** the review card shows the template body plus the account contact string, and edge receives the body as `text` plus the contact string in the existing `groupChatCode`/contact-info field

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

### Requirement: Comment target open waits for detail hydration on the same evidence as the read path

The comment path's open-target step SHALL allow the post detail to hydrate for a bounded window sized on the **same real-machine evidence** as the browse/read path's detail open, and SHALL NOT report open-failure before that window elapses. The comment path has its own open implementation, separate from the read path's; a widening applied to one does not reach the other, so the two windows SHALL be justified by the same observed hydration range and kept in agreement.

Facebook post detail hydrates measurably later than feed (observed 7–12s on real machines). A window narrower than the observed range makes open-failure a function of page speed rather than of the post being unavailable, which drops targets that were successfully found by the preceding search step — and reports them as if no suitable target existed.

The waiting budget for detail hydration SHALL be a **dedicated** budget, not shared with probes that run inside per-round retry loops (search-candidate probing and comment-editor coaxing). Widening a shared probe budget multiplies through those loops and overruns the step deadline, converting an honest open-failure into a timeout without changing the outcome the operator sees.

The cloud's open-step deadline SHALL be large enough to contain the edge's bounded window plus its own slack, so that the **edge answers first** with an honest terminal reason rather than the cloud cutting the step short. The submit step already deviates from the shared step deadline for the same reason.

Bounded-ness and honesty are unchanged: the window remains bounded, and a post whose detail never renders within it is still reported as an honest open-failure — never as success, and never as "no candidate found".

#### Scenario: Slow-hydrating post detail is not reported as open-failure

- **WHEN** the comment path opens a target permalink whose detail article renders within the observed hydration range but later than the previous narrow window
- **THEN** the open step succeeds and the comment proceeds, instead of reporting open-failure

#### Scenario: Never-rendering post detail is still an honest open-failure

- **WHEN** the comment path opens a target permalink whose detail article does not render within the bounded window
- **THEN** the step reports open-failure honestly, and does not report success

#### Scenario: Widened detail budget does not widen in-loop probes

- **WHEN** the detail-hydration budget is widened
- **THEN** the search-candidate probe and the comment-editor coaxing probe keep their original per-round budgets, and the open step's worst-case duration stays within the cloud's open-step deadline

#### Scenario: Edge answers before the cloud deadline

- **WHEN** the edge's open step runs its full bounded window without the detail rendering
- **THEN** the edge's honest open-failure reaches the cloud before the cloud's open-step deadline fires, so the recorded reason is open-failure rather than timeout

### Requirement: Comment target open confirms the requested canonical Facebook post identity

The Facebook comment path SHALL treat `note.open` as successful only when the hydrated detail derives the same canonical Facebook post identity as the requested target. Equivalent supported permalink forms for one post MUST compare equal. A detail for a different post, a profile/feed article, or an identity-less URL MUST NOT advance composition or create an approval request.

Edge SHALL perform this post-navigation validation inside the existing bounded detail-hydration window and discard transient mismatched details while waiting for the requested target. If the requested identity never appears, Edge SHALL return an honest terminal open failure before Cloud's open-step deadline. Cloud SHALL independently correlate returned detail evidence by canonical identity rather than raw URL equality and SHALL ignore evidence for another target.

#### Scenario: Equivalent permalink forms identify the same opened target

- **WHEN** Cloud requests a post through one supported Facebook permalink form and Edge reports the same post through another supported form
- **THEN** both sides derive the same canonical post identity
- **AND** the comment path may advance to composition and configured approval

#### Scenario: Stale article is discarded while requested detail hydrates

- **WHEN** the first detail sampled after navigation belongs to another post and the requested post appears within the bounded hydration window
- **THEN** Edge does not emit the stale detail as successful target evidence
- **AND** it returns the requested post detail once its identity is confirmed

#### Scenario: Requested target never hydrates

- **WHEN** only mismatched or identity-less detail is observable throughout the bounded hydration window
- **THEN** Edge reports an explicit open failure before Cloud's deadline
- **AND** Cloud records a non-submit outcome without composing a comment or creating an approval card

#### Scenario: Cloud rejects mismatched detail evidence

- **WHEN** Cloud receives detail evidence whose canonical Facebook post identity differs from the requested target
- **THEN** it does not accept the open step or advance the task
- **AND** it MUST NOT reinterpret timeout or mismatch as success

### Requirement: Facebook manual comment fast return

When and only when a manual single-comment task carries the explicit `--feed` switch, the Facebook Edge executor SHALL preserve all pre-submit gates and input verification, dispatch Enter to submit the comment, wait 500 milliseconds, skip the in-place acknowledgement/result-detection loop, and navigate directly to the canonical Facebook home page. The post-submit outcome MUST be `verification_ambiguous`/submitted-unconfirmed rather than confirmed success, so Cloud writes anti-retry deduplication without recording a confirmed comment or retrying the target. A Facebook comment without the switch SHALL retain the existing in-place platform-confirmation lifecycle, including confirmed, rejected, pending-approval, and ambiguous terminal distinctions.

**Automatically triggered Facebook comment paths MUST NOT set the fast-return switch.** This covers scheduled comments, rule-mode join-then-contact-comment batches, coverage-mode comments, and hot-lead triggered comments — every path whose trigger is not an operator's explicit `--feed` command. An automatic path that sets the switch is structurally incapable of ever reporting a confirmed comment: it reports submitted-unconfirmed on every run, which then writes de-duplication against the target and burns it while recording no confirmed comment, no coverage cooldown, and no daily-cap consumption. Cloud SHALL therefore pass the switch only from the manual command surface that parsed `--feed`.

#### Scenario: Facebook fast return after Enter dispatch
- **WHEN** a manual `/comment <nickname> --feed` Facebook task passes all gates and Enter is dispatched in the target post editor
- **THEN** Edge waits 500 milliseconds, navigates to the canonical Facebook home page without polling comment acknowledgement state, and reports the write as submitted but unconfirmed

#### Scenario: Facebook default path retains lifecycle evidence
- **WHEN** a Facebook comment task does not carry the explicit manual `--feed` switch
- **THEN** Edge MUST keep the existing in-place acknowledgement loop and preserve its confirmed, rejected, pending-approval, and ambiguous outcomes

#### Scenario: Rule-mode join-then-comment keeps the confirmation lifecycle
- **WHEN** the Facebook rule-mode batch triggers a join-then-contact-comment task without any operator `--feed` switch
- **THEN** Cloud MUST NOT request fast return, and the task's outcome reflects the real in-place lifecycle (confirmed / rejected / pending-approval / ambiguous) rather than a fixed submitted-unconfirmed result

### Requirement: Facebook scheduled comments are authorized by scoped product controls and fail closed

Facebook scheduled commenting SHALL be authorized by the account's enabled comment schedule, approval mode, platform match and active account state. A plain operator `/comment <昵称>` command is explicit manual intent and SHALL enter the same targeted-comment pipeline independent of the account schedule window. Neither path SHALL require a process-global automatic or shadow environment variable.

Every path MUST still enforce persona, joined-group ownership, deterministic content validators, structured approval policy, active identity/capability, per-account risk quota and daily cap, single-flight, idempotency and server-confirmed verification. Missing or disabled scoped configuration on an unattended schedule MUST produce an honest no-op and MUST NOT claim work occurred.

#### Scenario: Disabled account schedule prevents unattended posting
- **WHEN** a Facebook account's scheduled comment action is disabled or the account is paused
- **THEN** no unattended Facebook comment is posted or risk-recorded even if stale auto/shadow environment variables are present

#### Scenario: Enabled schedule needs no global switch
- **WHEN** a Facebook account has an enabled current comment schedule and satisfies all approval, target, identity, risk and quota gates
- **THEN** the scheduled targeted-comment pipeline runs without requiring `AIDCP_FB_COMMENT_AUTO`

#### Scenario: Manual command is not silently no-op'd by deployment state
- **WHEN** an operator issues a valid plain `/comment <昵称>` command for an active Facebook account
- **THEN** the targeted-comment pipeline returns an honest terminal outcome without consulting a global auto/shadow environment switch

