# Design: edge-client-proxy-platform-persona-ux

## Context

全部改动落 `aidcp-edge` 的 Electron 壳层（`src/electron/`：主进程 `main.cjs`、渲染层 `renderer/` 三件套、AdsPower 读写模块 `ads-*.cjs`）。现状与根因（10-agent 调查 + 对抗验证 confirmed，`文件:行` 以 2026-07-09 master `833a4ee` 为基）：

- **代理**：创建流硬编码 `proxyConfig: { proxy_soft:'no_proxy' }`（`ads-create-flow.cjs:93`，头注「代理全程手工」）；写客户端 `WRITE_ALLOWLIST = ['user/create','group/create','user/delete']`（`ads-write-api.cjs:19`），`user/update` 被回归测试钉死为禁止（`test/electron/ads-write-api.test.ts:43`）；`user/list` 读回的代理配置在 `normalizeProfile` 被压成展示摘要字符串（`ads-local-api.cjs:228,234-248`），结构化字段未透传。AdsPower `user_proxy_config` 字段（官方文档核实）：`proxy_soft`（自填用 `other`，无代理 `no_proxy`）、`proxy_type`（http/https/socks5）、`proxy_host/proxy_port/proxy_user/proxy_password`；改已有环境 = `POST /api/v1/user/update`，body `{ user_id, user_proxy_config }`。
- **平台**：平台唯一来源是 remark JSON（`t==='aidcp-env'` 的 `plat`，`ads-create-flow.cjs:40-57`），缺失一律回落 `xiaohongshu`（`ads-local-api.cjs:227`），`domain_name`/`open_urls` 被丢弃；platform 传到渲染层 `fleetView.envs` 后无任何视觉消费点（`renderer.js:1024` 后断链）；顶栏 `.acct-p` 徽标是静态写死「小红书」（`index.html:16`），`renderTitlebar` 不碰它（`renderer.js:574-588`）；平台配色 CSS 类从未存在。platform 经 `AIDCP_PLATFORM` 功能性注入核心（`fleet.cjs:110`）。
- **人设闸**：`updatePersonaGate` 要求 `status.auth==='logged in' && status.cloud==='connected'`（`renderer.js:1948-1954`）；`auth='logged in'` 全仓唯一写入方是 self 模式 cookie 门（`main.cjs:1074`，注释明言 adspower 不走此路）；AdsPower 登录权威信号「账号身份已确立」（`src/main.ts:181`，读不出身份即诚实 halt）到达 `main.cjs:1316-1321` 时只写 `status.account`、漏写 `auth` → 闸永不开，徽标恒「待启动」、生成按钮恒灰。订阅/渲染链路完好（`renderer.js:954,2058`），非渲染时机问题。
- **人设浮层**：`#persona-wizard-body` 无布局样式（区块垂直间距 0）；chip 寄生 `.seg`（未选中 = 无边框无底色裸文字）；主 CTA「生成人设/确认使用」用 `.seg` 透明灰字、弱于次要按钮 `.secondary`；badge 变体 `checking`/`near` 在 CSS 未定义；生成中只有一行 12px 小字；结果直接甩原始 soulYaml `<pre>`。
- **并发约束**：renderer 三件套 + main.cjs 是 48h 内 6+ 条直改 master 改动流的热点；`codex/edge-macos-developer-id-signing` 分支有 3 个未合并 commit 动 `main.cjs`；活跃 change `edge-environment-platform-select`（代码已落、待真机验收）独占 remark.plat / normalizeProfile / AIDCP_PLATFORM 地盘。

## Goals / Non-Goals

**Goals:**
- 客户端内完成代理配置闭环：新建可选填、已有环境可增改、可显式清除；失败诚实报错。
- FB 环境在数据层被正确识别（含存量手工建的环境）、在 UI 三处上色点呈现平台身份；误推断可人工纠正。
- 人设闸在 AdsPower 生产主路径下正确开启（登录+连云后徽标离开「待启动」、生成可点）。
- 人设浮层按现有设计语言系统化重排；rail 两个按钮字形修正。

**Non-Goals:**
- 不接代理池/自动采购（`proxyid`/`global_config` 引用已保存代理不做，扩展缝留在 proxyConfig 整对象透传）。
- 不改边云协议、不动 cloud/console、不动人设生成 IPC 链路与闸三态语义。
- 不解决「会话中途被登出 auth 不回翻」（登出处置属 identity-watcher 闭环，已归档 change 负责）。
- 不做「离线环境先选关键词后生成」（闸要求已启动+已登录+已连云是设计使然）。

