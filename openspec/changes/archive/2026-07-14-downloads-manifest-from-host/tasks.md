# Tasks

## 1. aidcp-cloud — downloads 清单端点

- [x] 1.1 新增 `src/panel/downloads-manifest.ts`：扫目录 → 解析文件名（`AIDCP-<ver>-arm64.dmg` / `AIDCP-<ver>.dmg` / `AIDCP Setup <ver>.exe`）→ 过滤非发布文件（`.bak-*` / 隐藏 / 非 dmg·exe）→ 同平台取最高语义版本 → 返回清单 <!-- aidcp-cloud 38f3082 -->
- [x] 1.2 纯函数可单测（目录内容作为入参），I/O 薄壳分离；目录路径读 `AIDCP_DOWNLOADS_DIR`，默认 `/opt/aidcp/downloads` <!-- aidcp-cloud 38f3082 -->
- [x] 1.3 `panel-server.ts` 挂 `GET /api/downloads`（受既有面板鉴权，与其他 `/api` 同）；目录不可读 / 空 / 无可识别包 → 诚实返回空清单（**不 500、不编造**） <!-- aidcp-cloud 38f3082 -->
- [x] 1.4 单测：解析 / 取最高版本 / 忽略 .bak / 空目录 / 目录不存在 <!-- aidcp-cloud 38f3082 -->

## 2. aidcp-console — 去掉硬编码版本

- [x] 2.1 `src/config/downloads.ts`：删除硬编码 `version` / `items`，只保留 URL 拼接与类型 <!-- aidcp-console aa3461d -->
- [x] 2.2 `src/api/`：加 `fetchDownloads()` <!-- aidcp-console aa3461d -->
- [x] 2.3 `AppShell.tsx`：下载菜单改为消费 API；加载中 / 空 / 失败 → 「暂无可用安装包」，**绝不回落写死版本** <!-- aidcp-console aa3461d -->
- [x] 2.4 单测：有包 → 渲染真实条目与版本；空 / 失败 → 空态，且 DOM 里没有任何下载链接 <!-- aidcp-console aa3461d -->

## 3. 验证与部署

- [x] 3.1 cloud：`npm test` + `test:acceptance` + `typecheck` <!-- aidcp-cloud 38f3082 -->
- [x] 3.2 console：`npm test` + `typecheck` + `build` <!-- aidcp-console aa3461d -->
- [x] 3.3 部署 dev（cloud `38f3082` + console `aa3461d`）：cloud 备份→干净快照 rsync→restart→active；console 备份（留最近 10 个 tar）→**不带 `--delete`** rsync→nginx :8088 index=200、`/api/downloads` 经反代 401（受鉴权，符合预期）。**端到端实证**：在 ECS 上对 dev 真实目录跑 `readDownloadsManifest()` → `{version:"0.3.18", items:[mac-arm64 0.3.18, mac-x64 0.3.18, win-x64 0.3.5]}`——正是 dev 目录里真实存在的包，`.bak` 与历史版本全部正确忽略 <!-- 2026-07-14 deployed -->
- [x] 3.4 记录：console 的两条「工件指针」搁浅提交（`7a1b718` / `88ce4c8`）**自动作废**——下载页版本不再是源码，无物可回流。`e5a4d1d`（edge `package.json` 版本）**不作废**：那是构建版本、合法地属于源码；纪律不变（出包前先抬版本，且必须严格高于已分发的 0.3.20 → 下次出包用 **≥0.3.21**） <!-- 2026-07-14 -->

## 4. 发版链路收口（本 change 内必做——不做就是坏的）

- [x] 4.1 `scripts/release-desktop-macos`：删掉「改 console 源码版本号 → 构建 console → 部署 console → 提交 downloads.ts」四步。**这不是可选清理**——脚本原第 217 行 `grep -q "version: '$VER'" "$DL_TS" || die` 会因为那个常量已不存在而**直接 die**，发版链路当场是坏的。现在交付 = 下载 → 静态校验 → 传包 → 验活；`bash -n` + `--help` 已验 <!-- aidcp (本 change) -->
- [x] 4.2 `aidcp-edge/docs/release-desktop.md`：§0 事实、§4/§5 两节改写为「已删除」并说明为什么，末尾指针指向新的清单来源 <!-- aidcp-edge -->
- [x] 4.3 OL 部署需用户明确要求（§5 铁律），故不在本 change 执行；已解耦登记到真机 backlog **簇 65.2**——同一份代码部署到 OL 后下载页应自动显示 0.3.20，这是本 change 核心主张「两台机器各说各的真话」的最终验收。 <!-- 2026-07-14 backlog 簇65 -->
