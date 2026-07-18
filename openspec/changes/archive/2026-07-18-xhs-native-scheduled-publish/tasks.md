## 1. 协议与存储基础

- [x] 1.1 同步扩展 cloud/edge `PublishCommandKind`、参数与结果注释，更新 `docs/protocol.md`，保持 MessageType 数量与通用 command 映射不变
- [x] 1.2 新增 additive migration 与 `PublishLogStore` 字段/状态/索引，提供 scheduled 落库、到期扫描、退避更新和原子公开确认方法
- [x] 1.3 扩展 panel projection、delegated candidate snapshot/patch 与草稿 CAS，权威校验小红书 1h–14d 时间窗并保证版本闸

## 2. Edge 原生定时执行与对账

- [x] 2.1 用专用 CDP handler 实现 `set_schedule`：北京时间格式化、开启控件、写值、三项正证据校验，失败关闭
- [x] 2.2 让 `submit_publish` 按已验证模式精确选择“发布”或“定时发布”，并保留 submitDispatched/提交窗口语义
- [x] 2.3 实现 `capture_scheduled` 与 `reconcile_scheduled` 的笔记管理导航、唯一匹配、内部 id/公开 id+URL 分离及真实错误分类
- [x] 2.4 增加 edge 聚焦/验收测试，覆盖时间边界、假定时文案不通过、按钮分流、无歧义匹配与不得伪造 URL

## 3. Cloud 编排与到期对账

- [x] 3.1 修改 command plan/sequencer：内容后设定时、`set_schedule` fail-fast、定时使用 `capture_scheduled`、输出 `scheduled_pending`
- [x] 3.2 修改 dispatcher：scheduled 落库不计数；立即发布保持既有 submitted/published 语义
- [x] 3.3 增加有界 `ScheduledPublishReconciler`，复用 edge task lease/账号绑定，成功原子转 published 后只记一次，未公开退避、耗尽 needs_review
- [x] 3.4 在 server 生命周期中装配/停止 reconciler，并扩展 companion/panel 状态的 null-safe 处理
- [x] 3.5 增加 cloud store/sequencer/dispatcher/reconciler/delegated/panel 单测与 AC-PUB/AC-PROTO/AC-RISK 验收

## 4. Console 定时编辑

- [x] 4.1 扩展 `PanelPublish` 类型和状态标签，诚实展示 scheduled 与目标北京时间
- [x] 4.2 在待审详情按“标题/正文/话题/其它选项 → 定时设置 → 批准”排布发布方式与 datetime-local 控件
- [x] 4.3 将模式/时间变化纳入 modify_candidate 补丁与未保存判断，前端提示范围但以 cloud 校验为权威
- [x] 4.4 增加前端测试并运行 lint/typecheck/build

## 5. 验证、文档与交付

- [x] 5.1 更新 `docs/architecture.md` 与 `docs/risk-control.md`，明确 scheduled 不计数、确认公开后恰记一次
- [x] 5.2 edge/cloud 依次运行聚焦测试、`test:acceptance`、全量测试、typecheck；console 运行项目规定的 lint/test/typecheck/build
- [x] 5.3 用「工程师大白」在 dev 做一条受控定时探针，确认平台定时列表、cloud scheduled 与零计数后取消测试稿并停止 profile
- [x] 5.4 `openspec validate xhs-native-scheduled-publish --strict`，回写各仓 commit/测试/偏差证据
- [x] 5.5 串行 land edge/cloud/console，推送默认分支并按规范部署 dev；验证健康、协议与定时对账扫描不影响其它账号

<!-- evidence 2026-07-18:
- edge `fa490bd53c291d49a09c774d36e9353cdebb2cf5`: focused 51/51, acceptance 24/24, typecheck and build:dist passed; full 1760/1761, with only the pre-existing Windows POSIX-mode assertion (`customer-auth-security.test.ts`, 0666 vs 0600) failing.
- cloud `993322480e2f5a59e78ebac81f405ea8e51b0961`: scheduled focus 114/114, acceptance 56/56, typecheck/build passed; because the repository glob script is not Windows-safe, all 277 test files were enumerated in 18 bounded tsx groups and all groups passed.
- console `9b14f8c30427f0d85212a20aaaddeaa7da598798`: ContentPage focus 26/26, full test/typecheck/build passed; this repository has no lint script. Vite emitted only the existing chunk-size warning.
- protocol evidence: edge/cloud committed `src/comm/protocol.ts` blobs are identical (`5bf71ff6878dce925d85e87a4ff6cf8cc7a0c0f2`); MessageType remains 91.
- task 5.3 platform probe: production edge sequence on verified 工程师大白 account `63e2ff0500000000260049ce` scheduled `定时探针07181815`, captured internal id `6a5b5231000000000100fefe` with no public post id/link, then deleted it. Manager count returned 38→37, no `定时探针*` remained, and AdsPower profile `k1e0ero8` was stopped (`Inactive`).
- task 5.3 dev completion: deployed `PublishLogStore.markScheduled` transitioned temporary record 128 to `scheduled`, kept `platform_post_id=NULL`, stored a separate internal id, and left the verified account's publish risk count at `0→0`; the probe row was deleted in `finally` and cleanup count was 0. This complements the platform probe without issuing a second public-platform write.
- task 5.5 land/deploy: edge/cloud/console `master` and `origin/master` point to the SHAs above; the three feature worktrees were removed normally. Dev backups are `/opt/aidcp/cloud.bak.20260718-182920.tar.gz`, `/opt/aidcp/cloud/.env.bak.20260718-182920`, and `/opt/aidcp/console.bak.20260718-182920.tar.gz`. Dev health passed: service active with `NRestarts=0`, listeners 8787/8090/5432, panel health and public console HTTP 200, PostgreSQL `select 1`, five scheduled columns + partial due index + expanded status constraint, Feishu WS onReady, and unrelated `isales-scheduler.service` remained active. There were no `scheduled` rows for the scanner to claim and no reconciler error log.
- deployed content hashes match canonical master: protocol `2509846896498f8a50e94527b749dfb2bb89d58d908a3943daec7853f75cae1e`, console index `d5ac5cd6e6f8963770e6594f2ee6caea6040e403a9ce9340b428b8de86d0da8c`, console JS `dfc9f750c7c06245bd14d7d03cdbe3d7ba2ac32350e9ec38eac340e9077a80a6`.
- deploy preflight deviation: Git Bash mounts NTFS with `noacl` and therefore reports the key as synthetic mode 0644 even after chmod; Windows `icacls` showed only the current user had read/write access. Target (`dev`), host, key path, and effective ACL were manually verified before SSH.
-->
