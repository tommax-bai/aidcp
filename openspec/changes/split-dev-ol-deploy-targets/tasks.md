## 1. Target Contract And Docs

- [x] 1.1 Update control-repo deployment docs to define `dev` and `ol`, including IPs, SSH key paths, runtime directories, and the rule that every ECS operation must name a target.
  <!-- aidcp docs/deployment-environments.md added; README.md and AGENTS.md updated. -->
- [x] 1.2 Update `docs/parallel-dev-worktrees.md`, `openspec/project.md`, and related handoff/deployment references that currently state cloud only deploys to `121.89.85.150`.
  <!-- aidcp docs/parallel-dev-worktrees.md, openspec/project.md, docs/acceptance-tests.md, docs/projects-and-progress.md, docs/handoff-2026-06-05.md, CLAUDE.md, scripts docs updated; historical handoff command blocks remain as history with top-level warning. -->
- [x] 1.3 Add or update a small target metadata/preflight helper in `scripts/` so deployment commands can verify target name, IP, SSH key path, and key permissions before SSH/rsync.
  <!-- aidcp scripts/deploy-target added; bash -n passed; dev/ol --check passed after ol.pem chmod 600. -->
- [x] 1.4 Update sibling deployment docs in `aidcp-cloud`, `aidcp-console`, and `aidcp-edge` to show dev vs ol target selection and `AIDCP_CLOUD_URL` expectations.
  <!-- aidcp-cloud docs/deployment-ecs.md, aidcp-edge README.md, aidcp-console README.md and deploy/aidcp-console.conf updated. -->

## 2. Database Boundary And Security

- [x] 2.1 Record the chosen initial ol database mode in this change: dedicated ol PostgreSQL/RDS, or temporary bridge to dev PostgreSQL with an explicit expiration note.
  <!-- initial mode recorded as temporary ol -> dev PostgreSQL bridge for bootstrap/smoke only; not online-ready/final topology. Dedicated ol DB/RDS remains required before marking ol stable online. -->
- [x] 2.2 If temporary bridging to dev PostgreSQL is used, back up dev PostgreSQL config and restrict access away from `0.0.0.0/0` to local dev plus the ol source only.
  <!-- dev PG pg_hba.conf backed up to /var/lib/pgsql/data/pg_hba.conf.bak.aidcp-dev-ol-20260706-113512; aidcp broad 0.0.0.0/0 rule replaced with 123.56.253.183/32 plus existing 127.0.0.1/32; systemctl reload postgresql. No password/data/isales changes. -->
- [x] 2.3 Verify dev cloud still connects to PostgreSQL after the allowlist change and verify ol can connect only from the allowed source.
  <!-- dev local PGPASSWORD psql select 1 ok; aidcp-cloud active and panel /api/version ok; ol psql to dev PG select 1 ok using runtime password via stdin only, not recorded. ol cannot reach dev private 172.17.201.88:5432, so bridge uses public 123.56.253.183/32 allowlist. -->
- [x] 2.4 Decide whether to rotate the `aidcp` PostgreSQL password after the current broad exposure; stop for user confirmation before changing any password or `.env` secret.
  <!-- user decision 2026-07-06: do not rotate the dev aidcp PostgreSQL password now. No PostgreSQL role password was changed. -->
- [x] 2.5 If a dedicated ol database is chosen, create it and verify `aidcp-cloud` schema self-initialization against it before marking ol online-ready.
  <!-- dedicated ol DB/RDS was not chosen for this first rollout. ol remains on the temporary ol -> dev PostgreSQL bridge; this is not the final online-ready database topology. -->

## 3. Runtime Credentials And Feishu Boundary

- [x] 3.1 Create an ol runtime env inventory listing required key names only; do not record values in git, tasks, docs, logs, or command-line args.
  <!-- key-name-only inventory added to docs/deployment-environments.md; no values recorded. -->
- [x] 3.2 Decide whether ol uses a separate Feishu app/chat or starts with Feishu ingestion disabled; stop for user-provided credentials before enabling ol Feishu.
  <!-- decision: ol Feishu remains disabled/not enabled for real command traffic until target-specific credentials or explicit reuse approval are provided. -->
  <!-- update 2026-07-06: user provided target-specific ol Feishu app credentials; values were written only to ol /opt/aidcp/cloud/.env and were not recorded in git. -->
