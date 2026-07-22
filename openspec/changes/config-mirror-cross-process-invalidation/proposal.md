## Why

云端有 15 处进程内配置镜像（分布在 14 个 store），全部只在 `init()` 和**本进程写入**时刷新。全仓无 watch、无 `setInterval` 刷配置、无 `LISTEN/NOTIFY`——`aidcp-cloud/src/config/` 与 `src/risk/` 下 `setInterval|LISTEN|NOTIFY|pg_notify` 命中数为 0，`src/server.ts:1430` 的注释已把这条性质写死。

这不是「拆分之后才会出现」的问题，今天已经在生产上成立：dev 与 ol 是**两个进程共用同一个 PostgreSQL 库**（`docs/deployment-environments.md:64-70`），而 `quota_config`、`pacing_floor_config`、`session_config_global`、`resume_config_global`、`model_config`、`role_config`、`category_config`、`hot_lead_config` 这 8 张表都是全局表、无 `execution_target` 列。在 dev 控制台改一个全局安全限额，ol 进程的镜像**到重启才可见**，中间没有任何日志、没有任何告警、后台还回显写入成功。拆成 `aidcp-api` / `aidcp-content` / `aidcp-automation` 之后，同一缺陷会从「跨 target 不可见」放大成「跨服务永远不可见」。

更硬的约束是读取契约：这些镜像的消费点被代码写死为「同步、零 IO、永不抛」（`aidcp-cloud/src/risk/types.ts:21-40`），`canDo` 在浏览闭环每个动作都调；人设闸是同步读镜像、读不到即返回 `false`（`src/server.ts:2618`、`:3154`、`:3479`、`:3661`）。方案 §5.1:233 的「任务创建时引用版本或快照」与 §6.1 的请求式内部 HTTP，**在形态上都满足不了这个契约**：浏览会话不是任务、没有创建时刻，而 controller 一旦建成永不驱逐（`src/risk/types.ts:38-40`），构造期快照会让后台改动到重启前零生效且零日志。

还有一条方向相反的隐患：今天两个热路径镜像是 **fail-open** 的——`src/account-state.ts:62` 的 `isPaused` 缓存 miss 即视为 `active`，`openspec/specs/accounts-master-data/spec.md:104-110` 把「人设行不存在」直接定义为「未绑」。同进程下这两条都正确（镜像是全量持久化投影）。一旦镜像变成跨进程副本，「副本里没有」就不再等于「库里没有」：前者会让被暂停的账号继续对真实平台动作，后者会把「未知」压成「未绑」，复现 change `persona-bound-tristate` 已经修掉的误弹向导，并把用户委托任务判成非重试终态 `needs_persona_setup`（`src/delegated-task/worker.ts:361-366`）。

## What Changes

- **归属重排**：`quota_config` / `pacing_floor_config` / `session_config_global` / `resume_config_global` 四个配置存储随其消费方一并归 `aidcp-automation`。依据已核实：`src/risk/` 对 `src/config/` 的 import 命中数为 0，而 `src/config/` 有 13 处 import `src/risk/`，依赖方向今天已经单向倒置。归属对齐后一次性消除四条跨服务同步读，`interaction-risk-gating` 的「每次现读、改完即热生效、MUST NOT 需要重启」逐字保住。
- **新增跨进程失效通道**：单张 `config_mirror_version` 版本表 + 消费侧有界轮询刷新器。版本表轮询是**权威且唯一承重**的通道；`pg_notify` 只作为可选的延迟加速器，MUST NOT 成为唯一通道。
- **镜像分两档**：闸门镜像（取值可决定是否对真实平台下发动作）与参数镜像（只改变动作参数）。闸门镜像 MUST 声明陈旧上限，超限即**停手**，MUST NOT 拿旧值继续放行真实平台动作，也 MUST NOT 用「回落最严档继续跑」代替停手。
- **never-brick 适用面收窄**：现有「提供者缺失即回落写死默认」只适用于**权威已答但缺行/值非法**，MUST NOT 适用于**权威未答（副本陈旧或不可达）**。
- **三态贯穿服务契约**：人设绑定判据从二值 `boolean` 改为 `bound | unbound | unknown`；`unknown` 映射成独立不可用态 `persona_unavailable`，MUST NOT 下发 `personaBound` 字段、MUST NOT 置 `needs_persona_setup`、MUST NOT 让委托任务落非重试终态。运营暂停态与环境自动化出口闸同族三态化。
- **展示与生效同源**：归属迁走后，面板对四类安全配置的读回值 MUST 透传权威服务，MUST NOT 由 `aidcp-api` 本地副本回答。

## Capabilities

### New Capabilities

- `config-mirror-invalidation`: 跨进程配置镜像的版本推进、失效刷新、有界陈旧度与陈旧停手契约。

### Modified Capabilities

- `interaction-risk-gating`: 四类限频配置存储随消费方归属 automation；never-brick 回落不覆盖「权威未答」；慢启动锚点作为跨服务副本时陈旧即停手。
- `accounts-master-data`: 人设绑定派生字段与运营暂停态在跨进程副本下升为三态，未知不得压成「未绑」或「活跃」。
- `persona-gated-session-start`: 会话启动闸从二值改三值，`unknown` 走独立不可用态而非未绑拒绝。
- `account-persona-config`: 人设写入在持久化成功后于同一事务推进镜像版本，供跨进程消费方失效。
- `user-delegated-tasks`: 权威未答导致的阻塞 MUST 判可重试延后，MUST NOT 判非重试终态。
- `console-panel-api`: 归属迁移后四类安全配置的面板读回值必须来自权威服务。

## Impact

- Cloud：`src/config/` 与 `src/risk/` 的模块归属划线；新增 `config_mirror_version` 表与迁移；新增镜像刷新器；`isPersonaBound` / `isPaused` / 环境出口闸三处签名由二值改三值；`src/delegated-task/worker.ts` 的终态分档；面板四类安全配置读路径改为权威透传。本变更**不改协议消息类型**，不触碰两份 `protocol.ts` 与命令桥动作映射。
- Edge：无代码改动。`personaBound` 的线上三态语义（`src/comm/protocol.ts:695-701`）保持不变——云端在 `unknown` 时**不下发该字段**，正是边缘既有的「未知」表达方式。
- Console：无契约改动。四类安全配置的读写端点与语义不变，只是服务端实现从本地镜像改为权威透传。
- Control：更新 `docs/cloud-service-decomposition-proposal.md` 的 §4.4 / §5.1 / §6.1 / §11 / §14；本变更为拆分方案的阶段 1 前置交付物，不改变拆仓决策本身。
