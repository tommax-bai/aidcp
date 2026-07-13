## Context

现有桌面客户端以手动下载安装包升级。macOS CI 已使用 Developer ID 签名和公证，并在 `dist-electron/` 生成 x64/arm64 zip、对应 blockmap 和 `latest-mac.yml`；但产物交付目前只发布 dmg，客户端也未依赖 `electron-updater`。

OL 是独立的线上环境。客户端的运行时云端选择允许改成 dev、ol 或自定义地址，因此更新源不能由该运行时选择推导，否则一个 OL 分发包可能因用户修改设置而走错更新通道。已有 `edge-installer-oss-distribution` change 负责把公开安装包迁至 OSS，但其明确不实现自动更新；本 change 只依赖其静态分发能力，不改写该 change。

当前 Electron 主进程把正常退出和优雅停止子进程绑定在一起。更新器的 `quitAndInstall()` 不能依赖普通 `before-quit` 回调完成收尾，故更新路径须显式完成停机后才调用安装。

## Goals / Non-Goals

**Goals:**

- 让已安装的 OL macOS 客户端发现高于当前版本的签名更新，并明确提示用户。
- 让用户控制下载与重启时机；更新安装前确保所有受监督 edge 子进程已完成有界、可见的停机。
- 用 generic HTTPS 静态源承载 OL 更新文件；版本文件不可覆盖、manifest 最后提升，发布失败不影响已上线版本。
- 保持 macOS x64 与 arm64 的正确产物选择、代码签名和公证验证。
- 在不引入 cloud、console 运行时依赖或边云协议改动的前提下，令发版脚本可重复验证更新通道。

**Non-Goals:**

- Windows 自动更新、Linux 自动更新、强制更新、静默下载/重启、差分更新策略调优，以及发布说明管理后台。
- 修改用户当前的云端选择、以云端下发更新 URL、或由 cloud/console 代理更新文件。
- 用更新机制回退已经安装的较高版本；错误版本仅通过发布更高版本的修复包处理。
- 把主账号 OSS AccessKey 放入 CI、仓库、日志或文档。

## Decisions

### D1. 仅对构建时固定为 OL 的已打包 macOS 应用启用更新

OL 分发构建在 app 内的 `package.json` 烘焙 `aidcpUpdateChannel=ol` 与固定的 HTTPS generic 更新基址；主进程只在 `app.isPackaged`、macOS 且该配置完整有效时创建更新器。运行时的 dev/ol/custom 云端设置不参与判断。

这复用现有“构建时烘焙 OL 缺省云端”的模式，并避免 custom 地址、开发运行或 dev 包意外访问线上更新源。备选的“按当前连接云端选择更新源”被否，因为设置允许在不重装 app 的情况下改变，而二进制的供应链信任边界不能随之漂移。

### D2. 使用 `electron-updater` + OSS generic HTTPS provider

`electron-updater` 作为应用依赖，通过打包生成的 `app-update.yml` / `latest-mac.yml` 使用 generic provider。更新基址为 OL 专用前缀，例如 `https://<updates-host>/ol/stable/`；不用 GitHub Release 作为客户端更新源，也不用 ECS 同机下载目录。

generic provider 只需要静态 HTTPS 托管，适合 OSS，也可在以后接 CDN 或域名而不改变客户端协议。当前 macOS 构建已经生成适用于两种架构的单个 `latest-mac.yml`；该 metadata 内的 `files` 列表由 updater 按架构选择 zip。备选的自建 cloud 更新 API 被否，因为会把本应静态、公开、可缓存的分发职责耦合到生产业务服务。

### D3. 版本文件不可变，manifest 最后 promotion

每次发布先将签名 zip、zip blockmap、dmg、`latest-mac.yml` 的候选副本上传到版本化 staging 路径并校验；校验通过后，把版本文件以带版本号的对象键放到 stable update prefix，最后单独写入 `latest-mac.yml`。版本文件使用长期 immutable 缓存；`latest-mac.yml` 使用 `no-cache, must-revalidate`。更新器只读 stable manifest。

上传失败、匿名 HTTPS 请求失败、版本号不匹配、长度/sha512 不匹配、签名或公证检查失败时，promotion 必须停止，保留原 manifest。备选的“直接覆盖固定文件名”被否，因为下载中的客户端可能拿到半包，且无法审计/回退。

### D4. 用户显式下载和安装；更新不抢占业务会话

