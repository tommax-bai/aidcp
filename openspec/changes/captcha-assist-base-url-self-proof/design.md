## Context

2026-07-16 运营点验证码协助链接报 `captcha_assist_unavailable`（503）。已实证的根因是**跨环境错投**，不是功能没开：

- 事故只活在**签发它的那个云端进程的内存**里（`captcha-assist.ts:129` 一张 Map，零持久化，重启即失）；
- 点击 / 抓帧指令只能发给**连在同一进程 8787 上**的边缘分身（`ws-server.ts:198-229`，找不到即诚实失败、拒绝广播）；
- 链接 = 基址直接拼 id + token（`captcha-assist.ts:424-429`），基址来自 env（`server.ts:1723`），**不做任何归属校验**。

dev 的基址原配 `http://aidcp.tommax.cc`——**2026-07-07 配置时是对的**（域名当时指 dev）；2026-07-11 域名割接给 OL 后，这条 env **一字未动就腐烂成了跨环境指针**，潜伏 5 天。同批腐烂还有：文档里 dev 的 `/capi` 可达地址、真机 backlog 簇 15 的「协助页外网 200」证据。割接的收尾清单扫了 nginx / 安装包 / 下载页，**从未审查过任何以域名为值的 `.env` 项**。

**约束（结构性，不可绕）**：

1. **签发时刻没有 HTTP 请求上下文**。链路是边缘经 WS 上报 → 处理器里当场造链接（`handler.ts:462-464` → `captcha-coordinator.ts:73-127` → `captcha-assist.ts:424-429`），与面板 HTTP 层是两个独立监听器。所以「从请求 Host 同源推导」**在签发时刻不存在**。
2. 飞书卡链接**发出即固化**，事后改配置救不回旧卡。
3. 红线：**MUST NOT 静默假成功**。
4. dev / ol 是两台独立 ECS，各自 systemd 跑一份 cloud；nginx 是手动 drop-in、不随部署走；`rsync --exclude .env`。
5. **`ol` 不进默认部署**（须用户明确要求 + 发布分支）⇒ 任何把收益押在「OL 也部署」上的方案，实际收益为零。

## Goals / Non-Goals

**Goals:**

- **G1 抓住运行期腐烂**：配置一字未动、脚下的世界变了。任何只检查「配置长什么样」的机制在定义上都看不见它——**只有真走一遍那条路才看得见**。
- **G2 不签发已知会失败的链接**：系统若已经知道基址不落在自己身上，还发一个长得像正常按钮的链接，就是红线的字面形态。
- **G3 降级不自残**：协助是云端的一个小功能。它的配置错，不能让边-云通道 / 发布 / 风控 / **验证码处置本身**一起停。
- **G4 让下一次错投可自解释**：接收方能说清「本实例不认识这条事故」。
- **G5 dev 单边部署当天生效**：见约束 5。

**Non-Goals:**

- 不做通用的服务发现 / 实例路由 / 配置中心。基址**全仓只有验证码协助一个消费者**（`PUBLIC_BASE_URL` 只命中 `server.ts:1723` 与 `:1745`）。
- 不救**已经发出**的旧卡（约束 2；且事故 TTL 30 分钟，收益趋近 0）。
- 不解决「验证码没人解」这个更大的业务痛点（见 Decisions 末条，另起 change）。

## Decisions

### D1 判据：问「那个地址上有没有协助服务」，不是「那个地址是不是我」

**选定**：周期性匿名 `GET ${base}/api/captcha-assist/<probe-id>`（无 token），判死 ⟺ `status===503 && body.error==='captcha_assist_unavailable'`，连续 2 次。

**为什么**：`captcha_assist_unavailable` 是**本系统自己的签名字符串**——它由 `panel-server.ts:233-236` 在鉴权之前发出，触发条件是协助服务未注入（`server.ts:3893`）。所以这条判据**零对端依赖**：不需要 OL 先部署、不需要新身份端点、不需要新 env 变量。

**2026-07-16 dev 实证（判据不是推理，是跑出来的）**：

| 探测目标 | 实测结果 | 结论 |
| --- | --- | --- |
| 错投的域名 `http://aidcp.tommax.cc` | `503 {"error":"captcha_assist_unavailable"}`，peer=`172.67.208.21`（Cloudflare） | **当场判死** ✅ |
| 自己的正确基址 `http://121.89.85.150:8088` | `401 {"error":"unauthorized","reason":"missing_token"}`，peer=`121.89.85.150` | 不误判 ✅（且回环通） |
| 同机 isales `127.0.0.1:8000` | `404 {"detail":"Not Found"}`（非我方信封） | 不误伤 ✅ |
| `getent hosts aidcp.tommax.cc` | Cloudflare IPv6；`/etc/hosts` 无 tommax 记录 | **无本机短路 / split-horizon** ✅ |

