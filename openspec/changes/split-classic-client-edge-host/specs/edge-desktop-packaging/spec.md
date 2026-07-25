## ADDED Requirements

### Requirement: 桌面安装包 MUST 由 Classic 精确组装一个 Host release

面向客户的桌面安装包 SHALL 仅由 `aidcp-classic-client` 构建，并 SHALL 从 lockfile 中精确锁定的
`@aidcp/edge-host` release 组装 Host API、编译后 Core、Native Page Engine 与 AdsPower runtime
资源。构建 MUST 校验 Host manifest、平台/架构和全部资源 SHA-256，并把 Classic version、Host
version、双方 commit 和 manifest hash 写入可诊断 provenance。`aidcp-edge-host` MUST NOT 另行
产出一个带产品 UI 的竞争安装包。

#### Scenario: Classic 构建已锁定的 Host

- **WHEN** Classic 使用 lockfile 中的精确 Host version 构建受支持平台安装包
- **THEN** 安装包只携带该 Host release 对应的已编译代码与校验通过的目标平台资源，并可读取双方 provenance

#### Scenario: Host 资源与 manifest 不一致

- **WHEN** 打包输入中的 Core、Native 或 AdsPower runtime hash 与已锁定 Host manifest 不一致
- **THEN** Classic 构建失败且不产出安装包，MUST NOT 复用上一次资源或联网选择另一 Host version

### Requirement: Host spawn 与 native 资源 MUST 使用真实 Resources 路径

Classic SHALL 将需要 spawn、写入或 native load 的 Host 资源放在 ASAR 外、由安装包签名覆盖的确定性
Resources 目录，并把该真实目录显式传给 Host。Host Core 子进程的 `cwd` MUST 是实际目录，MUST NOT
是 `app.asar` 文件路径；允许从 ASAR 加载的 JavaScript 与必须位于 ASAR 外的资源 SHALL 由 Host
manifest 明确区分。

#### Scenario: macOS 安装包从 ASAR 启动

- **WHEN** 已签名 macOS Classic 从 `app.asar` 加载 Electron main 并启动 Host Core
- **THEN** Core 使用 `process.resourcesPath` 派生的真实目录作为资源根和有效 `cwd`，native 资源位于 ASAR 外且签名可验证

#### Scenario: 构建遗漏 spawnable 资源

- **WHEN** Host manifest 声明的 spawnable 文件未被复制到安装包 Resources
- **THEN** package smoke 或启动校验具名失败，MUST NOT 从开发仓库补取该文件
