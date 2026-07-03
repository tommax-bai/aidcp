## ADDED Requirements

### Requirement: 安装包托管于 OSS 公读桶且键按版本分层

系统的桌面客户端安装包（dmg/exe）构建产物 SHALL 托管于阿里云 OSS 的 **public-read** 桶，作为唯一的公网下载权威来源。对象键 MUST 按版本分层为 `downloads/<version>/<file>`，使不同版本的对象天然隔离、发版不覆盖既有版本，且旧版本对象可保留（供回退）或按生命周期策略清理。桶级目录列举（list）SHALL 关闭，避免匿名目录遍历。

#### Scenario: 安装包以公读匿名方式可下载

- **WHEN** 终端用户浏览器请求某已发布版本的安装包 OSS URL（无任何签名/凭据）
- **THEN** 对象 SHALL 以 `200` 返回完整字节，且响应头 `Content-Type` 与 `Content-Disposition: attachment` 正确设置（dmg 为磁盘映像类型、exe 为可执行/八位字节流类型），使浏览器触发下载而非内联渲染

#### Scenario: 桶被误配为私有

- **WHEN** 桶或对象 ACL 未设为 public-read
- **THEN** 匿名请求 SHALL 返回 `403`，且该状态 MUST 在「发版后对象存在性校验闸」阶段被捕获、阻止版本切换（见对应 Requirement），绝不让前端下载按钮带着 403 的 URL 上线

### Requirement: console 下载 URL 以单一 base 契约指向 OSS

管理后台前端「下载客户端」按钮的下载 URL SHALL 由单一配置来源 `EDGE_DOWNLOAD.base` 决定：`base` 指向 OSS/CDN 的公网前缀（含版本段），`edgeDownloadUrl(file)` 的拼接与 `encodeURIComponent(file)` 逻辑 MUST 保持不变。含空格的文件名（如 `AIDCP Setup <ver>.exe`）SHALL 由既有的 `encodeURIComponent` 正确转义，无需在调用点特殊处理。console 运行时 MUST NOT 引入 OSS SDK 或任何签名逻辑——迁移只改 `base` 的取值来源，不改前端行为形状。

#### Scenario: 前端按钮生成 OSS 直链

- **WHEN** 用户在后台打开客户端下载区
- **THEN** 三平台按钮的 `href` SHALL 为 `base` 与经 `encodeURIComponent` 转义后的文件名拼出的 OSS 公网直链，点击即匿名下载对应安装包

#### Scenario: 切换发布版本仅改配置

- **WHEN** 发布新版本安装包
- **THEN** 前端侧的改动 SHALL 局限于 `downloads.ts` 的 `version` 与文件名（及 `base` 的版本段），`edgeDownloadUrl()` 与其调用点 MUST NOT 改动

### Requirement: 发版后对象存在性校验闸前置于版本切换

在切换 console 的 `version`（及重新构建/部署 console）之前，发版流程 MUST 对目标 OSS 桶内该版本的**全部三平台对象**逐一做匿名 `HEAD` 校验，要求返回 `200` 且 `Content-Length` 非零。任一对象未命中（`403`/`404`/零长度/网络失败）时，发版流程 SHALL 停手、MUST NOT 切换前端版本、MUST NOT 部署 console。此闸落实系统红线「绝不静默假成功」：前端引用的版本/文件名与桶内真实对象的一致性，MUST 在上线前被证实、而非事后靠用户遇到 404 才暴露。

#### Scenario: 三对象全部命中方可切版本

- **WHEN** 三平台安装包均已上传且匿名 `HEAD` 各返回 `200` + 非零 `Content-Length`
- **THEN** 发版流程 SHALL 允许切换 `version` 并部署 console

#### Scenario: 任一对象缺失或不可匿名访问

- **WHEN** 任一平台对象 `HEAD` 返回非 `200`、零长度、或私有 403
- **THEN** 发版流程 SHALL 中止并如实报出未命中的对象键，MUST NOT 切换前端版本、MUST NOT 部署，绝不静默以旧版本或坏链上线

### Requirement: 发版上传使用最小权限凭据且密钥绝不外发

安装包上传 OSS SHALL 使用**仅授予目标桶写入所需权限**的 RAM 子账号凭据（策略最小化到该桶的 `PutObject` 及校验所需只读），MUST NOT 使用主账号 AccessKey。凭据 SHALL 只存在于发版机的 `ossutil` 本机配置或 CI 的加密 Secrets 中，MUST NOT 出现在代码仓、日志、commit、tasks.md 或任何文档明文里。若启用 CI 直传，上传步骤的成功/失败 MUST 如实反映到步骤退出码，MUST NOT 用 `|| true` 之类吞掉失败。

#### Scenario: CI 直传失败必须让流水线失败

- **WHEN** CI 中的 OSS 上传步骤因凭据/网络/权限失败
- **THEN** 该步骤 SHALL 以非零退出码结束、使流水线失败，绝不静默继续，也绝不把「未真正上传」当成功

#### Scenario: 凭据不进任何可追溯载体

- **WHEN** 提交代码、写文档或打印日志
- **THEN** OSS AccessKey/Secret MUST NOT 以明文出现在其中；引用凭据时只记「读取方式/存放位置」，不记值

### Requirement: 迁移保留一版灰度回退且不触碰同机 isales

迁移期间，ECS 上原有的 `/downloads/` Nginx location 与 `/opt/aidcp/downloads/` 目录 SHALL 保留至少一个稳定版本，作为回退路径；回退 SHALL 仅需把 `EDGE_DOWNLOAD.base` 改回同源 `'/downloads'` 并重构建部署 console。本 change 的任何操作 MUST NOT 触碰同机 isales 的服务、目录或端口。

#### Scenario: 回退到 ECS 本地托管

- **WHEN** OSS 分发出现问题需回退
- **THEN** 把 `base` 改回 `'/downloads'` 并重新部署 console SHALL 使下载按钮重新指向 ECS 本地仍存在的安装包，无需重新上传字节

#### Scenario: 迁移不影响 isales

- **WHEN** 执行本 change 的 console 配置改动、发版流程调整或新建 OSS 资源
- **THEN** 同机 isales 的运行 SHALL 完全不受影响，ECS 上不对 isales 的服务/目录/端口做任何改动
