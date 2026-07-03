## Context

现状：aidcp-edge Electron 客户端的「创建环境」按钮（`renderer.js:397` → `ads:openCreate` → `main.cjs` `openAdsClient()`）只是 best-effort 拉起本机 AdsPower 客户端、退回打开官网，**零程序化创建**；分身全靠运营在 AdsPower UI 里手动新建并逐字段配指纹。只读客户端 `ads-local-api.cjs` 明确红线「只 `/status` + `user/list`」，其真实内涵是「主进程绝不碰浏览器生命周期 `browser/start|stop|active`（那是核心子进程单写）」。`user/list` 返回的是代理**配置**、非实测出口 IP（`ads-local-api.cjs:159`），且 `no_proxy` 可读出（`:167`）。云端 `accounts` 表 `machine_label` 是死列、无 `ads_profile_id`（`account-store.ts:37`），`ensureAccount` 只 INSERT `account_id/label`（`:194-201`），已有自愈 `ALTER ... ADD COLUMN IF NOT EXISTS` 惯例（`:44/47`）；`launch-multinode.ts:126` 显式 `delete AIDCP_ACCOUNT_ID`，身份由登录读出。

约束（已定）：客户端**不做多开**（单实例锁 `main.cjs:454` 不动，一次一个环境）；代理**人手配、软提示非硬闸**；本 change 经两轮多 agent 对抗式评审（29 洞 / 3 致命）定案，核心不变量已在 proposal 列明。反转已归档 D4「面板不做 `user/create`」。

前几轮已核实的领域事实（作为设计前提）：AdsPower 指纹层机制=真内核 + 读出口叠确定性噪声 + 部分字符串自定义（非硬件伪造，跨会话稳、跨机漂）；`cdp_mask`(藏自动化) ≠ `fingerprint_config`(造指纹)；`device_memory` 只允 2 的幂封顶 8（`6` 即伪造信号）；`webgl='3'`(random matching) 与 `webgl_config`(family lock) 互斥；检测方真查的是 OS 绑定链 + 屏窗自洽 + 时区↔IP，不查「CPU 配 GPU 性能」。

## Goals / Non-Goals

**Goals:**
- 把「造指纹」从运营手工收走，程序按验证过的规则一键设好，消除「怕自己配错」的核心痛点。
- 诚实区分「配置层已就绪」与「运行时实测已就绪」，绝不把没验证的环境当能投产（不静默假成功红线）。
- 建立账号↔分身↔机器的可审计对应，并在登录时校验绑定意图。
- 引入写能力而不侵蚀「主进程绝不碰浏览器生命周期」不变量。

**Non-Goals:**
- 客户端多开 / 同机多任务并发（一次一个环境；批量运行走 CLI 另议）。
- 代理供给自动化（人手配、软提示）；小红书登录自动化（人手扫码）；行为拟人 / 时序去相关（云端事）；fleet 级可观测（放开规模的前置、另立）。
- 程序化 `user/delete`（红线，孤儿只暴露引导人工删）。

## Decisions

**D1 · 指纹最大化委托 AdsPower 生成，aidcp 不逐字段手搓。** 只挑「OS/整机模板」+ 薄护栏 + 提交前一致断言。
- 理由：手搓 `fingerprint_config` 会原样复现「运营怕配错」的每个陷阱（`device_memory=6`、跨 OS 字体、webgl 模式互斥），且比 AdsPower 原生按 OS 自动生成的自洽整套更糟。委托生成 + 薄护栏才是「配不错」的正解。
- 备选（否决）：aidcp 侧全量组装 `fingerprint_config`——控制力高但正确性负担全压在我方、易造内部矛盾。

**D2 · 创建态与就绪态两相分离，`verifyState` 承载「是否实测过」。** 创建只保证配置层自洽 + 取值合法 + 有区分度 + 稳定，状态显式命名「仅配置层 / 未验证 / 不可投产」。
- 理由：`user/list` 是配置层、指纹字段读不回、非实测出口 IP，创建响应结构上证明不了隔离；把 `create` 回 id 当就绪 = 在「环境可投产」这层静默假成功（致命洞 C1）。
- 备选（否决）：信任创建响应即就绪——正面撞红线。

