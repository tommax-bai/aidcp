## Context

视频号 API-only 运行依赖浏览器授权时采集并加密保存的 Cookie 与请求上下文。浏览器页面的登录态与该 API 快照不是同一个事实：页面可以继续显示已登录，而平台已经轮换 Cookie 或使请求上下文失效。现场在同一会话上观察到业务码 `300334` 同时影响身份、帖子和私信读取，且浏览器 Cookie 已与快照发生漂移。

客户工作区的鉴权状态来自 Cloud 列表响应。当前没有独立的 renderer 推送通道，因此列表轮询本身就是鉴权状态收敛通道；用旧鉴权状态反过来停止该通道会形成自锁。

## Decisions

### Classify only the proven authorization-context code

`classifyHttpFailure` 只对平台业务码 `300334` 返回 `auth_expired`。该分类复用既有 `WECHAT_AUTH_REQUIRED` 和浏览器重新授权状态机，不新增协议枚举。其他 `platform_rejected` 继续保持原状，避免把任意业务拒绝误判成掉登录。

错误对象保留可安全输出的 `httpStatus` 与 `platformCode` 元数据。日志只输出稳定 endpoint、错误码和这些标量，不输出平台 message 或任何请求/响应材料。

### Reuse the existing sidecar refresh path

授权协调器已经能在 `auth_expired` 时打开 sidecar。sidecar 会在附着后启用 Network、刷新目标页、重新捕获请求上下文并读取当前 Cookie；随后身份与只读能力探针仍是保存新快照前的硬门禁。因此不新增旁路 Cookie 写入、不直接读取 AdsPower profile 文件，也不允许“浏览器页面能打开”冒充鉴权成功。

### Keep auth convergence independent from auth state

工作区可见且环境在线时，列表轮询持续运行：首次无快照时使用快速轮询，已有快照后使用既有低频轮询。鉴权状态、读取开关和当前读取能力只控制操作门禁，不再控制真态刷新通道本身。

重新授权请求被 Cloud 接受后不直接合成成功；renderer 依靠后续列表响应收敛到 Edge 实际上报的状态。

### Render reported closed state honestly

`browserState=closed` 是明确回报。`active + closed` 继续显示“后台模式”；非 active + closed 显示“已关闭”。只有 auth 或 browserState 缺失时才显示“未回报”。

## Testing

- 错误分类：`300334` 在 HTTP 200 下映射为 `auth_expired` 并保留安全元数据；其他平台码仍为 `platform_rejected`。
- 授权协调器：运行期 `300334` 进入 reauth/browser sidecar 流程，成功采集后恢复 `active`；非授权平台拒绝不误开浏览器。
- 连接器日志：包含 endpoint / HTTP 状态 / 平台码，不包含 Cookie、响应正文或合成敏感值。
- renderer：`login_required`、读取关闭和 `degraded` 状态仍安排后续刷新；`closed` 文案按授权状态正确区分。
- 运行 focused tests、acceptance、full tests 与 typecheck。
