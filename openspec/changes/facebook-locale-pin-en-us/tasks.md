# Tasks — facebook-locale-pin-en-us

> edge-only（`../aidcp-edge` master）。无协议 / cloud / ECS 改动。实装后按 sub-repo 分节回写 sha。

## 1. aidcp-edge — 新号指纹语言钉死 en-US

- [ ] 1.1 在 `src/electron/ads-fingerprint.cjs` 的 `buildFingerprintConfig` 里，把 `language_switch:'1'`（随代理 IP）改为关闭随 IP + 显式 `language=['en-US']`；语言取值收口为文件内单一中心常量（便于回滚 / 灰度）。**先跑 `scripts/adspower-fingerprint-probe.ts` 核实 `language_switch` 0/1 语义与 `language` 字段确切键名，勿凭记忆**（真机门未过前用常量占位并注释 TODO 键名）。
- [ ] 1.2 确认 `language` 不进 `assertOsCoherent`（`ads-fingerprint.cjs:107-130`）断言集——pin en-US 不触发 coherence 拒建；补一条单测断言「pin en-US 的 fingerprint 通过 `buildFingerprintConfig` 护栏与四者一致断言」。
- [ ] 1.3 补 / 改单测：`buildFingerprintConfig` 产物含 `language=['en-US']` 且 `language_switch` 为关闭态；时区仍 based-on-IP（`automatic_timezone:'1'` 不动）。

## 2. aidcp-edge — 启动参数与导入 cookie 兜边角 chrome

- [ ] 2.1 `src/cdp/browser-provider.ts:133` 的 `launchArgs` 追加 `--lang=en-US`（覆盖登出 / 未登录 chrome）；确认它经 `launch_args` JSON 正常下发、不与现有 `--window-size` / `--deny-permission-prompts` 冲突。
- [ ] 2.2 `src/electron/facebook-account-import.cjs` 归一化导入 cookie 时，若缺 `locale` 则注入 `locale=en_US`（`FB_COOKIE_NAMES` 已含 `locale`，:14）；补单测覆盖「缺 locale → 注入 en_US」与「已有 locale → 不覆盖用户值」两分支。
- [ ] 2.3 在代码 / 文档注释写明：`--lang` 与 cookie `locale` **只兜登出 chrome、不改登录态群面语言**（避免误判「pin 了但群面仍外语」为回归）。

## 3. aidcp-edge — 存量登录号结构性边界（只作证、不放宽）

- [ ] 3.1 补一条回归断言 / 测试，坐实 `src/electron/ads-write-api.cjs` 的 `user/update` 仅接受 `{ user_id, user_proxy_config }` 两键、拒绝透传 `fingerprint_config`——存量号指纹语言经写客户端**结构性改不动**（红线靠测试守）。**不放宽 allowlist**。
- [ ] 3.2 写存量号归一 runbook（docs 或 change 内）：一次性登入 → FB 账号设置改语言为 English (US) → 跨代理 / 会话验证界面英文；标注真实设置页导航路径为真机待验项。

## 4. 验证与回写

- [ ] 4.1 edge `npm run typecheck` + `npm test` 全绿（无回归）。
- [ ] 4.2 `openspec validate facebook-locale-pin-en-us --strict` 通过。
- [ ] 4.3 部署 dev（edge 侧）；把真机验证项登记到 `docs/real-machine-acceptance-backlog.md`：① `language_switch`/`language` probe 键值语义；② 新号建出后界面英文 + 内容不塌（非英文群实测）；③ 存量号改账号语言设置页路径。
- [ ] 4.4 回写本文件：各 task 标 `[x]` + `<!-- aidcp-edge <sha> 备注 -->`（部署后追 `<!-- <date> deployed -->`）。
