# Tasks

> 两个 bug 共用同一个触发器（冷待机唤醒），故同批实装。实装在前、记录在后（线上 bug，用户被阻塞）。

## 1. aidcp-edge — 关浏览器前排空浏览循环（BUG A）

- [x] 1.1 `BrowseSession.closeAndWait(timeoutMs)`：终态关闭 + 有界排空（复用既有 `operationIdleWaiters` 原语，不另造） <!-- aidcp-edge 0e383b3 -->
- [x] 1.2 `EdgeBrowseSession` 接口补 `closeAndWait`；`FacebookBrowseSession` 按命令链实现同语义 <!-- aidcp-edge 0e383b3 -->
- [x] 1.3 `enterStandby()` 与 `deactivate()`（退出/回收）改为先 `closeAndWait` 再关浏览器；排空超时诚实告警后照常关 <!-- aidcp-edge 0e383b3 -->
- [x] 1.4 启动段（`start()` 前置块 + `loop()` 首屏扫描）每个 await 后复核停止请求；扫描延迟改可打断 sleep <!-- aidcp-edge 0e383b3 -->
- [x] 1.5 首屏扫描纳入 `CdpDisconnectedError` 处理域（`runInitialScan`）：停止期间断连=干净退出，非预期断连=有界重连 <!-- aidcp-edge 0e383b3 -->
- [x] 1.6 `waitForVisibleCards` / `waitForCards` 不再吞断连（立刻上抛）；轮询体每圈复核停止请求 <!-- aidcp-edge 0e383b3 -->
- [x] 1.7 在途巡视命令被待机撕断时仍发诚实 `ok:false` 回执（防云端 excursionActive 永真 → 看门狗杀会话） <!-- aidcp-edge 0e383b3 -->
- [x] 1.8 `cdp.control_unavailable` 补冷待机守卫（与 `cdp.unrecoverable` 同口径，防待机期核心自杀） <!-- aidcp-edge 0e383b3 -->
- [x] 1.9 回归用例 3 条；已验证在修复前的代码上失败（空转 12001ms，与线上 13s 缺口逐帧吻合） <!-- aidcp-edge 0e383b3 -->

## 2. aidcp-cloud — 人设绑定态三态（BUG B，状态单写方先发）

- [x] 2.1 `ui-snapshot`：`personaBound` 改为 true/false 都下发；「全空不发包」判据同步 <!-- aidcp-cloud 707ea76 -->
- [x] 2.2 绑定态从重快照里摘出来先发（零 I/O 的 bit 不排在 5 个 PG/fs 往返之后） <!-- aidcp-cloud 707ea76 -->
- [x] 2.3 `pushPersonaBound()` + `personaFacade.onChanged` 钩子：绑定/解绑即时重推，不必等下次握手 <!-- aidcp-cloud 707ea76 -->
- [x] 2.4 `protocol.ts` 契约注释改为三态语义（不新增 MessageType，AC-PROTO-02 的 74 不动） <!-- aidcp-cloud 707ea76 -->
- [x] 2.5 单测 4 条（先发 / false 也发 / 绑解绑重推 / 无在线边缘如实放弃） <!-- aidcp-cloud 707ea76 -->

## 3. aidcp-edge — 人设弹窗只信权威（BUG B）

- [x] 3.1 `protocol.ts` 契约注释与 cloud 逐字一致 <!-- aidcp-edge 9761448 -->
- [x] 3.2 `ui-event-lines`：true/false 都转成行给外壳（原本只转 true，权威「未绑」被吞） <!-- aidcp-edge 9761448 -->
- [x] 3.3 外壳三态化：默认值与换会话重置从 `false` 改为 `null`（未知），入口双向采纳 boolean <!-- aidcp-edge 9761448 -->
- [x] 3.4 `persona-notice`：`!== true` → `=== false`（浏览器内横幅同守三态） <!-- aidcp-edge 9761448 -->
- [x] 3.5 渲染层：弹窗只由权威 `false` 触发；徽标未知=「待启动」绝不谎称「未设置」 <!-- aidcp-edge 9761448 -->
- [x] 3.6 删除整套宽限期机制（`PERSONA_PROMPT_GRACE_MS` / `personaUnboundSince` / 到点复评定时器 / 死代码清理点） <!-- aidcp-edge 9761448 -->
- [x] 3.7 纵深防御：系统自动弹出的窗在权威「已绑」到达时自动收起（手动打开的不动；折自 210f386） <!-- aidcp-edge 9761448 -->
- [x] 3.8 用例：未知永不弹 / 重启后回落未知不误弹 / 权威未绑才弹 / 误弹自动收起；旧宽限用例改写为三态契约 <!-- aidcp-edge 9761448 -->

## 4. 验证与部署

- [x] 4.1 edge：`npm test` 1170 pass、`test:acceptance` 19 pass、`typecheck` 干净 <!-- aidcp-edge 9761448 -->
- [x] 4.2 cloud：`npm test` 1925 pass、`test:acceptance` 50 pass（AC-PROTO/AC-PUB/AC-RISK 全绿）、`typecheck` 干净 <!-- aidcp-cloud 707ea76 -->
- [x] 4.3 两份 `protocol.ts` 逐字一致（diff 验证） <!-- aidcp-edge 9761448 -->
- [x] 4.4 部署 dev：备份 → `git archive HEAD` 干净快照 rsync → restart → 健康检查（active / 8787+8090 在听 / 人设存储就绪 / 飞书长连接已建立） <!-- 2026-07-14 deployed -->
- [ ] 4.5 真机验收（见 `docs/real-machine-acceptance-backlog.md`）：① 冷待机一轮：不再出现「浏览会话异常」+ 循环在关浏览器前已退出；② 工程师大白重启客户端：不再弹人设向导；③ 真未设置人设的账号仍照常弹一次

## 5. 遗留（不在本 change 范围，需另行处理）

- [ ] 5.1 `release/20260712-ol-recut` 上仍有 3 个 fix 未 forward-port 回 master：`36fe38f`（建号环境归属客户）、`1300f5b`（FB 联系评论确认）、`5ee9d2d`（客户端「更新人设」按钮）。下次从 master 切 OL 发布分支会**丢掉**它们。
