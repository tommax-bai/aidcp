# Cloud 服务适度拆分方案

> 状态：方案草案
>
> 日期：2026-07-21
>
> 适用仓库：`aidcp-cloud`、`aidcp-edge`、`aidcp-console`、控制仓 `aidcp`
>
> 目标阶段：增加 TikTok、抖音及视频/音频解析与简化生成能力之前

## 1. 一页结论

当前阶段不建议继续维持单进程 Cloud，也不建议立即拆成多个业务微服务或多个 Git 仓库。

建议把 `aidcp-cloud` 调整为**同一仓库内的三个独立运行单元**：

1. **Data API**：客户、环境、人设、配置、内容、草稿、审批、发布记录和客户端 HTTP 数据面。
2. **Automation**：Edge WebSocket、自动化调度、平台执行编排、任务状态机和风控。
3. **Media Worker**：视频/音频探测、解析、转写、简化生成、转码和产物校验。

三者初期继续：

- 使用同一个 `aidcp-cloud` Git 仓库；
- 部署在同一 Cloud 环境；
- 使用同一个 PostgreSQL 集群，但采用独立 Schema、账号和迁移边界；
- 使用 PostgreSQL Outbox/Inbox 完成可靠异步交接；
- 使用对象存储承载视频、音频和派生文件。

平台扩展采用统一能力合同和平台适配器，不为小红书、Facebook、微信视频号、TikTok、抖音分别建立 Cloud 服务。

## 2. 背景与当前问题

### 2.1 已经确定的客户端边界

当前架构已经明确：

- Electron 应用是客户端；
- Edge 子进程是按需运行的自动化引擎；
- 浏览器/CDP 是页面自动化执行器；
- 客户自有数据通过 customer-auth HTTP 逐请求读写；
- 自动化任务通过 Edge 与 Cloud 之间的 WebSocket 调度；
- 自动化事件可以触发客户端重新 HTTP 拉取，但不能覆盖 Cloud 已确认的数据；
- 普通数据管理不得依赖自动化引擎、WebSocket、浏览器或浏览器槽位。

详细合同见 [架构说明](architecture.md) 和 [边云协议](protocol.md)。

### 2.2 Cloud 当前仍是单一运行单元

虽然 Cloud 已经存在不同网络入口，但目前仍由同一个 `src/server.ts` 组合和启动：

- Edge 自动化 WebSocket；
- 管理后台 HTTP；
- 客户端 customer-auth HTTP；
- 进程内调度器、连接注册表、EventBus、RiskController；
- 内容、发布、客户、配置、风险等领域 Store。

因此当前只有传输和鉴权层面的初步隔离，没有形成独立的故障、重启、扩容和验收边界。

客户 HTTP 与管理后台还会直接读取自动化进程内对象，例如在线连接、调度开关、运行中任务和 RiskController 状态。单进程内开发方便，但会带来以下问题：

- 数据接口和自动化运行时形成隐性耦合；
- 自动化模块调整时难以独立判断对客户数据面的影响；
- 重启和多实例部署后，进程内状态的权威性不明确；
- 无法独立验收“自动化停止但数据管理仍可用”；
- 后续拆分会一次性暴露大量内部调用和共享状态。

### 2.3 后续能力会放大运行模型差异

计划增加：

- TikTok 平台支持；
- 抖音平台支持；
- 视频和音频解析；
- 音频抽取、语音识别、字幕与内容理解；
- 简化的脚本、封面、字幕、音频或模板视频生成。

媒体任务通常持续数秒至数十分钟，并产生明显的 CPU、内存、磁盘和网络负载。把这些任务放进 Automation 进程，可能影响 Edge 心跳、WebSocket 稳定性和任务调度，因此需要独立资源边界。

## 3. 设计目标与非目标

### 3.1 目标

- 客户数据面不依赖自动化和媒体任务在线；
- 自动化调度不受媒体高负载影响；
- 已批准任务和执行结果跨服务重启不丢失；
- 明确每类状态的唯一写入者；
- 支持 TikTok、抖音以显式能力声明接入；
- 保留当前单仓协作效率，控制部署和联调成本；
- 为将来按负载或团队进一步拆分保留稳定边界。