- [x] 3.3 Create `/opt/aidcp/cloud/.env` on ol atomically with target-local values, and verify `aidcp-cloud.service` loads it through `EnvironmentFile`.
  <!-- ol /opt/aidcp/cloud/.env created atomically with 600 root:root permissions; values were transferred over SSH without logging, PGHOST was set to 121.89.85.150 for the temporary bridge, and systemd shows EnvironmentFile=/opt/aidcp/cloud/.env. -->
- [x] 3.4 Verify dev and ol do not both process real Feishu command traffic unless a temporary duplicate-handler test is explicitly recorded.
  <!-- aidcp-cloud f4316def adds AIDCP_FEISHU_WS_ENABLED; dev remains default-enabled, while ol has AIDCP_FEISHU_WS_ENABLED=false and logs "飞书长连接已禁用", so ol does not receive real Feishu command events. -->
  <!-- update 2026-07-06: ol was moved to its own Feishu app credentials and AIDCP_FEISHU_WS_ENABLED=true; ol logs show "飞书事件接收已启动" and "WSClient onReady". dev remains active with its own default-enabled runtime. -->

## 4. Ol Bootstrap

- [x] 4.1 Install or verify ol prerequisites: Node.js 20/npm, rsync, nginx, curl, tar/gzip, and systemd availability.
  <!-- ol bootstrap 2026-07-06: installed from Alibaba Linux 4 repos: nodejs 22.22.0 (cloud engine is >=20), npm/npx 10.9.4, nginx 1.30.2, rsync 3.4.3, postgresql client 15.18; curl/tar/gzip/systemd already present. -->
- [x] 4.2 Create ol runtime layout: `/opt/aidcp/cloud`, `/opt/aidcp/console`, and optional `/opt/aidcp/downloads`.
  <!-- ol: created /opt/aidcp/{cloud,console,downloads}; console has temporary placeholder index.html until dist deploy. -->
- [x] 4.3 Install `aidcp-cloud.service` on ol with `WorkingDirectory=/opt/aidcp/cloud`, `EnvironmentFile=/opt/aidcp/cloud/.env`, and `ExecStart=/usr/bin/npx tsx src/server.ts`.
  <!-- ol: /etc/systemd/system/aidcp-cloud.service installed and daemon-reload done; service loaded inactive/disabled because .env and code are not deployed yet. -->
- [x] 4.4 Install ol nginx console routing so `/api` and `/ws` proxy to ol panel API on `127.0.0.1:8090` and static files serve from `/opt/aidcp/console`.
  <!-- ol: /etc/nginx/conf.d/aidcp-console.conf installed on :8088 only; nginx -t passed; nginx enabled/active; / returns placeholder 200, /api returns expected 502 until cloud panel starts. -->
- [x] 4.5 Configure ol firewall/security-group expectations for SSH, cloud WS `8787`, console HTTP, and PostgreSQL only as required by the chosen database mode.
  <!-- user opened Aliyun security group TCP 8088 and 8787 for ol; external curl http://123.56.253.183:8088/ returns console HTML and nc to 123.56.253.183:8787 succeeds. 80/443 remain deferred until domain strategy is set. PostgreSQL is not exposed on ol for this bridge. -->

## 5. Release And Deployment Flow

- [x] 5.1 Define the release source rule for ol: release branch only; reject dirty worktree deployments and direct tag/raw-SHA deployments.
  <!-- documented in docs/deployment-environments.md, AGENTS.md, CLAUDE.md, scripts/README.md, docs/parallel-dev-worktrees.md. -->
  <!-- update 2026-07-06: user set OL policy to explicit-request-only and branch-based; tags/SHAs can seed the release branch but are not the deployed ref. -->
- [x] 5.2 Add dev deployment notes that allow high-frequency default-branch deployment after validation.
  <!-- documented in docs/deployment-environments.md and related control docs. -->
  <!-- update 2026-07-06: user set DEV as the default automatic deployment target after completed production-facing development. -->
