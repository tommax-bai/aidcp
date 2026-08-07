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

The Facebook comment pipeline SHALL accept a container PINNED to a single just-joined group URL supplied by the caller, in place of choosing from the operator-configured container list or the LRU coverage window. Targeting mode SHALL still come from the account's Facebook comment configuration: non-empty keywords use container-scoped search inside the pinned group; no keywords use the pinned group's first eligible post without search. The pinned path MUST never use whole-site search or a blind DOM-order post. It SHALL update the membership ledger's coverage bookkeeping for that group (mark-commented on verified success; the existing left/inaccessible signal on the relevant failures), exactly as the coverage loop does.

#### Scenario: Pinned container overrides config selection
- **WHEN** a join-then-comment run supplies just-joined group G as the pinned container and the account has configured keywords
- **THEN** the pipeline searches inside G (not a config-listed or LRU-selected container) and runs the unchanged compose/validate/server-verify path

#### Scenario: Pinned path with no keywords uses the first eligible post
- **WHEN** the account has no configured Facebook keywords and a join-then-comment run pins group G
- **THEN** the pipeline performs no search, opens G's first eligible group post, and runs the unchanged compose/validate/approval/server-verify path

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

Each Facebook account's comment configuration SHALL support an explicit comment-body mode and SHALL persist whether that mode was explicitly configured independently of the mode value and template array. Explicit `generated` mode SHALL use the existing Facebook composer after the target post is opened and read. Explicit `template` mode SHALL first use valid operator-configured account templates; when the account template set is empty, it SHALL resolve the selected target group's region and use that region's configured common templates. When the account has no explicit comment-body configuration, the effective mode SHALL default to `template` and use the same regional-template resolution. Explicit `generated` MUST remain authoritative and MUST NOT be replaced merely because account templates are empty. The explicit-mode fact SHALL survive the existing Cloud internal sync-read path.

Both modes SHALL use target selection from the account joined-group ledger or a caller-pinned just-joined group, deterministic validation, configured approval, edge submit, server-confirmed verification, and honest audit outcomes. Search keywords are optional and select the targeting path; they MUST NOT determine whether generated mode is enabled or whether the scheduled comment path may run. Regional fallback MUST fail closed when the target has no region or the region has no valid templates; it MUST NOT fall back to generated comments, another region, or arbitrary text. Account and regional templates SHALL be sanitized for empties/duplicates while preserving meaningful internal whitespace. Generated mode MUST NOT require templates or keywords.

#### Scenario: Generated mode with keywords uses the composer after search
- **WHEN** a Facebook account is configured for `generated` mode with at least one keyword and a target post is opened from search
- **THEN** the pipeline calls the Facebook composer with the keyword, group label, post text, and discussion sample before validating and reviewing the produced body

#### Scenario: Generated mode without keywords uses target context without an empty keyword instruction
- **WHEN** a Facebook account is configured for `generated` mode with no keywords and the first eligible group post is opened
- **THEN** the composer is grounded in the post text and discussion sample and does not receive a fabricated or empty keyword requirement
- **AND** deterministic URL/contact/mention/spam/length/signal validation plus the configured approval policy remain active without fabricating a lexical keyword anchor

#### Scenario: Template mode skips generation
- **WHEN** a Facebook account is configured for `template` mode and has valid templates
- **THEN** the pipeline selects a template body and does not call the Facebook composer for that comment attempt

#### Scenario: Template mode without account templates uses target region
- **WHEN** a Facebook account's effective mode is `template`, its account templates are empty, and the selected target group has valid common templates for its region
- **THEN** the pipeline selects a common template for that target region and does not call the Facebook composer

#### Scenario: Missing explicit mode defaults to regional template
- **WHEN** a Facebook account has no explicit body mode and the selected target group has valid common templates for its region
- **THEN** the effective mode is `template` and the pipeline selects a regional common template

#### Scenario: Missing regional template fails closed
- **WHEN** the effective mode is `template`, account templates are empty, and the selected target has no region or no valid common templates for its region
- **THEN** the pipeline records/returns an honest non-submit outcome and MUST NOT fall back to generated comments

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

