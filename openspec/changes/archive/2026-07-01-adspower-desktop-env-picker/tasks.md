# Tasks — adspower-desktop-env-picker

> 承接 `adspower-browser-provider` §9（桌面外壳应用内 provider 选择）。改动仅在 aidcp-edge 的 Electron 外壳（`src/electron/`）+ AdsPower 本地 API 只读查询；核心 provider 启动/生命周期层（`browser-provider.ts` 的 `launch`/`kill`）、CDP 接入及下游、cloud/console/协议**零改动**。代码落 aidcp-edge，进度回写本仓。
> 实现主体见 edge `8eecded`（`src/electron/ads-local-api.cjs` + main/preload/renderer 接线 + 单测 11 + jsdom 冒烟 7）。

## 1. aidcp-edge — 主进程侧 AdsPower 只读模块（src/electron/ads-local-api.cjs）

> 因 Electron 主进程是 CJS、核心是 spawn 出的 ESM 子进程（两进程内存不通、`require` 也复用不了核心节流），只读模块**自包含**在主进程侧，比照现有 `chrome-launcher.cjs` 复制先例。核心 `browser-provider.ts` 的 `api<T>()` 与 `browser/start|stop|active` 不改、不复用（D3/D3a）。

- [x] 1.1 新增 `src/electron/ads-local-api.cjs`，只读 `status()`：按端点显式拼**根级** URL `${base}/status`（**不**加 `/api/v1/` 前缀），可达返回就绪、不可达/超时诚实返回不可用（不 throw 崩溃、供面板分档提示）；红线守卫：拼错前缀的 404 MUST NOT 冒充「不可达」<!-- aidcp-edge 8eecded -->
- [x] 1.2 只读 `listProfiles(opts?)`：显式拼 `${base}/api/v1/user/list`（分页 `page`/`page_size`，可选 `group_id`），归一化返回环境数组——**`user_id`=写入 `adsProfileId` 的唯一分身 id**；`serial_number`（UI 序号）/ 名称 / 分组 / 代理配置摘要（proxy 类型/host + 配置 `ip`/`ip_country`，可能缺失）**仅供下拉展示、MUST NOT 写入 `adsProfileId`**（下游 `browser/start` 只认 `user_id`，写 `serial_number` 会 `code≠0` 失败）；其余字段名以真机返回为准；`code≠0` / 鉴权失败 / 空列表分别如实回报 <!-- aidcp-edge 8eecded；normalizeProfile 取 user_id、summarizeProxy 只标代理配置 -->
- [x] 1.3 该模块**自持一条 ≥1.1s 串行节流**（复用与核心相同的间隔常量 `ADS_MIN_INTERVAL_MS` 逻辑、但为主进程内独立实例，**不**跨进程共享核心节流）+ 可选 Bearer；开 API 校验时 `user/list` 带 api-key，`/status` 免鉴权 <!-- aidcp-edge 8eecded -->
- [x] 1.4 单测（注入 fetch 桩，不起真客户端）：status 可达/不可达/超时 + 断言打的是根级 `/status`；listProfiles 成功/`code≠0`/疑似 401/空 + 断言取 `user_id` 而非 `serial_number`；断言**本进程内**只读调用串行、间隔 ≥1s（并注明该测试只覆盖单进程、跨进程碰撞走诚实降级、绿测不证明「跨进程同一节流」）；断言绝不触碰 start/stop/active <!-- aidcp-edge 8eecded；test/electron/ads-local-api.test.ts 11 项全绿 -->

## 2. aidcp-edge — Electron 主进程 IPC + preload 通道

- [x] 2.1 `main.cjs` 新增 IPC handler：`ads:status`（探测）/ `ads:listProfiles`（拉列表）/ `ads:openCreate`（打开新建入口），调 §1 只读模块；只在主进程调本地 API，渲染层不直连（D5）。`ads:listProfiles`（及需鉴权探测）**接受渲染层传入的当前表单 apiKey/apiBase 作调用级参数**（仅本次用、不持久化、不落日志），优先用之、表单空才回落持久化 `settings.adsApiKey`（解决「新填 key 未保存即刷新」回环，D5）<!-- aidcp-edge 8eecded；resolveAdsOpts -->
- [x] 2.2 `preload.cjs` 暴露 `ads:status` / `ads:listProfiles` / `ads:openCreate` 三通道（`contextIsolation` 下经 `contextBridge`）；只读通道不额外扩大 api-key 暴露面（其已随既有 `settings:get` 在表单框内，渲染层把当前表单值作调用级参数回传主进程仅本次调用用）<!-- aidcp-edge 8eecded -->
- [x] 2.3 `ads:openCreate` 实现：best-effort 拉起/聚焦 AdsPower 客户端；起不来退回 `shell.openExternal` 到 AdsPower 官方页面（复用/邻接现有 `ADS_DOWNLOAD_URL` 外链能力，D4）<!-- aidcp-edge 8eecded；darwin open -a + 失败兜底 openExternal -->
- [x] 2.4 探测触发接线到**实际存在的事件**：渲染层加载时探一次（低频）+ 切到 AdsPower 分段时探一次（复用现有 `prov-adspower` 点击）+ 保存并启动前探一次；结果经状态推送到面板；**不**写成「打开设置面板」（设置区常驻内联、无该事件）；**不做**后台常驻轮询（D1）<!-- aidcp-edge 8eecded -->

