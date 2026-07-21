## MODIFIED Requirements

### Requirement: 删除环境仅经界面逐个二次确认触发，绝不自动 / 批量

桌面外壳 MAY 提供删除环境（`user/delete`）功能，但 SHALL 仅由运维在界面上**逐个、二次确认**触发：第一次点击仅进入待确认态（如「确认删除?」，短时后自动收回）、**第二次点击才执行**删除。管理后台 MAY 作为第二个允许来源，但 SHALL 展示单环境影响并要求操作者逐字输入完整 envKey；该远程来源 SHALL 由 Cloud 直接调用其服务端配置的 AdsPower API，MUST NOT 建立 Edge maintenance poll/claim/result 责任或 Cloud→Edge 删除命令。删除前 SHALL 明确警示**不可恢复**（若该环境已登录账号，其登录态 / cookie 一并丢失）。删除 MUST NOT 自动触发、MUST NOT 批量执行、MUST NOT 由本机 ledger / 过期状态驱动。桌面写客户端对 `user/delete` 放行、但对浏览器生命周期（`browser/start|stop|active`）SHALL 仍**直接抛错**（M7 不变）。桌面凭据同建号只在内存持有；Cloud 凭据 MUST 使用服务端加密存储且不回传明文；两端日志均须脱敏。

#### Scenario: 桌面删除需二次确认
- **WHEN** 运维在桌面客户端点击某环境的删除按钮
- **THEN** 第一次点击仅进入「确认删除?」待确认态、不发任何删除请求；第二次点击才执行本地 `user/delete`，删前已警示不可恢复

#### Scenario: 管理后台删除由 Cloud 直接执行
- **WHEN** 管理员查看单环境影响并输入完整 envKey 后确认
- **THEN** Cloud 直接调用服务端 AdsPower `user/delete`，不等待 Edge installation、不创建 maintenance 责任且不发送 WS 删除命令

#### Scenario: 绝不自动 / 批量删
- **WHEN** 任何非界面逐环境明确确认的路径（自动清理 / 批量 / ledger 驱动）尝试删除
- **THEN** MUST NOT 触发 `user/delete`

#### Scenario: 写客户端仍禁浏览器生命周期
- **WHEN** 代码路径尝试经桌面写客户端调用 `browser/start|stop|active`
- **THEN** 直接抛错、不发出（管理后台改由 Cloud 直删不改变桌面 M7 生命周期红线）

#### Scenario: AdsPower 失败不删除 AIDCP 环境
- **WHEN** Cloud 的 `user/delete` 返回环境占用、限流、鉴权、不可达或其它失败
- **THEN** Cloud 保留 AIDCP 环境与真实错误，管理后台不得显示已删除
