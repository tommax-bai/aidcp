## Context

Facebook 环境单建和批量建已经共用主进程 `parseFacebookAccountImport`：渲染层只透传一次性文本，主进程先解析完整批次，再生成 AdsPower 创建计划。现有解析器只认识 `email----password----2FA----cookie`。新导出格式为 `uid|password|cookie|access_token|email|timestamp`，其中 Cookie 值可能自身包含 `|`，Access Token 又属于客户端建环境不需要的高敏凭据。

## Goals / Non-Goals

**Goals:**

- 在同一共用解析器内兼容两种格式，使单建与批量自动获得一致能力。
- 保持整批预校验、错误脱敏和仅内存处理边界。
- 正确处理 Cookie 内嵌竖线，并防止 UID 与 Cookie 登录身份明显错配。
- 确保 Access Token 与采集时间不进入 AdsPower 请求或后续创建对象。

**Non-Goals:**

- 不校验 Access Token 有效性、权限或期限，不调用 Facebook API。
- 不把 Access Token 当作 2FA key，也不保存 UID、Token 或采集时间。
- 不改变既有四字段格式、代理轮询、模板随机、串行创建或部分成功语义。

## Decisions

### 1. 在主进程共用解析器按行识别格式

每个非空行独立识别旧 `----` 格式或新 `|` 格式，允许一批输入中包含两种格式。识别以最先出现的候选分隔符为准：旧格式的 Cookie 即使含 `|`，其首个 `----` 仍位于 Cookie 之前；新格式的首个 `|` 位于 UID 后，即使 Cookie 内出现 `----` 也不会误判。

不在渲染层复制解析逻辑。渲染层仍只负责空输入快检和一次性 IPC 透传，主进程保持权威校验，单建与批量不会出现两套规则漂移。

### 2. 新格式从两端取固定字段，Cookie 占据中间可变区

新格式从左侧取 UID、密码，从右侧取 Access Token、邮箱、时间戳，中间全部片段重新以 `|` 拼回 Cookie。这样 Cookie 值含竖线时不会发生字段错位。密码、邮箱或时间戳自身包含未转义 `|` 不属于该导出格式能力范围。

### 3. 只构造 AdsPower 需要的最小账号对象

六字段格式输出的账号对象只含邮箱映射的 `username`、密码、规范化 Cookie 和既有 Facebook 域名/起始页配置；不设置 `fakey`，因为 Access Token 不是 2FA key。UID、Access Token 与时间戳在解析完成后不进入返回对象，从结构上阻止写客户端下发或后续日志误用。

当 Cookie 可读取 `c_user` 时与首字段 UID 精确比较，不一致按安全行号拒绝；无法从既有受支持的结构化 Cookie 读取时不臆造失败。该校验防止人工拼接或导出错行把一个账号邮箱与另一个登录会话绑定。

## Risks / Trade-offs

- [导出字段没有转义规则] → 采用两端定位覆盖最现实的 Cookie 内嵌 `|`；明确不承诺密码、邮箱、时间戳内嵌分隔符。
- [Token 被输入但不被利用] → UI 说明与契约明确其仅被识别后丢弃，避免误当 2FA 或扩大凭据面。
- [结构化 Cookie 无法可靠读出 UID] → 仅在可读取时做一致性校验，继续沿用既有结构化 Cookie 兼容边界。

## Migration Plan

1. 先补解析器单元测试，覆盖旧格式回归、新格式、Cookie 内嵌竖线、UID 不一致和敏感字段丢弃。
2. 实现共用解析器与 UI 格式说明，运行聚焦 Electron 测试、完整测试与 typecheck。
3. 集成 Edge 默认分支；不打包安装器，不执行真实账号创建。

回滚只需回退 Edge 源码提交；无持久化数据或配置迁移。

## Open Questions

无。
