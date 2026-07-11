# Tasks — edge-adspower-close-real-teardown

> edge-only（`../aidcp-edge`），不动协议 / 云端 / ECS。热点：`core-lifecycle.ts` + `browser-provider.ts` 与 `self-contained-ads-runtime` 逐字相同，单写、须 forward-port。改动后按回归纪律 `test:acceptance` → `test` → `typecheck`。

## 1. aidcp-edge — 权威关闭实证（provider 层，`src/cdp/browser-provider.ts`）

- [ ] 1.1 抽一个「探该 profile 调试端点是否仍应答」的判据（复用 `chrome-launcher.ts` 的 `/json/version` 端口探活思路），供 adspower 关闭确认用；host/port 取自 `launch` 交付的 endpoint，浏览器活=应答、死=不应答（有界轮询）。
- [ ] 1.2 重写 `confirmClosed()`：以 1.1 的端点实证为唯一「已关」判据；端点仍应答=未死继续；查询报错=不确定继续重试（**删除 `return true` 的「查不动就当已关」**）；有界上限内变暗=已关(true)；上限耗尽仍应答/不确定=如实返回未确认(false)。
- [ ] 1.3 `stop()` 失败不再静默吞：保留「容忍继续」但把失败纳入关闭结论与日志（不把失败伪装成成功）。
- [ ] 1.4 关闭按 profile `user_id` **重新发起**停止并按端点实证判定，MUST NOT 因关闭前 CDP 客户端连接已断（暂停驻留期）而静默空转当已关（对应 spec「暂停拆 CDP 后关闭仍收敛」）。

## 2. aidcp-edge — 升级实杀兜底（provider 层）

- [ ] 2.1 关闭序列改为：发 `browser/stop` → 有界等端点变暗 → 未暗则重发 `browser/stop` → 仍未暗则尽力 OS 级强杀该 profile 内核进程 → 再确认端点变暗。
- [ ] 2.2 内核进程句柄解析（尽力）：优先 AdsPower `browser/start`/`active` 回参（`webdriver`/debug_port）→ 次经调试端点反查占用该端口的进程 → 皆不得则**放弃 OS 杀、退回诚实未确认**（绝不假成功）。
- [ ] 2.3 OS 杀升级加 env 护栏（默认开，如 `AIDCP_ADS_CLOSE_OS_KILL`），便于一键回退到「仅软停止 + 诚实实证」层；设关闭总时长有界上限，到界如实判未确认、绝不无限挂起。

## 3. aidcp-edge — 核心关闭链路对接（`src/client/core-lifecycle.ts` / `src/main.ts`）

- [ ] 3.1 核对 `finalize`：`closeOwnedBrowser()`（→ `killAndConfirmDead` 新语义）返回未确认时走 `onCloseFailed`（`lifecycle.close_failed`），确认时才 `exit(0)`；确保新诚实判定被如实传导（此处逻辑已在、重在验证不回落假成功）。热点文件，谨慎最小改。
- [ ] 3.2 确认 `main.ts` 的 `closeOwnedBrowser` dep 把 provider 的新「未确认」结果如实透传（`freed=false` 不再被上层当已关）。

## 4. aidcp-edge — 外壳诚实收尾（`src/electron/main.cjs`）

- [ ] 4.1 修 `closeEdge` 的 **no-child 分支**：不再零回收直接标 `session:'closed'`；对本进程自有 profile 补一次停止 + `browser/local-active`（复用外壳已有 `listActiveProfiles`）实证，确认已关才呈现「已关闭」，否则如实报「无法确认已关」。外壳只读 ads-local-api 边界：如需外壳侧发停止走窄封装、不扩成通用写通道。
- [ ] 4.2 核对核心退出路径投影：确认关 → `session:'closed'`；`lifecycle.close_failed` → 保持暂停 + 「关闭状态未能确认」（该分支已在、验证不被绕过）。

## 5. aidcp-edge — 回归测试（聚焦假成功分支，勿逐场景堆测）

- [ ] 5.1 `test/cdp/browser-provider.test.ts` 补：停止未生效（端点仍应答）→ `confirmClosed` 不当已关；查询报错 → 不确定重试而非 true；软停止未生效 → 升级路径被触发；升级仍未暗且无 PID → 诚实返回未确认。
- [ ] 5.2 核心/外壳测试补：`finalize` 未确认 → `onCloseFailed`（不 exit 假成功）；外壳 no-child 关闭 → 无实证不标「已关闭」。（关键行为少数用例即可，桩验不了的 OS 杀真机部分转 backlog。）

## 6. aidcp-edge — 验证与收口

- [ ] 6.1 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（安全红线 `AC-*` 必过）。
- [ ] 6.2 若 `self-contained-ads-runtime` 等并发分支仍活跃且共享 `core-lifecycle.ts`/`browser-provider.ts`：land 后 forward-port，避免热点漂移。
- [ ] 6.3 干净 worktree 做最终确认后提交推 edge `master`（tasks.md 进度回写本仓，标注 commit-sha）。
- [ ] 6.4 真机验收项登记 backlog（运营机 pull master + 安装包重建后核：暂停→关闭浏览器真关、软停止失败态如实呈现、no-child 场景、OS 杀兜底是否触达、领先假设「暂停拆 CDP 致 AdsPower 判非活跃」是否属实）。
