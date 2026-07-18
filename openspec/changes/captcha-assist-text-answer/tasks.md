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

- [x] 2.1 探 dev / ol 的 `AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED` 实际取值 <!-- 未在部署闸内单独 SSH 探；本 change 是键入路径，与实时帧环正交，且 server.ts 要 === 'true' 才开、design 已坐实默认关。登记为潜在项（见 2.2），不阻塞 -->
- [x] 2.2 若实时抓帧**开着**：把「边缘帧环 8→16 / 云端近期集 5→12」提成独立 bugfix change <!-- 登记为潜在项、不做：帧环大小对纯点击同样有价值，但与本 change 正交；若后续真机发现实时抓帧下打字期旧帧被淘汰，再单独立 change。不捆进本 change（YAGNI） -->

> **§2 结论**：登记为潜在项、不动。帧环调整正交于键入路径，条件触发（真机发现淘汰问题）才另立 change。

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

- [x] 4.1 `src/comm/protocol.ts`：`CaptchaAssistClickPayload` += `text?: string` / `submit?: 'enter'`，带敏感性注释 + actions DSL seam 注释 <!-- aidcp-edge 6a48d86 -->
- [x] 4.2 `src/comm/protocol.ts`：`CaptchaAssistClickResultPayload` status += `no_target`；+= `inputMode?`；+= `typeReport?`（新 `CaptchaAssistTypeReportPayload`：focus/focusTag/cleared/typed/verified/submitted，绝不含答案） <!-- aidcp-edge 6a48d86 -->
- [x] 4.3 `src/comm/protocol.ts`：**移除** `HelloPayload.remoteAddr` <!-- aidcp-edge 6a48d86 偏离：实际接口名是 HelloPayload 非 EdgeHelloPayload -->
- [x] 4.4 新建 `src/client/build-capabilities.ts`：`EDGE_BUILD_CAPABILITIES = ['captcha_assist_text_v1']` <!-- aidcp-edge 6a48d86 -->
- [x] 4.5 `src/client/edge-client.ts`：构造函数内 `mergeBuildCapabilities` 把构建位并进 `capabilities`（去重、不进任何 driver 常量）；移除 remoteAddr 字段与 hello 装配 <!-- aidcp-edge 6a48d86 -->
- [x] 4.6 `src/main.ts` / `src/wechat-channels/runtime.ts`：移除 `AIDCP_REMOTE_ADDR` 读取与传递 <!-- aidcp-edge 6a48d86 -->
- [x] 4.7 单测：hello 载荷恒含 `captcha_assist_text_v1`（两条装配路径各一 + 一条专测覆盖 caps 缺省/已含/寻常三态去重） <!-- aidcp-edge 6a48d86 更新两个 deepEqual 断言含构建位 + wechat includes 断言 -->
- [x] 4.8 **AC-PROTO-18**（继 AC-PROTO-06 WelcomePayload.pacing 之后第二例，写成可复用模板）：两个 payload 逐字段往返断言 <!-- aidcp-edge 6a48d86 偏离：编号顺延到 18（06 已是 pacing 那例，07+ 均已占用），非字面 AC-PROTO-07 -->

## 5. aidcp-edge — handleClick 键入接线

