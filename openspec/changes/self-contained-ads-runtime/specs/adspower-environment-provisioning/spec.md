# adspower-environment-provisioning Specification

## ADDED Requirements

### Requirement: LocalAPI 操作前先确保随包运行时就绪，元数据操作不触发内核

`adspower` 模式下，桌面外壳的每一个 LocalAPI 操作——新建环境（`user/create` / `group/create`）、代理编辑、删除环境、巡视对拍、以及状态/分身列表读取——SHALL 在调用前 `await` 随包运行时的**服务确保**（`ensureAdsServiceOnce`），使用其解析出的实际 base，**MUST NOT** 在服务未就绪时裸调 LocalAPI 而把底层 `fetch failed` 直接抛给用户。**元数据类**操作（新建 / 代理 / 删除）**MUST NOT** 触发指纹内核下载（内核只在首次启动浏览器时下载）。状态/分身列表读取 SHALL 走缓存 base 快路径，仅在真的 `fetch failed` 时再确保，**MUST NOT** 每次面板轮询都拉起一次 CLI 子进程。

#### Scenario: 冷机新建环境不再报 fetch failed
- **WHEN** 运营在服务尚未就绪的机器上点「新建环境」
- **THEN** 桌面外壳先确保 CLI 服务就绪（数秒、不下内核）再调用 `group/create`/`user/create`；若确保失败，返回可重试的诚实错误「指纹浏览器运行时未就绪：<原因>」，**绝不**把裸 `本地指纹浏览器服务不可达(group/create): fetch failed` 抛给用户

#### Scenario: 建环境不被 735MB 内核下载拖住
- **WHEN** 在一台从未下过内核的机器上新建环境
- **THEN** 该操作只确保服务、不触发内核下载；内核下载仅发生在随后**首次启动浏览器**时

#### Scenario: 状态读取走缓存 base、不重复起子进程
- **WHEN** 设置面板周期性刷新分身列表 / 状态
- **THEN** 已有 base 时直接读该 base，不为每次轮询重跑 `ads status` 子进程；仅当读取遇 `fetch failed` 才重新确保服务
