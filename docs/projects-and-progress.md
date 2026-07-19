# AIDCP 当前进度查询指南

本文件保留旧路径，避免历史引用失效；它不再保存容易过期的项目进度快照。

## 查看当前工作

```bash
./scripts/task-preflight
openspec list
git worktree list
```

- `openspec list` 是活跃 change 及任务完成度的入口。
- `git worktree list` 用于确认实际并行分支，不能仅凭 change 名判断代码是否已集成。
- change 的 `tasks.md` 记录所属 repo、提交、验证、部署和偏差；勾选完成不自动等于已归档。

## 查看已经形成的契约

```bash
openspec list --specs
openspec validate <change-name> --strict
```

`openspec/specs/` 是已合并行为契约；`openspec/changes/archive/` 是历史变更证据。不要从旧
handoff、旧测试数量或某次部署记录推断当前能力。

## 核验“已经实现/已经上线”

1. 在 owning repo（`aidcp-edge` / `aidcp-cloud` / `aidcp-console`）确认目标提交已进入默认分支。
2. 在 owning repo 运行与风险范围相称的聚焦测试、验收测试和 typecheck。
3. 运行态变化默认核对 dev；ol 只在明确发布范围下核对 release 分支。
4. 服务状态、监听、health、日志、数据库和当前部署产物才是部署事实。
5. 真实平台动作或共享机器场景没有实际执行时，状态只能写“待真机验证”，并登记到
   [`real-machine-acceptance-backlog.md`](real-machine-acceptance-backlog.md)。

完整文档分层见 [`README.md`](README.md)。
