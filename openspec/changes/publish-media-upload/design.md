# Design: publish-media-upload

> 本设计经一轮「业界方案」对抗式评审产出（2026-06-20，11-agent workflow：5 路代码坐实 + 业界调研 →
> 综合 → 3 视角对抗评审 → 定稿）。核心结论：**配图主路径（CDP `DOM.setFileInputFiles`）的模块形状取决于一次实机
> 校准探针（task 0），该探针只能在运营机上对真实小红书发布页跑 CDP 才能定**——这正是父 change 把配图整块延后到此的根因。
> 协议零改动、消息数维持 54。

## Context & why-deferred

End-to-end image publishing is the last unwired leg of the command-driven publish path. The cloud already generates a genuine DashScope (通义万相) https CDN URL (`aidcp-cloud/src/publish-agent/wanxiang-client.ts:172-177`), threads it through CoverSelector → ContentAssembler (`content-assembler.ts:53`) → PublishExecutor (`publish-executor.ts:197` wraps it as `images:[url]`), and into `PublishSequenceInput.images` (`command-sequencer.ts:35`). But that input is read by nobody: `buildCommandSequence` never emits `upload_image`/`set_cover` (verified — the only mention is the deferral comment at `command-sequencer.ts:100`), and the edge dispatcher honestly stubs both kinds to `kind_not_implemented` (`publish-command-handlers.ts:209-212`). The whole-page v1 path additionally hard-rejects images (`publish-post.ts:294-296`).

The parent change `publish-trigger-and-apply` (`tasks.md:16-17`) deliberately took a five-item convergence on 2026-06-20 and sank ALL image-upload work here: cloud sequencer image-emit, edge `upload_image`/`set_cover`, lifting the v1 hard-reject, and the image-degrade AC. The protocol prerequisites are 100% met (kinds + `imageUrl` param already shipped from the runtime stage), so this change touches NO protocol type.

This change owns exactly that convergence and nothing more. Multi-image and video stay reserved-not-built (YAGNI).

## Mechanism (CDP file-input bridge)

PRIMARY: `DOM.setFileInputFiles` against the publish page's `<input type=file>` — the same browser-trusted primitive behind Puppeteer `uploadFile` / Playwright `setInputFiles`. The edge has a generic `CdpClient.send(method, params)` (`aidcp-edge/src/cdp/client.ts:114`), so the file-set is one new `cdp.send('DOM.setFileInputFiles', {objectId, files:[absPath]})` plus enabling the DOM domain — zero new npm dependency. It writes a real `FileList`, fires Chrome's native input/change events the XHS SPA listens for, and works on hidden / zero-size inputs without unhiding or clicking.

CORRECTION vs the survey's reuse claim: obtaining the node handle is NEW plumbing, not reuse. The existing executor (`action-executor.ts:47`) only ever calls `Runtime.evaluate` with `returnByValue:true` and returns a boolean; grep confirms zero `returnByValue:false` / `objectId` / `DOM.enable` usage today. The uploader runs its OWN `DOM.enable` (idempotent, once) + `Runtime.evaluate({returnByValue:false})` to resolve the file input to an `objectId`, then `DOM.setFileInputFiles`. This follows the repo's XPath-locate STYLE but reuses no existing engine code — so the unit-test stub must stand in for the whole locate+set, not just the set.

Why not the generic `op='input'` value path: a file `<input>` cannot be populated by JS value-injection (browser security), and `CdpActionExecutor` only handles click/input/scroll via value-setter (`action-executor.ts:40-94`). File upload is a bespoke flow outside `resolveAndAct`'s string-value semantics.

`set_cover` is NOT a CDP file primitive — selecting an already-uploaded image as cover is ordinary DOM interaction, done as a locate+click+post-verify atom on the existing `LocatingEngine` via `runAtom`, with a COVER-SPECIFIC post-validator (see Failure section).

FALLBACK (deferred behind the `FileInputSetter` interface, NOT built now): `Page.setInterceptFileChooserDialog` + `Page.fileChooserOpened` for widgets that create the input lazily on button click; completes via the same `setFileInputFiles`. Synthetic drag-drop/paste are `isTrusted=false` and out of scope.