系统 MUST 给该路径下发给边端的**每一条评论命令**（`facebook.search.execute` / `facebook.note.open` / `facebook.note.comment`）透传该租约的 `taskId`。这是硬性要求而非可选：边端 FB 命令入口按 `canExecute(payload.taskId)` 无差别门控——持租约期内**无 taskId 的命令一律被挡**，故评论自身的命令若不带匹配 taskId 会被自己持有的租约一起挡死（自锁死锁）。透传后：本任务的评论命令（taskId 匹配）放行、并发自治浏览闭环的无标识命令（`facebook.feed.scroll` / 返回等）被挡 → 页面钉死在目标帖。

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

The Facebook comment path SHALL treat `facebook.note.open` as successful only when the hydrated detail derives the same canonical Facebook post identity as the requested target. Equivalent supported permalink forms for one post MUST compare equal. A detail for a different post, a profile/feed article, or an identity-less URL MUST NOT advance composition or create an approval request.

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

### Requirement: First-post scroll continuation is measured and actuated on the element that actually scrolls

The bounded first-post scroll search SHALL move and measure the same scrolling element that the list probe already resolves. When the document itself does not scroll — the document scroll height equals the viewport height and the window scroll position stays at zero while an ancestor container of the feed holds the real scrollbar — the probe MUST NOT report window or document coordinates as its displacement and bottom evidence.

Exhaustion ("did not move and is at the bottom") SHALL be decided from that element's own metrics. The specified scroll budget MUST be spendable in full on such layouts; a layout that never scrolls the document MUST NOT cause the loop to exit after its first round.

The scroll budget SHALL also be spendable in full across **posture-class** probe failures. A probe failure that
describes the page's surroundings rather than the identity of a target — not landed yet, not hydrated yet, region
not resolvable, address decoration — SHALL consume one round and continue probing while rounds remain. Only
**identity-class** failures — candidate binding conflict, evidence changed under a resolved candidate — SHALL
terminate the loop immediately, because continuing past them risks acting on a different post. The two classes
MUST be distinguishable in the returned reason; a single undifferentiated "probe failed" value MUST NOT be used
to decide loop termination.

#### Scenario: Group layout scrolls an inner container, not the document
- **WHEN** the first-post probe scrolls a group discussion stream whose real scrollbar is on an ancestor of the feed
- **THEN** the probe actuates that container and reports its displacement and bottom state
- **AND** the bounded scroll loop continues while that container still moves or is not at its bottom

#### Scenario: Posture-class probe failure consumes one round and continues
- **WHEN** a probe round fails for a posture-class reason and scroll rounds remain
- **THEN** the loop consumes one round and probes again, instead of returning the failure immediately

#### Scenario: Identity-class probe failure terminates immediately
- **WHEN** a probe round fails because a resolved candidate's binding conflicts or its evidence changed
- **THEN** the loop terminates at once without spending further rounds, and the failure is reported under its own identity-class reason

#### Scenario: Ordinary window-scrolling layout is unchanged
- **WHEN** the document itself scrolls
- **THEN** displacement and bottom evidence come from the window as before
- **AND** the observable behaviour of the bounded scroll loop does not change

#### Scenario: Exhaustion is still reported honestly
- **WHEN** the resolved scrolling element neither moves nor has further content after the bounded rounds
- **THEN** the probe reports exhaustion
- **AND** it does not report a candidate it did not find

### Requirement: The first-post open budget chain is coherent from inner window to Cloud step

The first-post comment path SHALL size its identity readback window, its comment editor binding window, the enclosing Native command ceiling, and the Cloud first-post open step so that an inner window can be reached before any enclosing deadline fires.

Edge SHALL answer first: Cloud's step ceiling is a backstop only. Cloud MUST NOT fire before Edge's own ceiling plus transport slack, because doing so relabels an honest Edge outcome as a timeout and destroys the diagnosis without saving any comment.

The keyword-search open step keeps its existing ceiling; only the empty-keyword first-post step is widened. Group-join budgets are out of scope and MUST NOT be raised by this requirement.

#### Scenario: Slow but successful hydration completes inside the widened windows
- **WHEN** a group page hydrates the selected post's identity slower than the previous window allowed but within the widened one
- **THEN** Edge completes the identity readback and proceeds to compose and approve
- **AND** no enclosing deadline pre-empts it

#### Scenario: Enclosing ceiling never pre-empts an inner window
- **WHEN** the first-post path runs its worst-case sequence of navigation, bounded scrolling, editor binding and identity readback
- **THEN** the Native command ceiling for that command exceeds the sum of those windows
- **AND** the Cloud first-post step ceiling exceeds the Native ceiling plus transport slack

