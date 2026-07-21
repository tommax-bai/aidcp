## MODIFIED Requirements

### Requirement: 删除环境仅经界面逐个二次确认触发，绝不自动 / 批量

桌面外壳 MAY 提供删除环境（`user/delete`）功能，但 SHALL 仅由运维在桌面界面上**逐个、二次确认**触发：第一次点击仅进入待确认态（如「确认删除?」，短时后自动收回）、**第二次点击才执行**删除。删除前 SHALL 明确警示**不可恢复**（若该环境已登录账号，其登录态 / cookie 一并丢失）。删除 MUST NOT 自动触发、MUST NOT 批量执行、MUST NOT 由本机 ledger / 过期状态驱动。管理后台、Cloud、远程 maintenance、客户端 outbox 与 Cloud→Edge 命令 MUST NOT 触发 AdsPower 环境删除。桌面写客户端对 `user/delete` 放行、但对浏览器生命周期（`browser/start|stop|active`）SHALL 仍**直接抛错**（M7 不变）。桌面凭据只在内存持有，日志须脱敏。

#### Scenario: 桌面删除需二次确认
- **WHEN** 运维在桌面客户端点击某环境的删除按钮
- **THEN** 第一次点击仅进入「确认删除?」待确认态、不发任何删除请求；第二次点击才执行本地 `user/delete`，删前已警示不可恢复

#### Scenario: 管理后台不提供删除来源
- **WHEN** 管理员查看 Cloud 环境资产或直接请求曾存在的 Panel 删除路径
- **THEN** 系统不触发 AdsPower `user/delete`，不创建 Edge maintenance 责任且不发送 Cloud→Edge 删除命令

#### Scenario: 绝不自动 / 批量删
- **WHEN** 任何非桌面界面逐环境明确二次确认的路径（自动清理 / 批量 / ledger / Cloud 管理后台）尝试删除
- **THEN** MUST NOT 触发 `user/delete`

#### Scenario: 写客户端仍禁浏览器生命周期
- **WHEN** 代码路径尝试经桌面写客户端调用 `browser/start|stop|active`
- **THEN** 直接抛错、不发出，保留 M7 生命周期红线