## 3. aidcp-edge — 面板 UI（检测 / 环境下拉 / 刷新 / 新建）+ 中文化

- [x] 3.1 `renderer/index.html` + `styles.css`：新增「AdsPower 检测状态徽标（可含手动『检测』触发）」「环境下拉（每项：名称 / 分身 id / 分组 / 代理配置摘要）+ 刷新按钮」「打开 AdsPower 新建环境按钮」控件；手敲分身 id 输入框**保留为兜底**；设置区维持常驻内联、不新增模态（YAGNI）<!-- aidcp-edge 8eecded -->
- [x] 3.2 `renderer/renderer.js`：调三通道；探测可达/不可达分档展示（不可达给下载入口 + 明示「未就绪、启动可能失败」但不禁死流程，D6）；下拉选中即把该环境 **`user_id`** 写入 `adsProfileId`（覆盖手敲框、手敲框仍可编辑），保存校验非空 <!-- aidcp-edge 8eecded -->
- [x] 3.3 拉取失败诚实降级：`listProfiles` 失败 → 退回手敲 id + 如实提示原因；疑似 401 措辞兼顾「已填未保存」（如「若已在下方填了 API key，本次刷新已用当前填写值，请确认后重试」，刷新时把表单当前 apiKey/apiBase 经 `ads:listProfiles` 传入，D5/D6），MUST NOT 叫运维去填一个已填的框、MUST NOT 要求「先保存再刷新」；MUST NOT 谎报有环境、MUST NOT 禁死启动 <!-- aidcp-edge 8eecded -->
- [x] 3.4 防抖/防限速：探测/刷新按钮在请求在途时禁用（D7）<!-- aidcp-edge 8eecded -->
- [x] 3.5 全量中文化（新增控件文案 / 状态消息 / 提示语），承接 §9 风格；徽标 className 保英文状态码上色、仅展示文案本地化 <!-- aidcp-edge 8eecded -->

## 4. aidcp-edge — 回归与验证

- [x] 4.1 三 electron 文件 `node --check` 通过；`npm run typecheck` 0 错；`npm test`（含 §1 只读方法单测）+ `npm run test:acceptance` 全绿 <!-- aidcp-edge 8eecded；node --check 4 文件 / typecheck 0 / test 415 / acceptance 11 -->
- [x] 4.2 jsdom 无头冒烟补例：探测可达/不可达提示、下拉选中写入 `adsProfileId`、拉取失败退手敲、打开新建外链、按钮 in-flight 禁用、诚实降级各态 <!-- aidcp-edge 8eecded；test/electron/renderer-smoke.test.ts 7 项全绿 -->
- [x] 4.3 回归护栏：§9 既有契约不破——`selectBrowserProvider`（默认 adspower / 缺 user_id 报错 / 显式 self）、写盘失败诚实回报、adspower 缺分身 id「待配置」；`adsProfileId` 语义与下游注入不变 <!-- aidcp-edge 8eecded；browser-provider.test 等既有测试随全量 415 全绿 -->
- [x] 4.4 安全红线断言：新增本地 API 调用只读、绝不触碰 start/stop/active、绝不静默假成功/回落；api-key 不落日志 <!-- aidcp-edge 8eecded；单测「只读边界」断言 URL 从不含 browser/start|stop|active -->
- [x] 4.5 对抗性代码复查（+真机只读验证）修 3 项确认缺陷：D1 节流对并发不生效（改模块内串行队列，防两独立按钮/自动探测撞 1req/s 自伤成假失败）、D2 清空 API Key 框不回落已存 key（改与 API 地址同语义）、D3「已尝试打开 AdsPower」兜底误导（openAdsClient 异步返真实 launched、渲染层分档文案）；附并发串行化 + no_proxy + launched 分档测试。真机（AdsPower Global）坐实 /status 可达 / user_id≠serial_number / 1req/s 限速 <!-- aidcp-edge de33fda -->
- [x] 4.6 真机只读冒烟（§5.1 部分）：本机 AdsPower `status()` 就绪、`listProfiles()` 列出真实环境（工程师大白/组 aidcp/无代理），`user_id`/`serial_number` 归一化正确、no_proxy 显示「无代理配置」 <!-- 2026-07-01 本机 headless 只读验证；GUI 完整闭环仍待 §5.1 -->

## 5. aidcp-edge — 真机灰度（可选，gated）

> 需本机装 AdsPower 客户端 + 开本地 API，非代码级验证——待有真机环境时执行。