**D3 · `verifyState` 通过是启动路径的代码级硬前置，不是咨询字段。** 未过在起号出口（`pluggable-browser-provider` 起浏览器前 / `launch-multinode` 组装槽位）诚实拒绝，复用 `browser-provider.ts:131` 已有「失败诚实停手、绝不回落 self」同款闸。
- 理由：只回填不 gate 的验证字段会被绕过（运营照样把 user_id 填进去起），验证器沦为摆设（H1）。

**D4 · 运行时自检靠「开一次分身 + CDP 实测」。** 读真实出口 IP、`renderer` 非软渲染 SwiftShader、WebRTC 不漏真机 IP、时区↔IP、跨分身 Canvas/WebGL/Audio 哈希与 renderer 字符串去重，全过才置 `verifyState=ready`。
- 理由：唯一能证明「真实且有区分度」的手段是真渲染读值；因已砍多开、一次一个环境，此闭环可行、成本可接受。

**D5 · 新增独立「写客户端」+ 硬编码 allowlist，不在只读模块上原地放开。** 写客户端只放行 `user/create`/`group/create`，任何 `browser/start|stop|active` 路径直接抛错 + 回归断言。
- 理由：把生命周期禁令从「靠注释自觉」升为「结构上不可能」，否则未来改动者「就这一次」加个 `browser/start` 就侵蚀不变量、typecheck 抓不到（M7）。复用同一条 1req/s 节流；本机核心子进程活跃时不并发跑批量写（M6）。

**D6 · 代理软提示 + 无代理如实标注，不设创建闸。** 没配代理给提醒但允许创建；环境列表把 `no_proxy` 如实显示。
- 理由：用户决定——保留运营控制权、不强制。仅保留「别把无代理号伪装成已配好」的诚实（零成本，`ads-local-api.cjs:167` 已能读）。

**D7 · 账号绑定闭环 = `intendedAccountLabel` 预填 + 登录时回写比对。** 台账每条预填意图账号；登录握手边缘回写真实 accountId 并比对，不一致诚实告警不投产。`ads_profile_id` + `machine_label` 进握手落库、走已有自愈 ALTER。
- 理由：创建时账号未知（登录在后、人手扫码），profile↔账号绑定否则全生命周期无强制点，扫错分身零拦截（致命洞 C2）。落库与本 change 同批交付、不推迟到「以后」。

**D8 · write-ahead 台账 + reconcile + 原子写；主进程单飞互斥 + 点击即 disable。**
- 理由：远程 `create` 成功但台账未写的崩溃窗口会漏记真分身、下次重复建号复用代理（H4）；无锁的「查台账-再创建」是 TOCTOU、连点两下双建（H5）。

**D9 · 凭据只内存持有、绝不明文落盘。** POST 扩展后日志层脱敏 `proxy_user/password` 与 Authorization、禁 stringify 整个 body。
- 理由：`adsApiKey` 已明文存 settings（`main.cjs:35/79`），代理账密更敏感、是防关联命脉，落盘或进日志即被盗刷（H3）。

**D10 · OS 为整机模板第一锁定字段并显式下发；webgl 模式二选一。** 提交前静态断言「模板 OS == 下发 UA OS == 字体 OS == renderer 家族 OS」。
- 理由：`ua_auto` 只匹配内核版本、不接收 OS，模板却锁 OS 专属的字体/renderer/分辨率——不 pin OS 会让 AdsPower 按宿主生成 UA，造出比原生更糟的跨 OS 矛盾（H6）。`webgl='3'` 与 `webgl_config` 互斥，要家族自洽用 `2`+显式 config，要随机就删 config（H7），最终取舍由下码前实测定。

**D11 · 创建规模 N 与观测能力挂钩，观测未就绪时 N 收敛 2–3。**
- 理由：状态迁移未接真实封号信号 + 后台无逐账号可观测（CLAUDE.md §2），在盲区里放大在跑账号数会加重整簇连坐（H8）。放开 N 是能力门、不是时间顺序。