Co-location precondition (made explicit): `setFileInputFiles` reads from the BROWSER process's filesystem. This change assumes the driven Chrome is the co-located edge Chrome on the same host as the temp file. Publish runs headful today (`main.ts:67`, headless only when `AIDCP_CHROME_HEADLESS==='true'`); `setFileInputFiles` works in both modes, but a remote/forwarded CDP target would violate the local-file precondition and is out of scope. The `FileInputSetter` interface is the documented single swap point if that ever changes.

## End-to-end data flow

1. Cloud generation (already live): genuine time-limited DashScope https URL → `AssembledContent.imageUrl` → `images:[url]` in `PublishSequenceInput` (`publish-executor.ts:197`). `null` when `WANXIANG_API_KEY` unset → sequencer emits no image command (correct-but-dormant).
2. NEW build: `buildCommandSequence` consumes `input.images` and emits `upload_image` per URL (`params.imageUrl`) after `select_mode` (`command-sequencer.ts:92`) and BEFORE `fill_field` (`:93`). It does NOT emit `set_cover` (see degrade redesign).
3. NEW execute: `executePublishSequence` (`command-sequencer.ts:128-155`) special-cases `upload_image`: on failure (returned `ok:false` OR a caught timeout/exception for that kind), set a local `imagesOk=false` and CONTINUE — do NOT hit the line-143 abort. After all `upload_image` commands, if `imagesOk` is still true, DYNAMICALLY dispatch one `set_cover` (`params.imageUrl` = chosen cover) via `sendAndWaitResult`; if `imagesOk` is false, skip it. `set_cover` is therefore an EXECUTION-TIME conditional dispatch, not a build-time emission. Thread `imagesOk` into `PublishSequenceResult`.
4. Ordering remains: navigate_entry → select_mode → upload_image×N → [conditional] set_cover → fill_field(title/content) → add_with_candidate → set_option → set_schedule → [approved] submit_publish → capture_postId.
5. Each `upload_image` rides inside the existing `publish.command` envelope (`makeEnvelope` at `command-sequencer.ts:160`) — no new message type.
6. Edge dispatcher routes `upload_image` to the new uploader: validate+download URL → edge-local temp file → resolve input objectId → `DOM.setFileInputFiles` → post-verify the WIDGET's own success state (thumbnail/preview for this image), NOT merely `input.files.length>0` → unlink temp in `finally`. Routes `set_cover` to a `runAtom` with a cover-state validator.
7. Edge returns `publish.command.result` verbatim (`publish-command-handlers.ts:245-249`) — no fake `ok:true`.
8. Persistence reconciliation: `publish-executor.ts:129` stores `imageUrl` BEFORE the sequence runs. After the sequence, when `result.imagesOk===false`, the executor explicitly records the text-only truth (annotate/null the stored image-present signal — see Components) so no reader can infer image-present from a generated-but-never-attached URL.

## Components by repo

### aidcp-cloud
- **CommandSequencer.buildCommandSequence (image emit only)** — `src/publish-agent/command-sequencer.ts:84-125`. Loop `input.images`, emit `upload_image×N` after `select_mode`/before `fill_field`. Count-agnostic loop (forward-compatible with multi-image). Do NOT emit `set_cover` here. Add `cover?: string` to `PublishSequenceInput` (`:29-40`) and `imagesOk: boolean` to `PublishSequenceResult` (`:42-48`) — internal types, not protocol.
- **CommandSequencer.executePublishSequence (degrade-not-abort runtime)** — `src/publish-agent/command-sequencer.ts:128-155`. Special-case `upload_image`: on returned `ok:false` OR a caught exception whose `cmd.kind==='upload_image'`, set `imagesOk=false` and `continue` (do NOT `return` at `:140`/`:144`). After the upload block, if `imagesOk` dispatch one `set_cover`. Keep fail-fast for every non-image kind. Return `imagesOk`. Inline comment marking this as the ONE deliberate relaxation of fail-fast, only for images, because text-only is a valid honest outcome whereas a failed title is not.
- **PublishExecutor (persist the truth on degrade)** — `src/publish-agent/roles/publish-executor.ts:129,192-211`. Already passes `images` (`:197`). After `executePublishSequence`, when `result.imagesOk===false`, reconcile the already-stored `imageUrl` (`:129`): null it out OR set a distinct `imagesAttached=false` signal that all image-present readers must use. Never leave a generated URL implying image-present on a text-only post.

