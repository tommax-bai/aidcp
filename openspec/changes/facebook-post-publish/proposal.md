## Why

Facebook 账号当前已具备登录、浏览、评论、加群等能力，但没有发帖能力；现有发布链路仍以小红书图文发布页和小红书内容结构为中心，不能安全复用到 Facebook。

本 change 建立 Facebook 发帖的最小可验证闭环：账号配置中批量上传发帖图片，发布时从该账号图片素材池锁定对应图片，生成待审草稿，经既有审批/派发/边缘租约机制下发到 Facebook，并以服务端确认作为成功依据。

## What Changes

- 新增 Facebook 发帖能力，首版支持个人主页发帖：正文 + 账号图片素材池图片；不支持群组发帖、Page 发帖、视频、@人、位置、Facebook 平台内定时发布。
- 新增每账号 Facebook 发帖图片素材池：后台可批量上传图片，云端转存 OSS，按账号持久化图片组、顺序、状态、素材说明和使用记录。
- Facebook 发布生产段不调用图片模型；图片由账号素材池提供，素材不足时 fail-closed，不硬凑、不改走小红书生图。
- 发布草稿生成时从素材池锁定下一组图片并写入 `publish_log.images`；拒绝/提交前失败释放，已提交但确认不明时隔离，确认成功后标记已用。
- 平台化发布 profile 和命令序列：Facebook 不下发小红书专用的 title/topic/cover/visibility 等步骤；缺能力时诚实失败，绝不回落到小红书发布器。
- Edge 新增 Facebook 发帖执行器，覆盖宽屏/窄屏 composer 打开、聚焦、输入、上传、提交、服务端确认；提交后不确定状态进入人工核查，不自动重试。
- 内容排期和手动发布复用既有生成、待审草稿、授权信号、发布派发器、同账号 edge lease 和风险闸；MVP 默认只接 `review` 模式，不开启免审自动发送。
- 控制台在 Facebook 账号配置中增加发帖素材管理入口，支持批量上传、缩略图、排序、素材说明、停用/删除和状态展示。

## Capabilities

### New Capabilities
- `facebook-post-publish`: Facebook 发帖闭环、账号图片素材池、素材锁定/消费、Facebook Edge 发帖执行器与确认语义。

### Modified Capabilities
- `platform-runtime-abstraction`: Facebook driver/cloud registry 只有在发帖执行器和云端 profile 同落后才声明 `publish`；未实现能力必须继续诚实失败。
- `publish-pipeline`: 发布生产和下发按平台 profile 路由；Facebook 使用账号素材池图片，不继承小红书标题、话题、封面、生图和图片必需规则。
- `content-schedule`: 排期发帖对 Facebook 账号复用现有 review 待审路径，但触发前必须通过 Facebook 发布素材池可用性和平台 publish 能力检查。
- `cloud-oss-storage`: OSS 对象上传出口新增后台人工上传图片消费者；仍只返回稳定公网 URL，凭据不外发，上传失败诚实落空。

## Impact

- **aidcp-cloud**
  - 新增 Facebook 发帖素材池 store、DDL 和 panel deps，读写 `account_facebook_publish_image_set` / `account_facebook_publish_image`。
  - 新增后台上传接口，读取图片字节、校验大小/类型、转存 OSS、写入素材池；缺 OSS 或上传失败时返回诚实错误，不写假 URL。
  - 新增平台化 publish profile/selector，使 Facebook 发布跳过小红书生图/标题/话题/封面规则，从素材池锁定图片写入草稿。
  - 扩展 `PublishDispatcher` / `CommandSequencer` 按账号平台选择发布序列；Facebook 不支持的步骤不得下发。
  - 发布结果回写素材状态：成功标记 used，拒绝/提交前失败释放，提交后确认不明 quarantine。

- **aidcp-edge**
  - 新增 `FacebookPostExecutor` 或等价 publish capability handler，挂到 Facebook driver 的 `publish` 能力后才接收发帖命令。
  - 实装 Facebook composer 宽/窄布局定位、输入、图片上传、提交、确认；不复用 XHS `PublishCommandDispatcher`。
  - 提交前失败与提交后不确定状态分开上报，避免自动重试造成重复发帖。

- **aidcp-console**
  - 扩展现有 Facebook 账号配置入口，增加“发帖素材”tab 或独立弹窗。
  - 支持批量图片上传、缩略图列表、排序、素材说明、停用/删除、状态筛选和素材不足提示。

- **OpenSpec / docs**
  - 新增 `facebook-post-publish` spec。
  - 补充 `platform-runtime-abstraction`、`publish-pipeline`、`content-schedule`、`cloud-oss-storage` delta，明确平台能力、素材池来源、排期闸和 OSS 人工上传消费者。

- **Deployment / validation**
  - 默认只部署 dev；不做 edge 桌面安装包构建，除非后续明确要求 release/package。
  - 真提交探针只允许在操作员自有 disposable Facebook 目标上运行，必须显式 env gate，并以 reload/server confirmation 判成功。
