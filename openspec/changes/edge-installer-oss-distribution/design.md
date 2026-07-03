## Context

edge 桌面客户端安装包当前的公网托管链路：发版时在 edge 仓 `npm run electron:build:*` 出包 → `rsync` 到 ECS `121.89.85.150:/opt/aidcp/downloads/` → 手改 `aidcp-console/src/config/downloads.ts` 的 `version` + 三平台文件名 → 重构建部署 console。Nginx（`aidcp-console/deploy/aidcp-console.conf`）以 `location /downloads/ { alias /opt/aidcp/downloads/; autoindex on; }` 对外，前端「下载客户端」按钮经 `edgeDownloadUrl(file)` 拼出同源 `/downloads/<file>` 直链。

约束：① cloud + isales 同机运行，任何改动**绝不碰 isales**；② 系统红线「绝不静默假成功」贯穿全局，下载 URL 契约的版本/文件名必须与真实对象逐字对齐；③ 敏感值（AK/SK）绝不进仓/日志/commit；④ console 是纯前端静态站，运行时不应背上重依赖。

## Goals / Non-Goals

**Goals:**
- 安装包字节从 ECS 生产盘迁到阿里云 OSS 公读桶，卸下生产机的存储与分发带宽。
- 给到稳定、与单机解耦的公网下载 URL，为将来挂 CDN 留口。
- 发版流程可重复、可校验：切前端版本前先证明对象真的可匿名下载。
- console 侧改动最小化（只改一个 base 来源，`edgeDownloadUrl()` 与调用点不动）。

**Non-Goals:**
- 不做 P1 文生图配图字节转存（另立 change）。
- 不启用 electron-updater 自动更新 feed（休眠能力，YAGNI）。
- 不在本次强制绑自有域名 + CDN（需 ICP 备案，作为后续增量）。
- 不改 edge 的**构建**逻辑（属 `edge-desktop-packaging` spec，本 change 只管构建产物的托管分发）。

## Decisions

**D1. 公读桶 + 匿名直链，不用签名 URL。**
安装包是公开、匿名、跨全体用户浏览器下载的物件；后台按钮是 `<a download href>` 纯导航式下载。用私有桶 + 签名 URL 会：签名有过期、需 console 在运行时动态签发（引入 SDK + 凭据到前端，违背最小化）、URL 不可缓存分享。故选 **public-read 桶**。备选（私有桶 + 签名 URL）被否，仅在 P1 私密配图场景才用签名 URL。

**D2. 对象键版本化布局 `downloads/<version>/<file>`。**
按版本分目录，使旧版可保留（回退）或按策略清理，且新旧版对象天然隔离、发版不覆盖。备选（扁平 `downloads/<file>` 每次覆盖）被否——覆盖式无法回退、且覆盖瞬间有下到半包风险。

**D3. 发版上传工具：默认 `ossutil` CLI，`ali-oss` 仅在自动化时用。**
发版上传是运维在**发版机（非 ECS）**上跑的独立步骤、非应用运行时，用 `ossutil cp --acl public-read` 一行即可，零代码零依赖、最贴合现有手动发版流。若后续做 CI 直传，再在 `build-desktop.yml` 用 `ossutil`/`ali-oss` 加一步。备选（console/cloud 运行时用 SDK 传）不适用——上传不是运行时职责。

**D4. 鉴权按用户决定放松:用主账号 AK,不做子账号。**
上传发生在发版机(非 ECS),用显式 AK。用户已明确安全等级不高、不折腾子账号,故直接用现有主账号 AK 走 `ossutil` 本机配置即可,**绝不硬编码进仓/日志/commit**。唯一保留的红线:主账号 AK(全账号权限)**绝不放进 GitHub Secrets / CI**——一旦要做 CI 直传再单独议(那时才值得配最小权限子账号)。备选(最小权限子账号)更安全但用户嫌麻烦、本次不做;对照 change `cloud-oss-storage-integration` 的云端上传在 ECS 上跑、AK 存加密库,鉴权路径不同。

