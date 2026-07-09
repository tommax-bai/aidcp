# Tasks: edge-client-proxy-platform-persona-ux

> 全部代码改动落 `../aidcp-edge`，在 worktree `../aidcp-edge.wt/edge-client-proxy-platform-persona-ux`（分支同名）开发；进度回写本文件（`<!-- <repo> <commit-sha> 备注 -->`）。本仓 change 文档提交经临时 worktree 到 `main`（主 checkout 停在他人分支）。
>
> **实装完成 2026-07-09**：aidcp-edge 单提交 `9f5e0b8`（rebase 到并发提交 d644f1e「facebook adspower account import」之上、冲突已两边保留式解决），ff 合入 master 并推送；typecheck 干净、验收 16/16、全量 809/809 绿。edge-only，无 ECS 部署，用户侧重建/electron:dev 生效。

## 1. aidcp-edge — 代理配置（问题 1/2）

- [x] 1.1 新建 `src/electron/ads-proxy-config.cjs`：`normalizeProxyInput()` 归一/校验（no_proxy/全空→`{proxy_soft:'no_proxy'}`；否则 `proxy_soft:'other'`、type∈{http,https,socks5}、host 非空、port 1-65535、有 password 必须有 user；非法诚实报错），导出 `PROXY_TYPES`。
  <!-- aidcp-edge 9f5e0b8 -->
- [x] 1.2 `ads-write-api.cjs`：`WRITE_ALLOWLIST` 增补 `user/update`；新增 `updateProfileProxy({userId, proxyConfig})` body 只构造 `{user_id, user_proxy_config}` 两键；头注同步（M7 生命周期红线不动）。
  <!-- aidcp-edge 9f5e0b8 -->
- [x] 1.3 `ads-create-flow.cjs` + `ads-create-env-service.cjs`：`createEnvironment`/`createEnvironmentWithGroupRecovery` 增可选 `proxy` 入参，经归一层校验（非法诚实拒建），合法下发、缺省仍 `no_proxy`；头注「代理全程手工」改口。
  <!-- aidcp-edge 9f5e0b8 与并发 d644f1e 的 accountImport 入参合并共存 -->
- [x] 1.4 `ads-local-api.cjs`：`normalizeProfile` 增结构化 `proxyConfig` 透传（type/host/port/user/noProxy，**不透传密码**），摘要字符串 `proxy` 保留零回归。
  <!-- aidcp-edge 9f5e0b8 -->
- [x] 1.5 `main.cjs`：`ads:createEnv` 透传 proxy；新增 IPC `ads:updateEnvProxy`（校验→归一→`updateProfileProxy`，错误友好化，成功提示「下次启动生效」）；`preload.cjs` 暴露 `adsUpdateEnvProxy`。
  <!-- aidcp-edge 9f5e0b8 rebase 时把 proxy 同时接进 d644f1e 的 FB 批量导入分支（每环境共用同一份代理输入） -->
- [x] 1.6 renderer：新建表单代理区块（类型下拉默认「无代理」，选类型后显 host/port/user/pass 行）+ 已有环境行「代理」按钮与编辑浮层（预填非密字段、密码空态、无代理=显式清除、画像跳变运营警示一句）；`readProxyForm()` 一处封装、轻量前端校验。
  <!-- aidcp-edge 9f5e0b8 浮层另带「当前：<摘要>」行——UI 下拉表达不了的代理厂商类型如实呈现、保存=整体替换 -->
