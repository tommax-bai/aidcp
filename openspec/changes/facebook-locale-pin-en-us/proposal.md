## Why

FB 页面自动化对「加入 / 待审 / 已加入 / 写评论 / 同意 Cookie」等按钮与状态的识别，当前本质是**按可见文字关键词匹配**（`join-executor.ts` 有 ~15 语种词表，`consent.ts` / `comment-executor.ts` 多为中英正则）。跨国家 / 跨语言群组时界面语言随之改变，词表漏判即 fail-closed 静默跳过——该群永久不加、评论发不出，且各状态词表覆盖不对称（「加入」认得、「已加入」某些语种认不得）会导致「加进去了却判失败→重复加群」的真机事故。

根因不在「词表不够全」，而在**界面语言是个不受控的变量**。FB 的界面 chrome 语言由账号自身设置决定，与所看内容 / 群组语言无关——把界面语言在源头统一钉成英文，即可把大部分识别从「N 语」塌成「单语」，是整套跨语言识别分层方案的 P0（最独立、edge-only、无协议改动、治本先发）。这是先手；后续 C2（加群动作解耦 + 结构后置校验）、C3（同意浮层结构化）修那些「即便全英文也会坏」的语言无关 bug。

## What Changes

- **新号建号时把指纹语言钉成英文**：`ads-fingerprint.cjs` 现 `language_switch:'1'`（语言随代理 IP）改为固定英文（关闭 language-follows-IP + 显式 `language=['en-US']`）。**BREAKING（spec 级）**：这与 `adspower-environment-provisioning` 现有「时区/语言 SHALL based-on-IP」条款相冲突，需修改该条款——语言改为钉死英文、时区仍随 IP。
- **启动参数兜登出页 chrome**：`browser-provider.ts` 的 `launchArgs` 追加 `--lang=en-US`，覆盖未登录 / 登出页界面语言（登录态群面由账号语言主导，此参数只兜边角）。
- **导入号 cookie 带 en_US locale**：`facebook-account-import.cjs` 在导入 FB cookie 时确保存在 `locale=en_US`（缺则注入），统一初始会话界面语言。
- **存量登录号走账号服务端语言**：结构性事实——本客户端写 allowlist 的 `user/update` 仅放行改代理、`fingerprint_config` 只在 `user/create` 设，**存量号指纹语言改不动**。存量号唯一有效路 = 一次性登入后把 FB 账号语言改为英文（跨代理存活、压过 Accept-Language）。此路径以运维 runbook + 可选边缘自动化落地，标记真机验证门。
- **内容语言不动**：帖文 / 群名 / 人名等**内容**语言一律不塌，仍归云端多语判定；本 change 只统一界面 chrome。
- **不建 N 语字典**（YAGNI）：本 change 是 necessary-not-sufficient，不新增关键词表基础设施。

## Capabilities

### New Capabilities
- `facebook-ui-locale-normalization`: FB 互动号的浏览器界面语言（chrome）统一钉成规范 locale（en-US），与代理 IP 派生语言、内容 / 群组语言解耦，使下游按钮 / 状态的文字识别语言稳定；覆盖新号建号钉定与存量号一次性账号语言翻转两条路径；明确内容语言不受影响、且 pin 不破坏指纹一致性。

### Modified Capabilities
- `adspower-environment-provisioning`: 「薄护栏」需求中「时区/语言 SHALL based-on-IP」条款收窄——时区仍 based-on-IP，**语言改为钉死规范 en-US**（`language_switch` 关闭 + 显式 `language`），且明确 `language` 不进 OS 四者一致断言集（pin 不触发 coherence 拒建）。

## Impact

- **仓/部署**：edge-only（`../aidcp-edge` master）。**无协议改动、无 cloud 改动、无 cloud/ECS 部署**；edge 侧可部署 dev 验证。不触碰协议四处同步、不碰热点 `protocol.ts` / `command-bridge` / 角色注册 / 风控状态机。
- **代码**：edge `src/electron/ads-fingerprint.cjs`（language pin）、`src/cdp/browser-provider.ts`（launchArgs `--lang`）、`src/electron/facebook-account-import.cjs`（locale cookie）、`src/electron/ads-write-api.cjs`（存量号改不动的结构边界，只作证 / 不放宽）。
- **真机待验（落 backlog，不阻塞码级）**：① adspower CLI `language_switch` 的 0/1 语义与 `language` 字段键名（先跑 `scripts/adspower-fingerprint-probe.ts` 核实，勿凭记忆）；② 存量号改账号服务端语言的真实设置页导航路径；③ FB 界面语言确由账号设置决定、内容不随之变。
- **风险边界**：pin en-US 与「看起来像本地用户」不冲突（英文界面刷本地语言群是常见真实形态；`language` 不在一致性断言集；现「语言随 IP」反而在美国代理号突现越南语 UI 时更异常）。长期以 IP 派生语言运行的熟号可接受一次性翻转或维持现语言，不为一致性造不连续。