最后一行尤其重要：它排除了「dev nginx 那个 inert `server_name` 块把探针骗成假阳性」这一风险——探针走真实解析出网，够不着那个块。

**否决的替代方案**：

| 方案 | 否决理由 |
| --- | --- |
| **实例身份层**（`AIDCP_ENV` + boot id + health 回显 + 三态比对） | 只在「对端也 serve 协助」那个分支才需要，而那个分支未核；代价是新 env + 新 DTO + **必须先部署 OL** ⇒ 违 G5，dev-only 部署＝空转。且 `AIDCP_ENV` 本身**就是同一种腐烂**（手工维护、进程内不可验证的声明；`.env` 若从 dev 抄到 OL，两台都自称 dev ⇒ 恒判「是我」⇒ 机制归零）。**留成干净的缝**：将来真要做，主判别子必须是每进程随机 boot id，env 名只做文案。 |
| 云 metadata 推导基址 | 只给 IP，给不出 scheme / port / 域名（8787≠8088≠80）。OL 的正确基址是域名 ⇒ 照它办＝**用一个新错误替换旧错误**。 |
| Host / X-Forwarded 推导 | 签发时刻结构性不存在（约束 1）；且缓存 Host 再造带 token 的链接是有名字的投毒漏洞类——这是**「不该要」**，不只是「不可用」。 |
| 接住 WS upgrade 的 Host / 让边缘上报它拨的地址 | 只有 8787 那一跳，推不出面板的 scheme/port；边缘拨 IP 而基址是域名是**正常**的 ⇒ 比对无判决力。 |
| 反代转发 / sticky routing 到正主 | 需打通两台独立 ECS（隔离本身是安全边界）、需 owner registry（无）、nginx 又是手动 drop-in。**更根本**：转发是自愈，**自愈把配置错误永久掩埋**——这条 env 错了 5 天没人察觉，正因为没有任何东西在喊；加一层「指错也能用」等于把潜伏期从 5 天延长到无限。 |
| 基址挪进 DB | dev/ol 曾共库，共库时一个值服务两台＝**结构上保证至少一台是错的**；且 DB 里的值一样不可验证。 |
| 版本控制的 `{env: base}` 表 + 启动断言 | 表在 07-07 也会写 `aidcp.tommax.cc`——**变的是 DNS 不是表**。抓不住 G1。 |
| 飞书卡改回调按钮取代 URL | 协助页要的是截图 + 坐标点击的实时 UI，卡片给不了；且两台若连同一飞书 app，回调投给谁本身不确定，比 URL 更糟。 |
| token 加 `iss` claim | 503 在**鉴权之前**、claim 读不到；id 前缀已在 URL 里、三条错误路径全读得到。留缝不做。 |
| DNS 解析比对云 EIP | OL 域名前挂 Cloudflare ⇒ 解析到 anycast、**永远 ≠ 源站 EIP** ⇒ 会把**正确**的 OL 判坏。 |

**判据的盲区（写进 spec）**：对端**也开着**协助时 → 401 → 无判决力。这正是身份层将来的用武之地。

### D2 只在明确证伪时行动（unknown 一律不动）

401 / 404 / 200 / 5xx / HTML / Cloudflare 挑战页 / 传输失败 / 非我方 JSON 一律 `unknown` → 照常签发。

**理由**：基址正确但回环不通、出网被挡、对端是别的服务，都**不足以判定基址是错的**。宁可漏，不可误停 P0 路径的按钮。代价诚实说清：「基址配成一个死地址 / 打错端口」这类问题本机制看不见，会在运营第一次点击时暴露——MVP 明确不覆盖。

### D3 判死结论的唯一落点是链接签发处

`isAvailable()`（`:147`）有三个语义完全不同的消费者，落点写错会直接埋雷：

| 位置 | 语义 | 塞进判死的后果 |
| --- | --- | --- |
| `:156` `onDetected` 总闸 | 建 incident | 返 null ⇒ **不建 incident、不发抓帧** ⇒ 拿「配置错」惩罚「验证码处置」＝**违 G3 自残** |
| `server.ts:3893` 面板注入 | `isAvailable() ? svc : undefined` | **构造期一次性求值** ⇒ 塞动态态是死代码 + 「我以为加了闸」的假象 |
| `:425` `actionUrl()` | 签外链 | ✅ **唯一正确落点** |

