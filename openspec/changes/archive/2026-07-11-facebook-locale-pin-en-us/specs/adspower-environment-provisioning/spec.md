## MODIFIED Requirements

### Requirement: 程序化创建一个指纹环境（委托生成 + 挑整机模板 + 薄护栏 + OS 四者一致断言）

`adspower` 模式下，桌面外壳 SHALL 经 AdsPower 本地 API `user/create` **程序化创建一个**浏览器指纹环境，指纹的生成 SHALL **最大化委托 AdsPower 按 OS 自动生成自洽整套**（`ua_auto` 匹配内核、`canvas`/`webgl_image`/`audio`/`client_rects` 噪声开启），aidcp 侧 MUST NOT 逐字段手搓整套 `fingerprint_config`。aidcp 侧 SHALL 只承担三件事：① 由运维（或按模板轮换）挑一个「整机模板」，**OS 为第一锁定字段**，`device_memory`/`hardware_concurrency`/`screen_resolution` 等折进模板、MUST NOT 逐字段独立随机；② 一层薄静态护栏——`device_memory` SHALL 只允 2 的幂且封顶 8（**MUST NOT 提交 `6`** 等非 2 的幂）、`hardware_concurrency` SHALL 取真实值、`webgl` 模式 SHALL 不自相取消（`webgl='3'` 时 MUST NOT 同传会被忽略的 `webgl_config`）、`webrtc` SHALL 为替换成代理 IP 的模式、字体 MUST NOT 跨 OS 混装、**时区 SHALL based-on-IP；语言 SHALL 钉死规范 `en-US`**（`language_switch` 关闭 + 显式 `language=['en-US']`，与代理 IP 派生语言解耦，理由：界面语言随 IP 漂反而制造「美国代理号突现越南语 UI」的不自洽，且钉死英文让下游文字识别语言稳定）、「每次启动重随机指纹」SHALL 关闭；③ 提交前 SHALL 做「声明 OS == 下发 UA 的 OS == 字体的 OS == renderer 家族的 OS」四者一致断言，任一不符 SHALL **诚实拒绝创建**、MUST NOT 提交一个自相矛盾的环境。**`language` MUST NOT 进入该四者一致断言集**——钉死 en-US 不因与 OS/IP 不一致而被拒建（语言不是 OS 一致性字段）。aidcp 侧 MUST NOT 为「让检测方看着均衡」而强行匹配「CPU 性能档 == GPU 性能档」（检测方不查此项）。

#### Scenario: 委托生成 + 护栏放行合法自洽环境
- **WHEN** 运维选定一个整机模板（含 OS）点「创建环境」，且模板经护栏与四者一致断言校验通过
- **THEN** 桌面外壳以委托生成为主 + 模板锁定的 OS/整机字段构造 `fingerprint_config`，经 `user/create` 建号成功并返回分身 id

#### Scenario: 非法取值在提交前被护栏拦下
- **WHEN** 待提交的 `fingerprint_config` 含 `device_memory=6`（或其它非 2 的幂 / 超 8 的值）
- **THEN** 护栏在提交前诚实拒绝，MUST NOT 把该值发给 `user/create`

#### Scenario: OS 不自洽在提交前拒建
- **WHEN** 模板声明 Windows 但下发 UA / 字体 / renderer 家族任一不是 Windows（四者一致断言不符）
- **THEN** 桌面外壳诚实拒绝创建并说明不一致点，MUST NOT 提交该矛盾环境

#### Scenario: 语言钉死规范 en-US、时区仍随 IP
- **WHEN** 构造 `fingerprint_config` 时护栏落定语言与时区
- **THEN** `language_switch` 关闭且 `language=['en-US']`（不随代理 IP），而时区仍 based-on-IP；`language` 不参与四者一致断言，pin en-US 不因与 IP/OS 语言不符而被拒建
