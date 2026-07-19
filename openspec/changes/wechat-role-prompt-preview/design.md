## Context

`ROLE_CATALOG` 现在包含三类会调用文本/视觉模型的角色：事件驱动浏览角色、独立/interaction 角色、发布管线角色。管理后台统一调用 `GET /api/roles/:roleId/prompt`，但 `createRolePromptProvider()` 仍只完整处理浏览角色实例和发布预览注册表：interaction 角色被误走发布映射；独立的 Facebook 加群判定不在预览 dispatcher；后来新增的 `CoverCardWriter` 和三个 vision 角色也未进入预览注册表。

现有只读接口和 console 展示已经足够，缺口在 cloud 的 prompt 同源构建与预览路由。修复必须保留“只展示真实运行 prompt、不可用时诚实降级、预览不触发模型调用”的红线。

## Goals / Non-Goals

**Goals:**

- 视频号收件箱三个 interaction 角色均返回 `available:true` 的真实 prompt。
- 补齐本次调用链—目录—预览交叉审计发现的其它现役模型角色预览：Facebook 加群判定、此前漏入目录的 Facebook 定向评论撰写、封面文字卡文案、封面形态感知、整组视觉反推、视觉保真审核。
- 运行时与预览复用同一纯 prompt 构建函数，避免手抄与漂移。
- 建立目录级回归守卫，阻止将来新增非 browse 模型角色时再次只进目录、不进预览。

**Non-Goals:**

- 不开放 prompt 编辑或写接口。
- 不改变角色目录、模型解析、prompt 内容、调用门禁或推理行为。
- 不把纯规则角色或未登记的合成角色伪造成可预览角色。
- 不要求视觉预览加载真实图片；只展示真实发送给视觉模型的文本指令，并明确图片为示例占位。

## Decisions

1. **先抽取同源纯构建函数，再接预览。** interaction、Facebook 加群/定向评论与视觉角色当前有私有/内联 prompt 构建逻辑；将其导出为纯函数，运行时调用改为使用该函数，预览注册也调用同一函数。相比在预览层复制字符串，这能让测试以函数同一性约束防止漂移。

2. **按角色组显式路由预览。** `createRolePromptProvider()` 将 interaction、独立 browse、publish text、vision 与 image 分开处理；不再让“非 browse”默认等同“publish text”。interaction 不使用账号人设，因此选择账号时保留 prompt，但不冒充人设来源；Facebook 定向评论虽是独立角色，运行时会读取账号身份，预览仍按真实/示例 persona 口径渲染。

3. **多阶段视觉角色展示真实文本指令合集。** 单阶段视觉角色展示其实际 user text；整组视觉反推同时展示真实的粗分析指令和一个带示例下标的真实专家阶段指令，并用查看器说明标注这是多阶段视觉调用。图片 URL 不进入后台预览，避免网络读取和泄露真实业务图片。

4. **完整性测试以角色目录为边界。** 测试遍历所有非 browse 的现役模型角色并要求预览可用且非空；对不在 dispatcher 的 Facebook 加群角色单独断言同源预览。浏览侧按运行时开关未注册的角色仍允许诚实返回不可用，不用假实例掩盖真实注册状态。

5. **不消费 persona 的预览显式返回 `personaSource:none`。** console 将其显示为“不使用人设”，账号选择提示也限定为“消费人设的角色”，避免把缺省字段误解释成示例人设；接口字段已是向后兼容的可选枚举，不改路由形状。

## Risks / Trade-offs

- [视觉角色一次运行可能有多条 prompt] → 预览明确分段并复用每个阶段的真实构建函数，不声称拼接文本会作为一条请求发送。
- [抽取函数可能意外改动线上 prompt] → 仅移动/导出既有字符串和参数组装，增加运行时调用与预览输出的同源测试，并跑相关角色测试与全量测试。
- [选择账号时 interaction/vision 被错误标成人设 prompt] → 这两类预览不消费 persona，返回 `personaSource:none` 且不附账号/fallback，console 按可选枚举明确展示“不使用人设”。
- [未来目录新增角色再次漏映射] → 非 browse 目录级完整性测试随目录扩展自动失败，要求新增角色同时补预览来源或明确调整契约。