### aidcp-edge
- **PublishCommandDispatcher.dispatch (real upload_image + set_cover)** — `src/flows/publish-command-handlers.ts:209-212`. Replace the `notImplemented` stub: `upload_image` → new `ImageUploader`; `set_cover` → `runAtom` with cover-state validator. Preserve the red line — any failure/unverifiable → `ok:false` + real error (verbatim through `:245-249`).
- **ImageUploader (new, single linear flow, one injectable seam)** — `src/flows/image-uploader.ts` (new). Owns the whole flow: validate URL → download-to-temp (PRIVATE method, injected `fetchImpl`) → resolve file input objectId → call injected `FileInputSetter` → post-verify widget success → unlink in `finally`. Per the YAGNI review, download is a private method here, NOT a separate `ImageDownloader` module (single caller, no reuse today). Only `FileInputSetter` is a separate seam (genuine CDP-vs-stub swap point + documented remote-browser extension point). Constructor takes `fetchImpl?: typeof fetch` (mirrors `chrome-launcher.ts:37`) and a `FileInputSetter`.
- **CdpFileInputSetter (real DOM.setFileInputFiles primitive)** — `src/cdp/file-input-setter.ts` (new). Thin CDP impl behind a `FileInputSetter` interface: `DOM.enable` (once, guarded), `Runtime.evaluate({returnByValue:false})` → input objectId, `cdp.send('DOM.setFileInputFiles',{objectId,files})`. Built from the existing `session.cdp` singleton (`main.ts`). Add a single bounded re-resolve-and-retry on stale-handle error (SPA re-render between resolve and set) within the existing retry-cap discipline; no unbounded loop.
- **Image/cover anchors** — `src/flows/anchors.ts`. Add XHS file-input + cover-entry + cover-active-state + thumbnail-present anchors (goal/anchorHint); honest `no_target` when unmatched. Real DOM needs on-device CDP calibration (`publish-command-handlers.ts:55` note) — gated AIDCP_E2E.
- **v1 hard-reject → explicit redirect** — `src/flows/publish-post.ts:294-296`. Replace the silent-drop guard with an explicit `error: 'use command path for images'` (v1 `publishPost` has no upload step and already has a cloud↔edge payload-shape mismatch). Do NOT silently drop images (red line); do NOT build upload into the near-dead v1 path. Full v1 removal is out of scope.
- **Dispatcher wiring** — `src/main.ts:154-159`. Pass the uploader (built from `session.cdp` + a `CdpFileInputSetter`) into `PublishCommandDispatcher`. Reuse the existing `session`/`cache` singletons, never re-new.
- **Temp-dir startup sweep** — `src/main.ts` (boot). Before first use, `rm({recursive,force})` a dedicated `os.tmpdir()/aidcp-img-*` prefix to reclaim orphans from a crashed prior run (the `finally`-unlink cannot run on SIGKILL/OOM). Single well-known prefix so the sweep never touches isales or other tmp content.
- **AC-CMD test update** — `test/flows/publish-command-handlers.test.ts:140-149`. Replace the `kind_not_implemented` lock for `upload_image`/`set_cover` with success + honest-failure cases using a `FakeFileInputSetter` and fake fetch.

## Failure & degradation (imagesOk honesty)

Red line (MUST NOT 静默假成功) enforced at every gate. Edge `upload_image` failure taxonomy, each returning `ok:false` + a specific real error, never `ok:true`:
- invalid/disallowed URL → `image_url_rejected`
- fetch timeout/network → `image_fetch_failed`
- size cap exceeded → `image_too_large`
- non-image (magic-byte sniff) → `image_format_unsupported`
- file input not locatable → `no_target`
- `setFileInputFiles` threw / stale handle after retry → `engine_error`
- POST-VERIFY fails → `image_not_attached`

