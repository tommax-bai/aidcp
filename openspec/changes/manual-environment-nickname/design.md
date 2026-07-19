## Context

环境成员当前只持久化 `{ profileId, name, platform }`。`name` 会在 AdsPower 列表刷新时被实时名回填，平台身份事件还会触发 `user/update` 让 AdsPower 环境名跟随真实昵称；左栏又把真实昵称排在花名册名之前。三条路径都没有表达“这是人工命名、不要覆盖”的事实，且昵称双击已占用为显示浏览器动作。

## Goals / Non-Goals

**Goals:**

- 持久化人工昵称来源，并在左栏显示、列表回填和自动改名三条路径统一尊重。
- 双击左栏昵称进入小型就地编辑，支持 Enter 提交、Escape 取消和失焦提交。
- 保持旧设置兼容，并诚实呈现写盘失败。

**Non-Goals:**

- 不修改平台账号昵称、账号主键或 Cloud 账号主数据。
- 不新增批量改名、清除人工昵称或服务端同步。
- 不改变单击环境行的浏览器选择/显示/归位三态，不构建安装包。

## Decisions

### 1. 在花名册成员上持久化 `nameSource: 'manual'`

继续复用 `name` 保存当前环境显示名，仅为人工提交的成员增加可选 `nameSource: 'manual'`。旧成员缺省视为系统来源。相比新增第二个 `manualName` 字段，这能保持旧版回滚时仍可读到人工名称；归一层只接受精确的 `manual`，避免任意来源值穿透。

### 2. 人工来源贯穿 renderer → settings → handle → fleet snapshot

renderer 的花名册归一/保存保留标记，main/fleet 归一保留标记，`syncEnvHandles` 将其投影到环境 handle 与 fleet snapshot。`railDisplayName` 按人工名 → 平台昵称 → 环境名 → 尾号解析。这样人工优先级是可测试的纯决策，而不是仅靠 CSS 或某次 DOM 修改。

### 3. 两个系统写入点均显式跳过人工成员

`reconcileRosterNames` 遇到 `nameSource === 'manual'` 不从 `user/list` 回填；`maybeRenameEnvToNickname` 遇到同一标记不调用 AdsPower `user/update`。只改显示优先级不足以保护持久数据，也不能阻止外部 AdsPower 名被后台继续改动。

### 4. 双击昵称进入原位输入框

昵称节点截获自己的点击：单击仍以短延迟执行既有环境行激活，第二击会取消该动作并进入编辑，避免一次双击同时把浏览器抬前/归位。提交仅接受去空白后的非空值；成功立即更新内存显示并调用现有 `settings:save`，用栏内消息说明成功或未持久化。人工昵称采用轻微偏紫的文字与小圆点/提示，不覆盖平台头像、状态点、告警和选中态。

## Risks / Trade-offs

- [旧版客户端不认识 `nameSource`] → 旧版仍能读取 `name`，但其自动刷新可能再次覆盖；新版恢复运行后标记仍在，继续保护。
- [失焦误提交] → 只在值非空且与当前人工名不同的情况下写入；Escape 明确取消。
- [设置写盘失败造成重启后丢失] → 当次内存态保留，但栏内明确显示“未持久化、重启可能丢失”，不得报成功。
- [双击与单击手势冲突] → 仅昵称文字使用短延迟仲裁，环境行其余区域维持原三态交互。

## Migration Plan

旧设置无需迁移；缺少 `nameSource` 时按系统来源处理。回滚只需回退 Edge 代码，新增字段会被旧版忽略。运行时行为变更完成验证后按标准流程推送并部署 dev，不构建桌面安装包。

## Open Questions

无。
