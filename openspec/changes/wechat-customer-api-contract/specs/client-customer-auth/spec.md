## ADDED Requirements

### Requirement: 客户 API 路径清单必须由契约测试逐条覆盖

冻结契约（`docs/contracts/wechat-channels-interaction/v1/README.md` 的 Customer API 路径块）SHALL 有一份机器可读的路径清单 `route-inventory.json`，作为云端契约测试的唯一驱动源。云端 MUST 为清单中每条路径提供一个「真拼 URL、打真 HTTP、断言契约规定状态码」的契约测试用例；测试 MUST NOT 在客户 API 边界打桩绕开 URL 组装。清单中任一路径在云端退化为路由未命中（「接口不存在」）时，测试套件 MUST 失败。

新增或修改客户 API 路径时，MUST 先改清单、再改实现与测试；清单与云端实际路由不一致 MUST 使测试失败，MUST NOT 只靠人工比对两份文档发现漂移。

#### Scenario: 冻结路径在云端未实现即被测试拦下

- **WHEN** 契约清单声明 `PUT /environments/:envKey/replies/:jobId/draft`，而云端只实现了不带 `/draft` 段的版本
- **THEN** 契约测试对该路径的真 HTTP 请求收到路由未命中而非契约规定的成功响应，测试失败并指明是哪条路径漂移
- **AND** 该失败 MUST NOT 因为其他路径全绿而被掩盖

#### Scenario: 授权客户走通全部冻结路径

- **WHEN** 契约测试以 enabled 且持有该 env 权威归属的客户身份，按清单逐条请求全部客户 API 路径
- **THEN** 每条路径返回契约规定的状态码与 envelope（成功为 2xx 且 `meta` 含 requestId/asOf；契约明确规定 409/422 的用例返回对应码）
- **AND** 任一路径返回路由未命中即判失败

### Requirement: 草稿保存必须实现冻结的五段路径

云端 SHALL 在 `PUT /environments/:envKey/replies/:jobId/draft` 上实现草稿保存，与冻结契约、契约文档与客户端逐字一致。云端 MUST NOT 要求客户端改用未在契约中出现的路径形态；MUST NOT 保留从未进入契约的四段 `PUT /environments/:envKey/replies/:jobId` 作为别名。

#### Scenario: 客户保存草稿成功

- **WHEN** enabled 且有该 env 权威归属的客户以正确 `expectedVersion` 与 `finalText` 请求五段草稿路径
- **THEN** 云端返回 2xx 与 job 真态，草稿文本已落库

#### Scenario: 改稿后批准不再被草稿保存拖垮

- **WHEN** 客户先编辑草稿再批准，客户端因此先发一次草稿保存
- **THEN** 草稿保存成功，批准基于保存后的版本继续，MUST NOT 因路由未命中而使整条改稿链路不可达

### Requirement: 授权事务不得包住模型调用与外部往返

客户请求的授权边界（enabled user、权威 env ownership、interaction account binding）SHALL 在一个短事务内完成校验并取得 scope。该事务 MUST NOT 包住大模型调用、边缘往返或任何其他不受本进程时间约束的外部 I/O——单次模型调用天花板为 180 秒，持锁至其结束会阻塞边缘状态上报与环境解绑，并可让并发请求耗尽共享连接池、令全部租户的互动接口一起超时。

长耗时业务 SHALL 在授权事务之外执行；其结果落库前 MUST 在新的短事务内复核同一授权边界，并以 `expectedVersion` CAS 提交。复核失败（归属已撤销、账号已解绑、版本已变）MUST 拒绝写入并返回契约规定的 404 或 409，MUST NOT 部分写入，MUST NOT 把已失效的授权当作仍然有效。

#### Scenario: 重新生成期间不持有授权锁

- **WHEN** 客户请求 regenerate，云端需要连续发起多次模型调用
- **THEN** 授权事务在取得 scope 后即提交并释放连接与行锁，模型调用在事务外进行
- **AND** 同一时间边缘的状态上报与该环境的解绑操作不被该请求阻塞

#### Scenario: 生成期间归属被撤销则拒绝写入

- **WHEN** 模型调用进行期间管理员撤销了该客户对该 env 的归属，随后生成结果准备落库
- **THEN** 落库前的短事务复核发现授权已失效，写入被拒绝并返回不可枚举 404
- **AND** 该 job 不留下任何部分写入

#### Scenario: 并发重新生成不打满连接池

- **WHEN** 多个客户并发请求 regenerate
- **THEN** 每个请求只在鉴权与落库两个短窗口内占用数据库连接，MUST NOT 在整个模型调用期间独占连接
- **AND** 其他租户的互动接口在此期间仍可正常响应

### Requirement: 鉴权失败必须区分结构性无权与暂时不可判定

鉴权返回 404「资源不存在」SHALL 仅用于**结构上确定无权或确定不存在**的情形（无归属、归属已撤销、账号绑定不匹配、资源不属于该 env/account）。数据库暂时不可用、连接暂时取不到、依赖表尚未就绪等**暂时无法判定**的情形 MUST NOT 被判为 404，MUST 返回可重试的服务不可用状态并如实标注 `retryable`。

任何把「暂时不可判定」降级为拒绝的实现 MUST 说明恢复路径：依赖恢复后下一次请求即须正常放行，MUST NOT 需要客户重新登录、重新绑定或人工介入解除。

#### Scenario: 数据库暂时不可用不谎报无权

- **WHEN** 鉴权查询因数据库暂时不可用或连接耗尽而无法完成
- **THEN** 云端返回可重试的服务不可用错误，MUST NOT 返回 404「资源不存在」
- **AND** 数据库恢复后客户的下一次请求即被正常放行，无需任何人工操作

#### Scenario: 确定无权仍返回不可枚举 404

- **WHEN** 客户请求一个自己确无归属的 env
- **THEN** 云端返回不可枚举 404，与「不存在」不可区分，MUST NOT 泄漏资源存在性