POST-VERIFY (review blocker, corrected): `DOM.setFileInputFiles` populates `input.files` SYNCHRONOUSLY and unconditionally — reading `input.files.length>0` immediately is a guaranteed false-positive against the very failure it claims to catch (server-side reject, hung XHR, thumbnail never renders). So `input.files.length>0` is at most a necessary precondition, NEVER sufficient. Post-verify MUST bounded-poll (timeout via `AIDCP_*` env) for the WIDGET's own success state — a rendered thumbnail/preview node for THIS image — located via the engine's normal locate gate. On timeout → `image_not_attached` (`ok:false`). The exact success-state selector needs on-device CDP calibration and is gated behind a real-machine task, not shipped as a files-length stub.

Cloud per-command timeout coordination (review blocker): `sendAndWaitResult` rejects after 30s (`command-sequencer.ts:162-165`) and that rejection aborts the whole sequence (`:140`). A slow/expired URL — the design's OWN primary failure mode — is exactly what triggers it. Two coordinated fixes: (1) edge `AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS` + CDP-set + post-verify budget MUST stay comfortably below the cloud per-command timeout so the edge ALWAYS returns a clean `{ok:false,error:'image_fetch_failed'}` first (or raise `timeoutMs` specifically for `upload_image`); (2) in `executePublishSequence`, when the caught exception is on an `upload_image` command, treat it as degrade (`imagesOk=false`, continue), mirroring the returned-`ok:false` handling for that kind only. Without both, degrade is unreachable for the common case.

Partial multi-image: each `upload_image` is independent. If image k fails, set `imagesOk=false` (never reset to true even if a later image succeeds, so honesty holds) and skip `set_cover` (a cover of a never-attached image is logically impossible). Impl note (design↔code agreement): the executor loop does NOT short-circuit remaining `upload_image` commands after the first failure — it sets `imagesOk=false` and continues; since images are single today (`imageCount` hardcoded 1 cloud-side), this multi-upload branch is dormant and the only effect of a future short-circuit would be saving wasted attempts (a latency optimization, not a correctness/honesty change). The loop is count-agnostic for forward compat; if multi-image is enabled, optionally short-circuit remaining uploads then.

GRACEFUL DEGRADE distinction: unlike every other step failure (which aborts per `command-sequencer.ts:143`), an image-upload failure is degrade-not-abort — the post becomes honest text-only, the run continues to text/metadata/submit, `imagesOk=false` is returned, and the executor reconciles the stored `imageUrl` so `publish_log` records the text-only truth (no fabricated image-present). This is the one place fail-fast is deliberately relaxed, only for images. It MUST be locked by AC-MEDIA-DEGRADE so a future maintainer cannot silently "fix" it back to abort.

DashScope URL expiry (~24h) + human-approval window (review minor, surfaced): the URL is generated then sits through human approval (Feishu card, possibly overnight) before upload runs at approve-time. Expiry-at-upload is a likely steady-state, not an edge case. The edge downloads promptly at upload-command time; on expiry, fetch fails → `image_fetch_failed` → honest text-only degrade. Surface it loudly: persist a distinct reason for expiry-driven degrade so operators see WHY a post went text-only, and note in tasks.md that a re-host/regenerate-on-approve step may be needed if degrade rate is high (out of scope to build now).

DOM.enable is idempotent/guarded; the cdp singleton is reused.

## Security

`imageUrl` originates from OUR cloud (authenticated WS peer), not end-user input, so SSRF threat is materially reduced — proportionate defense-in-depth, NOT a full SSRF proxy. Apply:
1. Scheme allowlist: accept only `https:` (allow `http:` only behind an explicit AIDCP test-host env); reject `file:`/`data:`/`blob:`/`ftp:` to prevent local-file exfiltration.
2. Redirect handling (review major): the house fetch (`globalThis.fetch`) defaults to `redirect:'follow'` (≤20 hops), and an allowlist on the ORIGINAL URL is bypassed by the first redirect to `127.0.0.1`/`169.254.169.254`/a file host. Set `redirect:'error'` (reject all redirects) — DashScope result URLs are direct CDN links, not redirectors. Verify against a real DashScope URL during calibration before locking.
3. Streaming max-size guard: pre-check `Content-Length` AND enforce a running byte counter (Content-Length can lie); abort over cap (`AIDCP_*` env, conservative default e.g. 10MB).
4. Format validation by MAGIC BYTES (jpeg/png/webp leading bytes), not URL extension or Content-Type header alone, before handing to `setFileInputFiles`.
5. Explicit fetch timeout via `AbortController` + `AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS` (new pattern — current `chrome-launcher` fetches are unbounded; an unbounded download is a hang/DoS risk). Must be below the cloud per-command timeout (see degrade).
6. Temp files: `mkdtemp` + randomized name under a dedicated `os.tmpdir()/aidcp-img-*` prefix (NOT a predictable static path), `rm({force:true})` unlink in `finally`, plus the boot-time sweep for crash orphans.

