## 1. aidcp-edge — 既存诚实缺陷先修（准入，可独立合并验证）

> 这 5 条今天点击路径就有；键入把它们从潜伏变成常发。**必须先合并、先验证**，再进 §3。

- [x] 1.1 `src/browse/captcha-assist.ts`：`clicking` 集合改名 `writing`（防后来者新开 `typing` 集合再把洞开一次），同步 `liveTick` 的互斥判断 <!-- aidcp-edge d313630 -->
- [x] 1.2 `src/browse/captcha-assist.ts`：`handleCapture` 首行加 `writing` 互斥闸（与 `liveTick` 同形）——键入期的手动刷新帧会拍到打了一半的框、本就无价值 <!-- aidcp-edge d313630 -->
- [x] 1.3 `src/browse/captcha-assist.ts`：**摘掉「未经注入的单次 probe」发 cleared 的两处** —— `handleCapture` 的 `!kind` 分支、`recheckStaleBeforeReplay` 的 (a) 分支；两处只保留 `not_blocked` 回执（cloud `onClickResult` 已把 `not_blocked` → cleared，面板照常更新）。发出权只剩三条：①注入后 settle+fresh probe（`handleClick` 成功路径）②`liveTick` 的 K=3 ③overlay-report-gate 的翻转闸。**安全性已核实**：③ 独立轮询、遮罩真消失时发配对 cleared（`overlay-report-gate.ts:54`），不发不会滞留暂停态 <!-- aidcp-edge d313630 实装中扩了范围：recheckStaleBeforeReplay 的 (a) 分支同病同因，原 task 只列了 handleCapture 一处 -->
- [x] 1.4 `src/browse/captcha-assist.ts`：成功分支的 `sendRiskCleared()` 排到 `sendClickResult()` **之前**，二者**各自 try/catch**（承重的那条不能被装饰性的那条挡住） <!-- aidcp-edge d313630 新增 sendRiskClearedSafely/sendClickResultSafely 两个包装；吞异常但留日志，绝不静默 -->
- [x] 1.5 `src/browse/captcha-assist.ts`：catch 分支 best-effort 重抓帧回带 `snapshot`（失败时框里留着半截答案，运营看不见就无法带 clear 重来）；**重抓帧再失败 MUST NOT 盖掉原始 reason** <!-- aidcp-edge d313630 -->
- [x] 1.6 单测：注入期投递 `captcha.assist.capture` → 断言**零 snapshot 推送**（互斥闸的回归钉） <!-- aidcp-edge d313630 偏离：原写"断言零 risk.captcha_cleared"，实装中发现那是 1.3 在保证（handleCapture 根本不发 cleared）、不是互斥闸；互斥闸独有的职责是不回传半程画面，故断言改为零 snapshot。**已变异验证会咬人**（摘掉闸即红） -->
- [x] 1.7 单测：`sendRiskCleared` 先于 `sendClickResult`；后者抛错不影响前者已送达 <!-- aidcp-edge d313630 两个用例：顺序断言 + click_result 抛错时 cleared 仍已送达且 handle 不外抛 -->
- [x] 1.8 单测：`recheckStaleBeforeReplay` 的 (a) 分支回 `not_blocked` 且**零** `risk.captcha_cleared`（1.3 第二处的回归钉） <!-- aidcp-edge d313630 既有用例翻转：原用例名里就写着 "+ risk.captcha_cleared"，把缺陷本身钉成了契约 -->
- [x] 1.9 `npm test` + `npm run test:acceptance` + `npm run typecheck` 全绿后提交（本节可独立 land） <!-- aidcp-edge d313630 全量 1687 绿 / acceptance 23 绿 / typecheck 干净；已 ff 合入 edge master -->

> **§1 已 LANDED（edge `d313630`）**。**未部署**——edge 是客户端，改动需出包 + 逐台运营机换装才生效（出包非默认动作，见 CLAUDE.md §6）。本组对纯点击链路即刻有正收益，随下次出包一并生效。