### 3.2 非目标

当前阶段不做：

- 按平台建立独立 Cloud 服务；
- 把 Edge Gateway、调度器、RiskController 分别部署；
- 把人设、发布、身份、查询、通知拆成独立微服务；
- 拆分 `aidcp-cloud` 为多个 Git 仓库；
- 引入 Kafka、服务网格或分布式事务；
- 建设完整 GPU 调度平台；
- 把平台持久凭据迁移到 Cloud；
- 让媒体处理完成后绕过审批自动发布。

## 4. 目标架构

```text
┌──────────────────┐       customer-auth HTTP       ┌──────────────────┐
│ Electron 客户端   │ ─────────────────────────────▶ │ Data API         │
└──────────────────┘                                └────────┬─────────┘
                                                               │
                         AutomationRequested / MediaJobRequested
                                                               │
                         ┌─────────────────────────────────────┼──────────┐
                         ▼                                     ▼          │
                ┌──────────────────┐                  ┌──────────────────┐│
                │ Automation       │                  │ Media Worker     ││
                │ 调度 + 风控 + WS │                  │ 解析 + 简化生成   ││
                └────────┬─────────┘                  └────────┬─────────┘│
                         │                                     │          │
             automation WebSocket                        对象存储         │
                         │                                     │          │
                         ▼                                     ▼          │
                ┌──────────────────┐                  ┌──────────────────┐│
                │ Edge 自动化引擎   │                  │ 原始/派生媒体资产 ││
                │ 平台适配器 + 浏览器│                  └──────────────────┘│
                └──────────────────┘                                     │
                         │                                                │
                         └──── ExecutionResult / MediaAssetReady ─────────┘
```

## 5. 服务职责

### 5.1 Data API

Data API 是客户业务数据的唯一入口，负责：

- 客户鉴权和客户状态；
- 客户与环境归属；
- `envKey` 与平台账号的权威绑定；
- 人设、写作语言和运营配置；
- 内容素材、草稿和审批；
- 发布计划、业务状态和发布记录；
- 媒体资产元数据；
- 媒体任务的创建和查询；
- 客户端首页概览和其他查询投影；
- 管理后台中的持久数据接口；
- customer-auth HTTP。

Data API 不负责：

- 持有 Edge WebSocket；
- 直接启动或控制浏览器；
- 执行平台 API 或页面操作；
- 运行 FFmpeg、ASR 或媒体生成任务；
- 直接读取 Automation 的连接注册表或运行时对象。

管理后台需要读取实时自动化状态或下达启停操作时，Data API 可以调用 Automation 的窄内部接口。该接口失败只影响自动化状态卡，不得把客户业务数据标记为离线。

### 5.2 Automation

Automation 是自动化控制面，当前阶段包含：

- Edge WebSocket Gateway；
- 握手、心跳、能力协商和连接路由；
- 自动化任务状态机；
- 调度、租约、超时、重试、取消和幂等；
- 平台 API 自动化；
- 浏览器和页面自动化编排；
- RiskController；
- 配额、慢启动和节奏控制；
- 自动化运行时 EventBus；
- 执行回执和真实结果接收。

Automation 不负责：

- 修改客户、人设、草稿和审批业务表；
- 把普通数据命令推送给客户端；
- 保存媒体二进制文件；
- 承担视频和音频解析或生成计算。

Edge Gateway、任务调度和 RiskController 暂时保持在同一运行单元，因为三者运行时交互频繁。等连接规模或团队边界真正独立后，再评估继续拆分。

### 5.3 Media Worker

Media Worker 是无客户会话、无公开业务 API 的后台任务进程，负责：

- 媒体格式、时长、尺寸和编码探测；
- 视频抽帧；
- 音频抽取；
- 语音识别和字幕解析；
- 内容分段、摘要和结构化理解；
- 简化脚本生成；
- 简化封面、字幕、音频或模板视频生成；
- 转码、压缩和输出校验；
- 处理过程、尝试次数和失败原因记录。

