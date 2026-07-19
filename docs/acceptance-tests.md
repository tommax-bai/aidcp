# AIDCP 验证与验收策略

本文定义验证层级、执行入口和证据边界，不维护测试文件总数或协议消息总数。测试清单会随
实现演进，准确范围以各 sibling repo 的 `package.json`、`test/` 和类型定义为准。

## 1. 验证层级

| 层级 | 目的 | 典型依赖 | 能证明什么 |
| --- | --- | --- | --- |
| 聚焦单元/集成 | 验证本次改动及相邻路径 | 内存桩、jsdom、mock 服务 | 代码逻辑与回归闸通过 |
| 验收测试 | 守住跨模块安全与协议契约 | `test/acceptance/` | 红线、边云契约和关键流程未漂移 |
| 全量测试 + typecheck | 检查 owning repo 的总体回归 | repo 本地依赖 | 当前 checkout 的自动化验证通过 |
| 部署验证 | 核对指定 ECS 上的真实服务 | dev 或 ol、服务/端口/PG | 指定产物已运行且基础依赖健康 |
| 真机/真实平台验收 | 验证真实 DOM、账号、平台回执与人工界面 | Edge 客户端、真实浏览器与账号 | 目标场景在真实环境中发生并得到证据 |

自动化测试通过不能证明已经部署，也不能证明平台动作真实发生。握手成功只证明 WebSocket
通道可用，不能替代账号、浏览器、页面动作或平台回执验收。

## 2. 本地代码验证

首次进入新 worktree 时，每个 sibling repo 都必须安装自己的实体依赖树：

```bash
npm ci --prefer-offline
```

不要在 worktree 之间链接 `node_modules`。按改动范围先跑聚焦测试，再执行对应仓库的验收、
全量测试和类型检查：

```bash
# 在 aidcp-edge 或 aidcp-cloud 中
npm test -- <focused-test-pattern>
npm run test:acceptance
npm test
npm run typecheck
```

实际 test runner 是否支持额外 pattern 以该 repo 的 `package.json` 为准；不确定时直接用其中
记录的脚本。`aidcp-console` 使用它自己的脚本，不从 control repo 代跑。

协议、风控或发布改动的最低收口顺序是：聚焦测试 → 验收测试 → 全量测试 → typecheck。
文档或配置维护只运行与所改事实相关的静态检查和 OpenSpec 校验，不在 control repo 根目录
运行应用测试。

## 3. 跨仓契约验证

边云协议的权威实现投影位于：

- `aidcp-cloud/src/comm/protocol.ts`
- `aidcp-edge/src/comm/protocol.ts`
- 两仓 `test/acceptance/protocol-contract.test.ts`
- 本仓 [`protocol.md`](protocol.md)

协议消息新增、删除或改名时必须同步两端类型、Cloud command mapping、Edge active-command
路由、契约测试和 `protocol.md`。契约测试中的 `Record<MessageType, true>` 会让未同步的枚举在
typecheck 阶段失败；文档不再复制具体消息数量。

发布、风控和交互管理还需运行各仓现有的对应 acceptance 文件。不要依赖本文的文件名列表
判断覆盖是否完整，直接查看当前 `test/acceptance/`。

## 4. 部署与真机联调

### 4.1 先确认目标

任何 SSH、`rsync` 或远程验证前：

```bash
./scripts/deploy-target dev --check
# 只有明确要求线上发布时才使用：
./scripts/deploy-target ol --check
```

环境地址、密钥和服务名只以 [`deployment-environments.md`](deployment-environments.md) 与
`scripts/deploy-target` 的当前输出为准，不在验收文档复制。

### 4.2 Gated 连通性用例

Edge 与 Cloud 都保留 gated 的 `test/acceptance/real-e2e.test.ts`：

```bash
AIDCP_E2E=1 AIDCP_CLOUD_URL=<checked-ws-url> npm run test:acceptance
```

该用例验证 hello/welcome 与心跳等基础连通性。它不会自动执行发布、评论、点赞、验证码、
浏览器占用或部署完整性检查。

### 4.3 部署健康证据

Cloud 部署后至少核对：

- AIDCP 目标服务处于 `active (running)`；
- 文档规定的监听端口存在；
- health 路由返回健康；
- 飞书长连接已建立，或配置明确禁用；
- PostgreSQL `select 1` 成功，且数据库边界与目标环境一致；
- 当前部署产物对应预期分支和提交；
- 未触碰同机无关服务。

具体命令和回滚步骤见 `deployment-environments.md`。失败时不能只凭旧日志或自动化测试写成
部署成功。

### 4.4 真实平台验收

真实平台验证应记录：目标环境、Edge/Cloud 提交、账号与平台前置、实际动作、平台可见结果、
日志/截图/数据库证据以及是否涉及真实写入。未执行的场景登记到
[`real-machine-acceptance-backlog.md`](real-machine-acceptance-backlog.md)。

以下状态必须分开：

1. 请求被接受；
2. 人工已授权；
3. 命令已下发；
4. Edge 已执行；
5. 平台已确认结果。

只有拿到对应层级证据，才能声明该层成功。`submitted`、`scheduled`、`ambiguous`、
`needs_review` 等状态不得改写为 `published` 或 `confirmed`。

## 5. 收口记录

OpenSpec change 的 `tasks.md` 应简要记录：owning repo、落地提交、执行过的验证、部署目标与
结果、真机边界和偏差。完成后运行：

```bash
openspec validate <change-name> --strict
```

需要共享机器或人工继续验证的内容写入真机 backlog；不要留在临时 handoff 中当作长期
系统说明。