#### Scenario: Genuine failure is still reported honestly and promptly
- **WHEN** the selected post's identity or editor cannot be confirmed within the widened windows
- **THEN** Edge reports its own specific non-submit reason
- **AND** Cloud records that reason rather than a timeout

#### Scenario: Keyword search targeting is not widened
- **WHEN** a comment run supplies a search keyword
- **THEN** its open step keeps the previously established ceiling
- **AND** the widened first-post ceilings do not apply to it

### Requirement: A command's time ceiling is defined in several places at once and MUST be changed as one unit

The time ceiling for a single Native page command is not one number. It is spread across the request value, the edge admission check, the session timeout, the engine ceiling, and the engine's own protocol admission check — across two languages and two repositories. Changing a Facebook command's time budget SHALL change every one of those layers together.

Each omission has a different and non-obvious failure shape, and none of them is a compile or type error:

- Omitting the admission check makes the command **rejected before dispatch**; the page is never touched, while the operator-visible outcome describes the page instead.
- Omitting the session timeout makes the engine **silently clamp** the ceiling back to the old value, with no error and no log line.
- Omitting the engine's protocol admission makes **session open** fail, taking the whole platform offline rather than one command.

A machine-checked guard SHALL assert these relations so that a partial change fails a test rather than reaching a real account. The guard MUST cover: request ≤ admission, request ≤ engine ceiling, session timeout ≥ every command ceiling it can clamp, and session timeout ≤ every admission check it must pass.

Any budget carved out of a command's deadline for a later stage SHALL be large enough to contain that stage's own bounded waits plus room to deliver the receipt. A reserve exactly equal to the sum of its contents leaves no room to report the outcome.

#### Scenario: A budget is raised in only one layer
- **WHEN** a Facebook command's time budget is raised in the request value but not in the admission check
- **THEN** the guard fails
- **AND** the change does not reach a real account

#### Scenario: Session timeout would clamp a raised ceiling
- **WHEN** a command ceiling is raised above the session timeout
- **THEN** the guard fails, naming the clamp
- **AND** the raise is not silently ineffective

#### Scenario: Session timeout would be rejected at admission
- **WHEN** the session timeout exceeds an admission check it must pass
- **THEN** the guard fails
- **AND** the platform does not go fully offline at session open

#### Scenario: Pacing is not tolerance
- **WHEN** time budgets are scaled to tolerate slower pages
- **THEN** humanized keystroke and pointer pacing, polling intervals, and rate-limit floors are left unchanged
- **AND** only the windows that decide "waited too long, call it a failure" are scaled

### Requirement: Facebook keyword configuration selects search or first-post targeting

For every Facebook group-comment run, configured search keywords SHALL be a targeting-mode selector rather than an enablement prerequisite. When the account has one or more non-empty keywords, the pipeline MUST choose one configured keyword and use the existing container-scoped search path. When the account has no keywords, the pipeline MUST NOT dispatch `facebook.search.execute`; it SHALL open the target group discussion stream and select the first hydrated top-level post that exposes both a canonical group-post permalink and a post-level comment affordance.

The two paths MUST NOT silently fall back to each other. A configured-keyword search with no result remains an honest search-path no-target outcome. An empty-keyword first-post selection with no eligible post remains an honest first-post no-target outcome. The first-post path MUST NOT skip to another post because the first eligible post is already in the account's comment dedupe ledger.

#### Scenario: Configured keyword keeps the search path
- **WHEN** a Facebook comment run has at least one configured non-empty keyword
- **THEN** Cloud dispatches the existing container-scoped search before opening the selected permalink
- **AND** it does not inspect the group feed as a first-post fallback

#### Scenario: Empty keywords open the first eligible group post without search
- **WHEN** a Facebook comment run has no configured keywords
- **THEN** Cloud dispatches no `facebook.search.execute`, and Edge selects and opens the first hydrated top-level group post with a stable permalink and post-level comment affordance

