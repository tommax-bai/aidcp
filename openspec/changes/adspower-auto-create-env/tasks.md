## 1. 下码前置 — 真机实测（阻塞护栏细节，先做）

- [x] 1.1 对真实 AdsPower 打一次 `user/create`：观测 `device_memory=6` 行为 <!-- aidcp-edge scripts/adspower-fingerprint-probe.ts 实测: device_memory=6 → 运行时 navigator.deviceMemory=4(非6非8), 不忠实下发→护栏「只允2的幂、拒6」证实必要; deviceMemory 仅HTTPS暴露、自检勿用about:blank -->
- [x] 1.2 对真实 AdsPower 打一次 `user/create`：观测 `webgl` 模式与 `webgl_config` 交互 <!-- 实测: webgl='2' 逐字honor webgl_config; webgl='3' 无视config按OS给自洽随机→锁家族只能webgl='2'+显式config, webgl='3'传config白传 -->
- [x] 1.3 记录实测结论回写 design.md <!-- 已写入 design.md「实测结论」段; 另挖出更要命发现: 不pin OS时OS随机(Win/Mac/Linux/甚至iPhone)→模板MUST显式钉OS+桌面; H6现场坐实(Mac画像+NVIDIA/D3D11 renderer被照单全收)→四者一致断言必不可少 -->
- [ ] 1.4 （新增，据 1.3）整机模板 MUST 显式 pin OS + 限定桌面（Win/Mac，绝不放任随机分到 iPhone/Linux）；webgl 二选一（`webgl='2'`+OS 匹配 renderer / `webgl='3'` 纯委托）

## 2. aidcp-edge — 写客户端与红线（MVP，非 UI，可先行）

- [x] 2.1 新增与只读 `ads-local-api` 分离的「写客户端」，硬编码 allowlist 只放行 `user/create`/`group/create`，任何 `browser/start|stop|active` 路径直接抛错 <!-- aidcp-edge 7227783 src/electron/ads-write-api.cjs -->
- [x] 2.2 写客户端复用 ≥1 秒串行节流；本机核心子进程活跃时不并发跑批量写（撞每秒限速诚实降级、不假成功） <!-- aidcp-edge 7227783 串行节流单链已实现；「核心活跃时不并发批量写」的互斥闸留 task 4.3/M6 与 main.cjs 接线时落 -->
- [x] 2.3 回归断言：证明写客户端结构上到不了浏览器生命周期端点（红线靠测试守） <!-- aidcp-edge 7227783 test/electron/ads-write-api.test.ts：browser/start|stop|active + user/delete 抛错且零 fetch，11/11 过 -->

## 3. aidcp-edge — 指纹生成策略：模板 + 护栏 + 一致断言（MVP，非 UI）

- [x] 3.1 定义少量「整机模板」（Win/Mac 各若干套，OS 为第一锁定字段；`device_memory`/`hardware_concurrency`/`screen_resolution`/字体/renderer 家族折进模板、不逐字段独立随机） <!-- aidcp-edge b92989b DEVICE_TEMPLATES 5 套(win×3/mac×2)，OS 第一锁定 -->
- [x] 3.2 委托生成为主构造 `fingerprint_config`（**显式 pin OS 而非 ua_auto**、canvas/webgl_image/audio/client_rects 噪声=1、不启用「每次启动重随机指纹」、`webrtc=proxy`、时区/语言 based-on-IP） <!-- aidcp-edge b92989b buildFingerprintConfig；据探针 1.3 用 random_ua.ua_system_version pin OS(ua_auto 会随机分 OS/iPhone) -->
- [x] 3.3 薄静态护栏：`device_memory` 只允 2 的幂（拒 `6`）、`hardware_concurrency` 真实值、`webgl` 模式不自相取消、`webrtc` 禁 local/real、噪声必开、字体不跨 OS <!-- aidcp-edge b92989b validateGuardrails -->
- [x] 3.4 提交前「声明 OS == UA OS == 字体 OS == renderer 家族 OS」四者一致断言，不符诚实拒建 <!-- aidcp-edge b92989b assertOsCoherent，拦 H6「Mac 画像+Windows renderer」 -->

## 4. aidcp-edge — 创建管线：以 user/list 为账本 / 幂等 / 凭据安全（MVP，非 UI）

