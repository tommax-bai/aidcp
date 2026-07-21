## 1. Long-form card planning and contracts

- [x] 1.1 Extend Cloud text-card copy, plan, and audit types with optional article layout, paragraphs, and grouped source indices while preserving legacy fields.
- [x] 1.2 Classify ordered all-text-card sources deterministically and group every usable source slot into contiguous publish-card buckets.
- [x] 1.3 Add the article-flow prompt/parser, full paragraph anti-copy checks, and shared density preflight without adding retry loops.

## 2. Deterministic article rendering

- [x] 2.1 Implement the fixed simple article cover/page layout with semantic wrapping, regular-weight body text, bounded occupancy, and honest overflow failure.
- [x] 2.2 Pass article data through prompt composition and image generation, persist grouped mapping/audit metadata, and skip redundant style-only rerender for article cards.

## 3. Verification

- [x] 3.1 Add focused unit coverage for classification, contiguous grouping, parsing, anti-copy checks, layout density, overflow, determinism, and legacy compatibility.
- [x] 3.2 Add publish acceptance coverage proving a long reference carousel maps all usable source slots into at most nine article cards and retains the ending.
- [x] 3.3 Reproduce the approved nine-card result for the Xiaomao draft and inspect the rendered contact sheet plus per-card occupancy metadata.

## 4. Validation and delivery

- [x] 4.1 Run focused tests, publish/text-card acceptance tests, the full Cloud suite, and Cloud typecheck.
  <!-- aidcp-cloud e6b9289; focused 91/91, acceptance included, full 2759 passed + 8 skipped, npm run typecheck passed. -->
- [x] 4.2 Run strict OpenSpec validation and record implementation commits, validations, deployment, and deviations in this task list.
  <!-- control 1ca6916; aidcp-cloud e6b9289; openspec validate reference-aligned-textcard-layout --strict passed; no protocol, schema, dependency, or environment changes. -->
- [x] 4.3 Integrate and push the control and Cloud changes, deploy Cloud to dev, and verify service health plus a non-publishing Xiaomao generation smoke test.
  <!-- Both default branches were fast-forward pushed. Dev backup=/opt/aidcp/cloud.bak.20260721-152231.tar.gz env=/opt/aidcp/cloud.env.bak.20260721-152231; only aidcp-cloud.service restarted; active/NRestarts=0, 8787+8090 listening, panel health+version HTTP 200, PostgreSQL select 1, Feishu ready, no error journal entries, and pre-existing isales services remained active. ECS Xiaomao article-page smoke rendered 1728x2304/245847 bytes at occupancy 0.8368 with truncated=false and sanitized=false; no platform publish was performed. -->