## 2. 环境探查（不阻塞，决定是否另开 bugfix change）

- [ ] 2.1 探 dev / ol 的 `AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED` 实际取值（实测默认关：`server.ts` 要 `=== 'true'` 才开）
- [ ] 2.2 若实时抓帧**开着**：把「边缘帧环 8→16 / 云端近期集 5→12」提成**独立 bugfix change**（对纯点击同样有价值），**不捆进本 change**；若关着则登记为潜在项，不做

## 3. aidcp-edge — captcha 专用键盘原语（新模块）

- [x] 3.1 新建 `src/browse/captcha-type.ts`：ASCII 键位表（0-9 / a-z / A-Z / 空格 / 常见标点 → `{key, code, windowsVirtualKeyCode, needsShift}`），表外字符诚实拒绝 <!-- aidcp-edge 2ee4959 上档字符（'!'→Shift+Digit1）派发真实基键、非凭空造键；另加 validateCaptchaText（长度+字符集，注入前整单校验） -->
- [x] 3.2 `commitKeyStroke(cdp, spec, dwellMs, sleep)`：真 `keyDown{key,code,vk,text,unmodifiedText}` → sleep(dwell) → `keyUp`；需 Shift 的用真实 Shift keyDown/keyUp 包裹；**无 options 参数**（词法上插不进取消点）；try/finally 保证 keyUp 与 Shift-up 必发（照抄 `commitLeftClick` 已定案形状） <!-- aidcp-edge 2ee4959 命名从 dispatchTypedChar 改为 commitKeyStroke，与 commitLeftClick 同族（commit 前缀 = 原子区、无取消点） -->
- [x] 3.3 `dispatchHumanTyping(cdp, text, opts): Promise<number>`：复用 `generateKeyStrokes` 取 flight；dwell 独立采样 lognormal(median 75, σ0.3) clamp[30,180]；每字符 sleep → `assertInputSafety(opts)`（**顺序 checkpoint→deadline 不可反**）→ `commitKeyStroke`；循环边界 = strokes 数组长度（迭代限界） <!-- aidcp-edge 2ee4959 顺带导出 cdp-util 的 assertInputSafety（原为私有） -->
- [x] 3.4 `dispatchHumanTyping` 加 **RTT 补偿**：测量上次 CDP 往返、从下次 sleep 扣除 <!-- aidcp-edge 2ee4959 实测往返里扣掉自己 sleep 的 dwell，剩下才是传输层的账；medianMs 由调用方按 edgeId 派生偏置后传入（§5 接线时给） -->
- [x] 3.5 `probeFocus(cdp)`：evalRaw **只读** `document.activeElement` → `{tier, tag}`；形状异常一律判 none <!-- aidcp-edge 2ee4959 探针抛错的 fail-closed 在调用方（§5）处理 -->
- [x] 3.6 `clearFocusedField(cdp, tier)`（**强制、非开关**）：`editable` → JS select + Backspace + 回读 ⇒ `verified`；`opaque` → 键盘 select-all + Backspace ⇒ `attempted` <!-- aidcp-edge 2ee4959 -->
- [x] 3.7 `readFocusedText(cdp)`：**读全文** <!-- aidcp-edge 2ee4959 -->
- [x] 3.8 单测 15 例：键事件数 == 字符数、**零 `Input.insertText`**；Shift 包裹成对且必松开；keyDown 抛错也补发 keyUp 且不覆盖原始异常；表外字符拒绝；被抢占/超预算的诚实计数 + 接管优先于死线；焦点三态；清空三态；RTT 补偿；真实随机源下键间隔保留方差 <!-- aidcp-edge 2ee4959 三个关键断言经**先红后绿**变异验证会咬人（RTT 补偿 / Shift 松开 / 键事件数）。**过程中抓到自己一个假绿**：RTT 用例最初按「keyDown 计数==序号」判别 flight/dwell，把 dwell 误记成 flight，而 dwell 恰好撞上 flight-RTT 的值 ⇒ 摘掉补偿照样绿。判别器改按 keyDown/keyUp 配对状态（dwell 必夹在两者之间），不按计数更不按数值 -->

