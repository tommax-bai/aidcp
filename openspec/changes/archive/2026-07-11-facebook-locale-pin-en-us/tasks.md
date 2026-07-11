# Tasks — facebook-locale-pin-en-us

> edge-only（`../aidcp-edge` master）。无协议 / cloud / ECS 改动。实装后按 sub-repo 分节回写 sha。
> **全部代码 task 已实装 + land edge master `af83f38` + 对抗评审 0 确认缺陷（6 raw findings 全被证伪）。**
> edge dev = master（无 ECS）；真机验收登记 `docs/real-machine-acceptance-backlog.md` 簇 49，运营机 pull + 重建安装包后生效。

## 1. aidcp-edge — 新号指纹语言钉死 en-US

- [x] 1.1 在 `src/electron/ads-fingerprint.cjs` 的 `buildFingerprintConfig` 里，把 `language_switch:'1'`（随代理 IP）改为 `language_switch:'0'` + 显式 `language:['en-US']`；语言取值收口为文件内单一中心常量（便于回滚 / 灰度）。**字段语义已探针实证**（2026-07-11，本机 AdsPower CLI chrome_149）：`language_switch:'0'`+`language:['en-US']` → `navigator.languages=['en-US','en']`、`Accept-Language` 英文、**不随 IP**，且 timezone 仍随 IP 独立。直接用这组值，无需再 probe / 占位。 <!-- aidcp-edge af83f38 FINGERPRINT_UI_LANGUAGE=['en-US'] 单点常量；language_switch:'0'+language:[...]，automatic_timezone 不动 -->
- [x] 1.2 确认 `language` 不进 `assertOsCoherent`（`ads-fingerprint.cjs:107-130`）断言集——pin en-US 不触发 coherence 拒建；补一条单测断言「pin en-US 的 fingerprint 通过 `buildFingerprintConfig` 护栏与四者一致断言」。 <!-- aidcp-edge af83f38 测试「语言 pin: language 不进四者一致断言，pin en-US 不触发 coherence 拒建」 -->
- [x] 1.3 补 / 改单测：`buildFingerprintConfig` 产物含 `language=['en-US']` 且 `language_switch` 为关闭态；时区仍 based-on-IP（`automatic_timezone:'1'` 不动）。 <!-- aidcp-edge af83f38 测试「语言 pin: 每个模板产物 language=[en-US]、language_switch 关闭、时区仍 based-on-IP」 -->

## 2. aidcp-edge — 启动参数与导入 cookie 兜边角 chrome

- [x] 2.1 `src/cdp/browser-provider.ts:133` 的 `launchArgs` 追加 `--lang=en-US`（覆盖登出 / 未登录 chrome）；确认它经 `launch_args` JSON 正常下发、不与现有 `--window-size` / `--deny-permission-prompts` 冲突。 <!-- aidcp-edge af83f38 launchArgs += '--lang=en-US'；测试断言 launch_args 含 --lang=en-US -->
- [x] 2.2 `src/electron/facebook-account-import.cjs` 归一化导入 cookie 时，若缺 `locale` 则注入 `locale=en_US`（`FB_COOKIE_NAMES` 已含 `locale`，:14）；补单测覆盖「缺 locale → 注入 en_US」与「已有 locale → 不覆盖用户值」两分支。 <!-- aidcp-edge af83f38 header-pair 路径注入 FB_DEFAULT_LOCALE=en_US；结构化(JSON/TSV)路径原样透传不注入；两分支单测均加 -->
- [x] 2.3 在代码 / 文档注释写明：`--lang` 与 cookie `locale` **只兜登出 chrome、不改登录态群面语言**（避免误判「pin 了但群面仍外语」为回归）。 <!-- aidcp-edge af83f38 browser-provider.ts 注释标 belt-not-authority；facebook-account-import.cjs 注释标 belt + 结构化路径豁免 -->

## 3. aidcp-edge — 存量登录号结构性边界（只作证、不放宽）

- [x] 3.1 补一条回归断言 / 测试，坐实 `src/electron/ads-write-api.cjs` 的 `user/update` 仅接受 `{ user_id, user_proxy_config }` 两键、拒绝透传 `fingerprint_config`——存量号指纹语言经写客户端**结构性改不动**（红线靠测试守）。**不放宽 allowlist**。 <!-- aidcp-edge af83f38 测试「updateProfileProxy: 硬塞 fingerprint_config(含 language) 也进不了 body」；生产码本就结构性两键、未改 -->
- [x] 3.2 写存量号归一 runbook（docs 或 change 内）：一次性登入 → FB 账号设置改语言为 English (US) → 跨代理 / 会话验证界面英文；标注真实设置页导航路径为真机待验项。 <!-- 落 docs/real-machine-acceptance-backlog.md 簇 49 的「存量号归一 runbook」，设置页导航路径标真机待验 -->

## 4. 验证与回写

- [x] 4.1 edge `npm run typecheck` + `npm test` 全绿（无回归）。 <!-- aidcp-edge af83f38 typecheck clean；973 unit + 16 acceptance 全绿 -->
- [x] 4.2 `openspec validate facebook-locale-pin-en-us --strict` 通过。 <!-- 通过（控制仓）-->
- [x] 4.3 部署 dev（edge 侧）；把真机验证项登记到 `docs/real-machine-acceptance-backlog.md`：① ~~`language_switch`/`language` probe 键值语义~~ **已实证（2026-07-11 chrome_149），无需再登记**；② 新号建出后 FB 登录态界面英文 + 内容不塌（非英文群实测）；③ 存量号改账号语言设置页路径。 <!-- aidcp-edge af83f38 landed edge master（edge dev = master，无 ECS）；backlog 簇 49 登记（含②③ + 对抗评审揪出的 Intl/ICU locale seam 一致性核查）；真机 pending 运营机 pull + 重建安装包 --> <!-- 2026-07-11 deployed(edge master) -->
- [x] 4.4 回写本文件：各 task 标 `[x]` + `<!-- aidcp-edge <sha> 备注 -->`（部署后追 `<!-- <date> deployed -->`）。 <!-- 本次 -->
