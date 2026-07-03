## Why

edge 桌面客户端安装包（dmg/exe，约 280MB/版本）当前唯一的公网下载点是 ECS 生产机本地盘 `/opt/aidcp/downloads/`，由 Nginx `autoindex` 对外。这带来四个已坐实的痛点：① 大二进制常驻在同机跑 cloud + isales 的生产盘、旧版无清理会累积撑盘；② 下载可用性与该机及其 Nginx 强耦合，机器抖动即用户拿不到包；③ 每次发版靠手动 `rsync` 到 ECS；④ 分发带宽从生产机走。用户已开通阿里云 OSS，安装包是「公开、匿名、跨全体用户浏览器下载的大二进制」——正是对象存储的教科书用例。把它迁到 OSS 公读桶即可把存储/带宽从生产机彻底卸下、给到稳定公网 URL，并为将来挂 CDN 留口。

## What Changes

- **新增** 用户已开通的 OSS 桶 `aidcp`（华北2·北京 `oss-cn-beijing`，与云端配图存储 change `cloud-oss-storage-integration` **共用同一桶**：安装包在 `downloads/<version>/<file>` 前缀、配图在 `publish/` 前缀）作为安装包的权威公网托管，对象按版本分层便于保留/清理旧版；桶为公读（配图本也公开，故整桶公读即可）。
- **修改** `aidcp-console/src/config/downloads.ts`：`EDGE_DOWNLOAD.base` 从同源 `'/downloads'` 改为 OSS 公网 base（如 `https://aidcp.oss-cn-beijing.aliyuncs.com/downloads/<version>`）；`edgeDownloadUrl()` 拼接逻辑与调用点**不变**，仅 base 来源改变。
- **修改** 发版流程：安装包上传目的地从「`rsync` 到 ECS `/opt/aidcp/downloads/`」换成「用 `ossutil`（或 `ali-oss`）上传到 OSS 桶」。发版文档同步更新。
- **新增** 发版后的**对象存在性校验闸**：切换 console `version` 前，必须对桶内三平台对象逐一 HTTP `HEAD` 校验命中（`200` + 非零 `Content-Length`），任一未命中即停手、不切版本——落实红线「绝不静默假成功」。
- **新增（可选）** CI 直传：`aidcp-edge/.github/workflows/build-desktop.yml` 的 `upload-artifact` 之后加一步用 `ossutil`/`ali-oss` 把安装包直传 OSS，消掉「运维 `gh run download` → 本地 → `scp`/`rsync` 到 ECS」的往返；上传成败如实反映到步骤退出码（**不 `|| true` 吞错**）。GitHub artifact 仍保留 14 天做审计/回退。
- **保留一版灰度回退**：ECS `/downloads/` location 与目录暂不删，切 OSS 稳定一版后再摘。
- **不在本次范围**：P1 文生图配图字节转存 OSS（单独 change）；electron-updater 自动更新 feed（休眠能力，按 YAGNI 暂不做）。

## Capabilities

### New Capabilities
- `edge-installer-distribution`: 桌面客户端安装包**构建产物的公网托管与分发契约**——安装包托管于 OSS 公读桶 `aidcp` 的 `downloads/` 前缀、对象键的版本化布局、console 下载 URL 的单一来源契约、发版上传流程、发版后对象存在性校验闸、鉴权（发版机用 AK、主账号可、密钥不外发且绝不进 CI）、公读桶配置约束。区别于已有的**构建向** spec `edge-desktop-packaging`（管 dmg/nsis 如何被打出来），本 capability 只管「已打出的包如何被托管、被寻址、被下载」。

### Modified Capabilities
<!-- 无。edge-desktop-packaging 的构建 requirements 不变；downloads.ts 是配置常量、非既有 spec 的 requirement。 -->

## Impact

- **aidcp-console**：`src/config/downloads.ts`（改 `base`）；`deploy/aidcp-console.conf` 的 `location /downloads/`（灰度期保留、稳定后摘）。
- **aidcp-edge**：发版脚本/文档（`docs/release-desktop.md`）目的地改为 OSS；可选 `.github/workflows/build-desktop.yml` 增直传步骤。
- **基础设施（非代码）**：用户已建桶 `aidcp`（`oss-cn-beijing`，公读）；发版机配置 AK 供 `ossutil` 上传。**鉴权按用户决定放松**：用现有主账号 AK 即可、不做子账号（安全等级不高、可接受主账号全权限风险），但主账号 AK **绝不放进 GitHub Secrets / CI**（那会放大泄漏面）——CI 直传若真做再单议。
- **依赖**：发版侧引入 `ossutil` CLI（零代码，或直接在 OSS 网页控制台拖拽上传）；console 运行时**不引入** OSS SDK（只改一个 base 字符串）。
- **安全边界**：桶 public-read（误设私有 = 匿名下载按钮 403）；AK 绝不进仓/日志/commit；含空格的 `'AIDCP Setup <ver>.exe'` 用 `encodeURIComponent`（现有代码已做）+ OSS 设对 `Content-Type`/`Content-Disposition`；绑自有域名走 CDN 需 ICP 备案，短期先用默认 `oss-cn-beijing` endpoint；**绝不碰同机 isales**。