**决定**：新增 `canIssueLink()`（基址存在 + 语法合法 + 非判死）与 `isAvailable()`（服务能力）分离，**只有 `actionUrl()` 读前者**。

**降级链路已现成、成本≈0（逐跳核实）**：`actionUrl()` 返 undefined → `onDetected` 的 `actionUrl: ... ?? ''`（`:186`）→ coordinator `assist?.actionUrl || undefined`（`:111`）→ `cards.ts:136` 不渲染按钮 + `captcha-coordinator.ts:252-256` detail 切成远程桌面兜底。**incident 仍创建、抓帧仍武装、暂停闸不受影响**（`coordinator:106` 的 `pauseEdge` 在 assist 之前，且 assist 异常已被 `:112-114` try/catch 兜住）⇒ 爆炸半径收在「按钮」那一格。

**注入方式**：结论必须以**函数**注入（`getVerdict?: () => Verdict`），**不能是值**——deps 在 `server.ts:1721` 构造、面板 `~:4060` 才 listen。

### D4 三态诚实归因，不是二态布尔

`hasAssistAction: boolean` 承载不了两个原因。若把「基址判死」的新文案直接挂 false 分支，**压根没配协助**的卡（dev 常态）也会说「基址指错」＝凭空造事实＝红线的镜像形态（静默假**失败**归因）。

**决定**：`assistState: 'available' | 'not_configured' | 'refuted'`，三条文案分开，`not_configured` 保持今天原文（零回归）。

### D5 不拒启动

**三条理由，第三条是决定性的**：① 探针依赖网络，一次抖动 → crashloop → 边-云通道 / 发布 / 风控全停，为一条链接字符串赔上整个云端；② 与全仓姿态一致（`server.ts:4082/4112` 一律 warn + 不启子组件，systemd 是裸 `ExecStart`、**没有 readiness 消费者**，做了 gate 也只是一行日志）；③ **拒启是启动期机制，而这是运行期腐烂——它在 07-11 那天根本不在场**。

**真正会拖停云端的不是拒启，是探针实现**（见 D6）。

### D6 实现纪律（不写进 spec 就会炸）

| 纪律 | 不做的后果 |
| --- | --- |
| `void probe().catch(log)` + 顶层 try/catch | `setInterval(() => probe())` 且 reject 无 catch ⇒ Node 18+ 默认 `unhandled-rejections=throw` ⇒ **整个 cloud 退出** |
| 自调度 `setTimeout`（上次结束再排下次）+ `AbortSignal.timeout(≤5s)` + 限响应体大小 | `fetch` 默认无超时 ⇒ 探针堆叠 |
| timer `.unref()`（仓内惯例 `captcha-assist.ts:405`） | 测试 / 优雅退出挂住 |
| **显式不复用连接**（`Connection: close` / 独立 dispatcher） | undici 连接池复用 ⇒ 不重新 lookup ⇒ **割接后仍打旧 IP**＝恰好掩盖 G1 要抓的那个腐烂 |
| **匿名、无 Authorization、无 token、不跟随重定向** | 基址可能指向任意第三方 ⇒ 周期性把凭据送给陌生主机 |
| 首跑延迟到面板 listen 之后 + 退避 | nginx 手动 drop-in、systemd 无 `After=nginx` ⇒ 整机重启时顺序未定义 |
| 签发路径**零网络调用**（只读缓存结论） | 验证码爆发时探测风暴 + 给 P0 路径加延迟 |
| 结论与告警记录**对端 IP**（socket remoteAddress） | 「域名解析回本机」这类假象无法当场看见 |

### D7 不新开告警卡种

复用 `captcha-coordinator` 已有的 `lastAlertAt` 冷却范式（`:65`），把「协助链接已停用：该基址上没有协助服务（对端 IP）」作为**一行**塞进 P0 验证码卡 detail + 一条带冷却的 `console.error`。

**否决独立运维卡的三个代价**：① `unknown↔refuted` 抖动会重复发卡＝**训练运营忽略告警**；② 运维卡无 accountId，撞卡路由（`unify-card-routing-origin-then-team`）；③ `alertStore.raise` 的 type 枚举现为 `'captcha'|'block'`，加新 type 撞 console 枚举漂移白屏。

运营在**需要它的那一刻**看到即可。要主动告警，等有人真抱怨「点了才知道」再加。