- [x] 1.7 测试（克制）：`ads-proxy-config.test.ts` 归一化边界；`ads-write-api.test.ts` 禁止清单去掉 `user/update` + 新增「update 只带两键」「browser/* 仍抛错」断言；`ads-create-flow.test.ts` 新增带 proxy 下发用例（缺省 no_proxy 用例已有，仅改断言文案）。
  <!-- aidcp-edge 9f5e0b8 -->

## 2. aidcp-edge — 平台识别与平台化 UI（问题 3）

- [x] 2.1 `ads-local-api.cjs`：`inferPlatform(it)` 兜底推断链（remark 权威 → domain_name → open_urls → 分组/名称关键词 → 回落 xhs），输出 `platformSource`，缺字段安全降级；表驱动单测（remark 胜 domain 胜关键词、全空回落、fb 域名命中）。
  <!-- aidcp-edge 9f5e0b8 -->
- [x] 2.2 renderer 加入面板：环境行显式改平台入口（写既有 `saveSettings(environments)` 通道）+ 非 remark 来源标注「平台未标注（推断）」+ 平台标签染色。
  <!-- aidcp-edge 9f5e0b8 实现为每行「改平台」切换钮；花名册成员的人工标注显示优先于列表推断（防下次刷新悄悄改回）；推断来源以「?」后缀+title 提示 -->
- [x] 2.3 `styles.css`：`--plat-fb:#1877f2` 与 `.plat-facebook` 系列（rail 头像底色表平台、色环仍表状态；顶栏徽标蓝底）。
  <!-- aidcp-edge 9f5e0b8 -->
- [x] 2.4 renderer：`makeRailRow` 追加 `plat-<platform>` 类且 **renderRail 重建签名加入 platform**；`renderTitlebar` 随选中环境更新 `.acct-p` 文案/配色与 `#acct-ava`；健康浮层「小红书登录」行与登录提示文案按平台切换。
  <!-- aidcp-edge 9f5e0b8 另补：快照里选中环境平台变化时立即重渲染标题带（不等下一次状态心跳）；ui-logic fleetRailModel rows 增 platform 字段 -->
- [x] 2.5 平台类断言 + 签名含 platform 断言（防「改平台 UI 不刷新」回归）。
  <!-- aidcp-edge 9f5e0b8 fleet-console.test.ts「平台标识」用例：行类/顶栏徽标/改平台后重建 -->

## 3. aidcp-edge — 登录态投影修复（问题 4/5）

- [x] 3.1 `main.cjs` 身份事件分支（~1316）补 `next.auth='logged in'`；子进程 exit/spawn-error 对 adspower 复位 `auth:'checking'`。
  <!-- aidcp-edge 9f5e0b8 依据既有不变量：核心只在真读出登录身份后打「账号身份已确立」（读不出即诚实 halt），映射不构成静默假成功；self 幂等无害 -->
- [x] 3.2 renderer `openPersonaPop`：改用目标环境自身 status 评闸（无 status 按中立态），杜绝跨环境串状态。
  <!-- aidcp-edge 9f5e0b8 -->
- [x] 3.3 `fleet-console.test.ts` 删除手动 `gen.disabled=false` 放行，让用例真走「状态推送→闸开启」链路。
  <!-- aidcp-edge 9f5e0b8 改为断言「登录+连云后按钮必须自然可点」 -->

## 4. aidcp-edge — 人设浮层重设计（问题 6）+ rail 字形（问题 7/8）

- [x] 4.1 `index.html`：`#persona-pop` 内部重排——sticky 头（头像身份锚点 + 平台小标）/ 滚动体 / sticky 底部操作栏；两步指示（复用 .j-step）；三组关键词区块卡；结果区 identitySummary 标题 + `<details>` 折叠 YAML；`role="dialog"`。
  <!-- aidcp-edge 9f5e0b8 既有 id 全部保留（personaUi/测试零迁移成本） -->
- [x] 4.2 `styles.css`：`.persona-pop` 与 `.env-add-panel` 拆开选择器并放宽 560px；`.persona-body/.persona-foot/.persona-card/.kw-btn`（描边浅底/hover/选中蓝✓/focus 环）/`.persona-empty`/`.persona-alert`/骨架（respect prefers-reduced-motion）；补 `.badge.checking`；删死样式 `.persona-config`。
  <!-- aidcp-edge 9f5e0b8 错误警示条实现为 .persona-msg.error（红底描边），未另立 .persona-alert 类名；loading 用骨架条+按钮文字「正在生成…」传达（未做 CSS spinner，reduced-motion 下骨架自动静态化） -->
- [x] 4.3 renderer：stage 切换（选关键词↔预览确认，切环境清草稿同步回 Stage1）；空态/已绑态面板替代 hint 改写（「去启动」复用 FAB 流程）；生成 loading（骨架+in-flight 忽略遮罩关闭一次）；错误警示条（`setPersonaMsg` 驱动，签名不变）；主 CTA 换 `.setup-btn`；Escape 关闭 + `aria-pressed` + 兴趣「已选 n」计数。
  <!-- aidcp-edge 9f5e0b8 「去启动」按 FAB 三态分流：可启动则触发启动，已在运行（等登录）则抬浏览器窗口；行为契约（闸三态/草稿锚定/状态推送不重置已选/诚实失败）未动 -->
- [x] 4.4 `rail-add` 全角＋换内联 SVG 加号；`rail-toggle` 换 SVG chevron，`renderer.js` textContent 切换改 class（flip）切换。
  <!-- aidcp-edge 9f5e0b8 rail-foot-add（收起态加号）一并换 SVG -->
- [x] 4.5 关键行为用例（克制）：stage 切换不丢草稿、gate 面板显隐；视觉项转真机 backlog。
  <!-- aidcp-edge 9f5e0b8 fleet-console.test.ts「人设浮层」用例：空态面板/待启动徽标/生成进预览/改关键词回退草稿保留仍可确认 -->

## 5. 验证与集成

- [x] 5.1 worktree 内 `npm run typecheck` + `npm test`（全量）绿。
  <!-- rebase 前 802/802、rebase 后 809/809（含并发 FB 导入新用例）、typecheck 均干净 -->
- [x] 5.2 fetch + rebase 最新 master（撞上并发 d644f1e「facebook adspower account import」，5 文件冲突两边保留式解决：accountImport 与 proxy 入参共存、FB 批量导入循环带 proxy），`test:acceptance` 16/16 + 全量复跑 809/809，ff 合入 master 并 push（d644f1e..9f5e0b8）；主 checkout 已 ff 更新；worktree/分支已删。
  <!-- aidcp-edge 9f5e0b8 -->
- [x] 5.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（簇 29，原子 append）：人设闸、代理 update 语义、FB 环境推断识别、重设计视觉项；并注明簇 17/21 的徽标语义未变、hint 文案判据由簇 29 取代。
- [x] 5.4 本仓：tasks 回写 + `openspec validate edge-client-proxy-platform-persona-ux --strict`；**归档暂缓**——本 change 的 `platform-runtime-abstraction` delta 扩展活跃 change `edge-environment-platform-select` 的回落行为，归档须排在其后（其 task 2.3 真机验收 GATED on FB driver）。
  <!-- 2026-07-09 用户令提前归档：两 change 对 platform-runtime-abstraction 均为 ADDED、需求条目独立不冲突；platform-select 后归档时其条目照常合入，语义引用关系已写进本 change 条文 -->
