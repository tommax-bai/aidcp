## ADDED Requirements

### Requirement: 安装包捆绑可运行的 AdsPower CLI 运行时、但不捆绑浏览器内核

打包后的桌面应用 MUST 随包分发一份可直接运行的 AdsPower CLI 运行时（`adspower-browser`），使目标机在**不单独安装 AdsPower 桌面客户端、且无 npm / 独立 Node / 全局安装**的前提下即可经该运行时的 Local API 托管指纹浏览器。运行该运行时 MUST 复用 Electron 自带的 Node 运行时（`ELECTRON_RUN_AS_NODE`），MUST NOT 随包再打独立 Node 二进制。运行时中的 native 模块（sqlite）MUST 置于 asar 归档之外并随应用的 hardened runtime 一同签名，以便加载与 spawn 子进程。桌面应用 MUST NOT 把浏览器内核（约每架构数百 MB）捆绑进主安装包——内核由运行时在首次需要时按需下载。

#### Scenario: 无桌面客户端与工具链也能起运行时

- **WHEN** 目标机只装了本桌面应用、未装 AdsPower 桌面客户端、也无 npm/独立 Node
- **THEN** 应用用自带 Node 拉起随包的 AdsPower CLI 运行时并对外提供 Local API，无需任何额外安装

#### Scenario: 主安装包不含浏览器内核

- **WHEN** 构建产出主安装包
- **THEN** 安装包内 MUST NOT 含浏览器内核二进制；内核在运行期按需下载到用户可写目录

#### Scenario: native 模块随应用签名且可加载

- **WHEN** 在已签名/公证的 macOS 应用中加载运行时的 sqlite native 模块
- **THEN** 该 native 模块位于 asar 之外、随 hardened runtime 一同签名，能被 Electron 自带 Node 正常加载
