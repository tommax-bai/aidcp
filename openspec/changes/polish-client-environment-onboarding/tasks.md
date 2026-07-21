## 1. 首次环境空态

- [x] 1.1 在 Edge renderer 中用权威全量花名册标记零环境专用状态，并只在该状态隐藏平台筛选、汇总、批量人设和全部启动/关闭
- [x] 1.2 将空态入口改为无平台/状态伪装的“创建第一个运行环境”占位卡，并让占位卡与零环境栏头管理入口直达“新建环境”页
<!-- aidcp-edge a0973be: confirmed-empty rail state and creation entry. -->

## 2. 环境管理与创建反馈

- [x] 2.1 将环境管理标题、文字页签和新建环境表单重排为平台、系统、渐进式代理及底部动作区
- [x] 2.2 增加创建中交互锁、按钮状态和单个成功后切回环境列表；失败与批量结果保留创建上下文
<!-- aidcp-edge a0973be: redesigned creation form and truthful creation feedback. -->

## 3. 测试与交付

- [x] 3.1 补充零环境、筛选空结果、直达创建、创建中锁和成功/失败上下文的 Electron 渲染测试
- [x] 3.2 在 aidcp-edge 独立 worktree 运行聚焦 Electron 测试、完整测试和 `npm run typecheck`
<!-- Validation: fleet-console 73/73; post-rebase focused suite 121/121; landing acceptance 28/28; landing full suite 2137/2137; npm run typecheck; node --check; git diff --check. Actual HTML/CSS was visually checked at 620px modal width with no horizontal overflow. -->
- [x] 3.3 更新本清单的提交与验证证据并运行 `openspec validate polish-client-environment-onboarding --strict`
<!-- OpenSpec strict validation passed after recording the implementation and validation evidence above. -->
- [x] 3.4 安全 fast-forward 集成并推送 `aidcp-edge/master`；记录本变更不部署 ECS、不构建安装包
<!-- Delivered as aidcp-edge a0973be to origin/master with the project land-change ff-only workflow. Edge source-only change: no ECS deployment and no desktop installer build. -->