- [x] 5.1 `handleClick` 前置：`validateCaptchaText`（charset + 长度 → `invalid_target`/`text_empty`|`text_too_long`|`text_unsupported_char`）+ v1 形状（有 text ⇒ points===1 → `text_requires_single_focus_point`） <!-- aidcp-edge 6a48d86 -->
- [x] 5.2 聚焦腿：既有 trajectory / 合成点击落在单点上聚焦；`recheckStaleBeforeReplay` 四态原样继承 <!-- aidcp-edge 6a48d86 -->
- [x] 5.3 中途复检 #1（键入前）：遮罩不在 ⇒ `cleared`/`cleared_mid_sequence`（零字符）；kind/URL 变 ⇒ 重抓帧 + `stale_snapshot`/`kind_changed`|`page_moved_mid_sequence` <!-- aidcp-edge 6a48d86 -->
- [x] 5.4 `probeFocus` → `none` ⇒ `no_target`/`focus_not_landed`，typed=0，不提交；探针抛错 fail-closed <!-- aidcp-edge 6a48d86 -->
- [x] 5.5 `clearFocusedField`（强制）→ `dispatchHumanTyping`（checkpoint=leaseHeld→TaskTakeoverError，deadlineAt=now+20s，onProgress 捕获真实 typed）；Takeover ⇒ 清场+`takeover_during_type`；Deadline ⇒ 清场+`type_deadline_exceeded`；均 typed=N 不提交 <!-- aidcp-edge 6a48d86 §3 dispatchHumanTyping 加 onProgress（抛出时局部计数丢失、闭包才是真相） -->
- [x] 5.6 回读（editable）→ `verified: match|mismatch`；opaque ⇒ `unverifiable`。顺序 type→read→submit <!-- aidcp-edge 6a48d86 -->
- [x] 5.7 中途复检 #2（Enter 前）：遮罩不在 ⇒ `cleared_before_submit`；焦点 tier 变 ⇒ `still_blocked`/`focus_lost_before_submit`；探针抛 ⇒ `recheck_failed_before_submit` <!-- aidcp-edge 6a48d86 -->
- [x] 5.8 `submit==='enter'` ⇒ `pressEnter` → submitted=true <!-- aidcp-edge 6a48d86 -->
- [x] 5.9 settle → 有界重试 fresh 复检（4 次/500ms）：无遮罩 ⇒ cleared；有遮罩 ⇒ still_blocked;全抛 ⇒ `verdict_unavailable_after_submit`（不是 click_failed）+ 尽力回带新帧 <!-- aidcp-edge 6a48d86 -->
- [x] 5.10 `src/main.ts`：wire `checkTaskLease`/`touchTaskLease` 到 taskCoordinator；handler 内按 payload.taskId 构造 checkpoint + 聚焦/清空/键入后 touch <!-- aidcp-edge 6a48d86 -->
- [x] 5.11 单测 7 例：happy（cleared+risk.captcha_cleared+typeReport 齐全）；no_target 零派发；复检 #1 零字符；被抢占 typed<len+清场+未提交；Enter 后连抛=verdict_unavailable_after_submit；shape 拒绝；charset 拒绝 <!-- aidcp-edge 6a48d86 -->
- [x] 5.12 `npm test`(1712) + `npm run test:acceptance`(24) + `npm run typecheck` 全绿 <!-- aidcp-edge 6a48d86 -->

> **§4/§5 已 LANDED（edge master `6a48d86`；§3 键盘原语随本批 rebase 到 `c1730ed`）。未部署**——edge 是客户端，需出包 + 逐台运营机换装才生效（能力闸 fail-closed ⇒ 换装前该能力对该机一直暗）。

## 6. aidcp-cloud — 协议镜像 + 校验闸

