## MODIFIED Requirements

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