REJECTED as over-engineering against a trusted-cloud source: host allowlist (review minor — DashScope rotates opaque time-limited CDN hostnames; a hardcoded domain would turn legitimate images into `image_url_rejected`, a maintenance liability with marginal gain), DNS-rebinding re-resolution, per-request sandbox, full proxy. Never log the temp path with secrets; record only path conventions per repo rules. Do not touch co-located isales.

## Protocol impact

ZERO new message types. The MessageType count STAYS 54 (verified: both `protocol.ts` files have 54 MessageType members and 54 PayloadMap keys; `docs/protocol.md:19` says 54, consistent). `upload_image`/`set_cover` are `PublishCommandKind` members (`edge protocol.ts:383-384`, `cloud :384-385`) and `imageUrl` is a `PublishCommandParams` field (`edge :405-406`) — SUB-KINDS/PARAMS riding inside the already-shipped `publish.command` envelope, NOT MessageType members. The `PayloadMap`/`makeEnvelope` exhaustion guard (AC-PROTO-02) is untouched and cannot break. `command-bridge.ts` does NOT participate (it maps only browse-loop EdgeCommand names; `publish.command` is sequenced directly at `command-sequencer.ts:160`). `docs/protocol.md` needs NO header-count edit and NO new table row (the `publish.command` row already references the kind set abstractly). New types are internal-only: `imagesOk` on `PublishSequenceResult`, `cover` on `PublishSequenceInput` — both in `command-sequencer.ts`, not `protocol.ts`.

## Testability

CDP-dependent parts stay UNIT-TESTABLE via the existing DomProvider/ActionExecutor seam plus one new injected `FileInputSetter` seam, mirroring how `publish-command-handlers.test.ts` stubs the executor.
1. `FileInputSetter` is an interface; tests inject a `FakeFileInputSetter` that records the `(selector, paths)` it was asked to set AND writes a fake thumbnail into the jsdom DOM so the post-verify gate passes — the `FakeExecutor` pattern (`test:62-80`). Because no existing engine call yields the node handle, the fake stands in for the WHOLE locate+set, not just the set.
2. The download seam is the injected `fetchImpl` on `ImageUploader` (mirrors `chrome-launcher.ts:37`); tests pass a fake fetch returning controlled bytes/headers — no network.
3. `set_cover` reuses `runAtom` + `LocatingEngine` on jsdom, identical to existing `set_option` tests, but with a cover-state validator.

New AC cases: AC-MEDIA upload success / download-timeout / non-image / no-target / post-verify-fail (red-line reverse: sets files but renders NO thumbnail → `image_not_attached`, proving `input.files.length>0` is NOT sufficient); AC-MEDIA-SEQ (sequencer emits `upload_image×N` then conditional `set_cover`, correct order, submit still approval-gated); AC-MEDIA-DEGRADE (both returned-`ok:false` AND timeout-exception → `imagesOk=false`, set_cover skipped, text/metadata still emitted, executor reconciles imageUrl); AC-PUB regression asserted at the EXECUTOR approval gate (`publish-executor.ts:184-190`, the live mechanism), with the `buildCommandSequence` truncation kept as a redundant lower-layer guard.

The existing `kind_not_implemented` lock (`test:140-149`) is replaced. No real Chrome needed for unit tests; real-machine CDP calibration of the anchors + widget success-state selector + redirect verification is the separate gated `AIDCP_E2E` task 0.

## Task-0 calibration results (2026-06-20, on-device CDP against creator.xiaohongshu.com/publish/publish)