#### Scenario: Obfuscated timestamp href uses Facebook's explicit canonical story URL
- **WHEN** a hydrated top-level group post has a post-level comment affordance but its rendered timestamp `href` is only the group root plus an opaque fragment
- **AND** Facebook's React link/story data for that same rendered anchor explicitly contains a canonical group-post permalink
- **THEN** Edge MAY use that explicit canonical permalink for the candidate
- **AND** it MUST NOT infer or synthesize a post ID from the opaque fragment, text, or feed order

#### Scenario: First post already deduped does not advance to the second post
- **WHEN** empty-keyword mode selects the first eligible post and the account has already commented on that permalink
- **THEN** the run ends with an honest dedupe/no-strong-candidate outcome
- **AND** it does not substitute a later post or keyword search

### Requirement: First-post selection is a bounded read-open operation

Cloud SHALL request first-post selection through the existing `facebook.note.open` protocol message with a Facebook-only selection discriminator, the target group container, and the current task lease ID. Edge SHALL establish the canonical group discussion root before selecting the first post. Edge SHALL skip the root navigation when one fresh probe on the current CDP target proves that the page is the exact target-group root, the document and group scope are ready and unblocked, the feed is not loading, no modal obscures the surface, and the actual feed scroller is at its origin. Missing, malformed, failed, or mismatched reuse evidence SHALL fall back to one navigation to the canonical group root, except that an observed cancellation or task takeover SHALL terminate without navigation. Edge SHALL then select one eligible permalink or session-bound target, open or bind it as required, and emit the existing `note.detail` shape with the selected target as `noteId`. This operation MUST NOT emit a search activity receipt or be counted/reported as keyword search.

Before accepting a first-post candidate, Edge MUST prove in that candidate probe that the candidate still comes from the exact requested canonical group root, including origin, path, empty query/hash, surface, and group scope. A context change after an in-place reuse SHALL trigger the one canonical root navigation and a fresh candidate probe using only the command's remaining fixed scroll-round budget. A context mismatch after that navigation MUST end honestly without another navigation loop. Once Edge accepts a candidate, existing permalink or session-bound target binding rules remain authoritative and Edge MUST NOT navigate back to the group root to substitute another post.

When the container is invalid, the group feed cannot be opened, the page is blocked, no eligible post hydrates within the bounded window, or the selected target cannot be opened and bound, Edge SHALL return an honest `open_note` failure and MUST NOT emit a fabricated detail.

#### Scenario: Exact ready group root is reused
- **WHEN** the current CDP target is the exact requested group root, its document and unique group scope are ready and unblocked, its feed is settled, and its actual feed scroller is at the origin
- **THEN** Edge skips the canonical group-root navigation
- **AND** Edge freshly probes and binds the first eligible post on that current target

#### Scenario: Uncertain current page falls back to canonical navigation
- **WHEN** any current-page reuse field is missing, malformed, failed, or does not prove an exact reusable target-group root
- **THEN** Edge navigates to the canonical group root exactly once before first-post selection
- **AND** the reuse uncertainty itself is not reported as a completed or failed Facebook action

#### Scenario: Cancellation does not become a navigation fallback
- **WHEN** cancellation or task takeover is observed before or after the reuse probe
- **THEN** Edge terminates the command without navigating the current page

#### Scenario: Reused page changes context before candidate acceptance
- **WHEN** the initial group root was reused but the first-post candidate probe no longer proves the exact requested canonical group root
- **THEN** Edge performs the one canonical group-root navigation and continues with only the command's remaining fixed scroll-round budget
- **AND** if the context still mismatches after navigation, Edge returns `target_context_mismatch` without accepting a candidate, commenting, or navigating again

#### Scenario: First-post read returns the selected permalink as detail identity
- **WHEN** the first eligible group post is successfully selected and opened
- **THEN** Edge emits `note.detail` whose `noteId` is that post's canonical navigable permalink and whose content belongs to the same post

#### Scenario: Cloud accepts an equivalent multi-permalink identity
- **WHEN** Edge returns `https://www.facebook.com/groups/<group>?multi_permalinks=<post>` for the selected first post
- **THEN** Cloud accepts it as a canonical group-post permalink when `<post>` derives a stable Facebook post identity
- **AND** Cloud continues to reject non-group posts, empty identities, and unknown URL shapes

#### Scenario: No eligible feed post is an honest non-submit
- **WHEN** no top-level post with a stable group-post permalink or safely bound session target and comment affordance hydrates within the bounded selection window
- **THEN** Edge returns an explicit open failure and Cloud does not compose, approve, or submit a comment

