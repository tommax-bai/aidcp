## 1. Edge — auto-resolve container name

- [x] 1.1 Protocol: add optional `PageCardsPayload.containerName?` (byte-identical both `protocol.ts`; reuse message, count unchanged).
  <!-- aidcp-edge c8419c8 (landed on master 97799eb): containerName? on PageCardsPayload; AC-PROTO count unchanged. -->
- [x] 1.2 `FacebookCommentExecutor.searchInContainer` reads the container's real name (og:title → group header h1 → cleaned document.title, strips trailing "| Facebook") and returns it on all post-navigation paths; honest undefined when unreadable (never fabricates from id).
  <!-- aidcp-edge c8419c8: readContainerName + CONTAINER_NAME_JS; threaded into all searchInContainer returns. -->
- [x] 1.3 `FacebookCommentHandler` includes containerName in the page.cards reply.
  <!-- aidcp-edge c8419c8: onSearch adds containerName to reportPageCards. Tests: resolved + honest-null + handler passthrough. Edge focused 26/26. -->

## 2. Cloud — {url,name} model + auto-fill

- [x] 2.1 Config store container model `string[]` → `FacebookContainer[]` {url,name}; `coerceContainers` accepts legacy bare-url strings AND {url,name} objects, dedups by url; `effectiveConfigFor` returns objects.
  <!-- aidcp-cloud 8835d5d (landed on master 018ce5f): FacebookContainer type + coerceContainers/sanitizeContainersInput; backward-compat coerce. -->
- [x] 2.2 `resolveContainerName(accountId,url,name)`: best-effort auto-fill of a configured container's real name (no updated_by bump, ignores unconfigured urls, swallows errors — never touches the main path).
  <!-- aidcp-cloud 8835d5d: UPDATE ... SET containers RETURNING; cache refresh; url-not-configured → ignore. -->
- [x] 2.3 `facebook-edge-steps.searchInContainer` captures page.cards.containerName; scheduler picks container object, sends `.url` to the edge, uses the human name (resolved > configured > url fallback) for audit + receipt, and persists a resolved name via `facebookResolveContainerName` (wired in server.ts to the config store).
  <!-- aidcp-cloud 8835d5d: edge-steps returns containerName; runFacebookTargetedTask uses containerUrl for dispatch + human label for audit + void resolve on containerName. -->
- [x] 2.4 Panel PUT accepts containers as url strings or {url,name}.
  <!-- aidcp-cloud 8835d5d: panel-server PUT cast to Array<string|{url;name?}>; store coerces. Tests: model coerce/compat + resolveContainerName + scheduler auto-fill/honest-url-fallback. Full cloud suite 1560/1560. -->

## 3. Console — show group name not id

- [x] 3.1 `types/api.ts`: FacebookContainer {url,name}; FacebookCommentConfig.containers.
- [x] 3.2 `FacebookSearchConfig.tsx`: Select value = urls, tagRender shows the resolved name (or "待识别"), onChange reconciles {url,name} preserving learned names, PUT sends {url,name}[] — the raw group id/url is never shown to humans.
  <!-- aidcp-console 8c26990 (on master): container editor name-aware. Test: tags show name / "待识别" and never the id; save preserves names. vitest 68 pass/1 skip, tsc clean, build ok. -->

## 4. Validate & deploy

- [x] 4.1 Both protocol.ts byte-identical (PageCardsPayload). Edge acceptance 15/15, cloud 46/46 (AC-PROTO count 65 after concurrent persona change), typecheck clean both.
- [x] 4.2 Deploy: cloud master 018ce5f live on dev (rsync src, deps unchanged, healthcheck green, isales intact); console master 8c26990 deployed to /opt/aidcp/console (http 200). Edge is a local installer — auto-resolve activates on next edge repackage; for the live real-post test the edge runs from the master worktree so it already resolves names.
- [ ] 4.3 Real-machine confirmation of the auto-resolved name (a real FB comment run persists the group's real name into the container config; console then shows it). Ties into the facebook-scheduled-comment real-post test (backlog 簇 14).
- [x] 4.4 Run `openspec validate facebook-container-display-name --strict`.
