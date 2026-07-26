# facebook-proxy-preflight Specification

## Purpose
TBD - created by archiving change facebook-proxy-selection-preflight. Update Purpose after archive.
## Requirements
### Requirement: 离线 Facebook 环境选择 SHALL 预热代理检测
客户端 SHALL 在用户选中浏览器未运行的 Facebook AdsPower 环境后，于 Electron 主进程后台使用该 profile 已保存的代理配置执行一次有界代理检测。检测 MUST NOT 启动浏览器、占用浏览器槽位或阻塞环境选择；非 Facebook、无代理配置或浏览器已运行的环境 MUST NOT 触发该检测。

检测 SHALL 只发起不含 Cookie、账号、环境标识或业务正文的无身份 Facebook 连通请求。代理密码 MUST NOT 进入 renderer IPC、日志、设置文件或检测结果。

#### Scenario: 选择离线认证代理环境
- **WHEN** 用户选中一个浏览器未运行且保存了认证代理的 Facebook 环境
- **THEN** 主进程读取该 profile 的完整配置并后台检测一次，界面选择立即完成，浏览器保持关闭且不占槽位

#### Scenario: 快速切换环境
- **WHEN** 用户在短时间内连续切换多个环境
- **THEN** 客户端只为最终稳定选中的合格环境发起检测，同一环境已有检测在途时 MUST NOT 重复发起

#### Scenario: 密码不越过主进程边界
- **WHEN** 主进程用 AdsPower 返回的代理账号密码执行检测
- **THEN** fleet 快照、renderer IPC、日志和本机 settings 均不包含代理密码

### Requirement: 启动与唤醒 SHALL 复用短时预检结果
客户端 SHALL 按环境在内存中短时复用最近一次确定的预检结果。手动启动或冷待机唤醒遇新鲜成功结果 SHALL 直接继续；结果缺失、过期或正在检测时 SHALL 复用同一在途检测或补做一次，不得建立轮询。新鲜确定失败 SHALL 停止本次浏览器启动或唤醒并如实显示代理原因。

无法读取代理配置或检测设施自身异常 SHALL 表示“无法确认”，MUST NOT 冒充代理失效，也 MUST NOT 成为绕开既有启动行为的新单点阻断。客户端内修改代理配置后 SHALL 立即作废旧结果。

#### Scenario: 启动消费选择时的成功结果
- **WHEN** 用户选中环境后完成代理检测，并在结果有效期内点击启动
- **THEN** 启动流程直接复用结果，不重复请求代理检测，随后沿用既有浏览器启动流程

#### Scenario: 自动唤醒缺少结果
- **WHEN** 冷待机 Facebook 环境因系统任务自动唤醒且没有新鲜结果
- **THEN** 客户端在申请浏览器槽位前检测一次，成功后继续既有唤醒流程

#### Scenario: 确定失败不启动浏览器
- **WHEN** 检测确认代理类型、认证或连通性失败
- **THEN** 本次启动或唤醒失败，浏览器不被新建，并复用既有启动或冷待机失败处理，不新增代理专用重试定时器

#### Scenario: 检测设施未知不误杀启动
- **WHEN** AdsPower 配置读取或检测设施本身不可用，因而无法判断代理
- **THEN** 客户端显示无法确认并沿用既有启动行为，MUST NOT 显示代理无效

### Requirement: 预检状态 SHALL 与浏览器出口证据分离
客户端 SHALL 以独立安全投影展示代理预检状态。预检成功只能显示“代理可用”，MUST NOT 显示“代理已验证”或伪造浏览器实际出口；浏览器运行证据存在时 SHALL 继续由现有浏览器代际出口观测决定代理运行状态。

#### Scenario: 浏览器未启动但预检成功
- **WHEN** 离线环境的代理预检成功且没有当前浏览器代际证据
- **THEN** 代理入口显示“代理可用”及检测时间，浏览器实际出口仍显示未取得

#### Scenario: 浏览器启动后取得运行证据
- **WHEN** 同一环境随后启动浏览器并收到现有代理运行证据
- **THEN** 界面按运行证据显示已验证、疑似直连或无法确认，预检不得覆盖该结论

