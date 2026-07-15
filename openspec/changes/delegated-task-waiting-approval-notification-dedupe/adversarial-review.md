# Adversarial Review

## Review result

结论：2 个 BLOCKER、3 个 HIGH 均已在 design/spec 中收敛，没有实施阻塞。

## Findings

1. **BLOCKER — 只从队列移除 `waiting_approval` 会漏掉 console 审批和重启后恢复。**
   - 处理：保留周期对账和数据库 lease；仅把“仍未审批”的结果改为静默心跳。
2. **BLOCKER — 只在飞书层限流会继续制造版本漂移和过期按钮。**
   - 处理：waiting claim/release 保持业务状态与版本不变，通知指纹仅作为第二道防线。
3. **HIGH — 静默 release 可能覆盖并发取消或终态。**
   - 处理：release 必须同时匹配 task id、claim token 和 `waiting_approval`；匹配失败回读当前真态，不做回退写。
4. **HIGH — 多 worker 可能同时对账同一候选。**
   - 处理：保留 `FOR UPDATE SKIP LOCKED`、claim token 和 lease；不把静默等同于无 claim。
5. **HIGH — 语义指纹可能吞掉批准、驳回或真实进度。**
   - 处理：指纹覆盖 status、currentStep、四类计数、terminalOutcome、pause/cancel；测试 waiting→terminal 和控制变化。

## Explicit non-claims

- dev 观察可以证明重复心跳停止，但不会执行真实批准或平台发帖来制造成功结果。
- 未构建 Edge 安装包，未部署 OL。
