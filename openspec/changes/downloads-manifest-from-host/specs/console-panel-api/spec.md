## ADDED Requirements

### Requirement: 安装包清单由所在机器现扫得出，绝不写死在源码里

The panel API SHALL expose the edge desktop installer list by scanning the downloads directory **on the host it runs on**, and the console SHALL render the download menu from that response. The installer version and filenames MUST NOT be hardcoded in console source.

A hardcoded version describes deployment state ("which binary is sitting in *this* host's directory"), which differs per host. Baking it into source guarantees it is a lie on every host but one: trunk pointing at the `ol` artifact yields dead links on `dev`, and trunk pointing at the `dev` artifact silently downgrades the `ol` download page.

The scan SHALL ignore non-release files (backups such as `*.bak-*`, partial downloads). When several versions of the same platform's installer are present, the highest semantic version SHALL be offered. The directory location SHALL be configurable, defaulting to the deployed convention.

#### Scenario: 页面只提供确实存在的包

- **WHEN** the console renders the installer download menu
- **THEN** every offered entry corresponds to a file that exists in that host's downloads directory at request time
- **AND** the displayed version is derived from those files, not from console source

#### Scenario: 两台机器各说各的真话

- **WHEN** the same console build is deployed to a host holding `0.3.18` and to a host holding `0.3.20`
- **THEN** each one offers the installer it actually has, with no source change and no rebuild between them

#### Scenario: 没有可用安装包时诚实说没有

- **WHEN** the downloads directory is empty, unreadable, or contains no recognizable installer, or the API call fails
- **THEN** the console shows that no installer is currently available
- **AND** it MUST NOT fall back to a hardcoded version or emit a link to a file it has not confirmed exists

#### Scenario: 备份与残留文件不被当成发布包

- **WHEN** the downloads directory also contains backup or partial files alongside real installers
- **THEN** those files are excluded from the manifest

#### Scenario: 同平台多版本取最高版本

- **WHEN** several versions of the same platform's installer are present in the directory
- **THEN** the manifest offers the highest semantic version for that platform