**D5. 发版后「对象存在性校验闸」前置于版本切换。**
切换 console `version`（及部署）之前，MUST 对桶内该版本三平台对象逐一匿名 `HEAD`，要求 `200` + 非零 `Content-Length`；任一未命中即停手、不切版本、不部署。这把「文件名/版本手动对齐」这一红线风险点从「事后可能 404」变成「事前证伪」，落实「绝不静默假成功」。

**D6. console 只改 `EDGE_DOWNLOAD.base`，其余不动。**
`base` 从 `'/downloads'` 改为 OSS 公网 base（含版本段，如 `https://aidcp.oss-cn-beijing.aliyuncs.com/downloads/<version>`，或将来 CDN/自有域名的稳定形态）。`edgeDownloadUrl(file)` 的 `encodeURIComponent(file)` 逻辑保持不变，天然处理 `'AIDCP Setup <ver>.exe'` 的空格。上传时对象 MUST 设正确 `Content-Type`（dmg=application/x-apple-diskimage、exe=application/octet-stream 或 vnd.microsoft.portable-executable）与 `Content-Disposition: attachment`。

**D7. 灰度回退：ECS `/downloads/` 暂留一版。**
切 OSS 稳定一版后再摘 Nginx location 与目录。回退只需把 console `base` 改回 `'/downloads'` 并重构建部署（ECS 上仍有旧包）。

## Risks / Trade-offs

- **[误设私有桶 → 匿名下载按钮 403]** → D5 校验闸用**匿名** HEAD/GET 验证，私有桶会在校验阶段即失败、挡在切版本之前。
- **[版本/文件名与桶内对象漂移 → 404]** → D5 校验闸逐对象证实命中方可切版本；此为红线「绝不静默假成功」的直接落地。
- **[AK 泄漏]** → 用户已知并接受(安全等级不高、用主账号 AK)；仍守 AK 只进发版机 `ossutil` 本机配置、绝不进仓/日志/commit、**绝不进 GitHub Secrets/CI**。CI 直传若日后要做,须先换最小权限子账号,且上传成败如实反映退出码、不 `|| true` 吞错。
- **[无 CDN 时跨地域下载慢]** → 桶选就近 region 兜底；CDN + 自有域名作后续增量（需 ICP 备案）。
- **[公读桶暴露面]** → 与现状 `autoindex on` 等同（现即公开可下），可接受；但意识到「有 URL 即可下」，不放任何非公开物。关闭桶级 list 权限，避免目录遍历。
- **[同机 isales]** → 本 change 仅动 console 前端配置 + 发版流程 + 新建 OSS 资源，**不触碰 ECS 上 isales 的任何服务/目录/端口**；灰度期 Nginx `/downloads/` location 保持原样。

## Migration Plan

1. 用户已建桶 `aidcp`（`oss-cn-beijing`，公读）；发版机 `ossutil config` 写入主账号 AK（不做子账号、不进 CI）。
2. 用 `ossutil cp` 把当前 `0.2.0` 三平台安装包上传到 `downloads/0.2.0/`，设对 `Content-Type`/`Content-Disposition`。
3. **校验闸**：匿名 `HEAD` 三对象，确认 `200` + 非零 `Content-Length`（私有/缺失即停）。
4. 改 `downloads.ts` 的 `base` 指向 OSS 版本前缀，重构建 + 部署 console（承 console 部署纪律：rsync 到 `/opt/aidcp/console`、绝不 `--delete`）。
5. 真机点击三平台下载按钮各验一次可下载。
6. 稳定一版后摘 ECS `/downloads/` location 与目录（另起收尾提交）。
- **回滚**：`base` 改回 `'/downloads'` → 重构建部署 console（ECS 旧包仍在）。

## Open Questions

- 是否本次即绑 CDN + 自有域名（取决于 ICP 备案是否就绪）？未定则先用默认 `aidcp.oss-cn-beijing.aliyuncs.com` endpoint。
- 是否本次就做 CI 直传（`build-desktop.yml` 加步），还是先保留手动 `ossutil` 上传、稳定后再自动化？倾向先手动跑通再自动化。
- 旧版本对象的保留/清理策略（保留 N 版还是设 OSS 生命周期规则）？