客户端在主窗口可用后延迟检查，之后以不高于六小时一次的频率检查。已启用更新的 OL macOS 客户端同时在设置和托盘菜单提供“检查更新”手动入口；它复用同一不并发的检查服务，不下载、不重启，并在无更新时明确反馈当前已是最新。发现更新仅显示当前版本、目标版本、下载按钮和稍后提醒；用户确认下载后才调用下载。下载完成后显示“立即重启更新”与“稍后”。

用户点击立即更新时，主进程先展示会停止所有运行环境的影响，并取得确认。确认后进入专用的 `stopAllForUpdate()`：停止所有 edge 子进程、等待它们全部退出，并把任何超时/退出失败如实显示；只有不存在仍运行的子进程时才能调用 `quitAndInstall()`。常规退出也改为复用同一底层停机函数，但更新流程不得依赖 `before-quit` 才执行停机。

备选的“检查到即自动下载、下载完立即重启”被否：浏览器自动化任务具有外部副作用，必须由操作者决定中断时机。

### D5. macOS first；Windows 必须先补齐可验证的签名发行链

本 change 的可用范围为 macOS x64 与 arm64。macOS 产物维持同一 appId、Developer ID 签名与公证，且把 zip、blockmap、`latest-mac.yml` 纳入 CI 交付和发版校验。

当前 Windows 配置关闭可执行文件签名，CI Windows job 也尚未接入 self-contained runtime；因此 Windows 保留手动下载，不在此 change 创建任何 update feed 或客户端开关。备选的“先让 Windows 无签名自动升级”被否，因为公共更新源下无法达到与 macOS 相同的供应链验证标准。

### D6. 仍由受控发版机向 OSS 发布

CI 负责构建签名公证的 macOS artifact 并将完整 artifact 集交付给发布者；受控发版机的 `ossutil` 负责上传、校验与 promotion。主账号 AK 仅存在于该发版机本地配置，不进入 GitHub Actions。若以后需要 CI 直传，必须另行配置仅允许写入更新前缀的最小权限凭据。

这与当前 OSS 分发 change 的凭据边界一致。备选的“把现有主账号 AK 放入 CI”被否。

## Risks / Trade-offs

- **[用户仍停留在不含更新器的旧版]** → 首个含更新器的 OL 版本必须继续在下载页提供手动 dmg；后续版本才会弹提示。
- **[更新安装绕过正常退出钩子]** → 将停机逻辑拆为可 await 的独立函数，且把 `quitAndInstall()` 放在其成功之后。
- **[manifest 被 CDN/浏览器缓存导致延迟发现更新]** → `latest-mac.yml` 强制重新验证；版本对象保持 immutable。
- **[更新源存在坏包或文件错配]** → 以 HTTP、长度、sha512、签名、公证、包内版本和烘焙 OL 元数据组成 promotion 前闸；任一失败不改 stable manifest。
- **[错误版本已安装，无法“回滚”]** → 停止向更多客户端推广，并发布更高版本的修复包；不承诺自动降级。
- **[有运行任务时用户误点重启]** → 二次明确告知影响；停机失败时取消安装并保持当前 app 可用，绝不伪装已更新。
- **[同时推进 OSS 分发 change]** → 两个 change 保持单写边界；本 change 仅依赖其已落地的桶/发布约定，实际实施前先确认依赖状态。

## Migration Plan

1. 完成或确认 OSS 安装包分发的公共静态托管前缀、HTTPS 和发布凭据边界；不以 ECS 下载目录作为长期更新源。
2. 在 edge 中实现更新服务、OL 打包元数据、完整 macOS artifact 交付和可重复的 release/promotion 脚本。
3. 以一个新版本构建签名公证的 OL macOS bootstrap 包；人工安装到验收机。旧客户端不会自动获得这一步。
4. 在独立 staging 更新前缀上完成从旧版到 bootstrap 包的真机升级验收，覆盖 arm64、x64、无运行任务、有运行任务、下载失败与坏 metadata。
5. 通过完整发布闸后提升 OL stable manifest；下载页仍保留同版本 dmg 供新用户/旧用户手动安装。
6. 若 promotion 后发现问题，停止提升 manifest；若已有人升级，发布更高版本修复。若静态源不可用，客户端保留当前版本可继续运行，手动下载页作为兜底。

## Open Questions

- 更新源使用 OSS 原始 HTTPS 域名还是已有备案/CDN 域名；实现时优先选择已可稳定访问并满足 TLS 的地址。
- 产品是否需要在更新提示中显示人工维护的中文 release notes；本 change 可以先显示版本号与通用提示，避免把发布说明系统纳入第一期。
