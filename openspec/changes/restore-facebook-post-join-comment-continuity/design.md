# Design

## 1. Incident of record

Edge log, 2026-07-28 (UTC), environment `ads-k1f44fo4`; control `ads-k1enonmg` on the same machine and build.

```
11:23:45.518  group.join dispatched            (observe leg)
11:24:00.828  join_group ok=false observation_only        15.310 s
11:24:00.884  group.join dispatched            (click leg)
11:24:10.786  join_group ok=true  confirmed                9.902 s
11:24:10.832  task acquired kind=comment_prepare
11:24:10.849  note.open dispatched             (first commentable group post)
11:24:24.675  open_note ok=false not_started target_context_mismatch   13.826 s
11:24:25.599  page.scroll suppressed by task lease — no receipt to Cloud
11:24:35.265  scroll ok=false feed_continuation_unconfirmed
11:24:39.932  scroll ok=false feed_continuation_unconfirmed
11:24:51.788  scroll ok=false no_target
   (60 s with no command and no terminal state)
11:25:51      cold standby restart
```

Control, same minute: join confirmed in 4.677 s, first post opened in 5.182 s, comment submitted.

`feed_continuation_unconfirmed` is only producible when the probed surface is the home feed, which independently confirms the browser had been sent home.

## 2. Why the join budgets are not the problem

| Budget | Value | Observed | Headroom |
| --- | --- | --- | --- |
| Join readiness poll | 30 s | 15.310 s | 49% unused |
| Join post-click confirm | 45 s | ≈5 s | 89% unused |
| Join command ceiling | 90 s | 15.3 / 9.9 s | large |
| Cloud join step | 120 s | same | large |

The two legs are by design (observe, then a Cloud pre-click judgement of 40 ms, then click); `observation_only` is the observe leg's normal terminal value, not a failure. Of the click leg's 9.902 s, 3.5 s is fixed humanisation dwell. The remaining time is Facebook's own render latency: the same readiness poll took 2.640 s for the control account and 15.310 s here, a 6× page-speed difference measured before the first-post command was even issued.

Raising any join budget therefore buys nothing. It is out of scope.

## 3. The two first-post defects

### 3.1 Scroll budget collapses to one round

Some group layouts do not scroll the document: the document's scroll height equals the viewport height and window scroll position stays at zero while the real scroll container is an ancestor `div` of the feed. Change `facebook-first-post-comment-confirmation` task 2.7 fixed the **list probe** to measure the element that actually scrolls. The **first-post probe** scrolls through the dispatch branch, which still calls `window.scrollBy` and reads window/document coordinates for its movement report.

Consequence on those layouts: reported displacement is always zero and "at bottom" is always true. Native's exhaustion test is "at bottom and did not move", which is then satisfied from the first round, so the four-round budget stops after one. The specified behaviour — scroll down looking for the first commentable post — effectively does not happen.

Fix: the first-post scroll branch actuates and measures on the same element the list probe already resolves. One shared helper, two call sites, no new policy.

### 3.2 Identity and editor budgets are the failure boundary

Every first-post failure in the last two days: 9.84 / 10.74 / 11.73 / 11.80 / 12.48 / 12.72 / 12.88 / 13.70 / **13.83** / 15.76 s. Every success: ≤7 s. The boundary sits near 9 s and holds across five environments, three days and four distinct terminal reasons. The failing sample is at the centre of the failure cluster and the control at the centre of the success cluster.

Note that three distinct code paths emit `target_context_mismatch`: candidate rejected at binding, editor window expiring while a mismatch flag is set, and identity readback expiring. The log cannot discriminate them, but all three require the post container to have been **found** — "no post rendered" has its own separate reason. So the failure is "found the post, could not confirm its identity or its editor in the time allowed", not "the page never rendered".

Budgets, before and after:

| Window | Before | After | Rationale |
| --- | --- | --- | --- |
| First-post identity readback | 8 s | **20 s** | The ordinary detail read path allows 15 s for the same work; observed hydration reaches 15.8 s. Operator decision: 20 s. |
| First-post editor binding | 4 s | **12 s** | The window starts at "document interactive", which precedes content hydration on these pages. Operator decision: 12 s. |
| Native command ceiling (first-post open) | 30 s (default) | **90 s** | See §4. |
| Cloud first-post open step | 45 s (shared) | **105 s** (new, first-post only) | Edge ceiling plus transport slack, per the existing formula. |
| Cloud keyword open step | 45 s | 45 s | Unchanged; its budgets did not change. |

