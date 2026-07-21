## Why

小红书详情已经上报 `publishedAtText`，但 Cloud 只把它临时压成热度计算用的近似小时数，精选池既不保留原文也不保存可复用的标准时间；客户端还用精选记录更新时间代替来源发布时间展示，容易误导。需要建立一套诚实、可复用的来源发布时间标准化模型，并把结果贯通到精选持久化与展示。

## What Changes

- 在 Cloud 增加平台来源发布时间标准化能力，以观测时刻和平台时区为锚，输出原始文本、可选标准时间、精度和解析状态；无法识别时保留原文但不伪造时间。
- 让热度帖龄计算复用统一标准化结果，不再维护独立的文案解析分支，并保持不可解析内容 fail closed。
- 精选准入和机器人收藏补建路径保存来源发布时间原文、标准时间、精度和观测锚；重复观测只用本次确有的发布时间证据更新，缺失不得擦除既有证据。
- 精选后台与客户 HTTP 投影返回来源发布时间字段；Console 与桌面灵感库显示来源发布时间，未知时明确显示未知，不再以 `updatedAt` 冒充原稿发布时间。
- 历史精选行保持字段为空，不根据首次发现或更新时间回填来源发布时间。

## Capabilities

### New Capabilities

- `source-published-time-normalization`: 平台发布时间原始文案到可复用标准时间、精度和解析状态的统一转换契约。

### Modified Capabilities

- `feed-hot-lead-group-comment`: 热度帖龄判断改为消费统一标准化结果，并以事件观测时刻作为解析锚。
- `curated-inspiration-corpus`: 精选源帖保存来源发布时间证据，刷新和历史行遵守诚实缺失语义。
- `panel-curated-content`: 精选管理接口和页面返回、展示来源发布时间而非记录更新时间。
- `client-customer-auth`: 客户灵感库最小披露投影增加来源发布时间字段。
- `edge-companion-ui`: 桌面灵感库列表和详情展示来源发布时间，未知时不以更新时间替代。

## Impact

- `aidcp-cloud`: 新增时间标准化模块与测试；调整热度判断、精选准入、精选存储 schema/查询映射、客户认证 API 和面板 API 投影。
- `aidcp-edge`: 不改变上行协议；调整客户灵感库渲染和测试，仅消费 Cloud 返回的标准化字段。
- `aidcp-console`: 扩展精选类型、列表/详情展示和测试。
- PostgreSQL `curated_content`: 幂等新增 nullable 来源发布时间字段；无破坏性回填。
- 控制仓：新增能力规范并修改相关既有能力契约；`docs/protocol.md` 仅补充 Cloud 派生语义，不增加消息类型或上行字段。
