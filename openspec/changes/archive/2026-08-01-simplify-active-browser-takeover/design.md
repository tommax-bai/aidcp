## Context

The current configured-proxy path performs two different jobs before an AdsPower browser becomes usable:

1. For an Inactive profile, Edge resolves the frozen Cloud authority, prepares any system-upstream chain, verifies Facebook reachability, writes the effective proxy to AdsPower, reads it back, and starts the browser.
2. For an already-Active profile, Edge additionally acquires public-egress evidence through the effective proxy and through the browser, then requires exact IP equality before attaching.

The second path assumes public egress is stable across independent requests and makes takeover depend on a controlled egress endpoint plus CDP `Network.loadNetworkResource`. A core failure can leave a browser Active; the automatic recovery then encounters this separate egress gate and may replace the original failure with an unrelated takeover error.

## Goals / Non-Goals

**Goals:**

- Attach to every AdsPower profile reported Active without proxy authority, reachability, or public-egress gates.
- Keep the existing Cloud-authoritative proxy synchronization and Facebook reachability gate before a fresh Inactive-profile start.
- Remove public-egress acquisition, equality comparison, and corresponding UI claims.
- Keep receive-traffic aggregation without collecting request URLs, bodies, cookies, or proxy credentials.

**Non-Goals:**

- Change Cloud proxy-authority storage, revision/CAS behavior, credentials, or ownership.
- Change the system-upstream GOST topology for fresh browser starts.
- Validate or rewrite the proxy used by an already-running browser.
- Build, sign, package, or install an Edge client.

## Decisions

1. **Active status selects a separate direct-takeover path before network preparation.**

   Electron uses its existing serialized AdsPower Local API boundary to determine whether the target profile is Active. A confirmed Active profile is spawned in an internal active-only mode without resolving Cloud authority, preparing GOST, or running Facebook preflight. The child independently confirms Active and attaches to the reported debug port. If the profile becomes Inactive during that race, active-only mode fails without starting a new browser; a later explicit or bounded retry can use the normal fresh-start path.

   A profile confirmed Inactive keeps the existing preparation transaction. If it becomes Active after preparation but before the provider launch call, the provider attaches directly and ignores takeover egress because no such gate remains.

   Alternative considered: keep preflight before every child spawn and only remove IP equality. Rejected because an already-running browser would still be blocked by unrelated Cloud/preflight availability, contrary to direct takeover.

2. **Public-egress probing is removed rather than downgraded.**

   Proxy preflight performs only the bounded anonymous Facebook reachability request. It no longer calls the controlled egress endpoint or returns `expectedEgressIp`. Browser attachment no longer calls a public-IP endpoint, computes `same_as_host`, or produces `verified` egress state.

   Alternative considered: keep public-egress probing as a non-blocking diagnostic. Rejected because it retains the extra dependency, rotating-egress ambiguity, and misleading “verified” product language that motivated the simplification.

3. **Traffic aggregation remains independent of public-egress evidence.**

   The existing CDP `Network.loadingFinished.encodedDataLength` aggregation becomes a traffic-only observer. It resets per browser generation, emits bounded aggregate updates, and never reads URLs, credentials, or response bodies.

4. **Proxy UI reports configuration and reachability only.**

   The Facebook top-bar entry retains the non-secret proxy summary, preflight/reachability state and timestamp, and current-generation receive traffic. Browser/direct IP fields and “代理已验证 / 疑似直连” conclusions are removed. An Active browser attached without preflight is shown as attached/running; the UI does not infer that its runtime proxy matches Cloud.

5. **The Active-takeover terminal error is deleted.**

   `AdsPowerActiveProxyTakeoverError`, `adspower_active_proxy_takeover_rejected`, its Electron log classifier, and its no-respawn special case are removed. Other deterministic classifications such as environment-in-use remain unchanged.

## Risks / Trade-offs

- [An Active browser may use a proxy different from the current Cloud authority] → This is an accepted product boundary; the UI MUST NOT claim runtime proxy verification. Closing and freshly starting the profile remains the way to apply the frozen authority.
- [Active status can change between Electron and child checks] → Active-only mode MUST fail without starting an Inactive profile; it cannot silently bypass fresh-start preparation.
- [Removing browser/direct IP fields reduces runtime diagnosis] → Keep configuration, target reachability, timestamps, aggregate traffic, and ordinary browser/CDP health; do not replace removed evidence with inferred success.
- [Fresh-start behavior regresses while simplifying takeover] → Preserve existing authority, GOST, proxy write/readback, no-proxy, cache, and bounded reachability tests.

## Migration Plan

1. Land the Edge source and contract changes together.
2. Validate focused provider, preflight, traffic, renderer, and Electron lifecycle suites, then run the full Edge suite and typecheck.
3. No Cloud or database migration is required.
4. Existing installed clients retain the old egress gate until a separately authorized client release.

Rollback restores the prior source revision; there is no durable data migration to reverse.

## Open Questions

None.