媒体文件必须保存到对象存储。数据库、业务事件和 Automation WebSocket 中只能传输资源标识和元数据，不得传输视频或音频二进制。

Media Worker 必须具备：

- 幂等任务键；
- 有界重试；
- 超时和取消；
- 进程重启恢复；
- 输入、输出内容哈希；
- 独立 CPU、内存和并发限制；
- 处理结果校验。

## 6. 数据和状态所有权

| 状态 | 唯一写入者 | 存储位置 | 其他服务如何使用 |
| --- | --- | --- | --- |
| 客户与环境归属 | Data API | `business` | HTTP 或授权投影 |
| 人设和配置 | Data API | `business` | 任务创建时生成版本化快照 |
| 草稿和审批 | Data API | `business` | 通过持久事件触发自动化 |
| 发布业务记录 | Data API | `business` | 消费执行结果后更新 |
| 自动化任务与尝试 | Automation | `automation` | Data API 读取状态投影 |
| Edge 在线连接 | Automation | 进程内/实时路由存储 | 窄内部状态接口 |
| 页面租约和在途执行 | Automation | `automation` + 进程内 | 不允许 Data API 直接读取 |
| 最终风险状态 | RiskController | `automation` | Data API 读取持久投影 |
| 媒体资产业务元数据 | Data API | `business` | HTTP 返回给客户端 |
| 媒体处理尝试 | Media Worker | `media_runtime` | Data API 消费结果投影 |
| 原始视频和音频文件 | Data API（登记，客户端按授权直传） | 对象存储输入区 | 通过 `assetId` 和短期签名地址访问 |
| 解析和生成的派生文件 | Media Worker | 对象存储输出区 | Data API 消费结果后纳入资产视图 |

每张业务表只能有一个服务写入。共享 PostgreSQL 集群不等于共享数据所有权。

## 7. 服务交互合同

### 7.1 普通客户数据

客户数据继续使用逐请求 HTTP：

```text
Electron renderer
  → 窄 IPC
  → Electron main customer-auth HTTP adapter
  → Data API
```

请求不检查 Automation、Edge WebSocket、浏览器、CDP 或槽位状态。

### 7.2 发布任务

```text
客户端批准稿件
  → Data API 在同一事务保存审批和 Outbox
  → Automation 消费 AutomationRequested
  → RiskController 判断是否允许执行
  → Edge Gateway 下发任务
  → Edge 平台适配器执行并验证
  → Automation 保存真实任务终态
  → 发出 ExecutionResult
  → Data API 更新发布记录和首页投影
```

Automation 不在线时，审批仍可成功保存并进入等待。Automation 恢复后只能执行一次。

### 7.3 媒体任务

```text
客户端上传或引用素材
  → Data API 保存素材元数据并写入 MediaJobRequested
  → Media Worker 领取任务
  → 从对象存储读取原始文件
  → 解析、转写或简化生成
  → 派生文件写回对象存储
  → 发出 MediaAssetReady / MediaJobFailed
  → Data API 更新媒体资产状态
```

媒体任务成功只表示产物已准备好，不表示已经批准或发布。

### 7.4 实时通知

当前阶段可以继续采用客户端主动刷新或在既有用户级通道上发送失效提示。通知只能表达“数据发生变化，请重新 HTTP 拉取”，不能携带普通业务写命令，也不能复用环境自动化 WebSocket。

## 8. TikTok 与抖音平台设计

### 8.1 独立平台身份

TikTok 与抖音必须是两个独立平台标识：

```text
xiaohongshu
facebook
wechat_channels
tiktok
douyin
```

两者可以复用底层工具和抽象，但不能共享账号语义、能力声明、页面假设、风控参数或成功验证规则。

### 8.2 平台能力注册表

平台注册表必须显式声明：

- 支持的内容类型；
- 图文、视频发布能力；
- 即时或预约发布能力；
- 浏览、点赞、评论、回复、关注等动作；
- API 执行还是页面执行；
- 是否需要浏览器槽位；
- 需要的 Edge 能力版本；
- 平台节奏和风控参数；
- 不支持能力的明确原因。