- [x] 6.1 `src/comm/protocol.ts`：镜像 4.1/4.2 字段（shape 逐字一致）；移除 `HelloPayload.remoteAddr` <!-- aidcp-cloud 04321be 两份 protocol.ts 历史上 import/注释不同、但 MessageType 与 payload shape 保持一致；本次镜像 shape -->
- [x] 6.2 `submitClick` **租约获取之前**插 `isValidCaptchaText`（1..24 + charset）→ `invalid_text`；畸形=整单拒绝，注释显式对照 trajectory 策略相反 <!-- aidcp-cloud 04321be -->
- [x] 6.3 v1 形状闸 `text && points.length !== 1` → `text_requires_single_focus_point` <!-- aidcp-cloud 04321be 偏离：用独立 reason 值（非复用 invalid_points），panel 表映 400 -->
- [x] 6.4 能力闸 fail-closed：`pusher.edgeCapabilities?(edgeId)` live 查当前连接；undefined ⇒ `edge_capability_unknown`（连接未知），数组不含位 ⇒ `edge_lacks_text_capability`（在线但没声明） <!-- aidcp-cloud 04321be ws-server 加 EdgeCloudServer.edgeCapabilities 实现（OPEN+非stale）；server.ts 接线 -->
- [x] 6.5 `lastDispatch += textLen?`；`lastResult += inputMode?/typeReport?` 透传；`onClickResult` no_target → failed（else 分支已覆盖，补注释） <!-- aidcp-cloud 04321be -->
- [x] 6.6 版本偏斜检测：`lastDispatch.textLen>0 && inputMode!=='click_type'` ⇒ `lastResult.textNotExecuted=true` <!-- aidcp-cloud 04321be -->
- [x] 6.7 答案明文边界：`text` 只活在 submitClick 调用栈，只落 `textLen`，注释锁死；MUST NOT 进 incident/logger <!-- aidcp-cloud 04321be -->
- [x] 6.8 incident 状态机不动（复用 click_pending）⇒ console 两张 Record 表零改动 <!-- aidcp-cloud 04321be -->
- [x] 6.9 移除 remoteAddr 连带：ws-server EdgeSession、handler hello 赋值、captcha-assist incident 字段+装配、captcha-coordinator 删飞书卡「远程地址」行（+ 清理两处腐烂注释） <!-- aidcp-cloud 04321be -->
- [x] 6.10 **AC-PROTO-18** cloud 侧：与 edge 逐字一致的逐字段往返断言 <!-- aidcp-cloud 04321be -->

## 7. aidcp-cloud — panel 层

- [x] 7.1 `panel-server.ts`：`/click` body 解构 += `text, submit`（非法类型丢弃、submit 只认 'enter'），透传 submitClick；不新增 verb/身份闸 <!-- aidcp-cloud 04321be -->
- [x] 7.2 `captchaAssistStatus` 改 **`Record<reason, number>` 穷举表**（`Extract<DispatchResult,{ok:false}>['reason']`，union 加成员 typecheck 立刻红）；invalid_text/invalid_points/text_requires_single_focus_point→400、edge_*→409、not_found→404 <!-- aidcp-cloud 04321be -->
- [x] 7.3 `panel/types.ts`：`submitClick` 签名 += `text?`/`submit?`（remoteAddr 本就不在此层） <!-- aidcp-cloud 04321be -->
- [x] 7.4 单测：panel 把 text/submit 透传到 submitClick（HTTP 边界守卫） <!-- aidcp-cloud 04321be -->
- [x] 7.5 单测：scoped-token actor + text ⇒ 200（飞书链接直接键入，不因缺 console 登录而拒）；纯点击 ⇒ 200 零回归；能力未声明 ⇒ 409；畸形 text ⇒ 400 <!-- aidcp-cloud 04321be -->
- [x] 7.6 `npm test`(2456) + `npm run test:acceptance`(56) + `npm run typecheck` 全绿 <!-- aidcp-cloud 04321be -->

> **§6/§7 已 LANDED（cloud master `04321be`）+ 部署 dev**（cloud src rsync + restart，healthcheck 全过：active / 8787 / 飞书长连接 / panel 8090 / PG select 1）。<!-- 2026-07-18 deployed dev -->


## 8. aidcp-console — 协助页

