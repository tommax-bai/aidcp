## ADDED Requirements

### Requirement: OL 更新通道以 HTTPS 静态 manifest 和版本化文件提供

系统 SHALL 在 OSS 或其前置的 HTTPS 静态域名上提供独立的 OL macOS generic 更新通道。该通道 MUST 提供 `latest-mac.yml`、x64 与 arm64 签名 zip、各 zip 的 blockmap，以及同版本的手动安装 dmg。更新 manifest SHALL 只引用属于该 OL 通道的带版本号文件；版本文件 MUST NOT 被后续发布覆盖。dev、custom 和 Windows 分发 MUST NOT 复用 OL stable manifest。

#### Scenario: arm64 与 x64 客户端取得各自的 zip
- **WHEN** OL stable manifest 发布一个同时包含 arm64 与 x64 zip 的版本
- **THEN** arm64 macOS 客户端取得 arm64 zip，x64 macOS 客户端取得 x64 zip，且两者都由同一个 OL stable manifest 的文件元数据校验

#### Scenario: 手动安装仍可获得同版本 dmg
- **WHEN** 一个尚无自动更新能力的 OL 客户端需要升级
- **THEN** 下载页仍可提供与 stable manifest 同版本的签名 dmg，供用户手动安装 bootstrap 版本

### Requirement: OL 更新 promotion 必须先验证全部工件再发布 manifest

发布流程 MUST 先上传候选版本的全部更新工件，并逐项验证匿名 HTTPS 可访问、HTTP 状态、非零长度、manifest 的版本和 sha512 与实际文件一致、macOS 代码签名/公证有效、以及包内烘焙的更新通道为 OL。所有验证通过后，流程才 SHALL 更新 OL stable 的 `latest-mac.yml`；任何验证失败 MUST 以非零结果停止，且 MUST NOT 改动已发布的 stable manifest。

#### Scenario: 全部验证通过后提升新版本
- **WHEN** 候选版本的两个架构 zip、blockmap、dmg、manifest 和包内 OL 配置均通过验证
- **THEN** 发布流程更新 stable manifest 以指向该版本，并如实记录已提升的版本

#### Scenario: 任一工件缺失或校验失败
- **WHEN** 任一候选更新工件返回非成功状态、长度为零、sha512 不匹配、签名/公证无效或包内通道不是 OL
- **THEN** 发布流程以失败退出并保持之前的 stable manifest 不变，MUST NOT 宣称新版已上线

### Requirement: 更新 manifest 与版本文件具有适合更新的缓存和回退语义

OL stable `latest-mac.yml` SHALL 使用要求重新验证的缓存策略；带版本号的更新文件 SHALL 使用长期 immutable 缓存策略。发布流程 SHALL 把 manifest 作为最后一个可变对象写入，以避免客户端下载到指向未完成文件的更新信息。已经发布并被客户端安装的版本 MUST NOT 依赖自动降级；发现问题时流程 SHALL 停止后续 promotion，并通过更高版本的修复发布恢复。

#### Scenario: 客户端在 manifest 更新时不获得半包
- **WHEN** 新版本文件仍在上传、校验或签名验证中
- **THEN** stable manifest 继续指向前一个完整版本，客户端 MUST NOT 看到指向未完成工件的新版本

#### Scenario: 已发布版本需要修复
- **WHEN** 一个已经被部分客户端安装的 OL 版本需要撤回
- **THEN** 发布者停止该版本的后续 promotion，并发布更高版本的修复；系统 MUST NOT 把自动降级作为回退手段

### Requirement: 更新发布凭据与业务服务隔离

更新文件上传 SHALL 由受控发版机执行，更新通道 MUST NOT 需要 cloud 或 console 在运行时持有 OSS 写入凭据。主账号 AccessKey MUST NOT 出现在仓库、日志、文档或 GitHub Actions；如未来启用 CI 上传，CI MUST 使用仅允许目标更新前缀写入的最小权限凭据，并且上传失败 MUST 使发布失败。

#### Scenario: 受控发版机发布成功
- **WHEN** 发版机使用其本地受保护的 OSS 配置完成所有验证并提升 manifest
- **THEN** 客户端可以匿名通过 HTTPS 读取更新文件，且 cloud、console 和客户端均不持有写入凭据

#### Scenario: CI 更新上传失败
- **WHEN** 未来配置了 CI 直传且上传因权限、网络或校验失败
- **THEN** CI 任务 MUST 以失败结束，且 stable manifest 不被提升