## Risks / Trade-offs

- [配置层自洽 ≠ 运行时真实]（同机共享真 GPU、软渲染、代理欠费/漏 WebRTC 创建时都看不出）→ `verifyState` 硬闸 + 运行时自检兜底；未验证环境 UI 明示不可投产。
- [自检要真开一次浏览器、有时间/资源成本] → 因一次一个环境可接受；自检走异步、失败诚实标红不掩盖。
- [fleet 级代理/子网去重不在 MVP] → 本机去重是第二道、UI 明示「单机盲区」；N 收敛到 2–3 兜住风险，fleet 去重列为放开 N>3 的前置。
- [同机同模板 renderer 串可能撞车] → 自检把 renderer 字符串纳入跨分身去重断言，撞则改模板/重建。
- [跨机器执行使「本机已验」失效 + 破坏模板↔宿主硬件自洽（无独显退软渲染）] → `machineLabel` 进握手，云端校验「建号机==上报机」不一致告警；跨机消费视为未验证、强制重验。
- [AdsPower 对 `device_memory=6` / `webgl=3`+config 的实际行为未知] → 下码前实测阻塞护栏细节（见 Open Questions）。
- [与 `edge-companion-ui` 碰 `renderer/` 三件套] → 按钮 UI 钩子串行、待其落地后 rebase；非 UI 部分先行。

## Migration Plan

- **spec 反转**：本 change 的 `adspower-desktop-env-picker` delta 软化/反转 D4「面板不做 `user/create`」的 Non-Goal；archive 时合并进主 spec。
- **云端加列**：`account-store` 自愈 `ALTER ... ADD COLUMN IF NOT EXISTS ads_profile_id`、激活 `machine_label`——加性变更、随进程启动自建 schema（本项目无独立迁移器惯例），回滚安全（旧代码忽略新列）。握手载荷带这两字段，向后兼容（缺字段按 NULL）。
- **分期落地**（务实优先，放开 N 为能力门）：
  1. **下码前置**：对真实 AdsPower 打一次 `user/create` 实测两个存疑点（阻塞护栏与 webgl 取舍）。
  2. **MVP（N=2–3）**：写客户端 + allowlist + 单飞互斥 + 前置闸（去重/非空/OS 四者一致）+ 委托生成 + 薄护栏 + 凭据只内存 + write-ahead 台账/reconcile + 创建 config 回读标「未验证」+ 登录回写比对 + 云端加列 + **pre-flight gate 先接线好**（哪怕 verifyState 初期只 config-only 也打通通道）+ MUST NOT 接 `delete`。
  3. **迭代 2**：运行时实测自检置「可投产」+ 跨分身指纹去重 + 每日打开次数预算闸。
  4. **迭代 3（放开 N>3 前置）**：真机多号并发承载力验证 + 封号/限流信号接入状态迁移 + console 逐账号绑定/健康视图 + fleet 级代理去重。
- **回滚**：按钮行为可退回旧「拉起 AdsPower」外链；云端加列为加性、无需回退。

## Open Questions

- AdsPower `user/create` 传 `device_memory=6` 是被静默接受还是纠正？（决定护栏是「拒绝提交」还是「AdsPower 已兜」）
- `webgl='3'`(random matching) 时同传 `webgl_config` 是被忽略还是生效、随机池是否受 OS 约束？（决定「锁家族」能否做，还是只能 `webgl='2'`+显式 config）
- fleet 级代理去重落点：cloud 侧持代理分配台账（申领去重）vs 代理清单中心统一签发——放开 N>3 前必须定，MVP 先本机去重 + 明示单机盲区。
- 运行时自检的实测手段：CDP `Runtime.evaluate` 直接读指纹值 vs 载入一个自建自检页读取——需定，注意 §4.2「不常驻 `Runtime.enable`、优先 isolated world」的既有反检测约束。
- 初始整机模板数量（Win/Mac 各几套）与维护节奏（Chrome 升级 / 新 GPU 致模板漂移过时）。
