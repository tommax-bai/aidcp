## MODIFIED Requirements

### Requirement: Facebook scheduled contact comment joins a new group before commenting

排期的 Facebook 联系评论 SHALL NOT 先加群。它 MUST NOT 携带「先加群」标记，MUST 走既有的正常定向评论路径，其评论容器 MUST 由**已加入群账本的选群口**给出。

这条约束的理由是机制性的，MUST 随要求一起保留：选群口是预热期与单群冷却唯一生效的地方。一旦评论容器被外部钉死（例如钉死成刚加入的那个群），选群口根本不会被调用，两道闸就结构性失效——**不是被绕过一次，而是永远不参与判定**。

加群 SHALL 只由独立的自动加群动作驱动（见「Standalone Facebook automatic join remains join-only」）。系统 MUST NOT 保留任何「开启联系评论即隐式加群」的路径：那条路径不查每账号加群开关、不查加群日上限、也不查加群动作时段，等于让一个动作的开关去驱动另一个动作。

选定容器之后，目标选择 SHALL 继续遵循既有的 Facebook 关键词规则：配了关键词走群内搜索，没配则取该群第一条可评帖。既有的联系方式闸、尝试型日上限、评论风控闸、审批、去重、服务端校验、账号单飞与诚实结果回执 SHALL 全部保持不变。

以下三条路径 SHALL 继续使用「先加群再评论」的复合动作，本要求 MUST NOT 被读作把它们一并拆掉：飞书手动命令、委托任务、以及固定规则模式的轮次（后者另由 `facebook-rule-mode` 规定）。

非 Facebook 的排期联系评论 SHALL 保持其既有的不加群行为。

#### Scenario: 排期联系评论从账本选群，不加新群
- **WHEN** 某 Facebook 账号命中已开启的排期联系评论槽位且各前置闸通过
- **THEN** 系统不加任何新群，改从该账号已加入群账本中选出一个满足预热期与冷却的群，在其中选帖、撰写、审批并提交联系评论

#### Scenario: 账本里没有合规群时诚实空转
- **WHEN** 该账号已加入的群全部不满足预热期或仍在冷却中
- **THEN** 本次不评论、不加群，并如实回报无可用目标，MUST NOT 为了有事可做而去加一个新群

#### Scenario: 刚加入的群不会在同一轮被评论
- **WHEN** 独立自动加群动作刚刚为某账号确认加入了一个新群
- **THEN** 该群在满足预热期之前不会被排期联系评论选中

#### Scenario: 手动与规则模式仍先加群
- **WHEN** 运营发出带加群参数的手动评论命令，或固定规则模式命中其加群轮次
- **THEN** 系统仍执行「先加群、确认加入后在该群评论」的复合动作

#### Scenario: Non-Facebook contact comments do not acquire join semantics
- **WHEN** a non-Facebook account hits its existing scheduled contact-comment slot
- **THEN** the system uses the existing contact-comment path without `joinFirst`

### Requirement: Facebook scheduled contact comment is labeled 加群评论（联系）

旧名「加群评论（联系）」MUST NOT 继续用于该动作：拆分后它不再加群，旧名会让运营以为开启它就会加群，进而在真正的自动加群开关关着时把「不加群」误判成系统故障。

Facebook 侧的控制台动作名与排期执行 / 结果通知 SHALL 改用与其它平台**一致**的联系评论名，MUST NOT 再为 Facebook 保留一个特例名。具体字面量由各呈现面各自的既有通用名决定（排期执行与结果通知为「联系评论」，控制台排期表沿用其既有通用列名），本要求约束的是「不再有 Facebook 特例」，而不是统一到某一个字符串。内部动作键、接口字段与持久化结构 SHALL 保持 `contact_comment` 兼容。

固定规则模式面板中描述其轮次的文案 SHALL NOT 被本要求波及——规则模式仍然先加群，那里的措辞依然准确。

清空全部 Facebook 搜索关键词 MUST 被接受，不报错、也不给禁用态警告。控制台 MUST NOT 增加「当前使用群内首帖」一类的显式当前模式标签。

#### Scenario: Facebook 自动化页不再出现加群特例名
- **WHEN** 运营把自动化页筛选到 Facebook
- **THEN** 该动作的列名与控件用与其它平台一致的联系评论名，页面上不再出现「加群评论（联系）」

#### Scenario: 规则模式文案不受影响
- **WHEN** 运营查看某账号的固定规则模式面板
- **THEN** 其中关于加群轮次的说明保持原样，仍如实描述「先加群再评论」

#### Scenario: Empty keywords show no first-post mode status
- **WHEN** an operator clears and saves all Facebook comment search keywords
- **THEN** the save is accepted and the configuration dialog shows no “当前使用群内首帖” status or empty-keyword error
