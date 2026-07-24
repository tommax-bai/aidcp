# AIDCP 文档导航与维护规则

本页区分“当前系统说明”“行为契约”“设计参考”和“历史证据”。读者应先确定要回答的
问题属于哪一层，避免把旧交接、设计设想或测试快照当作当前运行事实。

## 1. 当前系统说明

这些文档描述长期有效的边界和工作方式。涉及实现细节时，仍应以代码和运行态复核。

| 文档 | 用途 |
| --- | --- |
| [`../README.md`](../README.md) | 系统入口、仓库边界和主路径 |
| [`architecture.md`](architecture.md) | Edge / Cloud / Console 组件职责与数据流 |
| [`protocol.md`](protocol.md) | 边云协议 v2 的消息与时序 |
| [`deployment-environments.md`](deployment-environments.md) | dev / ol 边界、检查和部署安全流程 |
| [`parallel-dev-worktrees.md`](parallel-dev-worktrees.md) | 多仓 worktree 与集成规范 |
| [`risk-control.md`](risk-control.md) | 风控机制、配额与状态语义 |
| [`acceptance-tests.md`](acceptance-tests.md) | 代码验证、协议验证和真机验证分层 |
| [`real-machine-acceptance-backlog.md`](real-machine-acceptance-backlog.md) | 尚未完成的共享机器/真实平台验证 |

`protocol.md` 和 `risk-control.md` 会随行为契约更新，但它们不能单独证明代码已部署或真实
平台已验证。部署与真机结论必须有对应的任务记录和运行证据。

## 2. 行为契约与当前进度

- `openspec/specs/`：已合并的行为契约基线。
- `openspec/changes/<change>/`：正在推进的 proposal、design、spec delta 和 tasks。
- `openspec/changes/archive/`：已归档变更的证据，不代表当前仍有待办。
- `docs/contracts/`：需要跨端保持一致的 schema、fixture 与真实证据样本。

查询当前状态时使用命令，不在总览文档复制统计数字：

```bash
openspec list
openspec list --specs
git worktree list
```

代码是否已实现要到所属 sibling repo 查看；是否已部署要核对目标环境服务、监听、health、
日志和数据库；是否通过真实平台验证要看 `real-machine-acceptance-backlog.md` 中对应项是否有
真实证据。自动化测试通过不能替代真机结论。

## 3. 产品与专题设计参考

以下文档用于解释产品意图或专题设计，不是当前实现清单：

- [`product-overview.md`](product-overview.md)
- [`product-dashboard.md`](product-dashboard.md)
- [`product-feishu.md`](product-feishu.md)
- [`product-task.md`](product-task.md)
- [`product-exception.md`](product-exception.md)
- [`anti-detection.md`](anti-detection.md)
- [`design-gaps-and-models.md`](design-gaps-and-models.md)
- [`design/conversation-driven-agent-client.md`](design/conversation-driven-agent-client.md)
- `design/` 与 `research/`

这些文档中的界面、字段、状态或路线图可能只处于设计阶段。实现判断必须回到 OpenSpec、
代码和运行态；若内容已成为行为契约，应迁入或同步到 OpenSpec，而不是继续在设计文档中
维护第二份权威定义。

## 4. 历史材料

按日期命名的 `handoff-*`、`deferred-verification-*` 仅用于追溯当时现场。它们包含当时的
分支、提交、测试数量、部署状态和未完成判断，不能用于回答“现在是什么状态”。清理时仅
保留仍被归档 OpenSpec 直接引用的证据；孤立且已被 tasks 或真机 backlog 接管的快照应删除。

需要查看已删除历史内容时使用 Git 历史，而不是把快照重新放回当前文档入口：

```bash
git log --all -- docs/
git show <commit>:docs/<historical-file>.md
```

## 5. 维护规则

1. 稳定入口写机制和事实源，不硬编码角色数、消息数、测试数或活跃 change 数。
2. 环境地址、服务名、密钥路径等易变运维事实只维护在 `deployment-environments.md` 和脚本中。
3. 新行为先写 OpenSpec；不要直接把设计稿或 README 改成新的行为契约。
4. “已受理”“已授权”“已下发”“平台已确认”分别表述，禁止合并成模糊的“成功”。
5. 真实平台、破坏性迁移和共享机器验证没有发生时，明确记录为未验证并登记 backlog。
6. 文档链接必须保持可解析；删除材料前先清理或改写引用。
