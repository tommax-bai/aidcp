## 1. 发布通道与打包前置

- [ ] 1.1 确认 `edge-installer-oss-distribution` 的 OSS 静态分发契约已可复用；若尚未落地，记录并协调其完成顺序，避免在本 change 中创建冲突的下载对象布局。
  <!-- Blocked 2026-07-13: `edge-installer-oss-distribution` 仍只有 OpenSpec 工件；`https://aidcp.oss-cn-beijing.aliyuncs.com/updates/ol/stable/latest-mac.yml` 匿名读取为 403。以下实现沿用提案中的 `updates/ol/stable` 布局，但不会执行发布或声称可复用，直到该访问闸真正完成。 -->
- [x] 1.2 在 `aidcp-edge` 增加 `electron-updater` 生产依赖，并为 OL macOS 构建加入固定的 generic HTTPS 更新配置与 `aidcpUpdateChannel=ol` 打包元数据；dev/custom/Windows 构建不注入该配置。
  <!-- aidcp-edge d98db6e: generic HTTPS provider and baked OL-only metadata; runtime cloud selection is intentionally excluded. -->
- [x] 1.3 调整 macOS 签名公证构建及 GitHub Actions 交付，保留 x64/arm64 dmg、zip、zip blockmap、`latest-mac.yml` 与应用内 `app-update.yml`；任何签名、公证或更新 metadata 缺失必须使构建失败。
  <!-- aidcp-edge d98db6e: CI retains the complete artifact set; signed build runs a fail-closed packaged metadata/manifest verifier. No installer was built in this change. -->
- [x] 1.4 为打包配置添加自动化断言：OL 包的版本、更新地址、通道、`latest-mac.yml` 文件清单和双架构 zip/blockmap 一致；非 OL 包不携带 OL 更新配置。
  <!-- aidcp-edge d98db6e: unit/packaging contracts plus the build-time artifact verifier. -->

## 2. OL 客户端更新行为

- [x] 2.1 在 `aidcp-edge` 主进程实现可注入、可测试的 macOS 更新服务，仅在已打包且烘焙 OL 更新元数据完整有效时初始化。
  <!-- aidcp-edge d98db6e: `auto-update.cjs` is injected/tested and is disabled outside packaged macOS OL metadata. -->
- [x] 2.2 在主窗口可用（并通过已有客户登录门时）延迟发起首次检查，并实现不高于六小时一次的后续检查、无更新静默和失败的本机诊断日志。
  <!-- aidcp-edge d98db6e: initial 15-second delay, six-hour interval, and local updater logs. -->
- [x] 2.3 实现中文更新提示、用户确认下载、下载进度/失败、更新已就绪和“稍后”状态；禁止未确认的自动下载或自动重启。
  <!-- aidcp-edge d98db6e: `autoDownload=false`; dialogs control download and restart. -->
- [x] 2.4 将现有优雅退出逻辑拆为可 await 的“仅停止全部 edge 子进程”函数；更新安装前显示影响并二次确认，全部子进程确认退出后才调用 `quitAndInstall()`，停机超时/失败则取消安装并如实提示。
  <!-- aidcp-edge d98db6e: shared bounded `stopAllEdgeChildren` gate prevents updater restart while a child remains. -->
- [x] 2.5 为更新通道选择、检查节流、用户取消、下载错误、已有运行任务、安全停机成功和停机失败补充 Electron 单元/契约测试。
  <!-- aidcp-edge d98db6e: focused updater and lifecycle contracts run under the full edge suite. -->

## 3. OL 更新发布与提升

- [x] 3.1 扩展或新增受控发版机脚本：下载 CI 的完整 macOS artifact 集，验证版本、sha512、Developer ID 签名、公证、包内 OL 配置和 manifest 文件引用，不打印任何敏感凭据。
  <!-- aidcp 2bd1b95: `scripts/promote-ol-auto-update` defaults to this read-only preflight and never prints OSS credentials. -->
- [ ] 3.2 使用发版机本地 `ossutil` 将候选文件上传到版本化 OL staging 路径；逐项以匿名 HTTPS 验证状态、长度与缓存头，并在提升前验证 manifest 与实际文件的 sha512 对齐。
  <!-- Blocked 2026-07-13: the guarded staging/public-validation implementation exists, but no `--yes` run is authorized while the configured public update prefix returns 403. -->
- [ ] 3.3 实现 promotion：先让所有带版本号文件可用，最后更新 stable `latest-mac.yml`；manifest 设重新验证缓存、版本文件设 immutable 缓存；任一闸失败必须保留旧 manifest 并以非零退出。
  <!-- Blocked 2026-07-13: script implementation is ready, but an end-to-end promotion cannot be validated until anonymous HTTPS works; old manifest remains untouched. -->
- [x] 3.4 更新桌面发版文档，明确首次 bootstrap 包仍需手动安装、已安装的高版本不能自动降级、问题版本须发布更高修复版，以及 Windows 自动更新仍不在范围内。
  <!-- aidcp-edge d98db6e and aidcp 2bd1b95: release checklists distinguish manual bootstrap, prompt-only OL mac updates, higher-version remediation, and Windows exclusion. -->

## 4. 集成验证与 OL 发布

- [x] 4.1 在 edge owning worktree 运行相关 Electron 测试、`npm test`、`npm run test:acceptance`（如适用）和 `npm run typecheck`；在控制仓运行 `openspec validate ol-client-auto-update --strict`。
  <!-- 2026-07-13: edge `npm test`, `npm run test:acceptance`, and `npm run typecheck` passed; control strict validation passed after this task update. -->
- [ ] 4.2 用独立 HTTPS staging 更新前缀做已安装包升级验收：分别从旧版升级到新 OL 包的 arm64 与 x64 macOS，覆盖无运行环境、运行环境确认停机、下载失败和坏 manifest 四种结果。
  <!-- Blocked: requires a signed OL package and anonymously readable staging prefix; neither is produced while the OSS 403 gate remains. -->
- [ ] 4.3 从干净的 OL release branch 构建签名公证 bootstrap 包，发布同版本手动 dmg 与 stable manifest；验证公开更新 URL、包签名、公证、manifest sha512 和客户端显示的版本一致。
  <!-- Pending after 1.1 / 3.2 / 3.3: no release branch, signed package, OSS write, or OL deployment was performed in this implementation pass. -->
- [ ] 4.4 将真机验收结果、发布对象版本、回退/修复决策和 commit SHA 回写本 change；全部完成后运行严格验证、归档 change。
  <!-- Pending real release and dual-architecture installed-client acceptance; this change must not be archived yet. -->