#### Scenario: First post starts below the initial viewport
- **WHEN** the canonical target group is open but its first feed cards begin below the cover/composer and outside the initial viewport
- **THEN** Edge performs a fixed bounded sequence of same-container downward scroll-and-probe rounds
- **AND** it opens the first eligible hydrated card without navigating home, searching, changing groups, or substituting a later targeting mode

#### Scenario: Native decoding preserves first-post intent
- **WHEN** Cloud sends `facebook.note.open` with `selection=first_commentable_group_post` and a canonical group container
- **THEN** every active Edge command-mapping and decoding layer preserves both fields and routes the bounded first-post operation
- **AND** the request MUST NOT degrade into a generic current-page `facebook.note.open`

#### Scenario: First-post failures remain distinguishable
- **WHEN** first-post opening ends because no candidate hydrated, the selected post has no uniquely bound comment editor, target context mismatches, or Cloud times out waiting for detail
- **THEN** the result and user-facing receipt preserve the corresponding reason
- **AND** Cloud MUST NOT report all of those outcomes as “群内未找到合适的可评论帖子”

### Requirement: First-post scroll settles before candidate probing

For `selection=first_commentable_group_post`, Edge SHALL retain the existing smooth-scroll completion wait and then wait an additional fixed 2 seconds after each bounded same-container downward scroll before probing rendered feed cards for that round. The candidate snapshot returned from the scroll operation MUST be collected after this additional settle interval, not before it.

The initial pre-scroll probe, maximum scroll-round count, exact-group binding, canonical-permalink and comment-affordance eligibility, stop conditions, and honest failure behavior SHALL remain unchanged. The additional wait MUST NOT apply to keyword-search targeting or create a fallback to search.

#### Scenario: Slow first post hydrates during the post-scroll settle

- **WHEN** the first bounded scroll completes and a commentable group post hydrates during the following 2-second settle interval
- **THEN** Edge probes after the settle and can select that hydrated post in the same scroll round
- **AND** it does not dispatch the next scroll before that probe

#### Scenario: Every exhausted scroll round remains bounded

- **WHEN** no eligible post appears after the additional settle in a scroll round
- **THEN** Edge may continue only within the existing fixed maximum scroll-round count
- **AND** it still returns an honest non-success when no eligible candidate appears

#### Scenario: Keyword search is unaffected

- **WHEN** a Facebook group-comment run has configured search keywords
- **THEN** it uses the existing search targeting path without the first-post post-scroll settle

### Requirement: Permalinkless first-post targets remain bound to one live group-post container

For empty-keyword Facebook group comments, Edge SHALL continue to prefer the first eligible post that exposes a canonical same-group permalink. When the first eligible hydrated group-feed post has a uniquely associated comment editor but exposes no canonical permalink, Edge SHALL bind that rendered post container, read its context in place, and return a strict Edge-issued first-post target reference instead of reporting `no_candidates`.

The target reference MUST be deterministic from normalized same-container evidence, MUST NOT be represented as a Facebook permalink or post ID, and MUST NOT be derived from an opaque fragment alone. Context extraction, approval identity, editor focus/fill, pre-commit target recheck, submit, and post-submit acknowledgement SHALL all use the same reference. The reference is valid for actuation only while its original page-local binding and keep-open task lease remain intact.

Canonical-permalink and in-place targets MUST NOT silently fall back to each other after selection. The first-post path MUST NOT switch to keyword search, reselect by document order before submit, or advance to a later post because the selected target is deduped or its binding is lost.

When a uniquely associated comment action must be activated before the editor exists, the page router SHALL return a fresh point target and MUST NOT call DOM `click()` as actuation. Native SHALL dispatch real CDP mouse move/press/release events at most once, then require exactly one eligible editor under the same selected target. Dispatch completion without that editor post-state is not success.

#### Scenario: Visible commentable first post has no canonical permalink
- **WHEN** the group discussion stream hydrates a first eligible post with uniquely bound context and comment editor
- **AND** every rendered story/timestamp link lacks a canonical group-post permalink
- **THEN** Edge returns `note.detail` for that same container with a strict first-post target reference
- **AND** Cloud may compose and approve against that reference without dispatching search or navigating to a fabricated post URL

