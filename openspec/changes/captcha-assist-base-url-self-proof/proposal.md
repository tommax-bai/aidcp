## Why

验证码协助链接的公开基址是一条**进程内无法验证的声明**：它的真假由进程之外的 DNS / nginx 决定。2026-07-16 事故坐实了代价——dev 的 `AIDCP_CAPTCHA_ASSIST_PUBLIC_BASE_URL=http://aidcp.tommax.cc` 在 2026-07-07 配置时**是对的**（当时域名指 dev），2026-07-11 域名割接给 OL 后**这条 env 一字未动就腐烂成了跨环境指针**：dev 签发的链接把运营送到 OL，而 OL 既没有该事故（事故只活在签发进程的内存里）、也够不着该边缘分身（指令只能发给连在同一进程 8787 上的分身），于是在鉴权之前就回 `503 captcha_assist_unavailable`。

**腐烂潜伏了 5 天，因为没有任何东西在喊。** 系统当时已经"知道"链接会失败（它自己就是那个 503 的作者），却仍然发出一个长得像正常按钮的链接——这正是全仓红线「MUST NOT 静默假成功」的字面形态。修 env 只是治标：下一次域名 / 端口 / 反代变更会以同样的方式再来一次。

## What Changes

- **新增周期性基址自证探针**（云端，~40 行）：匿名 GET `${base}/api/captcha-assist/<probe-id>`（**无 token**），判据 = `status===503 && body.error==='captcha_assist_unavailable'`，连续 2 次确认才判死。含义是**「那个地址上没有协助服务 ⇒ 它铁定不是我」**。其余一切（401 / 404 / 200 / 5xx / HTML / 超时 / 拒连 / 非 JSON）→ `unknown` → 不行动、只记日志。
  - **零对端依赖**：`captcha_assist_unavailable` 是我方自己的签名字符串，dev 单边部署当天生效——不需要 OL 先部署、不需要新身份端点、不需要新 env 变量。
  - **周期性是机制本身、不是加分项**：07-11 割接时进程没重启，纯启动期检查在腐烂发生的那一刻**不在场**；启动期那一次只是周期的第一次执行。
- **判死 → 不签发链接，诚实降级**：P0 验证码卡**照发**（incident 仍创建、抓帧仍武装、风控暂停闸不受影响），只是**没有按钮** + detail 明说「协助链接已停用：该基址上没有协助服务（对端 IP x.x.x.x）」。爆炸半径收在"按钮"那一格。
- **`hasAssistAction: boolean` → `assistState: 'available' | 'not_configured' | 'refuted'`**：boolean 承载不了两个原因，会让「压根没配协助」的卡也说「基址指错」＝凭空造事实（静默假失败归因）。`not_configured` 保持今天原文，零回归。
- **`isAvailable()` 拆出 `canIssueLink()`**：判死结论**只被 `actionUrl()` 读**，绝不折进 `isAvailable()`。
- **一行启动日志**：打印生效基址 + 它来自哪个 env 变量（消掉 `?? AIDCP_PANEL_PUBLIC_BASE_URL` 回落的迷雾）。
- **面板层禁用 + 协助开着 = 必坏组合** → 懒读判死（探针不覆盖它：面板不 listen → nginx 502 HTML → `unknown`）。
- **incidentId 加环境标签前缀 + 401/404/503 三条 `reason` 改人话**（`error` 保机器码不动）：让**下一次**错投能自我解释。收益需 OL 部署才兑现，随下一趟 OL 车走。

### 已知盲区（写进 spec，留干净扩展缝，本次明确不做）

对端**也开着**协助时 → 401 missing_token → **无判决力**。将来若要覆盖，再补身份层；届时**主判别子必须是每进程随机的 boot id，绝不能用可被复制的 env 名**（`.env` 被照抄正是本病的形态，用一条不可验证的声明去校验另一条不可验证的声明＝机制归零）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `captcha-incident-handling`: 新增「外部基址自证 + 判死即不签发链接」的行为要求；把「协助链接不可用」的卡片降级从 boolean 二态提升为三态诚实归因；明确判死结论的唯一落点（`actionUrl`）与**禁止**落点（`isAvailable` / 面板注入判据）。

## Impact

**代码（仅 `aidcp-cloud`，不碰任何并行开发热点文件）**：

| 位置 | 改动 |
| --- | --- |
| `src/comm/captcha-assist.ts` | 新增探针 + `canIssueLink()`；`actionUrl()`(:424) 读判死；`idGen`(:141) 加标签前缀 |
| `src/comm/captcha-coordinator.ts` | `hasAssistAction` → `assistState` 三态；复用既有 `lastAlertAt`(:65) 冷却范式 |
| `src/feishu/cards.ts` | 三态文案（`if (alert.actionUrl)`(:136) 无按钮路径已现成） |
| `src/panel/panel-server.ts` | 401/404/503 三条 `reason` 改人话（`error` 机器码不动） |
| `src/server.ts` | 启动日志一行；探针以**函数**注入（deps 在 :1721 构造、面板 ~:4060 才 listen，塞值会拿到构造期快照） |

**明确不碰**：两份 `protocol.ts`（探针是 HTTP，**不新增 MessageType** ⇒ 不触发协议四处/五处同步）、`command-bridge` 动作映射、`RoleName` 注册、`risk-state-machine`。**不动 `aidcp-console`**（运营看到的文案经 console `CaptchaAssistPage.tsx:40-41` 的 `readError` 取 `reason ?? error` 原样上屏 ⇒ cloud 单侧改 `reason` 即可到运营眼里，省掉第 4 仓改动与另一次 OL 部署）。

**不新增告警卡种**：独立运维卡有三个代价（`unknown↔refuted` 抖动刷屏＝训练运营忽略告警；卡无 accountId 撞卡路由；`alertStore.raise` 的 type 枚举现为 `'captcha'|'block'`，加新 type 撞 console 枚举漂移白屏）。改为塞进 P0 卡 detail 一行 + 带冷却的 `console.error`——运营在**需要它的那一刻**看到。

**依赖 / 运维**：无新增 env、无新增依赖、无 DB 变更、无 nginx 变更。**顺带登记一笔债**：撤 dev nginx 里 inert 的 `server_name aidcp.tommax.cc` 块（手动 drop-in、不随部署走，留着就是长期制造「域名还指向 dev」假象的源；已实证它**不影响本判据**——dev 无 hosts 短路，探针走真实解析出网）。