> **§3 已完成（edge `2ee4959`，在分支 `captcha-assist-text-answer` 上，未合 master）**。全量 1702 绿 / acceptance 23 绿 / typecheck 干净。纯新增模块 + 一处导出，零现役路径改动。

## 4. aidcp-edge — 协议字段 + 构建能力位

- [ ] 4.1 `src/comm/protocol.ts`：`CaptchaAssistClickPayload` += `text?: string` / `submit?: 'enter'`，带敏感性注释（MUST NOT 落日志/库/回执/URL，比照 `image.data` 口径）+ **actions DSL seam 注释**（未来升格路径）
- [ ] 4.2 `src/comm/protocol.ts`：`CaptchaAssistClickResultPayload` status += `no_target`；+= `inputMode?: 'click'|'click_type'`；+= `typeReport?`（`focus` / `focusTag` / `cleared` / `typed` / `verified` / `submitted`，**绝不含答案本身**）+ keystrokes seam 注释
- [ ] 4.3 `src/comm/protocol.ts`：**移除** `EdgeHelloPayload.remoteAddr`
- [ ] 4.4 新建 `src/client/build-capabilities.ts`：`EDGE_BUILD_CAPABILITIES = ['captcha_assist_text_v1']`
- [ ] 4.5 `src/client/edge-client.ts`：在 **构造函数内部**把构建能力拼进 `capabilities`（**MUST NOT 进任何 driver 常量**）；移除 `remoteAddr` 相关字段与 hello 装配
- [ ] 4.6 `src/main.ts` / `src/wechat-channels/runtime.ts`：移除 `AIDCP_REMOTE_ADDR` 读取与传递
- [ ] 4.7 单测：hello 载荷恒含 `captcha_assist_text_v1`（`main.ts` 与 `wechat-channels/runtime.ts` **两条装配路径各一**）
- [ ] 4.8 **AC-PROTO-07**：`CaptchaAssistClickPayload` / `CaptchaAssistClickResultPayload` 的**逐字段往返断言**（继 `WelcomePayload.pacing` 之后第二例；注释写明这是可被后续所有「扩载荷」路线照抄的模板）

## 5. aidcp-edge — handleClick 键入接线

- [ ] 5.1 `handleClick` 前置：`validateText`（charset `[0x20,0x7E]` + 长度 1..24 → `invalid_target` / `text_unsupported`）+ v1 形状纵深校验（有 `text` ⇒ `points.length === 1`）——与 `point_out_of_range` 同一位置纪律
- [ ] 5.2 聚焦腿：trajectory 或 `dispatchClick(points[0])`，坐标用**被 pin 那帧自己的 crop**；`recheckStaleBeforeReplay` 四态原样继承
- [ ] 5.3 **中途复检 #1**（键入前）：`probeBlockingKind` + `sameLocation` → 遮罩不在 ⇒ `cleared` / `cleared_mid_sequence`（零字符派发）；kind/URL 变 ⇒ 重抓帧 push + `stale_snapshot` / `page_moved_mid_sequence`
- [ ] 5.4 `probeFocus` → `none` ⇒ `no_target` / `focus_not_landed`，`typed=0`，**MUST NOT 提交**
- [ ] 5.5 `clearFocusedField`（强制）→ `dispatchHumanTyping`（checkpoint = `taskCoordinator.canExecute(taskId)`，`deadlineAt = now+20s`）→ `typed`；TaskTakeoverError ⇒ 清场 + `failed`/`takeover_during_type`；DeadlineError ⇒ 清场 + `failed`/`type_deadline_exceeded`；两者均 `typed=N` 如实回报、**MUST NOT 提交**
- [ ] 5.6 回读（仅 `editable`）→ `verified: match|mismatch`；`opaque` ⇒ `unverifiable`。**顺序 MUST：type → read → submit**
- [ ] 5.7 **中途复检 #2**（Enter 前）：`probeBlockingKind` + `probeFocus` 仍在原 tier；任一不满足 ⇒ 停手、不提交、诚实回执
- [ ] 5.8 `submit === 'enter'` ⇒ `pressEnter`（已带 `'\r'` 真实 keypress）→ `submitted = true`
- [ ] 5.9 settle → **有界重试的 fresh 复检（4 次 / 500ms，迭代限界）**：无遮罩 ⇒ `sendRiskCleared()` 后 `sendClickResult('cleared')`（排序已由 1.4 修）；有遮罩 ⇒ 重抓帧 + `still_blocked`；全抛 ⇒ `failed` / `verdict_unavailable_after_submit` + `submitted:true` + 尽力回带新帧
- [ ] 5.10 `src/main.ts`：把 `taskId` 透传给 handler 以构造 checkpoint；序列中途（聚焦后 / 清空后 / 键入后）`taskCoordinator.touch(taskId)`
- [ ] 5.11 单测：`no_target` 零派发不提交；中途复检 #1 触发 ⇒ 零字符；被抢占 / 超预算 ⇒ `typed < len` + 清场 + 未提交；Enter 后探针连抛 ⇒ `verdict_unavailable_after_submit`（**不是** `click_failed`）；`text` 且 `points.length !== 1` ⇒ 注入前拒绝
- [ ] 5.12 `npm test` + `npm run test:acceptance` + `npm run typecheck` 全绿