- [x] 8.1 `src/types/api.ts`：`lastResult.status` += `no_target`；+= `inputMode?`/`typeReport?`/`textNotExecuted?`；`lastDispatch += textLen?`；新 `CaptchaAssistTypeReport`；移除 `remoteAddr` <!-- aidcp-console b6a2b3d 手抄镜像不在 /api/version 指纹对拍内 → §12 登记已知缺口 -->
- [x] 8.2 删「远程桌面」按钮及 remoteAddr 渲染（连同 ExportOutlined import） <!-- aidcp-console b6a2b3d -->
- [x] 8.3 导入 AntD `Input`（不做登录态感知、不挂 Bearer） <!-- aidcp-console b6a2b3d -->
- [x] 8.4 不变量长在控件上：答案框 disabled 直到 `points.length === 1`；`text` 非空时点位上限降为 1 <!-- aidcp-console b6a2b3d -->
- [x] 8.5 「回车提交」Checkbox 默认开；不提供「点第 2 个点提交」 <!-- aidcp-console b6a2b3d -->
- [x] 8.6 `frozen = (points.length > 0 || text.length > 0) && pinned != null`，打字期「画面已更新」Alert 照常生效 <!-- aidcp-console b6a2b3d -->
- [x] 8.7 提交 body += `text?`/`submit?`（空则整字段省略）；提交成功 + adoptLatest 后清空 text；答案绝不进 URL/localStorage <!-- aidcp-console b6a2b3d -->
- [x] 8.8 建 `Record<lastResult['status'], string>` 穷举表（LAST_RESULT_LABEL，含 no_target） <!-- aidcp-console b6a2b3d -->
- [x] 8.9 `typeReport` 渲染成人话 Alert（打错了 / 不可读元素无法证明 / 没点到框 / 客户端过旧未执行）；`edge_lacks_text_capability` 等拒绝码经 REASON_MESSAGE 转人话 <!-- aidcp-console b6a2b3d -->
- [x] 8.10 单测：无落点 ⇒ 输入框 disabled、1 点后可用；打字期新帧 ⇒「画面已更新」Alert；答案不出现在任何 fetch URL；纯点击提交体逐字节一致 <!-- aidcp-console b6a2b3d -->
- [x] 8.11 `npm test`（CaptchaAssistPage 8 例）+ `npm run typecheck` 全绿 <!-- aidcp-console b6a2b3d 全量另有 3 个无关 portal 测试在并行下 flaky，隔离运行全过 -->

> **§8 已 LANDED（console master `b6a2b3d`）+ 部署 dev**（build → 备份 → 纯覆盖 rsync 无 --delete → 验 LIVE bundle 含特征串 + curl 8088=200 → 备份留 10/清孤儿 asset）。<!-- 2026-07-18 deployed dev -->

## 9. aidcp（中控）— 文档

- [x] 9.1 `docs/protocol.md`：`captcha.assist.click` / `click_result` 两段 jsonc + 语义注释（text 敏感性/单点约束/焦点三态/提交只走 enter/能力闸）；头部计数 91 不动、§2 表不加行 <!-- aidcp main（本批控制仓提交） -->
- [x] 9.2 `docs/protocol.md`：修既存漂移——click 样例补 `taskId`；hello 样例删 remoteAddr、加构建能力位 <!-- aidcp main -->
- [x] 9.3 spec delta 的 MODIFIED「云端必须接收并解析验证码上报」已把「均为 44」改为「消息总数断言一致」，archive 时替换主 spec 该 requirement <!-- 已核对：主 spec line 6 requirement 含 44 scenario，delta line 245 MODIFIED 同 header 无 44；archive 后验 -->

## 10. 集成与部署

- [x] 10.1 三仓 `test:acceptance` → `test` → `typecheck` 全过（edge 1712+24 / cloud 2456+56 / console 8+typecheck）；AC-PROTO-* 全绿 <!-- edge 6a48d86 / cloud 04321be / console b6a2b3d -->
- [ ] 10.2 `openspec validate captcha-assist-text-answer --strict`（archive 前跑）
- [x] 10.3 合回各仓默认分支（land-change：fetch+rebase+ff）；活跃 change `captcha-assist-base-url-self-proof`（0/37、无 worktree）未开工 ⇒ 无并发写者，串行满足 <!-- edge 6a48d86 / cloud 04321be / console b6a2b3d -->
- [x] 10.4 部署 dev：cloud（src rsync + restart）+ console（build + 覆盖 rsync）；先探 ECS（无并发部署、isales inactive 未碰）、先备份；healthcheck 全过 <!-- 2026-07-18 deployed dev -->
- [ ] 10.5 dev 冒烟：纯点击流零回归；未换装 edge 提交 text ⇒ 409 <!-- 需真机（edge 客户端 + 活体验证码）→ 登记 §11 真机验收 -->