- [x] 5.3 For cloud/console API-shape changes, document that ol promotion deploys cloud and console SHAs together and verifies `/api/version`.
  <!-- documented in docs/deployment-environments.md and tasks release notes requirement. -->
- [x] 5.4 Update edge release/operator docs so dev clients point at `ws://121.89.85.150:8787` and ol clients point at `ws://123.56.253.183:8787` or the future ol domain.
  <!-- aidcp-edge README.md and aidcp docs/deployment-environments.md updated. -->

## 6. First Ol Deployment And Validation

- [x] 6.1 From clean release-eligible checkouts, deploy committed cloud files to ol with `.env`, `node_modules`, and `.git` excluded.
  <!-- cloud deployed to ol from committed clean archive SHA f4316defd20eb0526d5e5ba578cd8e6e60766d15 via rsync; .env, node_modules, and .git excluded. -->
- [x] 6.2 Install cloud dependencies on ol and start/restart `aidcp-cloud.service`.
  <!-- ol: npm ci --no-audit --no-fund completed; aidcp-cloud.service enabled and active. -->
- [x] 6.3 Build console from the matching release source and deploy `dist/` to `/opt/aidcp/console` on ol.
  <!-- console built from clean archive SHA be0f9e5ac9764b0156811df8aa43cc20431973c8 using npm install --no-package-lock because package-lock.json is not tracked; dist/ deployed to /opt/aidcp/console. -->
- [x] 6.4 Run ol health checks: `aidcp-cloud.service` active, `8787` listening, panel API local `8090`, console HTTP response, configured PostgreSQL `select 1`, and Feishu readiness if enabled.
  <!-- ol health 2026-07-06: service active; ss shows 0.0.0.0:8787, 127.0.0.1:8090, 0.0.0.0:8088; local and nginx /api/version return panelApiVersion=2; external http://123.56.253.183:8088/ returns console HTML; PG select 1 ok; Feishu receiver intentionally disabled on ol. -->
  <!-- update 2026-07-06: after ol Feishu credential rotation, service active; ss shows 0.0.0.0:8787, 127.0.0.1:8090, 0.0.0.0:8088; local/nginx /api/version ok; PG select 1 ok; Feishu WS onReady ok. -->
- [x] 6.5 Record deployed cloud/console/edge SHAs, database mode, validation results, and any temporary bridge/Feishu limitations in this tasks file.
  <!-- deployed cloud SHA f4316defd20eb0526d5e5ba578cd8e6e60766d15; deployed console SHA be0f9e5ac9764b0156811df8aa43cc20431973c8; edge not deployed in this step, current local edge HEAD cd51b0707b11892972dfbf6caaefd4a174c7d308. Database mode remains temporary ol -> dev PostgreSQL bridge. Feishu app credentials may be shared, but ol has AIDCP_FEISHU_WS_ENABLED=false so dev is the only real Feishu event consumer. Validations: cloud npm test/test:acceptance/typecheck passed; console build passed; console full vitest passed with --testTimeout=20000 after default 5000ms timeout run exposed slow jsdom tests. -->
  <!-- update 2026-07-06: Feishu limitation changed from shared-app disabled receiver to target-specific ol app enabled receiver. Database mode remains temporary ol -> dev PostgreSQL bridge, so ol is still not final online-ready until a dedicated ol DB/RDS exists. -->

## 7. Validation And Closeout

- [x] 7.1 Run `openspec validate split-dev-ol-deploy-targets --strict`.
  <!-- passed on 2026-07-06 after ol deployment validation; control git diff --check and script bash/preflight checks also passed. -->
  <!-- update 2026-07-06: passed again after DEV-default automatic deployment and explicit OL release-branch policy update. -->
- [x] 7.2 Commit and push docs/script changes after validation passes.
  <!-- pushed on 2026-07-06: aidcp main a6d62f4 Define split dev ol deployment targets; aidcp-cloud master f4316def Add Feishu WS toggle for split deploy targets; aidcp-console master 76231fa Document split dev ol console deployment; aidcp-edge master bc2af14 Document split dev ol edge targets. -->
- [ ] 7.3 Archive the change only after ol deployment policy is implemented, required validation passes, and any temporary bridge status is explicitly recorded.
