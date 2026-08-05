## MODIFIED Requirements

### Requirement: cloud 在 back 成功后必须自驱动续刷

cloud orchestration SHALL 在收到 `action.completed{action:'back', ok:true}` 时主动发起一次 feed 续扫命令，而非仅依赖 edge 主动重报 `page.cards` 才能推进决策环。

该续扫 SHALL 以 `reason=rescan_after_back` 下发，使它在日志与回执里与「返回失败兜底」（`recover_after_back_failed`）可区分。两者 MUST 互斥：同一条返回回执 MUST NOT 同时触发续扫与失败兜底。

以下三种情况 MUST NOT 下发该续扫，且各自有独立的推进路径，MUST NOT 因此停摆：
- 会话已结束——此时任何续扫都是对一个不存在的会话下发命令；
- 浏览处于暂停期（如通知巡视进行中）——巡视有自己的收尾与恢复通道，此处再插一条滚动会污染巡视所在的页面；
- 就地读平台（读列表面且笔记未迁移详情）——那类平台的「离开当前内容」本就用滚动代替返回，不会产生返回回执。

「返回成功之后决策环仍能继续」MUST NOT 依赖任何计时器兜底（空闲 nudge、看门狗）作为常规推进手段：那类兜底的周期是分钟量级，用它顶替续扫会把连续浏览降级成每几分钟一条，且**外部观察不到异常**——每一层回执都成功，只是慢。

#### Scenario: back 完成回执触发续刷
- **WHEN** cloud 收到 `action.completed{action:'back', ok:true}`
- **THEN** cloud 下发一次 `scroll`（`reason=rescan_after_back`），edge 据此重扫并重新上报 `page.cards`，决策环得以继续

#### Scenario: 返回成功不得同时触发失败兜底
- **WHEN** cloud 收到 `action.completed{action:'back', ok:true}`
- **THEN** 只下发一次续扫，MUST NOT 另外下发 `recover_after_back_failed` 兜底滚动

#### Scenario: 浏览暂停期间的返回回执不插入续扫
- **WHEN** 通知巡视正在进行（浏览暂停开关按住）时到达一条返回成功回执
- **THEN** cloud MUST NOT 下发续扫，巡视仍按自己的收尾与恢复通道推进

#### Scenario: 边缘不再随附卡片时闭环仍自持
- **WHEN** 边缘的返回实现只回动作回执、不随附 `page.cards`
- **THEN** 决策环仍由云端的续扫推进，MUST NOT 停摆到只能靠空闲 nudge 或看门狗把它踢醒
