## Context

The Facebook groups page currently sends all imports through one text area. The cloud API already accepts structured items containing `url`, `name`, `region`, `park`, and `direction`, and it owns Facebook URL validation, canonicalization, duplicate detection, and metadata upsert behavior. The console therefore only needs to separate operator workflows and convert CSV rows into that existing item shape.

## Goals / Non-Goals

**Goals:**
- Make the common one-group workflow fast and explicit.
- Let operators select optional region, park, and direction metadata while adding one group.
- Import a predictable, documented CSV shape without requiring spreadsheet paste heuristics.
- Provide immediate file-level validation and an honest parsed-row count before submission.
- Keep server-side URL validation and canonicalization authoritative.

**Non-Goals:**
- Add or change cloud endpoints, database fields, or target lifecycle behavior.
- Support Excel workbook formats such as `.xlsx` or `.xls`.
- Build taxonomy administration for region, park, or direction.
- Replace the existing wide-text parser, which may remain available as a utility for compatibility.

## Decisions

- Present the two workflows through an Ant Design segmented control inside the existing Facebook groups management section.
  - Rationale: the modes are mutually exclusive actions in the same context, and a segmented control keeps the operational surface compact.
  - Alternative considered: separate cards. Rejected because nested or repeated cards would add unnecessary visual weight to a dense admin page.
- Default to single-group mode and keep its URL field separate from metadata selectors.
  - Rationale: adding one target is the quickest and most frequent action. Region, park, and direction remain optional, and clearing region also clears park.
- Parse CSV in a focused console utility that supports UTF-8 BOM, CRLF/LF, quoted fields, commas inside quoted fields, and escaped double quotes.
  - Rationale: CSV parsing must not rely on splitting lines and commas. A small local parser keeps the dependency surface unchanged while covering the template contract and common spreadsheet exports.
  - Alternative considered: add a third-party CSV package. Rejected because the required surface is small and fully testable without adding a runtime dependency.
- Define the template headers as `群组URL,区域,园区,方向,群组名称`; only `群组URL` is required per imported row.
  - Rationale: Chinese headers match the operators' working language, while optional metadata preserves the existing import contract. The parser also accepts stable English aliases to make programmatic exports practical.
- Download a UTF-8 BOM-prefixed, header-only template.
  - Rationale: the BOM prevents Chinese mojibake in common Excel setups, and omitting sample data avoids accidental import of a fake example target.
- Parse the file locally and show the selected filename plus importable-row count before enabling the import command.
  - Rationale: operators can catch wrong files and empty templates before any write request. The cloud response remains the source of truth for imported, updated, duplicate, and invalid counts.

## Risks / Trade-offs

- [Risk] A CSV exported with unsupported header names cannot be mapped. -> Mitigation: show a clear header error and provide the exact downloadable template.
- [Risk] CSV rows can contain syntactically valid text that is not a Facebook group URL. -> Mitigation: submit the row but rely on cloud canonicalization to count it as invalid; never claim it was imported locally.
- [Risk] Existing facet data may not contain a desired tag for single add. -> Mitigation: this change selects from current stored facets; new taxonomy values can still enter through CSV until taxonomy management is explicitly designed.
- [Risk] Large files can stall the browser. -> Mitigation: cap accepted CSV files at 5 MB and reject larger files before reading.

## Migration Plan

1. Add the CSV parser/template utility and focused tests.
2. Replace the existing paste area with the two-mode add/import controls.
3. Run console tests, typecheck, and production build.
4. Fast-forward the console default branch, publish `dist/` to `dev`, and verify the rendered controls and static asset.
5. Roll back by restoring the previous console static asset bundle; no server or data migration is involved.

## Open Questions

- Whether taxonomy management should later allow operators to create region, park, and direction options directly from single-group mode.
