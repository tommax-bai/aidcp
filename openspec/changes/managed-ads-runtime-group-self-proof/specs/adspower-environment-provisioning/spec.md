## MODIFIED Requirements

### Requirement: 幂等与生命周期——以 AdsPower user/list 为账本、预置分组/备注、单飞互斥

本 change 建的所有平台分身 SHALL 归入运营预先创建且名称严格等于 `aidcp` 的 AdsPower 分组。每次桌面应用会话第一次建立托管 AdsPower 运行时时，桌面外壳 SHALL 先经随包 CLI 自身的 `status`/`stop` 控制路径有界停止其登记的既有 CLI daemon，并确认停止完成后再用当前托管配置启动新 daemon；查询失败、停止失败或停止超时 SHALL 阻止继续创建并给出可操作错误。该受控重置每个成功建立的应用会话 SHALL 至多执行一次，MUST NOT 通过进程名扫描、`pkill` 或任意 PID 猜测去关闭独立 AdsPower 桌面应用或其他进程。

托管运行时建立后，CLI 实际上报的 API base SHALL 是本会话创建路径的单一权威；历史 renderer/settings `apiBase` MUST NOT 覆盖该 base 或把 `group/list`、`user/create` 导向其他端口。桌面外壳 SHALL 经该权威 base 的 `group/list` 解析预置分组当前 id，并以名称严格等于 `aidcp` 作为任何 `user/create` 前的自证。桌面外壳 MUST NOT 调用 `group/create`、MUST NOT生成后缀分组、MUST NOT 因分组查询失败或查无分组而继续 `user/create`。查询失败 SHALL 保留真实查询错误；查询成功但新建立的当前运行时仍未找到 `aidcp` SHALL 明确提示当前运行时账号/权限空间缺少该预置分组，不得把它表述成已经创建成功。

创建时 SHALL 把「意图账号 / 模板 / 建号机」写进分身 `remark`（随 `user/create` 一次写入、随 `user/list` 读回）。「有哪些分身、各绑什么代理」SHALL 以 AdsPower `user/list` 为**唯一账本**读取，MUST NOT 另建本机 write-ahead 台账（与 AdsPower 自身记录重复，徒增丢失 / 损坏 / 与 AdsPower 走样的同步面）。理由：号一旦登录、edge 一起即经握手把账号↔分身↔机器上报云端（见「握手载荷携带并持久化」需求），该上报已有、不重造；仅「创建后、登录前」空壳期云端不可见，而这段 AdsPower `user/list` 本就记着分身 + 各自代理，是现成账本。代理 SHALL 为**创建时可选项**：表单填了合法代理即随 `user/create` 下发 `user_proxy_config`，不填 SHALL 默认 `no_proxy` 建号（与历史行为逐位等价）；代理输入的归一与校验见「代理可在客户端配置」需求。创建动作在主进程 SHALL **单飞互斥**（同一时刻只一个创建在途，重入诚实返回「进行中」），渲染层触发控件 SHALL 在请求在途时禁用。崩溃后 SHALL 据下次 `user/list` 直接看见已建分身（在预置 `aidcp` 分组、带 `remark`，不丢账）。

#### Scenario: 既有 CLI daemon 在新会话中被有界重置
- **WHEN** 新桌面应用会话第一次建立托管 AdsPower 运行时，且随包 CLI 的 `status` 发现已登记 daemon
- **THEN** 桌面外壳先调用该 CLI 的 `stop` 并确认 daemon 已停止，再用当前托管配置启动新 daemon
- **AND** 本次成功建立的应用会话后续确保运行时时不重复停止该 daemon

#### Scenario: 已登记 daemon 无法停止时停止创建
- **WHEN** 首次托管运行时建立中的 CLI `stop` 失败，或有界确认后 daemon 仍在运行
- **THEN** 桌面外壳诚实提示 CLI daemon 无法停止及原始原因，并且不调用 `group/list`、`group/create` 或 `user/create`

#### Scenario: 独立 AdsPower 桌面占用默认端口时使用托管实际端口
- **WHEN** 独立 AdsPower 桌面或其他进程占用 `50325`，随包 CLI 启动后实际上报另一端口，且历史表单仍保存 `50325`
- **THEN** 创建路径以 CLI 实际上报端口为权威调用 `group/list` 与 `user/create`
- **AND** 桌面外壳不关闭独立 AdsPower 桌面，也不把创建请求发往历史表单端口

#### Scenario: 所有平台的新环境进入同一个预置分组
- **WHEN** 运维选择任一受支持平台并创建新环境
- **THEN** 桌面外壳在当前托管运行时解析名称严格等于 `aidcp` 的现有分组 id，并把该 id 传给 `user/create`
- **AND** 桌面外壳不调用 `group/create`

#### Scenario: 新建立运行时仍缺少预置分组时停止创建
- **WHEN** 当前托管运行时已重新建立且 `group/list` 查询成功，但仍看不到名称严格等于 `aidcp` 的分组
- **THEN** 桌面外壳明确报告当前运行时账号/权限空间缺少预置分组，并且不调用 `group/create` 或 `user/create`

#### Scenario: 崩溃后据 user/list 不丢账
- **WHEN** `user/create` 已成功建出分身但紧接着进程崩溃 / 关窗
- **THEN** 下次读 `user/list` 直接看见该分身（在预置 `aidcp` 分组、带 `remark`），无需本机台账即可续接

#### Scenario: 重复点击不双建
- **WHEN** 运维在创建在途时再次点击「创建环境」
- **THEN** 主进程单飞互斥拒绝重入、渲染层控件已禁用，MUST NOT 交错跑出两个各绑同一代理的分身
