## Context

`aidcp-console` is a Vite/React single-page app served by Nginx with history
fallback. The static server can return the app shell for `/intro.html`, but the
client router currently only recognizes `/login` and the registered business
routes. That makes `/intro.html` fail after the bundle loads, even though the
HTTP response and assets are healthy.

## Goals / Non-Goals

**Goals:**

- Treat `/intro.html` as a supported console entry alias.
- Keep auth behavior identical to other protected console routes.
- Keep the route hidden from the top navigation.
- Cover the alias with a focused route test.

**Non-Goals:**

- Do not add an unauthenticated intro or marketing page.
- Do not change cloud API behavior, login credentials, or JWT handling.
- Do not change Nginx routing unless deployment verification proves the static
  fallback itself is broken.

## Decisions

1. Register `/intro.html` in the shared `APP_ROUTES` table with
   `showInNav=false` and a `<Navigate to="/" replace />` element.

   This keeps route registration and navigation metadata in the existing single
   source of truth while preventing a legacy URL from appearing as a business
   tab. Auth remains enforced because `APP_ROUTES` is mounted under
   `RequireAuth`.

   Alternative considered: add a top-level redirect route outside
   `RequireAuth`. Rejected because it would bypass the existing protected-route
   source-path flow and could make unauthenticated `/intro.html` behave
   differently from other console entries.

2. Validate at the router level rather than by changing the static server.

   The live probe showed `/intro.html` returns the app shell and assets
   successfully; the failure is the client-side route match. A React route test
   is therefore the smallest regression guard.

## Risks / Trade-offs

- [Risk] Login redirects first return to `/intro.html` and then redirect to
  `/`. Mitigation: use `replace` so browser history ends at the canonical home
  route after authentication.
- [Risk] A future static server may stop serving the SPA shell for
  `/intro.html`. Mitigation: deployment verification should include a direct
  `/intro.html` browser load after the static release.

## Migration Plan

Ship as a console-only static release. Rollback is replacing the deployed
console bundle with the previous static backup; cloud runtime and database
state are unaffected.
