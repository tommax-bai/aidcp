## 1. aidcp-cloud — 采集触发从会话开始解耦为登录引导
<!-- aidcp-cloud 0db3335 已实现 + 部署 + 验证 -->

- [x] 1.1 `nickname_enricher` 移出会话角色集,改 `setup()` 永久 `subscribe`;新增 `armLoginCapture()`,与 `session_start` 共用 `arm()`
- [x] 1.2 `self.profile.capture → profile_open{direct}` 命令出口从会话期翻译移到 `setup()` 永久订阅
- [x] 1.3 dispatcher hello 入口:`canStartSession` 通过 → `restartSession`;被人设闸拦下且 `isDispatchActive` → `armLoginCapture()`;调度全局停则不驱动
- [x] 1.4 守红线:浏览反应链(contentEvaluator 等)仍只在会话激活订阅;未绑人设账号采完即闲置不浏览

## 2. aidcp-cloud — 测试

- [x] 2.1 enricher:`armLoginCapture`(无 `session_start`)→ 同款采集流程(武装 → 边缘就绪 emit → 落库回 feed);pending=false / default 零扰动
- [x] 2.2 dispatcher 红线:未绑人设 + 需采 → 恰一次 `profile_open{direct}`、零浏览命令;调度关 → 不驱动
- [x] 2.3 typecheck clean;受影响套件全绿(25/25,含既有 account-real-nickname enricher 用例 + persona-gated-start)

## 3. 真机回归(gated)

- [ ] 3.1 重连一个未绑人设(或已绑但未采)的已登录账号,确认登录后云端驱动一次 `profile_open` → 采到真名落库 → 后台显示真名,且全程不浏览(无 open_note/like)
- [ ] 3.2 确认采空(未登录)诚实留空 + 有界退避;绑了人设的账号行为不变(会话照常 + 采集随会话开始)

## 4. 部署与收尾

- [x] 4.1 已上线 ECS(cloud `0db3335`,与 `auto-start-on-persona-bind` 同提交 co-ship)并 healthcheck 绿(active / :8787 / 飞书长连接 / 各 store ready / 无错)
- [ ] 4.2 真机回归(task 3)后 `openspec validate nickname-capture-on-login --strict` → 归档(archived ≠ 已验证,见 archived-unverified 纪律)

> 现状:代码 + 测试 + 部署已完成且线上 healthcheck 绿;仅剩 **task 3 真机回归**(重连一个未绑人设/已绑未采的已登录账号,确认登录即采到真名、全程不浏览)。
