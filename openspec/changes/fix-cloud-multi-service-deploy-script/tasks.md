## 1. Deployment script repair

- [x] 1.1 Brace every deployment-script variable that is immediately followed by non-ASCII text.
- [x] 1.2 Add a focused source contract test for hazardous unbraced localized expansions.

<!-- Evidence: aidcp-cloud b4694df fixes all six matching expansions and adds the lexical regression test. No topology or fallback behavior changed. -->

## 2. Validation and delivery

- [x] 2.1 Run the focused test, Bash syntax check, Cloud typecheck, and strict OpenSpec validation.
- [x] 2.2 Commit, rebase, fast-forward integrate, and push Cloud and control changes.
- [ ] 2.3 Deploy the integrated Cloud default branch to DEV with the three-process script and verify content, automation, API, ports, schema, PostgreSQL, Feishu, and unrelated-service isolation.
  <!-- 2026-08-02 现状订正：2.3 仍未执行、未勾选；本轮只做 DEV 只读 SSH 核验，未部署、写文件、改库或操作 systemd unit，未碰 OL。 -->
  - **撤销旧阻塞归因**：本脚本同步并运行同一份 `aidcp-cloud`，三个 unit 都从
    `/opt/aidcp/cloud/src/server.ts` 以不同 `AIDCP_SERVICE` 启动；它不会执行 sibling
    `aidcp-api/src/server.ts`。后者的存储接线欠账属于 `split-cloud-automation-production-runtime`
    task 3.1e，且已在该 change 内补齐；无论其当时状态如何，都不是本脚本的可执行入口。
  - **本地前置证据**：Cloud `e7209bf` 用 fake pool/store 和随机端口覆盖真实生产装配 seam：
    API owner source → internal HTTP route → automation client 可读取 `facebook_operation_policy`。
    刷新失败按当前契约返回 HTTP 200 error envelope，再由客户端抛 `InternalHttpError`，不是
    literal HTTP 502。该用例只证明这条通道，不证明三进程整体可部署。
  - 本轮 `deploy-target dev --check` 通过；§1 的单体启动问题已由
    Cloud `c0de08b` 修复。当前 DEV 是健康单体，但 `.deployed-commit` 缺失，不能声称确认了 deployed SHA；
    只读核验时两个相关运行文件的 sha256 与 `c0de08b` 一致、与当时的 source master `8773130`
    不一致；随后集成的 `e7209bf` 又只前移源码与本地回环证据，仍未部署。

<!-- Validation: focused deployment contract 1/1, bash syntax and lexical scans, Cloud typecheck, and strict OpenSpec validation passed. Cloud b4694df and control 1fdb1fd were rebased, fast-forward integrated, and pushed without force. DEV deployment remains pending. -->

<!-- DEV attempt 2026-07-26: the repaired script completed backup, source sync, dependency install, capability probe, unit install, content health, and automation :8787 health. API then started :8091/:8094 but refused panel :8090 with `composition_dependency_unavailable: server` because the panel still requires automation-owned composition state. The script failed closed and automatically restored the monolith; aidcp-cloud.service is active/enabled with NRestarts=0 and :8787/:8090/:8091, schema gates, PostgreSQL, writer lock, outbox worker, reconciler, and Feishu healthy. Task 2.3 remains open: source segmentation does not yet prove a deployable three-process runtime. -->