## 6. aidcp-cloud — 协议镜像 + 校验闸

- [ ] 6.1 `src/comm/protocol.ts`：与 edge **逐字一致**镜像 4.1 / 4.2 的字段；移除 `EdgeHelloPayload.remoteAddr`
- [ ] 6.2 `src/comm/captcha-assist.ts`：`submitClick` 在**租约获取之前**插 `sanitizeText`（长度 1..24 + charset）→ `invalid_text`；**畸形 = 整单拒绝**，注释显式对照 trajectory 的「丢弃装饰、保留 points 继续」为何**策略相反**
- [ ] 6.3 `src/comm/captcha-assist.ts`：v1 形状闸 `text && points.length !== 1` → `invalid_points` / `text_requires_single_focus_point`
- [ ] 6.4 `src/comm/captcha-assist.ts`：**能力闸 fail-closed** —— `pusher` dep += `edgeCapabilities?(edgeId)`，**live 查当前连接**（不用 `onDetected` 快照，incident 可能比连接活得久）；未声明 ⇒ `edge_lacks_text_capability`；查不到 ⇒ fail-closed 且 reason 能分辨「在线但没声明」与「连接状态未知」
- [ ] 6.5 `src/comm/captcha-assist.ts`：`lastDispatch` += `textLen?`（`type` 联合**不动**）；`lastResult` += `inputMode?` / `typeReport?` 透传；`onClickResult` 映射 += `no_target` → failed
- [ ] 6.6 `src/comm/captcha-assist.ts`：**版本偏斜检测** —— `lastDispatch.textLen > 0 && 回执 inputMode !== 'click_type'` ⇒ `lastResult` 标 `text_not_executed`
- [ ] 6.7 `src/comm/captcha-assist.ts`：**答案明文边界** —— `text` 只活在 `submitClick` 调用栈，MUST NOT 写进 incident / logger；加注释锁死
- [ ] 6.8 **incident 状态机不动**（复用 `click_pending`，不加 `input_pending`）⇒ console 两张 Record 表零改动
- [ ] 6.9 移除 remoteAddr 连带：`src/comm/ws-server.ts`（session 字段）、`src/comm/handler.ts`（hello 赋值）、`src/comm/captcha-assist.ts`（incident 字段 + 装配）、`src/comm/captcha-coordinator.ts`（**删飞书卡「远程地址」行**）
- [ ] 6.10 **AC-PROTO-07** cloud 侧：同 4.8 的逐字段往返断言

