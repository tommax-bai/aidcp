## 1. Risk Window Semantics

- [x] 1.1 Update cloud risk counting so `day` uses the Asia/Shanghai calendar day while `minute` and `hour` remain sliding windows.
  <!-- repo: aidcp-cloud; commit: 148b558f2faa24cb111370fa6bb9e52449225df9; note: SlidingWindowCounter day window now uses explicit Asia/Shanghai calendar-day boundaries; minute/hour remain rolling windows. -->
- [x] 1.2 Ensure day quota retry/release timing returns the next local midnight and continues to drive view-quota sleep/resume.
  <!-- repo: aidcp-cloud; commit: 148b558f2faa24cb111370fa6bb9e52449225df9; note: quotaReleaseAfterMs/explain day retry now returns the next Asia/Shanghai 00:00, so view quota sleeps release at local midnight. -->
- [x] 1.3 Keep persisted `risk_counters` schema and existing quota values unchanged.
  <!-- repo: aidcp-cloud; commit: 148b558f2faa24cb111370fa6bb9e52449225df9; note: no schema migration or quota-number changes; existing counter timestamps are reinterpreted by query/window logic. -->

## 2. UI And Documentation Alignment

- [x] 2.1 Confirm companion `dailyUsage.windows.day` saturation and `releaseAt` use the same natural-day source of truth.
  <!-- repo: aidcp-cloud; commit: 148b558f2faa24cb111370fa6bb9e52449225df9; note: server dailyUsage metadata, persisted today aggregations, panel summaries, publish counts, and quota release hints now share explicit Asia/Shanghai day start. -->
- [x] 2.2 Update protocol/risk-control/acceptance docs to describe minute/hour sliding windows plus natural-day daily quotas.
  <!-- repo: aidcp; commit: pending-control-docs; note: protocol/risk/architecture/product docs updated in this OpenSpec change; final control commit recorded below. -->

## 3. Validation And Closeout

- [x] 3.1 Add or update cloud tests for natural-day day quotas and sliding minute/hour behavior.
  <!-- repo: aidcp-cloud; commit: 148b558f2faa24cb111370fa6bb9e52449225df9; note: added RiskController day-boundary tests plus SQL shape tests for Asia/Shanghai today aggregations. -->
- [x] 3.2 Run relevant cloud risk/acceptance validation and OpenSpec strict validation.
  <!-- repo: aidcp-cloud/aidcp; commit: 148b558f2faa24cb111370fa6bb9e52449225df9; validation: npm test pass 1417/1417, npm run test:acceptance pass 44/44, npm run typecheck pass, openspec validate calendar-day-risk-quotas --strict pass. -->
- [ ] 3.3 Record implementation commit, validation, and deployment notes in this task list.
