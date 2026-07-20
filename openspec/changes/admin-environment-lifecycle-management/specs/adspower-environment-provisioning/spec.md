## MODIFIED Requirements

### Requirement: 删除环境仅经界面逐个二次确认触发，绝不自动 / 批量

桌面外壳 MAY 提供本地删除环境（`user/delete`）功能，但 SHALL 仅由运维在界面上逐个、二次确认触发。管理后台 MAY 作为第二个允许的远程触发源，但同样 SHALL 逐环境展示影响预览并要求完整 envKey 确认；Cloud 只写删除期望状态，官方 Edge 主进程 MUST 通过客户鉴权 HTTP 主动拉取、领取匹配 installation 的责任后才执行。删除前 SHALL 明确警示不可恢复（若该环境已登录账号，其登录态/cookie 一并丢失）。删除 MUST NOT 批量执行，MUST NOT 由本机 ledger、过期、离线或陈旧状态自动触发，MUST NOT 通过 Cloud→Edge WS 删除命令触发。

写客户端对 `user/delete` 放行、但对浏览器生命周期（`browser/start|stop|active`）SHALL 仍直接抛错（M7 不变）。Edge SHALL 在本地执行路径先停止该环境的既有运行 handle；视频号还 MUST 等待既有 offboard 凭证清理达到允许物理删除的终态。AdsPower 返回成功或 claimed 权威 installation 明确返回不存在后，Edge 才可回写成功；其它错误 MUST 原样归为待重试失败。凭据同建号：只内存持有、日志脱敏。

#### Scenario: 本地删除需二次确认
- **WHEN** 运维在桌面客户端点击某环境的删除按钮
- **THEN** 第一次点击仅进入“确认删除?”待确认态、不发任何删除请求，第二次点击才执行本地受控删除，删前已警示不可恢复

#### Scenario: 管理后台远程删除需精确确认并由 Edge 拉取
- **WHEN** 管理员在环境页查看单环境影响预览、输入完整 envKey 并确认
- **THEN** Cloud 只记录删除期望；匹配 installation 的 Edge 经 HTTP poll/claim 后逐个执行 `user/delete`，不得收到新增 WS 删除命令

#### Scenario: 绝不按本地状态或批量删除
- **WHEN** 任何批量、自动清理、ledger、过期、离线或未确认路径尝试触发删除
- **THEN** MUST NOT 调用 `user/delete`

#### Scenario: 写客户端仍禁浏览器生命周期
- **WHEN** 代码路径尝试经写客户端调用 `browser/start|stop|active`
- **THEN** 直接抛错、不发出，放宽远程确认来源不改变 M7 生命周期红线

#### Scenario: AdsPower 失败不回报删除成功
- **WHEN** `user/delete` 返回环境占用、运行中、限流或其它非“不存在”错误
- **THEN** Edge 经 HTTP 回写真实失败并保留重试责任，Cloud 与管理后台不得显示已删除

