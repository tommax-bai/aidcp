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

昵称节点截获自己的点击：单击仍以短延迟执行既有环境行激活，第二击会取消该动作并进入编辑，避免一次双击同时把浏览器抬前/归位。提交仅接受去空白后的非空值；renderer 在第一次 `await` 前更新当前页面并标记“正在保存”，随后调用昵称专用的 `fleet:setManualNickname` IPC。主进程保存前保留旧 settings，仅在写盘成功后同步 handle/fleet；写盘失败则恢复旧内存 settings 并返回原因。renderer 收到失败后恢复原昵称、原来源和所有当前环境身份锚点。人工昵称采用轻微偏紫的文字与小圆点/提示，不覆盖平台头像、状态点、告警和选中态。

这里的“热更新”仅指昵称数据在已加载功能的当前页面即时变化；Electron 源码版本仍不具备运行时热加载能力。人工昵称是 Edge 本地环境花名册字段，本 change 不新增或伪造 Cloud 昵称接口。

### 5. 全客户端复用返回 `{ name, source }` 的环境显示名解析器

后续复现发现，`railDisplayName` 只覆盖左栏；标题栏、互动/内容工作区、引导、人设入口及主进程下发的浏览器内人设横幅仍各自直接读取 `status.account.name` 或 `env.name`，导致同一环境在不同位置显示不同名字。把纯逻辑下沉到进程无关的 `environment-display-name.cjs`，导出 `resolveEnvironmentDisplayName(row)` 并统一返回 `{ name, source }`，来源限定为 `manual` / `platform` / `environment` / `fallback`。renderer 通过普通 script 使用，main/persona notice 通过 CommonJS 同步使用；`uiLogic.resolveEnvironmentDisplayName` 与 `railDisplayName` 仅保留为兼容消费入口。

共享文件必须拥有真实、明确的 CommonJS 扩展名。项目根目录声明了 `"type": "module"`，因此 `.js` 即使写成 UMD 或包含 `module.exports`，Electron 31 内置的 Node 20 仍会把它分类为 ESM，`persona-notice.cjs` 的同步 `require()` 会在应用初始化阶段抛出 `ERR_REQUIRE_ESM`。不改根目录模块类型，也不把同步启动链改为动态导入；测试除 `tsx` 单元测试外，还使用项目锁定的 Electron 可执行文件和 `ELECTRON_RUN_AS_NODE=1` 启动一个无 loader 子进程，直接加载主进程依赖，防止 loader 掩盖模块边界回归。

保留来源而不只返回字符串，是为了让标题栏仍能只给真实平台昵称加 `@`，人工环境昵称不得冒充平台身份；当来源仅为尾号兜底但账号 ID 已知时，标题栏仍保留“账号 …尾4位”的原有语义。评论/私信参与者、内容作者等第三方真实昵称不属于环境锚点，继续读取其业务 DTO，避免人工环境别名污染外部身份。

## Risks / Trade-offs

- [旧版客户端不认识 `nameSource`] → 旧版仍能读取 `name`，但其自动刷新可能再次覆盖；新版恢复运行后标记仍在，继续保护。
- [失焦误提交] → 只在值非空且与当前人工名不同的情况下写入；Escape 明确取消。
- [乐观名称被误当成已保存] → pending 态与人工已确认态视觉/提示分开；失败恢复原昵称与来源并展示主进程返回的真实原因。
- [双击与单击手势冲突] → 仅昵称文字使用短延迟仲裁，环境行其余区域维持原三态交互。
- [抽象过宽会把环境别名写成平台身份] → 解析器只服务客户端环境锚点并返回来源；协议、路由、作者/参与者 DTO 和 Cloud 账号字段保持不变。
- [运行中的 Electron 不热加载新 renderer] → 验证和交付明确记录进程启动时间与代码提交时间；源码合入后必须重启客户端才能观察新行为，不把旧进程测试当成新代码失败。
- [`tsx` loader 掩盖 Electron 模块边界] → 除现有测试外，使用 Electron 31 内置 Node 20 在无 loader 子进程中同步加载 `persona-notice.cjs`；任何 `ERR_REQUIRE_ESM` 或非零退出都使验证失败。

## Migration Plan

旧设置无需迁移；缺少 `nameSource` 时按系统来源处理。回滚只需回退 Edge 代码，新增字段会被旧版忽略。运行时行为变更完成验证后按标准流程推送并部署 dev，不构建桌面安装包。

## Open Questions

无。
