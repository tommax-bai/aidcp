## Context

`deploy-multi.sh` runs with `set -euo pipefail`. In the active locale, expressions such as `$CLOUD_DIR（...` can be tokenized as a variable name containing the following non-ASCII bytes. The first live three-process switch reproduced this as an unset-variable failure after backup and before rsync or service changes.

## Goals / Non-Goals

**Goals:**

- Make every variable adjacent to non-ASCII prose unambiguous with `${name}`.
- Detect the same source pattern in automated tests.
- Preserve the existing backup, synchronization, topology switch, and automatic rollback sequence.

**Non-Goals:**

- Redesign the three-process topology.
- Add retries, fallback topology selection, or new deployment knobs.
- Modify any non-AIDCP service.

## Decisions

Use braced expansion at every matching site, not only the first failing line, because all matches share the same parser hazard and later ones are reachable during the same deployment. Add a source-level test for the hazardous lexical pattern because `bash -n` accepts it and cannot detect the runtime `set -u` failure.

## Risks / Trade-offs

- [Static pattern could overreach] → Restrict it to an ASCII shell identifier immediately followed by a non-ASCII code point.
- [Deployment can still fail for infrastructure reasons] → Keep the existing fail-before-stop ordering and automatic monolith rollback unchanged.

## Migration Plan

Commit and fast-forward the Cloud fix, run the focused test and typecheck, then execute the existing DEV three-process deploy script. On any service health failure, rely on its existing rollback to `aidcp-cloud.service`.

## Open Questions

None.
