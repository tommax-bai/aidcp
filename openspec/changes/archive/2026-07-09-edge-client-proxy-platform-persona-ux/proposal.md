# Proposal: edge-client-proxy-platform-persona-ux

## Why

客户端（aidcp-edge Electron 壳层）一轮体验修整，来自用户 2026-07-09 报告的 8 个问题。根因已经 10-agent 调查 + 4 项对抗验证确认：

1. **代理无法配置**（问题 1/2）：当年 change `adspower-auto-create-env` 定案「代理全程手工」——创建流硬编码 `no_proxy`（`ads-create-flow.cjs:93`）、写客户端 allowlist 无 `user/update`（`ads-write-api.cjs:19`，测试钉死）、spec SHALL 条款固化（三层刻意封死）。客户现在需要在客户端内直接完成代理配置（新建时设置 + 已有环境增改），继续「去 AdsPower 手配」的路径对客户不可用。
2. **Facebook 环境被误认为小红书**（问题 3）：双层断——数据层：手工建的环境无 `remark.plat` → 一律回落小红书，且错误平台会经 `AIDCP_PLATFORM` 注入核心、按小红书流程启动（功能性错误，非纯展示）；UI 层：platform 字段一路正确传到渲染层后**没有任何消费点**，rail 环境图标、顶栏头像与平台徽标全部写死小红书样式，FB 蓝色样式类在代码与 git 历史中从未存在。
3. **人设徽标卡「待启动」+ 生成按钮永久灰**（问题 4/5，同一根因）：人设闸要求 `status.auth==='logged in'`，但该值全仓唯一写入方是 self 模式 cookie 登录门（`main.cjs:1074`）；AdsPower 生产主路径下，登录成功的权威信号「账号身份已确立」到达主进程时只写了 `status.account`、漏写 `auth`（`main.cjs:1316-1321`）→ 闸永不开。既有桩测手动 `gen.disabled=false` 绕过了这条链路故全绿。
4. **人设浮层排版**（问题 6）：从设置抽屉搬进浮层的「功能拼装态」——向导主体无布局样式（区块间距 0）、关键词 chip 未选中态为裸文字不可辨、主 CTA 视觉权重低于次要按钮、badge 变体 `checking`/`near` 在 CSS 中未定义、十几秒生成任务只有一行 12px 小字、结果直接甩原始 YAML。
5. **rail 细节**（问题 7/8）：添加按钮用全角「＋」（U+FF0B）字形天然偏移不居中；收起按钮 `‹`/`›` 字形在 24px 按钮里过小。

## What Changes

- **环境代理配置**（aidcp-edge + spec 修订）：
  - 新建环境表单增加可选代理区块（类型 http/https/socks5 + host/port/user/password，默认「无代理」）；填了则随 `user/create` 下发 `user_proxy_config`，不填保持 `no_proxy` 零回归；非法输入诚实拒建。
  - 已有环境行增加「代理」编辑浮层：预填现配置（`user/list` 读回的非密字段），保存经受限放行的 `user/update` 下发，body 结构性限定只含 `user_id + user_proxy_config`；「无代理」保存 = 显式清除。
  - 写客户端 allowlist 增补 `user/update`（仅此用途），浏览器生命周期红线（M7）不动；凭据只内存持有、日志脱敏（复用既有 `redactSensitive`）。
- **平台识别与平台化 UI**（aidcp-edge）：
  - 存量无 `remark.plat` 环境的平台兜底推断链：remark（权威）→ `domain_name` → `open_urls` → 分组/名称关键词 → 回落小红书；输出推断来源供 UI 标注。**显式扩展活跃 change `edge-environment-platform-select` 的回落行为**（该 change 定义「无标注一律回落小红书」，本 change 在其前插入只读信号推断，remark 语义不变）。
  - 加入面板环境行提供显式改平台入口（写入本机 settings，经既有通道，误推断可人工纠正）。
  - 三处 UI 按平台上色：rail 环境行头像/图标、顶栏头像与平台徽标（FB 蓝 `#1877f2`，小红书维持现状）；顶栏平台徽标文案随选中环境切换（不再写死「小红书」）。
