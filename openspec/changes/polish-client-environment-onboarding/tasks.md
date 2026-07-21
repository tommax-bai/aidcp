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

## 4. 完整零环境引导态

- [x] 4.1 在 shell 中增加右侧首次引导结构，并用同一权威 `rosterEmpty` 原子切换标题栏、环境工作区和引导面板
- [x] 4.2 设计“创建环境 → 登录账号 → 开始运行”三步价值路径、唯一创建主按钮、键盘焦点和减弱动态效果样式
- [x] 4.3 隐藏零环境时的旧环境身份、平台、代理、生命周期操作、零值工作区和内部原因码；第一个真实环境进入花名册后完整恢复
- [x] 4.4 补充进入/退出零环境、CTA 直达创建、内部错误不泄漏、键盘语义和视觉布局回归测试，并完成实际窗口视觉检查
<!-- Session validation: fleet-console 75/75; npm run typecheck; node --check; git diff --check. Actual index.html/styles.css were checked at 1440x900 and 820x720: no horizontal overflow, CTA opened the existing create tab, and all three environment-scoped workspaces were hidden while Cloud/settings stayed reachable. -->
- [x] 4.5 在独立 worktree 完成聚焦测试、验收、完整测试、typecheck、OpenSpec strict 校验及 ff-only 集成；不部署 ECS、不构建安装包
<!-- Delivered as aidcp-edge 057ff4e to origin/master by ff-only push. Validation: fleet-console 75/75; acceptance 28/28; serial full suite 2141/2141; npm run typecheck; node --check; git diff --check. Visual QA passed at 1440x900 and 820x720 with no horizontal overflow, all environment-scoped workspaces suppressed, Cloud/settings reachable, and the CTA opening the create tab. Edge source-only change: no ECS deployment and no desktop installer build. -->

## 5. 首次引导视觉收口

- [x] 5.1 将右侧引导改为靠上定位，移除伪进度装饰，降低左侧占位卡强调度，并缩短第三步说明
- [x] 5.2 补充视觉层级和文案回归断言，在宽屏与窄屏实际窗口复核留白、换行、横向溢出和 CTA 路由
<!-- Session validation: fleet-console 75/75; npm run typecheck; node --check; git diff --check. Actual index.html/styles.css were checked at 1280x720 and 820x720: the card starts 74px below the content origin, the false progress decoration is absent, the 820px page has no horizontal overflow, the final step stays on one line, and the CTA opens the existing create tab. -->
- [x] 5.3 在独立 worktree 完成聚焦测试、验收、完整测试、typecheck、OpenSpec strict 校验及 ff-only 集成；不部署 ECS、不构建安装包
<!-- Delivered as aidcp-edge 989122e to origin/master by ff-only push. Validation: fleet-console 75/75; acceptance 28/28; serial full suite 2149/2149; npm run typecheck; node --check; git diff --check; OpenSpec strict validation. Edge source-only change: no ECS deployment and no desktop installer build. -->

## 6. 首次创建后的主界面接续引导

- [x] 6.1 为从零花名册创建的首个单环境增加双重权威确认，确认进入设置花名册与 fleet 后关闭环境管理并选中主界面
- [x] 6.2 在主界面启动按钮旁增加绑定精确环境的一次性提示、有限光环、主动关闭和减弱动态效果支持
- [x] 6.3 补充首次/后续/批量/失败/快照延迟、提示显示与清除的回归测试，并完成实际窗口交互检查
- [x] 6.4 在独立 worktree 完成聚焦测试、验收、完整测试、typecheck、OpenSpec strict 校验及 ff-only 集成；不部署 ECS、不构建安装包
<!-- Delivered as aidcp-edge a03b9a2 to origin/master after rebasing onto concurrent renderer changes. Validation: fleet-console 81/81; smoke + fleet 160/160; post-rebase fleet/smoke/companion-ui/ui-logic focused suites passed; acceptance 28/28; serial full suite 2158/2158; npm run typecheck; node --check; git diff --check. Visual and interaction QA passed at 1280x720 and 820x720: the guide stayed inside the summary layout, pointed to the exact start action, did not overflow, did not steal focus, and closed on click. -->

## 7. 启动加载态与大窗口视觉收口

- [x] 7.1 增加 fleet roster `loading / ready / error` 三阶段，HTML 首帧先展示中性加载骨架，权威快照后再进入零环境或日常态
- [x] 7.2 增加读取失败重试且禁止失败冒充零环境；保留不支持 fleet API 的旧主进程兼容路径
- [x] 7.3 用自适应间距与非语义化低对比环境光收口大窗口底部留白，并补充减弱动态、矮窗和窄窗样式
- [x] 7.4 补充老用户无空态闪烁、零环境加载收敛、失败重试和视觉布局测试
<!-- Runtime source-only delivery: no ECS deployment and no desktop installer build. Actual-page QA covered loading, confirmed-empty, and first-start states; the empty-state ambient treatment carries large-window whitespace without fake environment rows, metrics, or progress semantics. -->

## 8. 同机历史环境下的首次交接修复

- [x] 8.1 首次创建候选仅以当前账号权威 fleet 零环境为准，本机其他账号或历史 settings roster 不得阻断自动关窗与启动引导
- [x] 8.2 补充同机历史环境回归测试，完成聚焦测试、typecheck、OpenSpec strict 校验、ff-only 集成与默认分支推送；不部署 ECS、不构建安装包
<!-- Delivered as aidcp-edge cafc771 to origin/master by ff-only merge and push. Validation: the regression failed before the fix and passed after it; fleet-console 82/82; renderer smoke + fleet + companion-ui + ui-logic passed; acceptance 32/32; full suite 2177/2177; npm run typecheck; node --check; git diff --check; OpenSpec strict validation. Source-only Edge delivery: no ECS deployment and no desktop installer build. -->

## 9. 登录后的账号环境原子加载

- [x] 9.1 将 settings、当前账号环境同步和最终 fleet 读取串行为一个 loading 阶段，登录初期空快照不得提前触发新用户空态
- [x] 9.2 补充老用户登录同步延迟回归测试，完成聚焦测试、验收、全量测试、typecheck、OpenSpec strict 校验、ff-only 集成与默认分支推送；不部署 ECS、不构建安装包
<!-- Delivered as aidcp-edge 13b4025 to origin/master by ff-only merge and push. Validation: the delayed account-roster regression failed before the fix and passed after it; unresolved account sync plus empty fleet stays retryable instead of entering onboarding; fleet-console 84/84; renderer smoke + fleet + companion-ui + ui-logic 302/302; acceptance 29 passed with the gated real-machine E2E skipped; final committed tree full suite exited 0; npm run typecheck; node --check; git diff --check. Source-only Edge delivery: no ECS deployment and no desktop installer build. -->