Ran read-only probes + one real `DOM.setFileInputFiles` upload of a test image (never published; draft discarded). Scripts: `aidcp-edge/scripts/calibrate-publish-probe.ts`, `calibrate-imgtab-probe.ts`, `calibrate-upload-probe.ts`.

- **0.1 — file input is STATIC + hidden (not lazy).** After clicking the「上传图文」tab, the page has exactly one `input[type=file]`: `input.upload-input`, `accept=.jpg,.jpeg,.png,.webp`, `multiple`, `hidden=true`, present BEFORE any upload click. → PRIMARY `DOM.setFileInputFiles` confirmed; `FileChooser` fallback NOT needed. The publish page defaults to the「上传视频」tab (its lone file input is `accept=.mp4,...`) — `select_mode` must click「上传图文」first (existing anchor text「图文」matches; confirmed). Locked selector (injected in `main.ts`): `input.upload-input[type=file]` (fallback `input[type=file]`).
- **0.1 end-to-end validated.** `DOM.setFileInputFiles` on that input really populated and the SPA reacted: thumbnails + the full editor rendered.
- **0.2 — editor IS image-gated.** Before upload `editables=0` (only the dropzone「上传图片，或写文字生成图片」); after upload `editables=4`: title `input.d-text` (placeholder「填写标题会有更多赞哦」, matches existing anchor), content `div.tiptap.ProseMirror[contenteditable=true]`. → A 图文 post REQUIRES ≥1 image; all-images-failed CANNOT yield a valid post → must be honest `failed`, NOT text-only. This is now encoded: `executePublishSequence` aborts `failed`(`all_images_failed`) before `fill_field` when images were requested and all failed.
- **0.3 — success-state node confirmed; `input.files` is NOT a success signal.** After a successful upload `input.files.length === 0` (XHS consumes the FileList into its own state) — vindicates the fail-closed "never trust `files.length`" rule. Real success node: a rendered thumbnail `img` with a `src` inside `div.img-preview-area` (e.g. `img.img.preview` blob:, `img#creator-preview-image-0`). Locked `hasThumbnail` (injected in `main.ts`): an `img` with non-empty `src` under `.img-preview-area` / `#creator-preview-image-0`.
- **set_cover finding.** Single-image cover is automatic (the uploaded image IS the cover) — there is no independent "set cover" control; the only cover-ish entry is「获取封面建议」(`div.cover-detect`/`.get-cover-suggest`, an AI suggestion, not selection). → `set_cover` is now emitted ONLY for multi-image (`images.length > 1`); single-image emits none (a stray `set_cover` would `no_target`→fail-fast and kill the publish). Multi-image cover-active selector remains pending a future multi-image calibration.
- **0.4 — NOT run locally** (`WANXIANG_API_KEY` not on this machine, so no real DashScope URL to test `redirect:'error'` against). The `redirect:'error'` guard stays; verify against a real DashScope URL during deploy E2E (task 8.4).

## Open decisions (defaults chosen; flag to override)

- **XHS DOM shape** (static hidden `<input type=file>` vs lazy/dropzone): build PRIMARY first; resolve via the calibration spike (task 0) BEFORE locking the uploader shape. Fallback (`FileChooser` interception) slots behind `FileInputSetter` if the spike shows a lazy input. Do NOT pre-build drag-drop.
- **Multi-image**: count-agnostic plumbing only; multi-image generation/selection NOT built (cloud `imageCount` hardcoded 1). Reserved.
- **Degrade product rule**: image-upload failure → honest TEXT-ONLY + continue (the parent change's decided rule), UNLESS the spike shows XHS gates the editor on a successful image — then all-images-failed becomes an honest `failed`, not a text-only post.
- **Timeout/size defaults**: `AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS` conservative (edge total budget < cloud 30s per-command), size cap ~10MB; both env-tunable, tuned on-device.
- **v1 reject**: explicit "use command path" error, not silent drop, not full v1 removal.
- **WANXIANG_API_KEY on ECS**: verify via SSH before declaring live; if unset, the change is correct-but-dormant — declare "merged, dormant pending key", not "live". Do not record the key value.