- **AdsPower 登录态投影修复**（aidcp-edge）：主进程身份确立事件分支补写 `auth='logged in'`（核心只在真读出登录身份后才发该信号，读不出即诚实退出，不违反「不静默假成功」）；核心子进程退出时 adspower 路径 auth 复位 `checking`；人设浮层打开时用目标环境自身状态评闸（杜绝跨环境串状态）；删除桩测里手动放行 `gen.disabled=false`，让用例真走状态链路。
- **人设浮层重设计**（aidcp-edge，纯视觉/结构，不动 IPC 与闸语义）：三段式骨架（sticky 头带身份锚点 + 滚动体 + sticky 底部操作栏）、两步向导（选关键词 → 预览确认）、chip 可辨识样式、CTA 层级归位（主动作实心蓝）、空态/已绑态专属面板、生成 loading（spinner+骨架）与错误警示条、结果摘要优先 + YAML 折叠。
- **rail 细节修**（aidcp-edge）：添加按钮加号改 SVG/半角并居中；收起按钮箭头加大并光学居中。

## Capabilities

### New Capabilities

（无——全部落在既有能力的需求修订上）

### Modified Capabilities

- `adspower-environment-provisioning`：① 写 allowlist 需求：增补 `user/update`（body SHALL 只含 `user_id + user_proxy_config`，生命周期红线不动）；② 幂等与生命周期需求：废除「代理全程手工、本按钮 MUST NOT 碰」条款，改为「创建可选填代理、不填默认 no_proxy」；③ 「代理为软提示」需求：改写为创建可选填 + 已有环境可编辑（保留「未配代理仍可创建」与「MUST NOT 自动采购/管理代理池」）；④ 凭据需求：内存持有/脱敏条款扩展覆盖 update 流。
- `platform-runtime-abstraction`：新增需求——存量未标注环境的平台只读兜底推断链与显式改平台入口（扩展活跃 change `edge-environment-platform-select` 的「未标注一律回落小红书」行为；本 change 归档须排在其后，归档撞车时按 memory 纪律移回重归档）。
- `edge-fleet-console`：新增需求——① 环境行与顶栏身份区按平台呈现视觉标识（FB 蓝）；② AdsPower 路径登录态投影以核心「账号身份已确立」事件为准（人设闸、引导链路共同依赖），子进程退出诚实复位。

## Impact

- **仓库**：仅 `aidcp-edge`（Electron 壳层：`src/electron/*.cjs` + renderer 三件套 + test/electron）+ 本仓 spec 修订。无 cloud/console 改动、无协议改动、无 ECS 部署（edge 本地客户端，用户侧重建生效）。
- **热点/并发**：`renderer.js`/`styles.css`/`index.html`/`main.cjs` 是 48h 内 6+ 条改动流的热点，必须开 worktree、落地前 rebase；`main.cjs` 另与未合并分支 `codex/edge-macos-developer-id-signing` 有冲突面。与活跃 change `edge-environment-platform-select` 的地盘重叠已在上文显式声明。
- **风险**：① `user/update` 对「已打开环境」的行为（拒绝或下次生效）与 `user/list` 是否回传 `proxy_port`/`proxy_user` 未真机验证——UI 文案按「整体替换 + 下次启动生效」保守口径，编辑表单容忍空预填；② 给已养熟账号改代理会引起画像跳变（指纹 webrtc/时区随代理 IP），编辑浮层给运营警示；③ 平台推断误判会让环境按错误平台启动——remark 永远最高优先、非 remark 来源在 UI 标注并可人工改平台。
- **真机验收**：人设闸修复、代理 update 语义、FB 环境启动打开 facebook.com 等真机项按仓规登记 `docs/real-machine-acceptance-backlog.md`；人设重设计会使 backlog 簇 17/21/21 的验收判据失真，落地时同步修订。