新增平台时，未知能力和缺少声明必须 fail-closed，返回 `capability_unsupported` 或更具体的原因。不得回落成小红书，不得因为注册表缺项而按支持处理。

### 8.3 平台适配器

建议保持一个平台无关的任务外壳，并允许版本化的平台专有载荷：

```text
platforms/
  xiaohongshu/
  facebook/
  wechat-channels/
  tiktok/
  douyin/
```

Cloud 负责平台能力、策略和任务编排；Edge 负责真实平台 API、浏览器、DOM/CDP 操作和结果验证。

只有页面自动化可以申请浏览器槽位。媒体处理和普通客户数据不得占用浏览器槽位。

## 9. 仓库和部署组织

### 9.1 仓库

当前阶段保留一个 `aidcp-cloud` 仓库：

```text
src/
  apps/
    data-api/
      main.ts
    automation/
      main.ts
    media-worker/
      main.ts

  domains/
    identity/
    environment/
    persona/
    content/
    publishing/
    automation/
    risk/
    media/

  platforms/
    xiaohongshu/
    facebook/
    wechat-channels/
    tiktok/
    douyin/

  contracts/
    automation-request/
    automation-result/
    media-job/
    media-result/

  infrastructure/
    postgres/
    outbox/
    object-storage/
```

`contracts` 只包含版本化协议和 DTO，不得成为共享业务实现的后门。

### 9.2 部署单元

建议部署为：

```text
aidcp-cloud-data.service
aidcp-cloud-automation.service
aidcp-cloud-media-worker.service
```

每个服务独立拥有：

- 启动入口；
- 配置校验；
- 健康检查；
- 日志标识；
- systemd 生命周期；
- 资源限制；
- 回滚和就绪验证。

客户 HTTP 的独立 JWT 密钥和路由边界必须保留。即使管理后台 HTTP 和 customer-auth HTTP 同属 Data API，也可以继续使用不同监听端口、密钥和路由表。

### 9.3 数据库

初期继续使用同一个 PostgreSQL 实例，至少划分：

```text
business
automation
media_runtime
```

每个运行单元使用独立数据库账号。允许通过明确授权读取必要投影，禁止跨 Schema 任意写业务表。

可靠交接初期采用 PostgreSQL Outbox/Inbox。只有当事件量、跨机器部署或消费者数量证明 PostgreSQL 已成为瓶颈时，再引入专门消息中间件。

## 10. 故障与降级语义

| 故障 | 应保持可用 | 允许受影响 |
| --- | --- | --- |
| Automation 停止 | 人设、配置、草稿、审批、历史、媒体管理 | 新自动化任务等待、实时在线状态不可用 |
| Data API 停止 | 已领取的自动化和媒体任务安全收敛，结果持久等待 | 新客户数据请求和新任务创建 |
| Media Worker 停止 | 客户数据、已有自动化、发布记录 | 新媒体任务等待处理 |
| Edge 离线 | 客户数据和媒体处理 | 对应环境自动化任务等待或明确失败 |
| 浏览器槽位满 | 客户数据、API 自动化、媒体处理 | 页面自动化排队 |
| 对象存储不可用 | 非媒体客户数据、无需媒体的自动化 | 媒体读取、生成和发布等待/失败 |
| PostgreSQL 不可用 | 已在 Edge 安全边界内的动作按合同收敛 | 三个 Cloud 单元进入不可写或不可就绪状态 |

任何降级都不得把请求已接收、任务已派发或进程仍在运行冒充业务成功。

## 11. 分阶段实施

### 阶段 1：建立代码和状态边界

- 盘点 `src/server.ts` 的组合根；
- 盘点所有进程内状态及其读取方；
- 标记每张表和每类状态的唯一写入者；
- 把跨领域直接调用收口到显式接口；
- 增加模块导入边界检查；
- 将必须跨重启保留的事件迁出进程内 EventBus。

此阶段可以仍运行一个进程，但代码边界必须先成立。

### 阶段 2：拆分 Data API 与 Automation

