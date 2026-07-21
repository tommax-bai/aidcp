## ADDED Requirements

### Requirement: XHS publish home surface SHALL summarize the current environment queue

Electron 陪伴界面 SHALL 在明确的小红书环境中把原单记录发布区域呈现为“发布进度”摘要。摘要 SHALL 优先展示等待客户确认的内容，并提供进入完整发布队列的入口；仅有系统处理中内容时 SHALL 保持紧凑，无活跃内容时 SHALL 展示最近真实发布或“暂无进行中”。既有稿件审核入口、发布/取消和版本安全语义 MUST 保持不变。

#### Scenario: 待确认稿件自动突出

- **WHEN** 当前环境队列含至少一条 waiting approval 内容
- **THEN** 首页摘要自动展开最需要处理的一条，显示“确认前不会发布”并提供现有稿件审核入口

#### Scenario: 只有系统处理中的内容

- **WHEN** 当前环境只有 queued、generating 或 submitted 内容且无需客户操作
- **THEN** 首页显示紧凑数量摘要和“查看全部”，不为每条内容占据运行首页空间

### Requirement: Expanded publish summary SHALL support restrained item switching

Electron 展开态发布摘要 SHALL 在当前环境可展示项超过一条时，提供位于卡片最左和最右的上一条、下一条按钮，并显示当前位置与总数。按钮 SHALL 默认使用弱化颜色，在 hover 与 `focus-visible` 时轻度加深；按钮 SHALL 是原生键盘可达控件并以目标内容标题提供可访问名称。单条、加载、错误与收起态 MUST 隐藏并禁用切换控件。

切换序列 SHALL 先展示待确认 active，再展示其它 active 与尚未开跑 tasks；无进行中内容时 MAY 在 recent 内切换。左右边界 SHALL 循环。HTTP 刷新后若当前稳定身份仍存在 SHALL 保持当前项，消失时 SHALL 回到新的首项；切换环境或平台 MUST 清除选择。切换 MUST NOT 发送写请求、改变任务顺序、跨环境复用索引，或把展示位置描述成精确队列名次。

#### Scenario: 鼠标或键盘切换到下一稿件

- **WHEN** 客户点击右侧按钮，或在该原生按钮上按 Enter / Space
- **THEN** 卡片更新为下一条内容，位置提示与按钮可访问名称同步更新，完整队列和 Cloud 状态保持不变

#### Scenario: 当前稿件在刷新后仍存在

- **WHEN** 客户正在查看第二条内容且 HTTP 刷新仍返回同一稳定身份，即使列表位置改变
- **THEN** 卡片继续展示该内容，不因刷新跳回首项；若该身份消失才回到新的首项

#### Scenario: 切换环境或只剩一条内容

- **WHEN** 客户切换账号、平台，或刷新后当前环境只剩一条可展示内容
- **THEN** 客户端清除旧选择，隐藏且禁用左右按钮，不保留可聚焦的不可见控件

### Requirement: Publish queue SHALL reuse the in-app content workspace safely

Electron SHALL 在现有主窗口内容工作区页面栈内展示发布队列，不创建新的系统窗口。关闭 SHALL 返回运行首页；打开稿件审核后返回 SHALL 回到队列。环境切换 SHALL 清除取消确认、忙态和旧内容；旧环境迟到回包 MUST NOT 重新打开或覆盖新环境页面。

#### Scenario: 从队列进入稿件审核再返回

- **WHEN** 客户从等待确认的队列项打开稿件审核并完成查看后返回
- **THEN** 客户回到同一环境发布队列且不丢失当前分区

#### Scenario: 取消确认中切换环境

- **WHEN** 客户正在确认取消环境 A 的任务时切换到环境 B
- **THEN** 确认态立即关闭，任何 A 的在途回包不得修改 B 的队列或显示成功提示

### Requirement: Renderer SHALL use narrow publish queue IPC only

Renderer SHALL 只通过 preload 暴露的发布队列读取与取消方法操作当前本地 `envId`。Electron main SHALL 解析真实 envKey、持有客户令牌并构造固定路径；renderer MUST NOT 直接访问 customer-auth HTTP、传入任意 URL/鉴权头/`accountId`，或在取消时省略 task version。

#### Scenario: Renderer 发起取消

- **WHEN** 客户确认取消当前队列中的任务
- **THEN** renderer 只向 preload 提交当前 envId、任务 id 与整数 version，main 将其绑定到该环境的固定客户取消路径

### Requirement: Publish progress rail SHALL read as one connected, non-interactive sequence

发布队列的四阶段步骤条 SHALL 在宽屏将节点和文案按同一四列对齐，并只在相邻圆点外缘之间绘制连接线。第一节点之前与最后节点之后 MUST NOT 出现线段，连接线 MUST NOT 穿过圆点或阶段文案。窄屏 SHALL 改为等价的纵向连接，保持阶段顺序与状态文字可读。步骤项只表达状态，MUST NOT 使用 hover、手型光标或点击反馈暗示可操作性。

#### Scenario: 已确认稿件等待发布

- **WHEN** 前三阶段完成而发布结果尚未开始
- **THEN** 第三个圆点与第四个圆点之间显示已推进连接，第四个圆点保持待处理样式，轨道首尾无悬空短线且文字不遮挡线段

#### Scenario: 窄屏查看四阶段

- **WHEN** 客户在窄屏窗口查看同一任务
- **THEN** 四阶段按从上到下排列，连接线只连接相邻圆点，完整标签与状态文字换行可读且页面无横向溢出