## Decisions

**D1 代理归一层单点真源**：新建 `src/electron/ads-proxy-config.cjs`，`normalizeProxyInput()` 把 UI 原始输入归一为合法 `user_proxy_config` 或诚实报错（`no_proxy`/全空 → `{proxy_soft:'no_proxy'}`；否则 `proxy_soft` 固定 `'other'`，`proxy_type∈{http,https,socks5}`、host 非空、port 1-65535、有 password 必须有 user）。创建与编辑两条链共用，非法输入拒发不静默降级。*备选*：在 create-flow 与新 IPC 各写一遍校验——两处漂移风险，弃。

**D2 `user/update` 受限放行**：allowlist 增补 `user/update`，但新函数 `updateProfileProxy` 的 body **只构造** `{ user_id, user_proxy_config }`、不接受其他键——结构性保证放行只为改代理，防未来顺手扩写面（fingerprint/remark）。M7 生命周期红线（browser/* 抛错）与回归断言不动；比照当年 `user/delete` C3 放宽先例修订 spec。*备选*：绕过写客户端直连本地 API（07-08 人肉 curl 补 plat 的做法）——把红线变成摆设，弃。

**D3 密码语义按「整体替换」保守口径**：`user/list` 不回传密码，无从「留空=保留」；编辑浮层密码留空且原配置带鉴权时前端提示需重填，按所填整体提交。真机验证 update 对在跑环境的行为（拒/下次生效）后再调整文案。渲染层不回显旧密码、不落盘（复用 `redactSensitive`，`ads-write-api.cjs:36` 已覆盖 proxy_user/proxy_password）。

**D4 平台推断只读且 remark 权威**：`normalizeProfile` 内 `inferPlatform(it)` 优先级：remark plat → `domain_name` 命中 facebook.com/fb.com 或 xiaohongshu.com → `open_urls` 同规则 → 分组/名称关键词（/facebook|\bfb\b|脸书/i）→ 回落 xiaohongshu；同时输出 `platformSource` 供 UI 对非 remark 来源标注。**不程序化回写 remark**（那需要 user/update 扩到 remark，违背 D2 的结构性限定）；平台归属人工纠正走加入面板显式改平台入口 → 既有 `saveSettings(environments)` 通道（`fleet.cjs:23-33` 已支持 facebook，零协议改动），只存本机。*备选*：user/update 回写 remark 跨机生效——扩大写面且撞 D2，弃；domain 字段各版本形态未验证，推断函数对缺字段安全降级。

**D5 平台上色走 class 透传，签名必须含 platform**：`makeRailRow` 的 `btn.className` 追加 `plat-<platform>`；**`renderRail` 的 DOM 重建签名（`renderer.js:1102`）必须同步加入 platform**，否则改平台后 rail 因签名未变不重建（本修复与签名改动同提交）。顶栏 `renderTitlebar` 增读选中环境的 platform，更新 `.acct-p` 文案与平台类、`#acct-ava` 同步；健康浮层「小红书登录」行标签与登录提示文案按平台切换。CSS 新增 `--plat-fb:#1877f2` 与 `.plat-facebook` 系列：头像底色表平台、外圈色环继续表运行状态，两者正交。用户所称「顶部 tab 标签」在现代码无对应元素，按最可能所指（顶栏账号区平台徽标）实现，加入面板列表行也补平台染色。

**D6 登录态投影一行补写 + 诚实复位**：`main.cjs` 身份事件分支（`1316-1321`）补 `next.auth='logged in'`——核心只在真读出登录身份后才打「账号身份已确立」（读不出即 halt，`src/main.ts:157-169`），映射为已登录不违反「不静默假成功」；self 模式重复置幂等无害。子进程 exit 补丁对 adspower 追加 `auth:'checking'` 复位（gate 已被 cloud disconnected 关住，此项为徽标诚实）。`openPersonaPop` 改用目标环境自身 status 评闸（`renderer.js:868`，null 输入已是安全中立态）。已知残留：`source=env-override` 时也会翻已登录（显式运维逃生阀，接受）；日志行格式契约（`src/main.ts:181` ↔ `ui-events.cjs:83`）靠既有 identity 解析单测钉住。*备选*：把日志→状态推断抽纯函数全面单测——main.cjs 无测试 harness、改动面大，按补测克制原则只登记真机验收项。

**D7 人设浮层重设计以三段式 + 两步向导落地**（细案见调查产出，要点）：`.persona-pop` 放宽到 `min(560px, calc(100vw-32px))` 且与 `.env-add-panel` 拆开选择器；内部 flex 三段（sticky 头带 22px 头像身份锚点 + 平台小标 / 滚动体 / sticky 底部操作栏——草稿与按钮永不沉到折叠线下）；两步指示复用 `.j-step` 旅程点语言；chip 新建独立 `.kw-btn` 规则（默认描边浅底、hover、选中蓝 + ✓、focus-visible 环），JS toggle 逻辑零改；主 CTA 换 `.setup-btn` 实心蓝；空态/gate 态/已绑态各给专属面板（替代改写一行 hint），「去启动」按钮复用既有 FAB 流程不新增 IPC；生成中 CTA spinner + 预览区骨架条（respect prefers-reduced-motion），in-flight 忽略遮罩关闭一次并提示；错误升级为警示条；结果 identitySummary 升标题、YAML 收进 `<details>` 折叠（可选浅解析，失败整体回退 raw pre）。必须保留的行为契约：闸三态语义、状态推送不重置已选关键词/草稿、`personaDraftEnvId` 锚定、切环境清草稿（同步回 Stage1）、诚实失败展示、`openPersonaPop` 先 `selectEnv` 的副作用（用身份锚点可视化它）。补齐 `.badge.checking` 中性灰变体、删死样式 `.persona-config`、Escape 关闭 + `role="dialog"` + `aria-pressed`。

**D8 字形修正**：`rail-add` 的全角「＋」（U+FF0B，CJK 字形偏移是不居中根因）换成内联 SVG 加号（stroke 绘制，天然居中）；`rail-toggle` 的 `‹`/`›` 换内联 SVG chevron（约 14px 视觉尺寸），`renderer.js:1109` 的 textContent 切换改为 class/transform 切换。*备选*：调字号硬凑——跨平台字体渲染不稳，弃。

**D9 集成纪律**：开 worktree `../aidcp-edge.wt/edge-client-proxy-platform-persona-ux`（分支同名），不在主 checkout master 直改（833a4ee 的 ad-hoc session 可能仍活跃）；动 `main.cjs` 前查看签名分支的 diff 段落避让；落地前最后一刻 fetch+rebase，push 遇 non-ff 一律 rebase 绝不 force；worktree 提交显式列文件（防软链/外溢物入仓）。本仓 change 文档提交走临时 worktree 到 main（主 checkout 停在 codex/remote-captcha-assist）。

## Risks / Trade-offs

- [user/update 语义未真机验证（在跑环境拒/下次生效、list 是否回传 port/user）] → UI 按「整体替换 + 下次启动生效」保守文案；编辑表单容忍空预填；真机项登记 backlog 后按实测修文案。
- [给养熟账号改代理引起画像跳变（指纹 webrtc/时区/语言随代理 IP）] → 编辑浮层内置一句运营警示；产品口径，不做技术拦截。
- [平台误推断会让环境按错平台启动（AIDCP_PLATFORM 功能性注入）] → remark 永远最高优先；非 remark 来源 UI 标注「平台未标注（推断）」；显式改平台入口兜底。
- [renderer 三件套 + main.cjs 热点撞车；platform-select change 按旧判据验收失真] → D9 纪律；proposal 已显式声明扩展关系，本 change 归档排在 `edge-environment-platform-select` 之后，其 task 2.3 验收判据不受影响（remark 语义未变）。
- [人设重设计使真机 backlog 簇 17/21/22 判据失真] → 落地时同步修订 backlog 描述（原子 append 纪律）。
- [.persona-pop 与 .env-add-panel 现为合写选择器] → 拆开后逐条核对添加环境面板零回归。

## Migration Plan

edge 本地客户端，无 ECS 部署。worktree 开发 → 全量 `npm test` + `npm run typecheck` → rebase 集成 ff 合入 master → push → ff 更新主 checkout（用户在那跑 electron:dev）。回滚 = revert 该合并区间。真机验收项登记 backlog，不阻塞归档（仓规）。

## Open Questions

- 用户所称「顶部 tab 标签」按顶栏平台徽标实现；若实际另有所指（如设想中的顶部环境 tab 条），需求另立。
- `user/list` 对 `proxy_port`/`proxy_user` 的回传完整度待真机确认，决定编辑预填的完整程度。
