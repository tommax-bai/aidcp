## ADDED Requirements

### Requirement: 人工上传的 Facebook 发帖图片经 OSS 稳定化

系统 SHALL 复用云端 `ObjectStore` 上传出口处理控制台人工上传的 Facebook 发帖图片。上传 API MUST 接收图片字节、校验类型/大小、生成账号隔离的对象 key，上传到 OSS 后只把稳定公网 URL 持久化到 Facebook 发帖素材池。OSS 凭据仍按既有加密库优先、环境变量回退方式加载，MUST NOT 回传前端或写入日志。上传失败 MUST 对该文件诚实落空，不得用 provider URL、临时本地文件、base64 data URL 或占位 URL 代替。

#### Scenario: 人工上传图片返回稳定 URL
- **WHEN** 控制台上传一张合法 Facebook 发帖图片且 OSS 可用
- **THEN** cloud SHALL 通过 `ObjectStore.put` 上传图片字节，返回并持久化 OSS 稳定公网 URL

#### Scenario: 对象 key 按账号隔离
- **WHEN** 不同 Facebook 账号上传同名图片文件
- **THEN** OSS object key SHALL 包含账号隔离前缀或等价隔离信息，避免跨账号覆盖

#### Scenario: 凭据不外发
- **WHEN** 上传接口返回给前端、打印日志、或写 OpenSpec/tasks
- **THEN** OSS AccessKeyId/Secret 明文 MUST NOT 出现；只允许返回图片素材元数据与稳定公网 URL

#### Scenario: 上传失败不存占位
- **WHEN** OSS 上传失败或图片类型/大小非法
- **THEN** 该图片 SHALL 不进入素材池，响应 SHALL 带失败原因，MUST NOT 持久化临时路径、base64 data URL、占位 URL 或假 OSS URL