**但「没有落点的检测不算检测」**：现存那条 warn（`server.ts:1743-1747`）已经证明了反面——它既**只在基址为空时才触发**（可用性判断只做真值检查，`:147-149`，"存在但指错"结构上不可能触发），又只是一句 console.warn 进 journald。所以判死**必须**落到运营看得见的地方（P0 卡正文），不能只落日志。

### D8 文案落点在 cloud 单侧，不动 console

运营屏幕上那串 `captcha_assist_unavailable` 是 **console 渲染的**：`CaptchaAssistPage.tsx:40-43` 自己实现了 `readError`（`body.reason ?? body.error ?? res.statusText`），不走中文映射表。

**决定**：`error` **保机器码不动**（不破坏既有契约），**人话放进 `reason` 字段** ⇒ console 零改动、OL console 零重新部署。**不新增 `message` 字段**（那要改第 4 仓 + 另一次部署）。

### D9 不并入「console 事故列表页」

评审力荐、但**属另一个病**：console 现只有一条 token 驱动的 `/captcha-assist/:incidentId` 路由（`App.tsx:22`），**没有事故列表页** ⇒ 协助能力对这条 env 是**单点依赖**。加一个 JWT 鉴权的列表页可让运营**完全不依赖基址**处理验证码（incident 就在同进程内存里，运营平时就在用那台的 console），且**成本更低、无跨机验收、无 env 依赖**。

**但它治的是「验证码没人解」，本 change 治的是「发出去的按钮是坏的」。** 一个 change 不治两个病 ⇒ **另起 change**。

## Risks / Trade-offs

| 风险 | 缓解 |
| --- | --- |
| **对端也开着协助 → 401 → 判据失明** | 已知盲区，写进 spec。留身份层作为干净扩展缝（主判别子必须是 boot id，不能是可复制的 env 名） |
| **误判死 → 白白关掉好用的按钮** | 判据极窄（必须是我方签名 body）+ 连续 2 次确认 + 一切模糊状态归 `unknown`。实证：正确基址回 401、isales 回非我方 404 ⇒ 均不判死 |
| **探针崩掉整个云端** | D6 全部纪律；这是比拒启更真实的拖停路径 |
| **undici 连接池掩盖 DNS 割接** | 显式不复用连接。分钟级周期 + 默认 4s keepAlive 大概率不中，但那是**运气不是设计** |
| **探针把凭据送给配错的第三方地址** | 匿名、无 Authorization、不跟随重定向 |
| **基址配成死地址 / 错端口** | 本机制看不见（→ `unknown`），MVP 明确不覆盖，运营首次点击时暴露 |
| **判死粘性 / 抖动** | 判死需连续 2 次；恢复由下一次非判死结论解除（判据极窄 ⇒ 不会因网络抖动误入判死态，故可安全解除） |
| **dev nginx 的 inert `server_name` 块制造假象** | 已实证**不影响判据**（dev 无 hosts 短路，探针走真实解析出网）。但它仍是长期误导排查的源 ⇒ 登记为债，本 change 不动 nginx |
| **8088 将来加第二个 vhost** | IP 基址的 Host 不匹配任何 `server_name` ⇒ nginx 落到该端口**第一个** server 块。今天 8088 上只有 console 一个块所以能中。记为隐式依赖，不做 |

## Migration Plan

1. cloud 实装 + 单测（桩即可，不需真机）。
2. 部署 dev（默认目标）。**无新增 env、无新增依赖、无 DB 变更、无 nginx 变更** ⇒ 无需上机改 `.env`（这点很重要：本机制要治的病，根因恰恰是"没人上机改 env"；若它自己也依赖新 env，会静默未武装）。
3. **当天验收**（见 tasks，A1/A2/A3 为 archive 前阻塞门，**不 park 进真机 backlog**）。
4. 随下一趟 OL 车兑现 D8 的文案收益（接收方渲染，需 OL 部署）。

**回滚**：判死逻辑只影响链接签发一处；最坏情况把探针周期设为不启用即回到今天行为。

## Open Questions

1. **探针周期取值**（分钟级；太密＝噪声，太疏＝腐烂窗口长）。倾向 5 分钟，实装时定。
2. **OL 的 `.env` 到底缺 enabled / publicBaseUrl / tokenSecret 中的哪一项** —— 未实证（本次分析未 ssh 生产机）。不影响本设计：OL 缺什么都不是根因，且判据不依赖它。
3. **两台 token secret 是否相同** —— 未核。只影响错投落 503 还是 401，而 401 分支正是已声明的盲区。
