## MODIFIED Requirements

### Requirement: 环境名跟随真实账号昵称——建号不写死模板名、登录后渐进改名

桌面外壳 SHALL 使未人工命名的 AdsPower 环境名向该环境登录账号的**真实平台昵称**看齐，作为运维辨识环境的显示名；人工昵称是运营明确指定的最高优先级显示名，存在人工来源标记时 MUST NOT 再由平台身份事件自动改名。具体：

① **建号不写死模板名**：创建环境时 SHALL NOT 把整机模板标识（如 `win11-intel`）写作环境名——`user/create` MUST NOT 下发一个等于设备模板 key 的 `name`，交由 AdsPower 默认命名或留空（登录前空窗期的显示名由左栏兜底，见 `edge-fleet-console`）。

② **登录后改名跟随昵称，但保护人工昵称**：当核心读出未人工命名环境的真实登录昵称（`account-identity-resolution` 定义的显示名，昵称仅作显示、非账号主键）后，若 AdsPower 环境名与该昵称不一致，桌面外壳 SHALL 经写客户端的改名封装把该环境名改为昵称；存在人工来源标记时 SHALL 跳过此写入。

③ **幂等去抖**：AdsPower 环境名已与昵称一致或人工保护生效时 MUST NOT 发起 `user/update` 改名。

④ **限速合规**：自动改名 SHALL 复用写客户端 ≥1s 串行节流，MUST NOT 与核心的本地 API 调用同秒并发撞每秒限速。

⑤ **诚实降级**：自动改名失败（不可达 / `code≠0` / 撞限速）SHALL 诚实降级——保持原名、后续再有机会重试，MUST NOT 假成功、MUST NOT 阻塞或中断该环境的浏览闭环。

⑥ **存量渐进、不即时批量、不依赖云端**：未人工命名的既有环境 SHALL 靠同一「登录读昵称 → 按需改名」路径**随正常运营渐进**改到位；本 change MUST NOT 引入即时一次性批量改名，MUST NOT 引入云端侧 profile→昵称导出依赖（改名所需昵称由该环境自身的身份读取本地提供）。

#### Scenario: 建号不写死模板名
- **WHEN** 运维经客户端创建一个新指纹环境
- **THEN** `user/create` 的 body 不含等于设备模板 key 的 `name`（不下发 name 或用 AdsPower 默认命名），左栏该环境登录前的显示名不呈现设备模板名

#### Scenario: 登录后改名跟随昵称
- **WHEN** 未人工命名的环境读出真实登录昵称，且当前 AdsPower 环境名不同
- **THEN** 桌面外壳经改名封装把该环境改名为昵称，下次 `user/list` 读回该环境名即为昵称

#### Scenario: 人工命名后不再自动改名
- **WHEN** 某环境存在人工昵称，之后核心上报不同的平台真实昵称
- **THEN** 桌面外壳不发起 `user/update` 改名，人工昵称与人工来源保持不变

#### Scenario: 名字已一致不重复写
- **WHEN** 未人工命名环境的 AdsPower 名已等于真实昵称且再次上报同一昵称
- **THEN** 桌面外壳 MUST NOT 再发起 `user/update` 改名

#### Scenario: 改名失败诚实降级
- **WHEN** 自动改名的 `user/update` 不可达或返回 `code≠0` 或撞每秒限速
- **THEN** 该环境保持原名、不假成功、不阻塞其浏览闭环，后续有机会再试改名

#### Scenario: 存量渐进而非即时批量
- **WHEN** 一批未人工命名的既有环境仍是模板名 / AdsPower 默认名
- **THEN** 它们各自在下次登录读出昵称时被逐个改名，桌面外壳 MUST NOT 触发一次性批量改名或云端昵称导出
