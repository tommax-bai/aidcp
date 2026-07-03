# Tasks — edge-installer-oss-distribution

> 本 change 以基础设施 + 配置为主、代码改动小。标 **[需用户操作]** 的项需在阿里云控制台/发版机完成（我无凭据、代不了）。真机点击验收按项目惯例解耦到 `docs/real-machine-acceptance-backlog.md`。

## 1. 阿里云 OSS 资源准备（基础设施，非代码）

- [x] 1.1 桶 `aidcp` 已建（`oss-cn-beijing`，公读，与配图 change 共用；安装包用 `downloads/` 前缀）<!-- 用户已在阿里云控制台建好 -->
- [ ] 1.2 ~~子账号~~ 按属主决定不做子账号；发版机 `ossutil config` 用现有主账号 AK；AK 绝不进仓/日志/commit、**绝不进 CI**
- [ ] 1.3 **[需用户操作]** 用 `ossutil cp`（或 OSS 网页控制台拖拽）把当前 `0.2.0` 三平台安装包上传到 `oss://aidcp/downloads/0.2.0/`，逐对象设对 `Content-Type`（dmg=application/x-apple-diskimage、exe=application/octet-stream）+ `Content-Disposition: attachment`
- [ ] 1.4 定 console 的 `base` 前缀 = `https://aidcp.oss-cn-beijing.aliyuncs.com/downloads/0.2.0`（CDN/自有域名待 ICP 备案后再换）

## 2. aidcp-console — 下载 URL 契约切到 OSS

- [ ] 2.1 改 `src/config/downloads.ts` 的 `EDGE_DOWNLOAD.base` 从 `'/downloads'` 改为 `https://aidcp.oss-cn-beijing.aliyuncs.com/downloads/0.2.0`；`version`/`items` 文件名与桶内对象逐字对齐
- [ ] 2.2 确认 `edgeDownloadUrl()` 的 `encodeURIComponent(file)` 逻辑与调用点**未改动**（空格文件名 `AIDCP Setup 0.2.0.exe` 由既有转义处理）
- [ ] 2.3 更新 `src/config/downloads.ts` 顶部注释里的发版步骤（rsync-to-ECS → 上传 OSS + 校验闸），保持文档与实现一致
- [ ] 2.4 `npm run build` + `npm run typecheck` 通过

## 3. 发版后对象存在性校验闸（落实红线「绝不静默假成功」）

- [ ] 3.1 提供发版校验步骤/脚本：对桶内该版本三平台对象逐一匿名 `HEAD`，要求 `200` + 非零 `Content-Length`；任一未命中即非零退出、如实报出未命中对象键（可用 `curl -sI` 或 `ossutil stat`，成败反映退出码、不 `|| true` 吞错）
- [ ] 3.2 把「先跑校验闸通过 → 再切 `version` → 再部署 console」的顺序写进发版文档，明确校验未过 MUST NOT 切版本/部署

## 4. aidcp-edge — 发版流程与文档

- [ ] 4.1 更新 `docs/release-desktop.md`：上传目的地从 `rsync` 到 ECS `/opt/aidcp/downloads/` 改为 `ossutil cp ... --acl public-read` 到 `oss://aidcp/downloads/<version>/`，并串接第 3 节校验闸
- [ ] 4.2 **[可选，可后置]** `.github/workflows/build-desktop.yml` 的 `upload-artifact` 后加一步 `ossutil`/`ali-oss` 直传 OSS（AK 走 GitHub Secrets），上传成败如实反映退出码、不 `|| true`；GitHub artifact 仍保留 14 天做审计/回退。倾向先手动跑通再自动化

## 5. 部署与验证

- [ ] 5.1 承 console 部署纪律部署新 console（rsync 到 `/opt/aidcp/console`、**绝不 `--delete`**，混着非构建 `intro.*` 文件）
- [ ] 5.2 部署后 healthcheck：console 站点可访问、下载区渲染正常
- [ ] 5.3 **[真机验收 → backlog]** 在 `docs/real-machine-acceptance-backlog.md` 登记：真机点击 mac-arm64 / mac-x64 / win-x64 三个下载按钮各验一次可匿名下载、文件名正确、浏览器触发下载
- [ ] 5.4 全程确认**未触碰同机 isales**（服务/目录/端口）

## 6. 灰度回退收尾（稳定一版后另起提交）

- [ ] 6.1 OSS 分发稳定一个版本周期后，摘除 ECS `aidcp-console.conf` 的 `location /downloads/` 与 `/opt/aidcp/downloads/` 目录（回退窗口关闭前保留）
- [ ] 6.2 记录回退手册：`base` 改回 `'/downloads'` + 重构建部署 console 即回退（ECS 旧包在灰度期仍在）

## 7. 归档前

- [ ] 7.1 `openspec validate edge-installer-oss-distribution --strict` 通过
- [ ] 7.2 全部 task 标 `[x]` 并附 commit-sha/偏离说明（格式 `<!-- <repo> <sha> 备注 -->`；部署后追 `<!-- <date> deployed -->`）
- [ ] 7.3 archive 该 change
