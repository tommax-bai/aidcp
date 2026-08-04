## 1. Deployment script repair

- [x] 1.1 Brace every deployment-script variable that is immediately followed by non-ASCII text.
- [x] 1.2 Add a focused source contract test for hazardous unbraced localized expansions.

<!-- Evidence: aidcp-cloud b4694df fixes all six matching expansions and adds the lexical regression test. No topology or fallback behavior changed. -->

## 2. Validation and delivery

- [x] 2.1 Run the focused test, Bash syntax check, Cloud typecheck, and strict OpenSpec validation.
- [x] 2.2 Commit, rebase, fast-forward integrate, and push Cloud and control changes.
- [ ] 2.3 Deploy the integrated Cloud default branch to DEV with the three-process script and verify content, automation, API, ports, schema, PostgreSQL, Feishu, and unrelated-service isolation.
  <!-- 2026-08-02 现状订正：2.3 仍未执行、未勾选；本轮只做 DEV 只读 SSH 核验，未部署、写文件、改库或操作 systemd unit，未碰 OL。 -->
  <!-- ⚠️ 2026-08-04 15:20 外部订正（由 change defer-transient-publish-predispatch-failures 的部署撞到）：
       **下面这段「三个 unit 都从 /opt/aidcp/cloud 启动」的描述已经不成立了。** 它描述的是本脚本的形态；
       但同日 change `deploy-derived-services-to-dev` 在 dev 上完成了切换，现网三个 unit 的
       WorkingDirectory 实测分别是 /opt/aidcp/api、/opt/aidcp/automation、/opt/aidcp/content，
       各自跑各自派生仓的入口（api-service-entry.ts / server.ts / content-service-entry.ts），
       单体 `aidcp-cloud.service` 已 inactive。
       **危害是假部署**：照下面这段操作 = rsync 到无人运行的目录 + 重启一个已停用的服务 + 以为部署成功。
       本段保留只为追溯本脚本自身的设计意图；**MUST NOT 当作 dev 现状引用**。
       dev 现状口径以 `docs/deployment-environments.md` 的「dev 与 ol 的运行形态已经不一样了」一节为准。 -->
  - **撤销旧阻塞归因**（**该描述已过期，见上方订正**）：本脚本同步并运行同一份 `aidcp-cloud`，三个 unit 都从
    `/opt/aidcp/cloud/src/server.ts` 以不同 `AIDCP_SERVICE` 启动；它不会执行 sibling
    `aidcp-api/src/server.ts`。后者的存储接线欠账属于 `split-cloud-automation-production-runtime`
    task 3.1e，且已在该 change 内补齐；无论其当时状态如何，都不是本脚本的可执行入口。
  - **本地前置证据**：Cloud `e7209bf` 用 fake pool/store 和随机端口覆盖真实生产装配 seam：
    API owner source → internal HTTP route → automation client 可读取 `facebook_operation_policy`。
    刷新失败按当前契约返回 HTTP 200 error envelope，再由客户端抛 `InternalHttpError`，不是
    literal HTTP 502。该用例只证明这条通道，不证明三进程整体可部署。
  - **当前真实组合根阻塞**：`AIDCP_SERVICE=api` 只跑 segA + segD、跳过 segC，但 segD 在
    `startPanelApi()` 前仍同步 `requireSegment(server, 'server', 'automation')`；`server` 只由 segC
    赋值，因此 API panel 启动必抛。该异常被非致命捕获，故 8091 / 8094 可以监听而 8090 缺失，
    与 2026-07-26 现场逐项一致。更深一层，独立 API 模式尚未启动 automation-owner 同步读
    consumer：`ApiSyncReadMirrors` 当前只在单体自举里构造。只把 `edgeServer` 改成可选会让端口
    表面起来，却仍没有 A3-A6 的真实镜像来源，不能作为修复。
  - **最小后续范围**：为独立 API 进程建立 automation-owner 同步读 consumer 生命周期，首轮
    拉取并 fail-closed 建立 A3-A6 镜像，再把 panel 的账号→edge 解析切到该镜像；保留单体的本地
    `edgeServer` 快路。验收须用随机端口跑真实 automation route → HTTP client/consumer →
    api-mode panel 组装，并断言不运行 segC 时 8090 仍能监听；源码正则不算运行证据。
  - 本轮 `deploy-target dev --check` 通过；§1 的单体启动问题已由
    Cloud `c0de08b` 修复。当前 DEV 是健康单体，但 `.deployed-commit` 缺失，不能声称确认了 deployed SHA；
    只读核验时两个相关运行文件的 sha256 与 `c0de08b` 一致、与当时的 source master `8773130`
    不一致；随后集成的 `e7209bf` 又只前移源码与本地回环证据，仍未部署。

<!-- Validation: focused deployment contract 1/1, bash syntax and lexical scans, Cloud typecheck, and strict OpenSpec validation passed. Cloud b4694df and control 1fdb1fd were rebased, fast-forward integrated, and pushed without force. DEV deployment remains pending. -->

<!-- DEV attempt 2026-07-26: the repaired script completed backup, source sync, dependency install, capability probe, unit install, content health, and automation :8787 health. API then started :8091/:8094 but refused panel :8090 with `composition_dependency_unavailable: server` because the panel still requires automation-owned composition state. The script failed closed and automatically restored the monolith; aidcp-cloud.service is active/enabled with NRestarts=0 and :8787/:8090/:8091, schema gates, PostgreSQL, writer lock, outbox worker, reconciler, and Feishu healthy. Task 2.3 remains open: source segmentation does not yet prove a deployable three-process runtime. -->