#### Scenario: Canonical permalink remains the preferred target
- **WHEN** the first eligible group post exposes a canonical same-group permalink
- **THEN** Edge uses the existing permalink detail path
- **AND** it does not replace that canonical identity with an in-place target reference

#### Scenario: Opaque group-root fragment is not promoted to a post identity
- **WHEN** a rendered timestamp link is the group root plus an opaque fragment
- **THEN** Edge does not accept that link as a permalink and does not infer a Facebook post ID from the fragment, text, author, media URL, or feed order
- **AND** any fallback identity remains explicitly typed as an internal first-post target reference

#### Scenario: Context and editor resolve to the same live container
- **WHEN** Cloud returns the approved comment with the Edge-issued first-post target reference
- **THEN** Edge resolves the originally bound container, verifies its normalized evidence is unchanged, and requires exactly one eligible editor inside that boundary before typing
- **AND** it never uses an editor from another post or the document root

#### Scenario: Comment editor requires a trusted pointer activation
- **WHEN** the selected first post has exactly one eligible comment action but no hydrated editor
- **THEN** Edge returns that action's fresh coordinates without invoking DOM `click()`
- **AND** Native dispatches `mouseMoved`, `mousePressed`, and `mouseReleased` through CDP
- **AND** the workflow proceeds only after the same target exposes exactly one eligible editor

#### Scenario: Real click does not hydrate the selected editor
- **WHEN** Native dispatches the bounded pointer activation but the same target does not expose a unique eligible editor
- **THEN** Edge reports an honest non-submit outcome
- **AND** it does not repeat the click, invoke DOM `click()`, or select another post

#### Scenario: Bound container is replaced during approval
- **WHEN** Facebook detaches, recycles, or materially changes the bound post container before submit
- **THEN** Edge reports an honest target-moved or context-mismatch non-submit outcome
- **AND** it does not re-run first-post selection or comment on the new first rendered post

#### Scenario: Duplicate container evidence is ambiguous
- **WHEN** more than one rendered post container produces the same fallback reference or the selected boundary contains multiple peer comment editors
- **THEN** Edge reports an ambiguous target and submits nothing

#### Scenario: In-place acknowledgement remains scoped to the bound post
- **WHEN** Enter is dispatched through an in-place first-post target
- **THEN** server acknowledgement is evaluated only within the bound container using the existing own-account and persistence evidence
- **AND** an optimistic row, editor clearing, or a comment visible under another post does not confirm success

#### Scenario: Cloud rejects opaque references outside first-post selection
- **WHEN** a search candidate, ordinary `openPost`, or unrelated platform flow supplies a non-canonical target reference
- **THEN** Cloud rejects it as an invalid target
- **AND** only the result of the active `first_commentable_group_post` request may introduce the strict first-post reference form

#### Scenario: Deterministic fallback reference preserves dedup
- **WHEN** the same unchanged permalinkless group post is selected on a later run
- **THEN** Edge derives the same first-post target reference from its normalized same-container evidence
- **AND** the existing comment dedup ledger may prevent a repeated comment without pretending the reference is a Facebook post ID

### Requirement: Facebook targeted comments use visible safety quotas without a hidden feature cap

Every automatic Facebook targeted-comment entry point SHALL pass the account's current `RiskController` state and minute/hour/day comment quota. The targeted-comment pipeline MUST NOT apply `AIDCP_FB_COMMENT_DAILY_CAP` or any equivalent hidden feature-local daily veto.

Visible content-schedule enablement and schedule-level planning limits SHALL retain their existing admission role at the schedule entry point. They MUST NOT be reconstructed from `risk_interactions` inside the targeted-comment pipeline. Manual `/comment` override behavior SHALL remain unchanged.

#### Scenario: Automatic targeted comment follows the visible safety policy

- **WHEN** an automatic Facebook targeted comment reaches the write pipeline and the account `RiskController` allows `comment`
- **THEN** the pipeline continues to its existing session, approval, de-duplication, target and submission gates
- **AND** no hidden environment daily cap may stop it

#### Scenario: Safety quota rejects before submission

- **WHEN** the account `RiskController` rejects an automatic Facebook comment for a minute, hour or day quota
- **THEN** Cloud MUST NOT submit the comment and SHALL report the named quota reason without promoting it to success

#### Scenario: Manual override remains explicit

