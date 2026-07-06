## Context

The role model configuration page opens a read-only prompt preview by calling `GET /api/roles/:roleId/prompt`. For browse roles, cloud calls the live role instance's `previewPrompt()`, which uses minimal sample runtime data plus the current preview persona to call the same `buildPrompt()` logic used at runtime.

The viewer can highlight persona-derived spans when a role implements `personaSegments()`. The highlighter is intentionally strict: every persona segment must occur exactly once in the rendered prompt, and the split segments must rejoin to the original prompt. This prevents false highlighting, but it also means a stale `personaSegments()` implementation silently falls back to flat prompt display.

`CuratedNoteEvaluator` currently has that drift: its real prompt says `你的创作领域 / 兴趣（作软背景，不要硬性字面匹配）：...` and includes `seed_keywords`, while its `personaSegments()` returns a shorter `创作领域 / 兴趣：...` string without seed keywords. The prompt remains faithful, but the UI loses the source highlight and looks more like a generic example.

## Goals / Non-Goals

**Goals:**

- Restore persona highlighting for `精选准入·正文评估` without changing its runtime prompt text.
- Make the prompt viewer's persona source visible before the prompt body, not only in a small selector above the role table.
- Keep all preview language honest about sample runtime inputs versus selected-account persona.

**Non-Goals:**

- No prompt editing path.
- No runtime prompt wording change.
- No model routing, category fallback, role registration, or database schema change.
- No attempt to display a historical real LLM call. The prompt viewer remains a template preview, not an execution replay.

## Decisions

1. **Fix the role's `personaSegments()` to match `buildPrompt()` exactly.**

   This keeps the existing strict highlighter and avoids weakening the anti-false-highlight gate. The segment should include the same label and the same interest list, including `seed_keywords`.

2. **Return a persona source label from the preview provider.**

   The backend already knows whether `accountId` was omitted, selected with a persona, or selected but missing persona. Adding optional metadata lets the UI show a compact, explicit persona-source banner while keeping old viewers compatible.

3. **Keep sample-data notes separate from persona-source text.**

   The preview should keep saying runtime inputs are sample placeholders. Persona text should separately say sample persona, selected account persona, or fallback sample persona. This avoids implying that sample title/body/card data came from a real run.

## Risks / Trade-offs

- **[Risk] More text in the prompt modal can make it noisy.** -> Use a compact banner and keep detailed fallback warnings only for unbound accounts.
- **[Risk] Optional API fields can drift from TypeScript types.** -> Update cloud and console API types together and cover provider behavior in tests.
- **[Risk] Persona segmentation can regress on later prompt edits.** -> Add a direct test for `CuratedNoteEvaluator.previewPrompt()` + `personaSegments()`.
