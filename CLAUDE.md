# AIDCP 中控仓开发规范

> 本仓 `ai-dcp`（`/Users/bears/codes/ai-dcp`）是 **aidcp\* 家族的中控 / 总览仓**：
> 契约（架构 / 协议 / 产品设计）在这里定义，后续开发、测试、部署在这里**触发与编排**，
> 走 **openspec** spec-driven 流程。本文件是该仓的工作规范，约定 OVERRIDE 默认行为。

## 1. 三仓关系（类比 isales meta + sub-repos）

| 仓 | 路径 | 默认分支 | 角色 |
| --- | --- | --- | --- |
| **ai-dcp**（本仓，中控） | `/Users/bears/codes/ai-dcp` | `main` | 契约 / 文档 / openspec changes / 测试与部署编排 |
| **aidcp-edge** | `/Users/bears/codes/aidcp-edge` | `master` | 边缘端：CDP / 定位 / 浏览 / 拟人化 / 反检测 / 发布 / Electron |
| **aidcp-cloud** | `/Users/bears/codes/aidcp-cloud` | `master` | 云端：协议 / 事件驱动编排 / 风控 / 发布 / 概念池 / 飞书 Bot |

中控仓定义契约与变更，代码改动落到对应 sub-repo；进度回写在本中控仓的 openspec change 里。

## 2. openspec 工作流（参照 isales，spec-driven）

- 所有跨 spec 的功能改动都走 **openspec change 流程**，不要绕过 openspec 直接改 `openspec/specs/` 下的 spec 文件。
- 新 change：`openspec new change "<kebab-name>"` 或 `/opsx:propose "<想做什么>"`；探索/实装/归档用 `/opsx:explore` `/opsx:apply` `/opsx:archive`。
- **实装前**：先看 `openspec/changes/<active-change>/tasks.md`，定位当前要做的 task；不凭空起 task。
- **实装中**：代码改动落在对应 sub-repo（edge / cloud）；`tasks.md` 进度回写在本中控仓。tasks.md 按 sub-repo 分节（如 `## 1. aidcp-cloud — …`）。
- **实装后**：用 HTML 注释在 tasks.md 把 task 标 `[x]`，写清 PR# / commit-sha / 偏离说明，格式 `<!-- <repo> <commit-sha> 备注 -->`（部署完追加 `<!-- <date> deployed -->`）。
- spec delta 写在 `openspec/changes/<change>/specs/`；**完成 change 所有 task → `openspec validate <change> --strict` → archive**（archive 时 delta 合并进 `openspec/specs/`）。

## 3. git / 提交 / 推送（默认自动）

- **默认主动 `git commit` + `git push` 到 origin**（本中控仓 + 各 sub-repo 都适用），不需每次问。
- commit message 末尾带 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
- push 到各仓**默认分支**（本仓 `main`、edge/cloud `master`）。
- **仍需先确认**：force-push、非 fast-forward、推到非默认的 protected branch。
- commit message / PR 描述 / 命令 / 文件名保持英文；正文回复默认中文。

## 4. 测试（中控触发，落到 sub-repo 执行）

- edge：`cd /Users/bears/codes/aidcp-edge && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- cloud：`cd /Users/bears/codes/aidcp-cloud && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- 本地只做**代码级验证**；cloud 正式运行只在 ECS，本地**不要起 cloud**。

## 5. 部署（云端 ECS，带安全闸）

> **部署铁律**：cloud 只跑在 ECS `121.89.85.150`，本地永不起 cloud；edge 本地跑、连 `ws://121.89.85.150:8787`。
> **同机另有 `isales` 独立运行 —— 任何 ECS 操作绝不能碰 `isales`（不同 systemd 服务、不同目录、不同端口）。**

- ECS 上 cloud：`/opt/aidcp/cloud`，由 systemd `aidcp-cloud.service` 托管，对外监听 `8787`，PostgreSQL 同机 `127.0.0.1:5432` 库 `aidcp`。
- 部署是**显式的发布就绪动作**（不在每次 commit 自动触发），按安全序列执行：
  1. 对应 sub-repo 测试通过；
  2. ECS 上**先备份**当前版本（`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）；
  3. `rsync -av -e 'ssh -i ~/codes/isales-4.pem' --exclude .env --exclude node_modules --exclude .git <本地 src/等> root@121.89.85.150:/opt/aidcp/cloud/`；
  4. `systemctl restart aidcp-cloud.service`；
  5. healthcheck：服务 `active (running)` + `8787` 监听 + 飞书长连接已建立 + PG `select 1` 可通；
  6. 失败即回滚到备份。
- SSH：`ssh -i ~/codes/isales-4.pem root@121.89.85.150`（私钥必须 `chmod 600`）。
- 详见 `docs/handoff-2026-06-05.md` 与 `aidcp-cloud/docs/deployment-ecs.md`。

## 6. 沟通与收尾

- 默认中文回复；代码 / 注释 / commit / PR / 命令保持英文。
- **每次对话收尾给一段「说人话」的总结**：用非技术语言讲清楚——这次做了什么、对系统有什么影响、下一步是什么。技术细节照常给，但总结那一段要让非工程视角也能看懂。

## 7. 安全边界

- 文档 / 提交 / tasks.md 里**不记录任何敏感值**（PostgreSQL 密码、token、私钥内容）；只记路径、服务位置、命令用法、配置读取方式。
