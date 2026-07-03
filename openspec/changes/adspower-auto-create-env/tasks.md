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

## 4. aidcp-edge — 创建管线：台账/幂等/凭据安全（MVP，非 UI）

- [ ] 4.1 write-ahead 台账：发 `user/create` 前写 `pending`（模板/代理位/时间戳），回 id 补齐置 `created`，原子写（临时文件 + rename）
- [ ] 4.2 reconcile：拉 `user/list` 与台账全量对账，标 `untracked-orphan`/`stale`，创建前/启动前可跑
- [ ] 4.3 主进程创建动作单飞互斥（重入诚实返回「进行中」），渲染层触发控件在途禁用
- [ ] 4.4 凭据只内存持有、绝不明文落盘；POST 日志/错误层脱敏 `proxy_user`/`proxy_password`/`Authorization`，禁 stringify 整个 body
- [ ] 4.5 创建成功仅标「仅配置层/未验证/不可投产」，绝不把 `create` 回 id 当就绪
- [ ] 4.6 创建时可预填 `intendedAccountLabel` 并随台账持久化
- [ ] 4.7 MUST NOT 接线任何程序化 `user/delete`；孤儿只暴露 user_id 引导人工在 AdsPower 删
- [ ] 4.8 单次创建规模 N 与观测能力挂钩：观测未就绪时限 N≤3 并说明原因

## 5. aidcp-edge — preload/IPC + 按钮 UI（与 edge-companion-ui 串行，待其落地后 rebase）

- [ ] 5.1 `preload.cjs` + 主进程新增创建 / 自检 / 台账查询的 IPC 通道
- [ ] 5.2 「创建环境」入口改触发程序化建号（挑模板 + 可选预填意图账号，不在面板逐字段配指纹），本地 API 不可达/创建失败诚实降级、保留「打开 AdsPower 手动新建」兜底
- [ ] 5.3 环境列表如实呈现就绪态（仅配置层/未验证 / 已验证 / 验证失败含失败项）+「无代理」标注；代理软提示、非硬闸（未配代理仍允许创建）
- [ ] 5.4 UI 钩子在 `edge-companion-ui`（17/22）落地后 rebase 到其新 renderer 三件套上（标记串行）

## 6. aidcp-edge — 创建后自检 + 投产硬闸（MVP 先接通道，实测置位入迭代 2）

- [ ] 6.1 投产硬闸先接线：起号出口（`pluggable-browser-provider` 起浏览器前 / `launch-multinode` 组装槽位）读 `verifyState`，非 `ready` 诚实拒绝启动（复用 `browser-provider.ts:131` 同款闸）——MVP 即打通此 gate 通道
- [ ] 6.2 运行时自检（迭代 2）：开一次分身经 CDP 实测出口 IP / renderer 非软渲染 / WebRTC 不漏真机 IP / 时区↔IP / 跨分身 Canvas·WebGL·Audio 哈希与 renderer 字符串去重 → 置 `verifyState`（全过 ready / 任一失败 failed 标红）
- [ ] 6.3 `verifyState=ready` 绑定建号机 `machineLabel`；跨机消费（建号机 != 当前机）视为未验证、强制重验/拒投产

## 7. aidcp-cloud — 账号↔分身↔机器映射（与本 change 同批交付，不推迟）

- [ ] 7.1 `account-store` 自愈 `ALTER ... ADD COLUMN IF NOT EXISTS ads_profile_id`，激活 `machine_label` 写入（加性、向后兼容）
- [ ] 7.2 边缘握手载荷携带 `ads_profile_id`/`machine_label`，云端幂等 upsert 一并落库（不覆盖运营已配字段、缺字段按 NULL）
- [ ] 7.3 登录握手回写真实 accountId 并与环境 `intendedAccountLabel` 比对，不一致诚实告警且不投产

## 8. 测试与回归

- [ ] 8.1 写客户端 allowlist 回归断言（到不了 `browser/start|stop|active`）
- [ ] 8.2 护栏单测：`device_memory=6` 被拒、OS 四者一致断言、`webgl` 模式取舍
- [ ] 8.3 台账崩溃窗口 / reconcile / 单飞互斥 / 幂等单测（含「create 成功台账未写」恢复）
- [ ] 8.4 凭据脱敏测试（账密/Authorization 不进日志、不落盘）
- [ ] 8.5 投产硬闸测试：非 `ready` 环境被启动出口拒绝
- [ ] 8.6 安全红线复跑：`AC-PROTO-*`/`AC-PUB-*`/`AC-RISK-*` + `npm run test:acceptance` 后全量 `npm test`（edge & cloud）
- [ ] 8.7 `npm run typecheck`（edge & cloud）

## 9. 验收与归档

- [ ] 9.1 `openspec validate adspower-auto-create-env --strict`
- [ ] 9.2 各 task 标 `[x]` 并写 commit-sha / 偏离说明（`<!-- <repo> <sha> 备注 -->`）
- [ ] 9.3 全部完成后 archive（delta 合并进 `openspec/specs/`）
