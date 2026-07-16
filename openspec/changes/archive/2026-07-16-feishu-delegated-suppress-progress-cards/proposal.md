## Why

委托任务对每条命令都叠加了一层自有的「委托任务 · queued / failed」进度卡,与底层动作**本来就会发**的正常业务结果卡重复——运营发一条 `/comment` 实际收到 3 张卡:排队受理卡 + 委托终态卡 + 评论链结果卡。进度卡是过度设计:结果通知本应由每个任务自己的业务卡承担,委托层不该再叠一层噪音。

## What Changes

- 委托层**不再主动推送**任务进度卡(`queued` / `executing` / `completed` / `waiting_approval`)。
- 结果通知归属明确下沉到底层动作:
  - 评论 → 评论链的正常结果卡(`postResultCard`,已存在);
  - 发帖成功 → 发布人审卡自证(成功不重复报绿);
  - 发帖等待人审 → 发布人审卡本身;
  - **发帖类终态失败** → 委托层补发一张诚实失败 / 部分完成卡(唯一兜底,红线:绝不静默失败);
  - 评论类终态失败 → **不**由委托层补发(评论链已报,避免重复)。
- 精确旧 slash 写命令(`source=legacy_command`)直接排队时**静默受理**——只保留已读表情,不发队列提示卡;结果由任务自身业务卡回报。
- 自然语言委托的结构化确认卡**不变**(仍先确认)。控制命令(查看 / 暂停 / 取消)与卡片按钮点击等**用户主动请求**的回卡不变。

## Capabilities

### Modified Capabilities

- `user-delegated-tasks`: 通知模型从「委托层统一推进度卡」改为「底层业务结果卡承担 + 发帖失败兜底 + 精确命令静默受理」。

## Impact

- `aidcp-cloud`: 新增 `delegatedPublishOutcomeReceipt` 纯函数(可单测);worker `onTaskUpdated` 从推进度卡改为只兜发帖类终态失败;`CommandResult` 增 `silent` + ws-receiver 静默受理;auto-queue 回执改静默。无迁移、无协议改动、不碰热点文件(协议 / 风控 / 角色注册)。
- `aidcp`: 本 change 的 proposal / spec delta / tasks。
- 部署:仅 cloud `dev`;不涉及 Edge 安装包、console、OL。
