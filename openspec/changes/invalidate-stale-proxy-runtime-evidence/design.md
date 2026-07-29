## Context

`proxyRuntime` is produced by the Edge core for one attached browser generation and projected through the Electron parent into the renderer. The core already emits `stale` when an owned browser enters cold standby, but the Electron parent retains the last verified snapshot when the whole child exits. A later startup can also fail during runtime/kernel/network preparation before the existing spawn-time `proxyRuntime: null` reset is reached.

The renderer intentionally prefers a live browser runtime result over proxy preflight. That precedence is correct only while the evidence belongs to a browser generation that is still live.

## Goals / Non-Goals

**Goals:**

- Make the Electron parent invalidate browser IPs, direct IPs, timestamps, and session traffic as soon as their owning browser/core generation ends.
- Make a new AdsPower startup attempt begin without any previous browser generation's runtime evidence, including when preparation fails before spawn.
- Reuse the existing `stale` state so an absent replacement result is explicit while a current preflight may still provide its separate offline conclusion.
- Preserve current-generation runtime precedence and existing Active-browser fail-closed behavior.

**Non-Goals:**

- Add periodic or manual proxy re-probing.
- Change the meaning of `verified`, `same_as_host`, preflight `available`, or Active takeover equality.
- Change Cloud proxy authority, AdsPower profile synchronization, proxy retries/cooldowns, protocol messages, or Native Page Engine behavior.
- Package or release a desktop installer.

## Decisions

1. **Expire evidence in the Electron lifecycle owner at confirmed boundaries.**

   The parent knows when a managed child errors or closes, when the browser-only standby acknowledgement confirms teardown, and when a new no-child start attempt begins. It will invalidate the runtime projection at those boundaries. It will not invalidate on a close request, `coldStandbyPending`, ordinary preflight updates, or `close_failed`, because those states do not prove that the current browser generation has ended. Relying only on a final core event was rejected because an abnormal exit cannot guarantee that stdout drains a new semantic event before close.

2. **Canonicalize `stale`, not a synthetic failure.**

   Invalidation preserves only a bounded generation marker and sets `sessionReceivedBytes` to zero; it removes browser/direct IPs and `checkedAt`. The Electron parent neither synthesizes nor increments that marker; the core may advance its observer generation through the existing mechanism to cancel an in-flight probe. Neither path converts an ended browser into `unavailable`, because no current browser probe failed. The normalizer applies this canonical shape to every incoming `stale` event so a late core event cannot restore old evidence. `null` remains reserved for a generation that has not produced any runtime snapshot.

3. **Invalidate at both generation end and replacement start.**

   Child error/close handling invalidates the projection before any terminal branch. Browser-only standby invalidates in the core only after `killAndConfirmDead()` succeeds and is reinforced by the parent lifecycle acknowledgement. Both the normal no-child AdsPower start and browser-absent control bootstrap invalidate before their first asynchronous preparation. This prevents historical evidence from masking a preparation failure before `spawnEdgeChild` without erasing proof from a browser whose close has not been confirmed.

4. **Keep renderer precedence unchanged.**

   `pending`, `verified`, `same_as_host`, and `unavailable` from a live generation remain authoritative over preflight. Canonical `stale` is already outside that current-runtime set, so a current preflight can render independently; no broad “preflight always wins” fallback is introduced.

5. **Test the lifecycle composition, not only labels.**

   Unit coverage will verify canonical stale projection, zeroed observer traffic, and renderer precedence outcomes. Source-level lifecycle contracts will require invalidation at the no-child AdsPower start boundary, standby acknowledgement, and common child error/close boundaries, while also proving pending/failed close requests do not clear current evidence.

## Risks / Trade-offs

- [A future terminal branch omits invalidation] → Clear once before child error/close branching and keep a focused source-contract test.
- [An expired browser is mistaken for a failed proxy] → Use canonical `stale`, not `unavailable`; let the independent preflight state describe only its own result.
- [A late core event restores expired details] → Canonicalize every incoming `stale` snapshot and reset observer traffic before emitting it.
- [Preflight overwrites evidence from a still-live browser] → Do not change renderer precedence and do not invalidate on ordinary preflight updates while a child/browser generation is live.
- [A close request erases evidence before teardown succeeds] → Invalidate only on lifecycle acknowledgement or child termination, never on the request or `coldStandbyPending`.
- [A replacement start briefly shows expired evidence] → Apply invalidation before asynchronous runtime, kernel, and network preparation begins.

## Migration Plan

No data migration or Cloud deployment is required. Ship the Edge source change through the normal desktop release path when explicitly authorized. Rollback restores the previous in-memory projection behavior; no persisted state needs reversal.

## Open Questions

None.
