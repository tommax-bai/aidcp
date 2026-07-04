## ADDED Requirements

### Requirement: 云端提供可复用的 OSS 对象上传出口

系统 SHALL 在云端提供一个可复用的对象存储上传能力:接受一段字节 + 目标对象键 + 内容类型,上传到配置的阿里云 OSS 桶,返回该对象的稳定公网 URL。此能力 SHALL 定义为可注入接口(`ObjectStore`),使调用方与具体实现解耦、并可在不连真实 OSS 的情况下注入内存假实现做单元测试;OSS 实现内部的网络请求出口 SHALL 可注入(如 `fetchImpl`),对齐现有 provider 客户端的测试接缝范式。该能力 MUST NOT 绑死于「配图」单一用途,SHALL 可供后续任意图片/文件上传场景复用。

#### Scenario: 上传字节返回稳定公网 URL

- **WHEN** 调用方以字节 + 对象键 + 内容类型调用上传出口,且 OSS 凭据就绪
- **THEN** 字节 SHALL 被 PUT 到配置桶的该键,并返回可匿名访问的稳定公网 URL(形如 `https://<bucket>.oss-cn-beijing.aliyuncs.com/<key>`)

#### Scenario: 脱离真实 OSS 可单测

- **WHEN** 在本地/CI 环境注入内存假 store 与假网络出口运行测试
- **THEN** 上传逻辑 SHALL 可被完整验证,MUST NOT 依赖真实 OSS 网络连接

### Requirement: 生成配图转存到 OSS 并以稳定链接持久化

发帖配图在图片生成成功之后、写入 `publish_log` 之前,系统 SHALL 把每张图片生成厂商返回的临时 URL 的字节抓取并转存到 OSS(公读),并将随后持久化到 `publish_log.image_url` / `images` 的 URL 替换为 OSS 的稳定公网 URL。转存对下游 SHALL 透明:选封面、内容组装、落库、以及派发给边缘的 `upload_image` 指令 MUST 仍只承载 URL 字符串,边缘收到的仍是一个可 fetch 的 URL,**边缘侧不做任何改动**。既有的存量行(provider 临时 URL)不在本要求的强制回迁范围内。

#### Scenario: 配图落 OSS 稳定链接

- **WHEN** 一次发帖生成了 N 张配图且 OSS 上传能力就绪
- **THEN** `publish_log` 持久化的封面与正文图 URL SHALL 是 OSS 稳定公网 URL 而非会过期的 provider 临时 URL,且发布延迟(如等待人工审批)超过 provider 原始 TTL 后,边缘仍能从 OSS URL 成功下载

#### Scenario: 边缘下发契约不变

- **WHEN** 派发配图上传指令给边缘
- **THEN** 指令 SHALL 仍为携带一个可 fetch URL 的 `upload_image{imageUrl}`,该 URL 指向 OSS 对象,边缘无需感知来源变化

### Requirement: OSS 转存失败必须诚实降级不伪造

当某张配图的 OSS 转存(抓字节或 PUT)失败时,系统 SHALL 令该张诚实落空——沿用现有「失败那张不进图片数组、真实附着张数如实反映」的语义,MUST NOT 伪造 OSS URL、MUST NOT 以占位/假链接充数、MUST NOT 把「未真正转存」当成功。当 OSS 上传能力整体未配置/未注入时,系统 SHALL 保持与集成前完全一致的行为(直接使用 provider URL),不产生回归。

#### Scenario: 单张转存失败

- **WHEN** 某张配图抓字节或 PUT OSS 失败
- **THEN** 该张 SHALL 不进入最终图片数组,`publish_log` 记录的真实附着张数 SHALL 相应减一,系统 MUST NOT 写入任何伪造/占位 URL

#### Scenario: 未配置 OSS 能力时零回归

- **WHEN** 运行环境未提供 OSS 凭据或未注入上传能力
- **THEN** 配图路径 SHALL 与集成前一致地使用 provider URL,发布链路 MUST NOT 因缺 OSS 而中断或报错

### Requirement: OSS 凭据从加密库读取回退环境变量且绝不外发

系统 SHALL 在启动期加载 OSS 的 AccessKeyId / AccessKeySecret,优先从加密凭据库读取(`provider='oss'` 的对应字段),读不到时回退环境变量,复用现有密钥加载范式;凭据库表 SHALL 沿用通用 `(provider, field)` 结构、MUST NOT 因新增 OSS 而改动 schema。region / bucket 等非敏感配置 MAY 走环境变量。凭据明文 SHALL 仅在启动期用于构造客户端,MUST NOT 出现在日志、MUST NOT 回传前端、MUST NOT 以明文进入代码仓 / commit / 文档。

#### Scenario: 库内优先、env 回退

- **WHEN** 启动期加载 OSS 凭据
- **THEN** 系统 SHALL 先查加密库该字段、查不到再读环境变量,二者皆无时 OSS 上传能力视为未配置(触发上一要求的「零回归」路径)

#### Scenario: 凭据不外发

- **WHEN** 打印日志、返回前端响应、或提交代码/文档
- **THEN** OSS AccessKeyId/Secret 明文 MUST NOT 出现在其中;引用时只记读取方式与存放位置,不记值