## 7. aidcp-cloud — panel 层

- [ ] 7.1 `src/panel/panel-server.ts`：`/click` 分支 body 解构 += `text, submit`（**不新增 verb、不新增身份闸** —— 键入与点击共用同一授权面，见 design D9）
- [ ] 7.2 `src/panel/panel-server.ts`：`captchaAssistStatus` 从 if 链 + default 改成 **`Record<reason, number>` 穷举表**（reason union 一加成员 typecheck 立刻红）；定码 `invalid_text`/`invalid_points`→400、`edge_lacks_text_capability`→409、`not_found`→404
- [ ] 7.3 `src/panel/types.ts`：`submitClick` 签名 += `text?` / `submit?`；移除 remoteAddr
- [ ] 7.4 单测：**panel 把 `text`/`submit` 透传到 `submitClick`**（HTTP 边界手写解构的守卫——漏字段 = 静默丢弃 + typecheck 全绿）
- [ ] 7.5 单测：`actor='captcha-assist-token'` + text ⇒ **200 且命令已下发**（飞书链接可直接键入，MUST NOT 因缺 console 登录而拒）；**纯点击 ⇒ 200（零回归）**；未声明能力 ⇒ 409 且**命令未下发**；畸形 text ⇒ 整单拒绝、未下发
- [ ] 7.6 `npm test` + `npm run test:acceptance` + `npm run typecheck` 全绿

## 8. aidcp-console — 协助页

- [ ] 8.1 `src/types/api.ts`：`lastResult.status` union += `no_target`；+= `inputMode?` / `typeReport?`；**移除 `remoteAddr`**（手抄镜像，不在 `/api/version` 指纹对拍内 ⇒ 登记为已知缺口）
- [ ] 8.2 `src/pages/CaptchaAssistPage.tsx`：**删「远程桌面」按钮**及 `remoteAddr` 相关渲染
- [ ] 8.3 `src/pages/CaptchaAssistPage.tsx`：导入 AntD `Input`（**不做登录态感知、不挂 Bearer** —— 键入与点击共用同一 scoped token 授权面，见 design D9）
- [ ] 8.4 `src/pages/CaptchaAssistPage.tsx`：**不变量长在控件上** —— 答案框 disabled 直到 `points.length === 1`（label「先在截图上点中输入框，再在此键入答案」）；`text` 非空时不让放第 2 个点
- [ ] 8.5 `src/pages/CaptchaAssistPage.tsx`：「回车提交」Checkbox 默认开；**不提供「点第 2 个点提交」**（聚焦滚动会让旧坐标失效且 `sameLocation` 检测不到）
- [ ] 8.6 `src/pages/CaptchaAssistPage.tsx`：**pin 触发扩到首次键入** —— `frozen = (points.length > 0 || text.length > 0) && pinned != null`，使「画面已更新」Alert 在打字期照常生效
- [ ] 8.7 `src/pages/CaptchaAssistPage.tsx`：提交 body += `text?` / `submit?`（空则整字段省略，与 trajectory 同「全有或全无」纪律）；**提交成功与 adoptLatest 后立即清空 text state**；答案绝不进 URL / localStorage
- [ ] 8.8 `src/pages/CaptchaAssistPage.tsx`：建 **`Record<lastResult['status'], string>` 穷举表**（现为裸打英文枚举、无表 ⇒ 新增的 `no_target` 本会从这个洞溜走）
- [ ] 8.9 `src/pages/CaptchaAssistPage.tsx`：`typeReport` 渲染成三句人话（**用户价值兑现点**）——「字打进去了，但答案不对」/「焦点在跨源/不可读元素内，无法证明字符已落入；请对照新画面确认」/「那一点没点到输入框」；`edge_lacks_text_capability` ⇒ 「该机器客户端版本过旧，不支持远程输入」（不裸打英文 reason）
- [ ] 8.10 `src/pages/CaptchaAssistPage.test.tsx`：无落点 ⇒ 输入框 disabled；打字触发 pin ⇒ 「画面已更新」Alert；答案不出现在任何 fetch URL；**纯点击提交体与今天逐字节一致**
- [ ] 8.11 `npm test` + `npm run typecheck` 全绿