- [ ] 5.1 真机：AdsPower 客户端已开本地 API → 面板探到就绪、`user/list` 列出真实环境、下拉选中启动跑通闭环；关掉本地 API → 面板诚实提示不可达 + 下载入口
- [ ] 5.2 真机：开 API 校验未配 key → `user/list` 鉴权失败 → 面板退手敲 + 提示填 key；`/status` 仍探到可达
- [ ] 5.3 真机：点「打开 AdsPower 新建环境」→ 客户端被拉起/聚焦（或退回官网），AdsPower 内新建后回面板点刷新 → 新环境出现在下拉

## 6. aidcp（中控）— 文档 + 校验

- [x] 6.1 `aidcp-edge/OPERATOR.md` 补「可用性探测 + 环境下拉选择 + 打开新建入口」用法（双 provider 章节内 adspower 段）<!-- aidcp-edge 8eecded；§2A 重写 + §5 排查补一条 -->
- [x] 6.2 `openspec validate adspower-desktop-env-picker --strict` 通过 <!-- aidcp 本提交 -->
- [x] 6.3 tasks 进度按 sub-repo 分节回写本仓，完成项标 `[x]` 并附 `<!-- <repo> <commit-sha> 备注 -->` <!-- aidcp 本提交 -->

## 7. aidcp-edge — 面板 UX 改造（2026-07-01，D8–D12，并入本 change）

> 用户拍板：① 环境直接列表（非下拉）+ 就绪自动加载；② API 地址/Key 折叠进「高级」默认收起；③ 分身 id 默认由选中环境带出 +「手动填写」开关（默认关）；④ 保存/启动拆分（保存只存不打断）+ 悬浮三态会话按钮（停→启动/跑→暂停/停顿→恢复）+ self 不显示保存。改动仅在 Electron 外壳。

- [x] 7.1 环境**直接列表**替代下拉：探测就绪即**自动拉一次** `listProfiles`（无需先点刷新）；渲染成可点行（名称/序号/分组/代理配置），点选带出 `user_id`、高亮选中；「刷新」只更新；列表限高滚动；未就绪/失败诚实降级不留空 <!-- aidcp-edge 3e9f815 -->
- [x] 7.2 **分身 id（只读展示 + 手动填写开关 + 手敲输入框）+ API 地址 / API Key** 一并折叠进「高级设置」默认收起；主区只留状态 + 环境列表 + 新建/下载入口；探测未就绪 / 拉取失败时**自动展开**高级设置使「手动填写」可达 <!-- aidcp-edge 3e9f815（折叠 API）→ 分身 id 也收进高级 + 失败自动展开迭代 -->
- [x] 7.3 分身 id 默认由选中环境带出（只读显示 `#ads-profile-display`）+「手动填写」开关（默认关；开=手敲兜底 `#ads-profile`）；保存/启动前校验最终分身 id 非空、写入的是 `user_id` <!-- aidcp-edge 3e9f815 -->
- [x] 7.4 **保存并入启动**（无独立保存按钮，用户二次拍板）：启动 = 先 `saveSettings` 再 `edge:start`（`adspower` 校验分身 id 非空、缺则诚实提示不启动）；「按新设置重启」= 先 `saveSettings` 再 `edge:restart`，仅在 **dirty && 核心在跑**时出现；`settings:save` 只写盘不重启（作为启动/重启内部步骤被调用）；`self` 启动同样先存再起、无分身校验 <!-- aidcp-edge 3e9f815（拆分）→ fc0d9ab 保存并入启动二次迭代 -->
- [x] 7.5 悬浮三态会话按钮（窗口右下角固定 `#session-fab`）：`session=paused→恢复` / `edge=stopped/warning→启动` / 其余→`暂停`，触发 resume/start/pause；顶部原「暂停/恢复」toggle 收进它（「重新登录」保留）<!-- aidcp-edge 3e9f815 -->
- [x] 7.6 全量中文化 + jsdom 冒烟改版 14 项：自动加载列出、点选带出 user_id、手动开关切换、高级折叠、无独立保存按钮/启动先存再起、缺分身诚实不启动、改动+在跑才现「按新设置重启」（先存再重启）、self 启动、悬浮三态随状态、新建分档 <!-- aidcp-edge 3e9f815 → fc0d9ab 保存并入启动迭代 -->
- [x] 7.7 回归：`node --check` 4 文件 + typecheck 0 + 全量 test 423 + electron 冒烟 13 全绿；§9 既有写盘诚实回报 / 缺分身 id「待配置」契约不破 <!-- aidcp-edge 3e9f815 -->
- [x] 7.8 真机 GUI 灰度：用户在本机看过并认可整套面板交互（环境自动列出 / 点选带出 / 分身 ID 收高级 / 悬浮三态 / 启动即保存）<!-- 2026-07-01 用户 review 认可；完整连生产云浏览闭环仍归 §5.1 可选 -->

## 8. 待办（延后/可选）

- [ ] 8.1 resolve design OQ#1：环境数很大时是否加 `group_id` 分组过滤（`settings.adsGroupId` 可选，默认拉全量）
- [ ] 8.2 resolve design OQ#3：核对 `user/list` 返回是否含实际出口 IP；若无则仅展示代理配置摘要 + 提示以 AdsPower「检测代理」为准
