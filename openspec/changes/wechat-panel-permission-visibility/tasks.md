## 1. Contract and Cloud

- [x] 1.1 Add the read-only six-permission catalog and effective panel-user intersection.
- [x] 1.2 Add JWT-protected `GET /api/config/interaction-permissions` without mutation routes or sensitive fields.
- [x] 1.3 Add focused Cloud unit and panel API tests, and bump the panel API version if required.

<!-- Cloud implementation: aidcp-cloud commit 9c1ab4a. The overview intersects parsed panel users with parsed grants, returns six fixed definitions, filters stale actors and exposes GET only after panel JWT. Focused panel regression passed 31/31; full Windows-safe batched suite passed 2494 with eight environment-gated skips; typecheck passed. -->

## 2. Console

- [x] 2.1 Add aligned API types and a query for the permission overview.
- [x] 2.2 Add a read-only Video Channels permission card to Settings with independent loading/error/empty states.
- [x] 2.3 Add focused Settings page tests for all six permissions, descriptions, users and the absence of editing controls.

<!-- Console implementation: aidcp-console commit 78c9153. Focused Settings tests passed 3/3, full suite exited 0, typecheck and production build passed. Browser rendering at 1440x1000 and 820x720 showed all six rows, user/empty states, no horizontal overflow and no permission mutation controls. -->

## 3. Validation and delivery

- [x] 3.1 Run focused tests and typecheck in Cloud and Console.
- [x] 3.2 Run `openspec validate wechat-panel-permission-visibility --strict` and record evidence.
- [x] 3.3 Rebase, fast-forward integrate and push Cloud, Console and control default branches without force; deploy Cloud and Console to dev through documented target checks.

<!-- Delivery (2026-07-18): Cloud was rebased, tested, fast-forward pushed and landed as master df151f21cc1b07853389c34f437eecdcfe1287e8. Console was rebased, passed its full suite/typecheck, fast-forward pushed and landed as master 78c9153352444fc71f808c6f1609216e24963aaf; its production build emitted assets/index-CpAL4WaN.js. `scripts/deploy-target dev --check` selected 121.89.85.150. Remote backups are `/opt/aidcp/backups/cloud.bak.20260718-210310.tar.gz`, `/opt/aidcp/backups/cloud.env.bak.20260718-210310`, and `/opt/aidcp/backups/console.bak.20260718-210310.tar.gz`; `.env` remained byte-identical. Only `aidcp-cloud.service` was restarted. It is active with NRestarts=0, ports 8787/8090/8088 listen, panel health is ok, PostgreSQL returned 1, Feishu WS reported ready, the unauthenticated new endpoint returned 401, and all four colocated isales services remained active. -->
