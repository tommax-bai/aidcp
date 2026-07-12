# Facebook Post Publish Probe Plan

This plan keeps Facebook probing non-destructive by default. Real submit is
allowed only when the disposable target gates in the OpenSpec tasks are
explicitly enabled by the operator.

## Baseline Composer Probe

- Use an operator-known Facebook test/import AdsPower profile.
- Run the probe at `1365x900`, `768x900`, and `430x932`.
- Navigate to the Facebook home/timeline entry point and verify the signed-in
  account identity with sanitized hashes only.
- Use real CDP mouse events to open the post composer.
- Record only structural evidence: overlay state, login/checkpoint state,
  composer entry count, dialog/editor counts, file input count, media control
  count, final path, viewport, and sanitized account/profile hashes.
- Do not type, attach media, or submit in the baseline probe.

## No-Submit Text Probe

- Open the composer with the same structural locator path as the baseline.
- Focus the editable composer body with a real click.
- Type a short sentinel string that contains no secret or user content.
- Verify the editor text count/length and that the publish button remains
  detectable but is not clicked.
- Clear the typed text with keyboard selection and delete/backspace.
- Verify the editor returns to an empty state before closing the composer.

## No-Submit Media Probe

- Use a small local generated probe image or a manually supplied non-sensitive
  image from the operator account's media pool.
- Open the composer, resolve the active file input, and attach the image.
- Wait for a thumbnail/readiness signal and record sanitized counts only.
- Remove the media from the composer when the UI exposes a remove control.
- Verify the thumbnail count returns to zero before closing the composer.
- If removal cannot be verified, close the composer without submit and mark the
  probe as `media_cleanup_unverified`.

## Real Submit Gate

Real submit remains blocked unless all conditions are true:

- `FACEBOOK_POST_PROBE_SUBMIT=1`
- `FACEBOOK_POST_PROBE_DISPOSABLE_TARGET=1`
- The selected profile and target are operator-owned disposable assets.
- Baseline, text, and media no-submit probes passed in the same session.
- The probe can verify success by reload/server/permalink evidence after submit.

Real submit evidence must be sanitized and limited to status, reason codes,
counts, viewport, timestamps, and hashes. Cookies, tokens, raw body text, and
personal identifiers must never be persisted in probe output.