## 4. The budget chain must move together

Widening only the inner windows changes nothing: the enclosing ceiling fires first and reports a less informative outcome. Worst-case first-post path after this change:

```
group navigation + document ready        8 s
first probe                            ≈ 2 s
4 scroll rounds × ≈3 s                  12 s
optional permalink navigation + ready    8 s
editor binding                          12 s
identity readback                       20 s
                                       ------
                                       ≈62 s
```

So the Native ceiling for this command becomes 90 s — the same value the join command already uses, which keeps the set of ceilings small. Cloud's step ceiling keeps its documented shape (edge ceiling + transport slack) at 105 s. Both remain far inside the comment keep-open lease (6 min) and inside the session idle watchdog (~240 s), and the 200 s figure seen in logs is lease **acquisition** queueing, unrelated to command duration.

Cloud's ceiling stays a backstop, never the first to fire: Edge self-times and answers honestly, and Cloud firing first would only relabel an honest failure as a timeout, collapsing both into the same operator-visible card while destroying the diagnosis.

## 5. The two continuity defects

### 5.1 Lease-suppressed commands must be reported

A task release and a browse command arriving in the same millisecond causes the command to be discarded after a log line, with nothing sent back. Cloud then waits out its own step timeout. This is the forbidden silent-drop shape and is already recorded as deferred work in `facebook-first-post-comment-confirmation` task 5.6.

Fix: reply with an honest non-execution receipt naming lease suppression, so Cloud learns immediately and can retry or terminate rather than waiting blind.

### 5.2 Reels re-entry deadlock

Authorizing the Reels surface requires the fallback state to be idle. The only transition back to idle requires a non-empty ordinary feed to arrive. An account is on Reels precisely because its ordinary feed produced nothing, so once anything sends it home, that unlock condition can never be satisfied and the account is stuck on a surface that yields no work.

The batch tail issues an unconditional browse scroll with no task id. Ownership therefore moves from the task back to the browse loop, the page session is rebuilt for the new owner, browse position resets to its default (home), and the pre-scroll "ensure we are on a list surface" check accepts only home/search/group — not Reels — so it navigates home. That is the observed jump to the home feed.

Two fixes, both needed:

- The unlock must not depend solely on a non-empty ordinary feed. A confirmed-empty ordinary feed is equally decisive evidence that Reels should be re-authorized, and must return the state to idle.
- The dispatcher must have a handling branch for a scroll receipt reporting no target. Today five candidate branches each miss it and the generic fallback explicitly excludes scroll actions, so the session emits no command and reaches no terminal state — a 60 s stall ending only at cold standby.

**This pair is independent of the comment outcome.** The same account would have stalled the same way after a fully successful comment. It is included here because the incident exposed it, not because it caused the comment failure.

### 5.3 The visible Vietnamese Feed-recovery control is an actuation path

The affected page exposes a visible control labelled `Đi đến Bảng feed`; operator evidence is that navigating away from the unusable surface requires activating that control. Treating the page as merely empty and sending more wheel input cannot exercise that recovery path.

The router therefore recognizes only a unique visible control whose normalized accessible label or rendered text is exactly `Đi đến Bảng feed`. JavaScript is observation-only: it returns a viewport coordinate and MUST NOT call `HTMLElement.click()`. Native brings the exact CDP target to the foreground, re-runs the target probe to avoid a stale coordinate, and emits one `mouseMoved → mousePressed → mouseReleased` sequence.

The pointer sequence is not itself success. Native waits for the same recovery control to disappear and for the page probe to classify the destination as the home surface. A missing or moved target before dispatch is not executed; an ambiguous/out-of-viewport target is rejected; a dispatched click without the home-surface postcondition is reported as ambiguous. Only a confirmed recovery is allowed to re-enter the existing Feed scan/scroll path.

## 6. Explicitly not in this change

- Any group-join budget (§2).
- Splitting `verification_ambiguous` into "did not look" and "looked and did not see" (`facebook-first-post-comment-confirmation` task 5.5).
- Normalising multiple join buttons by group id (that change's task 5.3).
- Scrolling a trusted-click target into the viewport before reading its coordinates (that change's task 5.4).
- The unverified lead that an in-place first-post fingerprint deliberately excludes the canonical permalink while identity readback may depend on one. If true it would make failure more likely the *better* the page hydrates, which is the opposite of the hydration-speed correlation measured in §3.2. It needs a real-machine capture of the returned identity to confirm and is recorded in the acceptance backlog rather than guessed at here.
