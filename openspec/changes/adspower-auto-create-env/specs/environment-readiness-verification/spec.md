## ADDED Requirements

### Requirement: 创建后一次性运行时自检置 verifyState

一个环境创建后，桌面外壳 SHALL 经**开一次该分身 + CDP 实测**来判定其是否「真实且有区分度」，并据此置 `verifyState`。自检 SHALL 至少覆盖：实测出口 IP（与该环境所配代理一致、且与本机同批其它环境互不相同）、`renderer` **非软渲染**（MUST NOT 为 SwiftShader/llvmpipe 等软件渲染器）、WebRTC **不泄露本机真实 IP**（只暴露代理 IP）、时区/语言与出口 IP 地理一致、跨本机同批分身的 Canvas/WebGL/Audio 哈希与 renderer 字符串**互不相同**。全部通过 SHALL 置 `verifyState=ready`；任一不过 SHALL 置 `verifyState=failed` 并诚实标红说明失败项，MUST NOT 静默置为就绪。自检 CDP 取值 SHOULD 遵循既有反检测约束（不常驻 `Runtime.enable`、优先 isolated world）。因客户端一次只处理一个环境，该「创建 → 开一次 → 自检 → 通过才就绪」闭环 SHALL 逐环境执行。

#### Scenario: 自检全过置就绪
- **WHEN** 新建环境开一次分身后，实测出口 IP 与代理一致且与同批互异、renderer 非软渲染、WebRTC 不漏真机 IP、时区↔IP 一致、指纹哈希跨分身互异
- **THEN** 该环境置 `verifyState=ready`

#### Scenario: 软渲染 / 漏 IP 置失败不掩盖
- **WHEN** 自检发现 renderer 为 SwiftShader（软渲染）或 WebRTC 暴露了本机真实 IP
- **THEN** 该环境置 `verifyState=failed` 并诚实标红说明失败项，MUST NOT 置为就绪

#### Scenario: 同机指纹撞车判失败
- **WHEN** 新环境实测 Canvas/WebGL/Audio 哈希或 renderer 字符串与本机同批已存在环境相同
- **THEN** 判失败并提示改模板/重建，MUST NOT 放行两个同机撞哈希的环境

### Requirement: verifyState 是投产的代码级硬前置，不是咨询字段

`verifyState=ready` SHALL 是环境进入启动/投产路径的**代码级硬前置**：起号出口（`pluggable-browser-provider` 起浏览器前 / `launch-multinode` 组装槽位时）SHALL 读取该环境的 `verifyState`，未达 `ready` SHALL **诚实拒绝启动**并说明原因，复用既有「失败诚实停手、绝不回落 self」同款闸。`verifyState` MUST NOT 仅作展示用的咨询字段而被启动路径绕过。

#### Scenario: 未验证环境被启动出口拒绝
- **WHEN** 某环境 `verifyState` 为 `failed` 或 `unverified`，运维仍试图用它起号
- **THEN** 启动出口读到非 `ready` 即诚实拒绝启动、说明原因，MUST NOT 放行

### Requirement: 跨机器消费的环境视为未验证并强制重验

「本机已验证」SHALL 只对**建号机**成立。环境的 `verifyState=ready` SHALL 绑定其建号机标识（`machineLabel`）。当一个环境在**非建号机**上被消费（如导出 `AIDCP_ADS_USER_IDS` 拷到别机、或经 AdsPower 云同步拉到别处），启动路径 SHALL 据握手/上报的机器标识发现「建号机 != 当前机」，将其视为**未验证**并诚实拒绝投产 / 强制重验，MUST NOT 沿用旧机的就绪判定（换机后真实 renderer/软渲染/时区↔IP 可能已变）。

#### Scenario: 换机执行触发重验
- **WHEN** 一个在机 A 上 `verifyState=ready` 的环境被拷到机 B 上起号
- **THEN** 启动路径发现建号机 != 当前机，将其视为未验证、诚实拒绝或强制在机 B 重验，MUST NOT 直接沿用机 A 的就绪判定