- 增加两个启动入口；
- 分离 HTTP 数据面与 Edge WebSocket；
- 增加独立 systemd 服务和健康检查；
- 使用 Outbox/Inbox 交接任务与结果；
- 管理后台实时状态改走窄内部接口或投影；
- 验证独立启动、停止、重启和回滚。

### 阶段 3：增加 Media Worker

- 建立对象存储资产模型；
- 建立媒体任务和处理尝试模型；
- 首批支持探测、音频抽取、转写和摘要；
- 再增加简化生成、转码和结果校验；
- 配置独立资源限制和并发控制。

### 阶段 4：扩展 TikTok 和抖音

- 扩展 `PlatformId` 和能力注册表；
- 先消除新增平台路径上的未知能力 fail-open；
- 定义 Cloud 和 Edge 的能力协商版本；
- 每次只接入一个平台和一组可真实验收的能力；
- 未完成能力保持 `capability_unsupported`；
- 完成真实账号、真实目标和真实结果的端到端验收后再扩大范围。

## 12. 验收红线

拆分完成至少满足：

1. Automation 停止或重启时，客户数据 HTTP 仍可用。
2. Media Worker 高负载不影响 Edge WebSocket 心跳和自动化调度。
3. Automation 停止时批准稿件，恢复后任务只执行一次。
4. Data API 暂时不可用时，Automation 和 Media Worker 的结果不会丢失。
5. 三个运行单元可以独立启动、健康检查、重启和回滚。
6. Data API 不直接引用连接注册表、调度器或 RiskController 对象。
7. Automation 不直接修改客户、人设、草稿和审批业务表。
8. 最终风险状态仍由 RiskController 单写。
9. 未知平台和未声明能力 fail-closed，不回落到其他平台。
10. TikTok 与抖音任务不能串账号、串环境或串平台适配器。
11. 视频和音频二进制不进入 PostgreSQL、业务事件或 Automation WebSocket。
12. 媒体处理成功不等于发布成功，发布仍经过审批、自动化执行和平台结果验证。
13. 浏览器关闭、槽位满和 Edge 离线不影响普通客户数据和媒体任务。
14. 自动化事件只能使客户端缓存失效并触发 HTTP 重拉，不能覆盖 Cloud 权威数据。

## 13. 后续进一步拆分的触发条件

只有出现明确证据时才继续拆分：

- Edge WebSocket 连接规模需要独立扩容：考虑拆 Edge Gateway；
- GPU 或转码任务成为主要负载：考虑拆媒体分析与媒体生成 Worker 池；
- 某个平台形成独立团队和发布节奏：考虑独立平台包或仓库，不默认独立服务；
- Data API 查询投影成为独立瓶颈：考虑独立 Query/Projection 服务；
- PostgreSQL Outbox 无法满足吞吐、延迟或跨机器可靠性：考虑专门消息中间件；
- 两个服务长期由独立团队维护、绝大多数变更不再跨边界：再评估拆 Git 仓库。

在这些条件出现前，继续保持三个运行单元和一个 Cloud 仓库。

## 14. 待确认事项

进入 OpenSpec proposal 前需要最终确认：

1. `TK` 是否统一指国际版 TikTok，并与中国区抖音完全分开建模；
2. 首期媒体输入来源：客户上传、平台采集、对象存储引用，还是三者都支持；
3. “简化生成”的首期范围：摘要/脚本、封面/字幕、音频、模板视频分别做到哪一层；
4. 对象存储沿用现有 OSS 还是建立新的媒体 Bucket 和生命周期规则；
5. 首期 TikTok、抖音需要真实交付的动作集合与验收账号；
6. Media Worker 初期与 Cloud 同机部署，还是从第一版开始使用独立计算节点。

## 15. 建议决策

建议批准以下方向作为后续 OpenSpec 的输入：

> `aidcp-cloud` 保持单仓，拆分 Data API、Automation、Media Worker 三个运行单元；客户数据走 HTTP，自动化走 Edge WebSocket，媒体处理走异步任务与对象存储；TikTok、抖音通过显式平台能力和 Edge 适配器接入，不按平台拆 Cloud 服务。
