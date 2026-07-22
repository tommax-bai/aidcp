## MODIFIED Requirements

### Requirement: 运行时路径跨平台

edge 运行时 MUST NOT 依赖 POSIX-only 的硬编码路径。发布审批信号文件闸 SHALL 被限定为**本机开发夹具**，MUST NOT 作为与云端的跨服务契约存在：其默认目录仍 MUST 为当前系统的临时目录（`os.tmpdir()`）并 MUST 可经 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 覆盖，但该闸 MUST 仅在显式开发开关与该目录变量同时给出时才启用；未同时满足时 MUST 立即返回可区分的「闸未启用」拒因，MUST NOT 静默通过、MUST NOT 静默等待到超时。

生产桌面客户端的算子路由表内 MUST NOT 存在整页发布处理器；生产发布 MUST 只执行云端逐条下发的发布原子指令，人审授权判定 MUST 完全在云端完成。edge MUST NOT 以任何本机文件作为「是否已授权」的判据。

#### Scenario: 开发夹具未显式启用时不静默放行
- **WHEN** 未同时提供开发开关与信号目录变量却调用该闸
- **THEN** 立即返回「闸未启用」拒因，不读取任何文件、不等待、不放行

#### Scenario: Windows 上本地开发夹具不因 /tmp 缺失而失败
- **WHEN** 在 Windows 上按显式开关运行本地开发夹具
- **THEN** 信号文件落在 `os.tmpdir()` 或显式目录下、可被正常写入与读取，不因 `/tmp` 不存在而失败

#### Scenario: 生产路径无文件依赖
- **WHEN** 检查打包后的桌面客户端算子路由表与发布执行路径
- **THEN** 整页发布处理器不存在、发布只走原子指令，且没有任何生产代码路径读取审批信号文件