- **WHEN** an authorized operator invokes manual `/comment` through the existing override entry point
- **THEN** the existing manual override semantics remain unchanged
- **AND** removing the hidden Facebook cap MUST NOT add a new manual restriction or bypass a non-quota safety gate that the manual contract retains

### Requirement: First-post group-root navigation confirms landing before any probe runs

The first-post comment path SHALL NOT begin probing for a candidate post until it has confirmed that the browser
actually landed on the requested group root. Document readiness alone MUST NOT be accepted as landing evidence:
a navigation that has been dispatched but not yet applied leaves the **previous** document in a ready state,
which satisfies a readiness-only wait instantly and lets every downstream check run against the wrong page.

Landing confirmation SHALL require both document readiness and the current address resolving to the requested
group root, within a bounded window. Failing to confirm landing within that window is a **posture-class** failure:
it SHALL spend one unit of the corrective budget and re-probe, and MUST NOT be reported as a post-identity failure
and MUST NOT terminate the step on its own.

This requirement is the direct guard against acting on a stale page. Any page-posture conjunct that exists only
because landing was never awaited SHALL be justified against this requirement before it is relaxed.

#### Scenario: Stale ready document is not accepted as landing

- **WHEN** navigation to the group root is dispatched while the previous page is still displayed and already reports a ready document
- **THEN** the path does not begin probing, and continues waiting until the address resolves to the requested group root or the bounded window elapses

#### Scenario: Landing timeout is posture-class, not identity-class

- **WHEN** the bounded landing window elapses without the address resolving to the requested group root
- **THEN** the failure spends one unit of the corrective budget and the path re-probes
- **AND** the reported reason distinguishes "did not land on the requested group root" from "post identity could not be confirmed"

#### Scenario: Normal landing is unchanged

- **WHEN** navigation applies and the address resolves to the requested group root within the window
- **THEN** probing begins exactly as before, with no additional delay beyond the confirmation itself

### Requirement: The first-post corrective navigation budget is spent only by failures

The first-post path's corrective re-navigation budget SHALL be a distinct quantity from the record of whether the
preparation phase already navigated. Preparation-phase navigation — the initial jump performed because the starting
page was not already the clean group root — MUST NOT decrement the corrective budget.

Collapsing the two makes the corrective branch statically unreachable in the common case: after joining a group the
starting page is essentially never the clean group root, so preparation always navigates, so a corrective branch
gated on "has not navigated yet" can never fire. The failure mode is silent — no error, no log, simply a recovery
path that never runs.

The corrective budget SHALL start at its full value regardless of what preparation did, SHALL be decremented only
when a probe actually fails, and SHALL be reported as exhausted ("retried N times") rather than as an inability
when it runs out.

#### Scenario: Preparation navigation leaves the corrective budget intact

- **WHEN** the starting page is not the clean group root, so the preparation phase navigates once, and the subsequent probe fails with a posture-class reason
- **THEN** the corrective re-navigation still runs, because the preparation jump did not consume the corrective budget

#### Scenario: Corrective budget is consumed only by failures

- **WHEN** repeated probe failures consume the corrective budget in full
- **THEN** the step terminates with a reason expressed as "retried N times without success", not as "cannot be done"

#### Scenario: Already-correct starting page is unchanged

- **WHEN** the starting page is already the clean group root and preparation performs no navigation
- **THEN** the corrective budget is the same value it would have been had preparation navigated

### Requirement: The requested group address is validated after stripping URL decoration

Validation of the group address supplied by Cloud SHALL strip query string and fragment before comparing, and
SHALL judge the address invalid only when it is not a group-address form at all. A tracking parameter carried on
an otherwise valid group link MUST NOT fail the step.

When the supplied address genuinely is not a group address, the reported reason SHALL name that condition. It
MUST NOT reuse the post-identity reason value: reporting an input-format problem as a page-identity problem sends
the operator to look at the wrong thing, and hides a defect that is trivially fixable at the caller.

#### Scenario: Decorated group link is accepted

- **WHEN** Cloud supplies a valid group address carrying a query string or fragment
- **THEN** validation strips the decoration, accepts the address, and the step proceeds

#### Scenario: Non-group address is rejected under its own reason

- **WHEN** the supplied address is not a group-address form
- **THEN** the step fails with a reason naming an invalid requested group address, distinct from the post-identity reason

