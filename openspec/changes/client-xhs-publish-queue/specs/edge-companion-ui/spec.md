## ADDED Requirements

### Requirement: XHS publish home surface SHALL summarize the current environment queue

Electron 陪伴界面 SHALL 在明确的小红书环境中把原单记录发布区域呈现为“发布进度”摘要。摘要 SHALL 优先展示等待客户确认的内容，并提供进入完整发布队列的入口；仅有系统处理中内容时 SHALL 保持紧凑，无活跃内容时 SHALL 展示最近真实发布或“暂无进行中”。既有稿件审核入口、发布/取消和版本安全语义 MUST 保持不变。

#### Scenario: 待确认稿件自动突出

- **WHEN** 当前环境队列含至少一条 waiting approval 内容
- **THEN** 首页摘要自动展开最需要处理的一条，显示“确认前不会发布”并提供现有稿件审核入口

#### Scenario: 只有系统处理中的内容

- **WHEN** 当前环境只有 queued、generating 或 submitted 内容且无需客户操作
- **THEN** 首页显示紧凑数量摘要和“查看全部”，不为每条内容占据运行首页空间

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