## 9. aidcp（中控）— 文档

- [ ] 9.1 `docs/protocol.md`：改 `captcha.assist.click` / `click_result` 两段 jsonc + 语义注释（`text` 敏感性 / 单点约束 / 焦点三态 / 提交只走 enter）；**头部计数 91 不动、§2 表不加行**
- [ ] 9.2 `docs/protocol.md`：顺手修既存漂移 —— click 样例漏了 `taskId`
- [ ] 9.3 `openspec/specs/captcha-incident-handling/spec.md` 的「消息数断言均为 44」已腐烂（实测 91）—— 已在 spec delta 的 MODIFIED 里改为不写死数字，归档时自然生效；**确认 archive 后主 spec 无残留 44**

## 10. 集成与部署

- [ ] 10.1 三仓分别 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`（协议改动的回归纪律）；安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过
- [ ] 10.2 `openspec validate captcha-assist-text-answer --strict`
- [ ] 10.3 合回各仓默认分支（fetch + rebase + ff）；**热点文件与活跃 change `captcha-assist-base-url-self-proof` 串行**
- [ ] 10.4 部署 dev：cloud + console（先探 ECS 真实现状、先备份、rsync 排除 .env/node_modules/.git、restart、healthcheck；**绝不碰同机 isales**）
- [ ] 10.5 dev 冒烟：纯点击流零回归；未换装的 edge 提交 text ⇒ 409 + 人话文案

## 11. 真机验收登记（新簇，写入 docs/real-machine-acceptance-backlog.md）

- [ ] 11.1 登记：模糊数字图片类字符识别码 ⇒ `focus:'editable'` + `verified:'match'` 全绿、验证码真被解开
- [ ] 11.2 登记：焦点被 canvas / iframe 抢走 ⇒ `opaque` + `unverifiable` + 像素判据
- [ ] 11.3 登记：点空 ⇒ `no_target`，拒绝键入且不提交
- [ ] 11.4 登记：打字期挑战换图 ⇒ pin + 「画面已更新」
- [ ] 11.5 登记：**Enter 提交导航后不被误报 failed**
- [ ] 11.6 登记：未换装新包的运营机 ⇒ 409 + 人话文案（**需一次 edge 出包 + 逐台换装才能验**）
- [ ] 11.7 登记：**从飞书卡链接直接点开协助页（未登录控制台）即可键入并解开验证码**（授权面不变的真机钉）
- [ ] 11.8 登记：焦点假阳性取证 —— `focusTag` 是否足以事后判别「打进了错误的框」
- [ ] 11.9 登记：确认协助页与飞书卡**已无远程桌面入口**

## 12. 独立登记（不在本 change 内做）

- [ ] 12.1 登记独立 change：**cleared 断连不可达** —— overlay-report-gate 无论 send 成没成都消费掉 `reportedKind`，断连时解决掉的验证码永不到云端、账号一直暗着（要改 gate 的「已投递 vs 已尝试」记账）
- [ ] 12.2 登记：incident TTL 30min 只在 `onDetected` 刷新、无续期入口
- [ ] 12.3 登记：console 三处手抄 union 不在 `/api/version` 指纹对拍内（cloud 改了 console 零提示）
- [ ] 12.5 登记：**「卡的可见范围 = 操作范围」** —— 协助页在登录门外凭 scoped token 授权、飞书群路由无内外部标记，看得见卡的人就能操作。**既有性质**（今天已完整适用于协助点击与其它审批卡），本 change 不引入、不扩大、不解决；归属是路由层的内外部标记
- [ ] 12.4 登记（条件）：classifier 词表零条输入类文案 —— 本次报障形态已能被检出故非准入；若后续发现同类漏检，扩词表 MUST 用**真实文案**（裸词误命中已付过代价），不能凭猜