<!-- 简化(用户 2026-07-03)：去掉自建本机 write-ahead 台账，改以 AdsPower user/list 为账本 + 专用分组 + remark 承载意图/模板/机器。理由：登录后 edge 握手即上报账号↔分身↔机器(Task 7)，只有创建-登录空窗云端不可见，而 user/list 本就是现成账本。 -->

- [x] 4.1 本 change 建的分身归入专用分组；创建时把「意图账号 / 模板 / 建号机」写进分身 `remark`（随 `user/create` 一次写入）——不建本机台账 <!-- aidcp-edge 03b6dde ads-create-flow.cjs encodeRemark；专用分组经写客户端 createGroup(7227783) -->
- [x] 4.2 崩溃后据下次 `user/list` 直接看见已建分身（专用分组 + `remark`，不丢账、无需本机台账续接）；**代理全程手工、本按钮不碰（不下发/不校验/不去重）** <!-- aidcp-edge 03b6dde 无本机台账；createEnvironment 只传 no_proxy、零代理逻辑 -->
- [x] 4.3 主进程创建动作单飞互斥（重入诚实返回「进行中」） <!-- aidcp-edge 03b6dde ads-create-flow 单飞互斥；「渲染层控件在途禁用」随 task 5 UI 接线 -->
- [ ] 4.4 凭据只内存持有、绝不明文落盘 <!-- 机制就绪：ads-write-api 错误不含 body + redactSensitive(7227783)；「不落 settings.json」的接线随 task 5 main.cjs -->
- [x] 4.5 创建成功仅标「仅配置层/未验证/不可投产」，绝不把 `create` 回 id 当就绪 <!-- aidcp-edge 03b6dde status=UNVERIFIED -->
- [x] 4.6 创建时可预填 `intendedAccountLabel`，写进分身 `remark`（随 `user/list` 读回，供登录时比对） <!-- aidcp-edge 03b6dde encodeRemark/parseRemark -->
- [x] 4.7 MUST NOT 接线任何程序化 `user/delete`；孤儿只暴露 user_id 引导人工在 AdsPower 删 <!-- aidcp-edge 7227783 allowlist 已断言禁 user/delete；「孤儿暴露」随 task 5 UI -->
<!-- task 4 核心逻辑（编排/护栏/断言/remark/互斥/无台账/无代理）已落 aidcp-edge 03b6dde；剩「凭据不落 settings」接线随 task 5（main.cjs/UI，串行等 edge-companion-ui）。「规模上限」已砍（用户 YAGNI）。 -->

## 5. aidcp-edge — preload/IPC + 按钮 UI + 「是否配代理」提示（与 edge-companion-ui 串行，待其落地后 rebase）

- [ ] 5.1 `preload.cjs` + 主进程新增「创建环境」IPC 通道（调 `ads-create-flow`）；凭据不落 `settings.json`、日志用 `redactSensitive`（4.4 接线落此）
- [ ] 5.2 「创建环境」入口改触发程序化建号（挑整机模板，不在面板逐字段配指纹）；本地 API 不可达/创建失败诚实降级、保留「打开 AdsPower 手动新建」兜底；成功即呈现「已创建」
- [ ] 5.3 环境列表对每个环境显示**唯一提示：是否配置了代理**（`no_proxy`/空 → 「未配置代理」纯提醒、不拦任何操作；代理由运维手动在 AdsPower 侧配）。不做就绪态/自检/硬闸
- [ ] 5.4 UI 钩子在 `edge-companion-ui`（17/22）落地后 rebase 到其新 renderer 三件套上（标记串行）

## 6. 收尾验证与归档

- [ ] 6.1 edge `npm run typecheck` + 全量 `npm test`（确认新模块未破坏既有；新模块单测已随实装绿：ads-write-api / ads-fingerprint / ads-create-flow）
- [ ] 6.2 `openspec validate adspower-auto-create-env --strict`
- [ ] 6.3 各 task 标 `[x]` 写 commit-sha；完成后 archive（delta 合并进 `openspec/specs/`）

<!-- 已砍（用户 2026-07-03，YAGNI）：创建后自动自检 + 投产硬闸（原组 6）、云端 profile↔machine 映射与登录比对（原组 7）、单次规模上限、复杂就绪态。本功能 = 一键建配好的指纹环境 + 一个「是否配代理」提示；是否可用由运维登录时人工确认。将来要规模化 / 后台看板再另立 change。 -->