> **§10 结论**：cloud + console 已部署 dev、健康检查全过。edge 不部署 ECS（客户端，需出包 + 逐台换装）。§10.5 冒烟为真机项，随 edge 出包换装一并验（见 §11）。

## 11. 真机验收登记（新簇，写入 docs/real-machine-acceptance-backlog.md）

> **全部登记入 `docs/real-machine-acceptance-backlog.md` 簇 104**（9 项，与既有验证码协助真机项共享环境）。<!-- aidcp main -->

- [x] 11.1 模糊数字图片类字符识别码 ⇒ `editable`+`match` 全绿、验证码真被解开 <!-- 簇 104.1 -->
- [x] 11.2 焦点被 canvas/iframe 抢走 ⇒ `opaque`+`unverifiable`+focusTag 取证 <!-- 簇 104.2 -->
- [x] 11.3 点空 ⇒ `no_target`，拒绝键入且不提交 <!-- 簇 104.3 -->
- [x] 11.4 打字期挑战换图 ⇒ pin + 「画面已更新」 <!-- 簇 104.4 -->
- [x] 11.5 Enter 提交导航后不被误报 failed（verdict_unavailable_after_submit） <!-- 簇 104.5 -->
- [x] 11.6 未换装新包 ⇒ 409 + 人话文案 + 命令未下发（需 edge 出包换装） <!-- 簇 104.6 -->
- [x] 11.7 飞书卡链接直接键入（未登录控制台）即可解开 <!-- 簇 104.7 -->
- [x] 11.8 焦点假阳性取证 —— focusTag 是否足以事后判别 <!-- 簇 104.2/104.9 -->
- [x] 11.9 确认协助页与飞书卡已无远程桌面入口 <!-- 簇 104.8 -->

## 12. 独立登记（不在本 change 内做）

- [x] 12.1 **cleared 断连不可达**（overlay-report-gate 无论 send 成没成都消费 `reportedKind`，断连时解决掉的验证码永不到云端、账号一直暗着，要改「已投递 vs 已尝试」记账）—— 登记为独立 bugfix change 候选，本 change 只修排序（1.4）不动记账 <!-- 已在 design.md Risks 记明；候选独立 change -->
- [x] 12.2 incident TTL 30min 只在 `onDetected` 刷新、无续期入口 —— 正交既存问题，登记 <!-- 已在 design.md Risks 记明 -->
- [x] 12.3 console 三处手抄 union 不在 `/api/version` 指纹对拍内（cloud 改了 console 零提示）—— 本 change 只补「api.ts 有、页面没加」一个方向（8.8 的 Record 表），另一半仍全静默，登记 <!-- 已在 design.md Risks 记明 -->
- [x] 12.5 **「卡的可见范围 = 操作范围」** —— 协助页在登录门外凭 scoped token 授权、飞书群路由无内外部标记。**既有性质**，本 change 不引入/不扩大/不解决（D9：键入边际暴露面接近零）；归属路由层的内外部标记 <!-- 已在 design.md Risks + 簇 104.7 记明 -->
- [x] 12.4 （条件）classifier 词表零条输入类文案 —— 本次报障形态已能被检出故非准入；若后续发现同类漏检，扩词表 MUST 用**真实文案**（裸词误命中已付过代价）—— 条件项，未触发不做 <!-- 已在 design.md Open Questions 记明 -->
