# Tasks — fb-publish-fill-deadline

> 背景：change `facebook-post-publish` 的 task 6.8（edge `4e466ca`）把 FB 正文从「一次性 insertText」
> 改成逐字输入（编辑器要求），但云端等待窗口仍是与长度无关的常数 30s。实测每字约 150–165ms
> （拟人节奏 + CDP 往返），正文超过约 175 字必然超时。当前 Facebook 已使用专用 prompt，
> 正文目标为 100–350 字，但仍无确定性长度校验。该 change 已于 2026-07-14 归档，故本批另开 change 承载修复。
>
> 已核实**不需要**做的：身份监测体在发布期间不必挂起——FB 身份从 `c_user` cookie 读取，与编辑器
> 弹层无关，抬预算不会新增其射程（XHS 侧则由 `creator-app` 页面上下文闸豁免）。

## 1. aidcp-cloud — 按长度下发单步预算

- [x] 1.1 新增正文填写预算纯函数（`base + 每字 × 字数`，上限硬钳；字符数按码位计，与边缘 `Array.from` 同口径）。 <!-- aidcp-cloud cf6cd8c src/publish-agent/fill-budget.ts；默认 20s + 250ms/字、上限 240s。250ms/字 与 FB 评论路径既有的 220ms/字（facebook-edge-steps.ts）同源、略保守 -->
- [x] 1.2 Facebook `fill_field` 随指令下发预算；小红书全路径不带预算。 <!-- aidcp-cloud cf6cd8c src/publish-agent/platform-profile.ts；复用协议既有的 PublishCommandPayload.timeoutMs（早已声明、无人读写）→ 不改协议、不新增 MessageType、不碰主动命令白名单 -->
- [x] 1.3 等待窗口反转：带预算的指令等「预算 + 兜底余量」（默认 8s），使边缘必定先答；不带预算者逐字节沿用旧常数窗口。 <!-- aidcp-cloud cf6cd8c src/publish-agent/command-sequencer.ts -->
- [x] 1.4 正文超出预算上限可打完的长度 → 诚实 `content_too_long`，绝不截断、一条指令都不下发。 <!-- aidcp-cloud cf6cd8c src/publish-agent/command-sequencer.ts；初始默认上限 880 字，远高于管线 200–500 字的设计区间 -->
- [x] 1.5 预算上限按发布租约 TTL 收敛（≤0.4×），启动时钳回并告警；新增 env `AIDCP_PUBLISH_FILL_BASE_MS` / `_PER_CHAR_MS` / `_MAX_MS` / `AIDCP_PUBLISH_RESULT_SLACK_MS`，默认值逐字节复现今日行为。 <!-- aidcp-cloud cf6cd8c src/server.ts -->
- [x] 1.6 默认 Facebook 正文硬上限从 880 字提高到 1520 字；保持 20s + 250ms/字不变，将填写预算上限同步提高到 400s、默认发布租约提高到 1000s，继续满足预算 ≤ 租约 0.4×。 <!-- aidcp-cloud 55417a5；定向 46/46、acceptance 144/144、全量 3582 pass / 11 skip、typecheck pass -->

## 2. aidcp-edge — 自我掐表 + 诚实中止 + 全文验收

- [x] 2.1 逐字输入循环支持可选截止时刻（复用既有 `InputDispatchDeadlineError`）；不传即行为完全不变（XHS 搜索/评论、FB 评论零回归）。 <!-- aidcp-edge 4162339 src/browse/cdp-util.ts；每字符的拟人节奏一个字节未动 -->
- [x] 2.2 正文填写按下发预算自我掐表；预算耗尽即停手、清场、诚实回报（清不干净则标 dirty）。云端未下发预算时用 25s 兜底（小于云端 30s 常数窗口 → 即使对端未升级也是边缘先答）。 <!-- aidcp-edge 4162339 src/facebook/publish-executor.ts -->
- [x] 2.3 验收闸从「前 20 字前缀」换成**全文回读包含**；额外内容超容差（typeahead 劫持）亦判失败。 <!-- aidcp-edge 4162339；红线：插入调用没报错 ≠ 文本进去了 -->
- [x] 2.4 打字前先清空编辑器并校验为空，清不干净则诚实 `composer_not_clean`、绝不在残稿之上追加。 <!-- aidcp-edge 4162339；composer 复用已存在编辑区 + 光标处追加，是脏稿拼接的根因 -->
- [x] 2.5 修正聚焦守卫的恒真返回；聚焦改为尽力而为，以全文回读为唯一判据。 <!-- aidcp-edge 4162339 -->

## 3. 测试与回归

- [x] 3.1 edge 补五例：编辑器吞字 / 预算耗尽停手 / 预算够用打完长正文 / 脏 composer 先清空 / 清场失败诚实失败。用推进虚拟墙钟的假时钟——原 `instantSleep` 让墙钟恒为 0，deadline 分支在那种桩下不可测。 <!-- aidcp-edge 4162339 test/facebook/publish-executor.test.ts -->
- [x] 3.2 cloud 补五例：预算随长度伸缩并被上限钳 / 上限按租约收敛 / **XHS 指令 MUST NOT 带预算**（反回归）/ 越界诚实失败且零下发 / 带预算者等待窗口叠余量。 <!-- aidcp-cloud cf6cd8c test/publish-agent/fill-budget.test.ts -->
- [x] 3.3 两仓回归：`test:acceptance` → `npm test` → `typecheck` 全过。 <!-- aidcp-cloud: acceptance 50 pass / npm test 1930 pass / typecheck pass；aidcp-edge: acceptance 19 pass / npm test 1175 pass / typecheck pass -->
- [x] 3.4 部署 dev（云端，两轮：初版 + 复审补洞版）。edge 为客户端侧改动、无 ECS 部署，需运营 / 客户机重建安装包后生效（按约定本批不出安装包）。 <!-- 2026-07-14 deployed：从 origin/master 干净快照（cf6cd8c，git archive，非脏共享工作区）部署 dev；部署前核实 ECS 上 command-sequencer.ts 的 md5 恰等于 cf6cd8c^（无并发漂移可被覆盖）；备份 /opt/aidcp/cloud.bak.20260714-141047.tar.gz + .env.bak.20260714；无依赖变更故未跑 npm ci。健康：aidcp-cloud.service active，8787/8090/8088 监听，panel /api/health {"ok":true}，公网 8088 /api/health 200，飞书长连接 onReady，无启动错误、无预算钳位告警（600s 租约 > 240s 上限）。未碰同机 isales。 --> <!-- 2026-07-14 15:08 复审补洞版重新部署：origin/master 2944fbf 干净快照（git archive），备份 cloud.bak.20260714-150819.tar.gz；部署后三文件 md5 与 origin/master 逐字节一致；健康：service active，8787/8090/8088 监听，panel /api/health {"ok":true}，飞书长连接已建立，**预算告警 0 条 + 错误 0 条**（配置健全）。注：本次 land 时 canonical cloud checkout 的 master 上有并发 session 未推送的提交、致 land-change 同步主 checkout 未能 ff——部署一律以 origin/master 为准（eligible ref），未把他人未推送 WIP 带上线。 -->
- [x] 3.5 将 1520 字硬上限变更追加到 OL release 分支并部署：备份、迁移状态、stop-then-start、service/listener/health/PostgreSQL/三属主 schema 契约门/自动化写者锁/飞书验证，且不触碰 `isales`。 <!-- 2026-07-27 07:28 CST，OL release/20260726-ol-current 8de0726；代码备份 /opt/aidcp/cloud.bak.20260727-072810.tar.gz，环境备份 /opt/aidcp/cloud.env.bak.20260727-072810；三属主 pending=0。共享库 API 账本已到 expand 迁移 0081、release 构建认识到 0078，按契约精确设置 AIDCP_ALLOW_SCHEMA_AHEAD=0081_offboard_admission_claims（非通配），启动日志确认只放行 (0078,0081]。stop-then-start 后 service active / NRestarts=0，8787/8090/8091/8088 监听，内外 health 均 {"ok":true} / HTTP 200，三属主 schema gate 通过，自动化写者锁 target=ol，飞书 WSClient onReady，warning 0；远端运行时 maxChars=1520 / fill maxMs=400000 / publishLeaseMs=1000000；#204 无重投日志，未触碰 isales -->

## 3b. 对抗性复审补洞（5 视角 × 逐条反驳；15 条候选，10 条被反驳，5 条成立）

- [x] 3b.1 edge：打字途中抛出的 CDP 异常（命令超时 / 协议错误 / 断连）**绕过了清场**——半篇正文留在活着的编辑器里，却报成不带 dirty 标记的「干净失败」，下一篇在复用的编辑区里接着追加。所有 mid-typing 失败统一走 `abandonFill`。 <!-- aidcp-edge 26233b6；这是上一版自己新立的契约被自己破坏 -->
- [x] 3b.2 edge：清场结果改三态——清干净 / 编辑器已消失（`_composer_gone`，无残文可留）/ 真脏页（`_dirty_composer`）。原先「编辑器不在」被误报成 `composer_not_clean: ""`（自相矛盾）。打字前编辑器就不在 → 诚实 `no_target`。 <!-- aidcp-edge 26233b6 -->
- [x] 3b.3 cloud：发布租约 env 原用裸 `Number()`（抄自旧写法），而同批三个新旋钮走 NaN-safe 的 `readEnvNumber`。写成 `600_000` / `10m` → NaN → 预算 NaN → 下发 `timeoutMs: NaN` → 云端 `setTimeout(NaN)` 约 1ms 触发，**把本 change 刚拆掉的孤儿打字级联原样复活**，同时诚实长度闸（`chars > NaN` 恒 false）失效。 <!-- aidcp-cloud 2944fbf -->
- [x] 3b.4 cloud：预算上限只有上界没有下界——租约调到 60s，正文上限就变成 16 字，**每一篇 FB 帖都以 `content_too_long` 失败**，而错误信息把矛头指向内容生成侧。新增 `sanitizeFillBudget`（非有限/非正/base≥max 一律回落 + 告警）+ `warnIfFillBudgetUnusable`（启动时吼「真凶是配置不是内容生成」）+ 非法租约不得污染天花板 + Sequencer 构造处再挡一道。`AIDCP_PUBLISH_FILL_PER_CHAR_MS=0` 会让上限变成无穷、诚实闸整个关掉，同批堵上。 <!-- aidcp-cloud 2944fbf -->
- [x] 3b.5 cloud：修一条**本 change 自己引入的失败延迟回归**——等待窗口从常数 30s 变成随长度伸缩（可达数分钟），而发布按账号串行；边缘一死若还傻等满预算，该账号后面所有已审稿件都被堵住。新增 `CommandSequencer.invalidateEdge`，边缘断开即诚实失败其在途指令。 <!-- aidcp-cloud 2944fbf -->
- [x] 3b.6 复审后回归：cloud acceptance 50 / npm test 1935 / typecheck；edge acceptance 19 / npm test 1179 / typecheck，全过。
- [x] 3b.7 复审存活但**不修**的一条（已核实非本 change 引入、不破红线）：预算是**自我计时、不是取消令牌**。云端 WS 断连时边缘会 reset 租约并恢复浏览循环，而打字循环仍在跑（现在**有界**、且全文回读会诚实失败、提交被租约闸挡住 `task_lease_mismatch`）。改动前那条循环**完全无界且每篇必触发**，故本 change 严格改善。彻底消灭需要「租约 / 连接 epoch 取消令牌」，属 edge 生命周期层，见 5.3。

## 3c. Native-only 切换回归

- [x] 3c.1 根因追溯：Native 抽取提交 `073eadc8` 直接继承早期内嵌 router 的整段填写实现，没有以已归档的 TS `FacebookPublishExecutor` 及 `facebook-post-publish` 逐字契约作为行为 oracle；Native 测试只覆盖 owner/mapping 和 navigate/select/submit，未执行 `fill_field` 的真实 CDP 事件序列，故切换时未被闸住。
- [x] 3c.2 Native Facebook `fill_field` 恢复逐 Unicode 码位拟人输入；透传 Cloud `timeoutMs` 至 400 秒并只放宽该命令的 TypeScript/Rust ceiling（Native session/protocol 仍为 90 秒）；保留审核正文首尾字符，打字前清空校验，预留 8 秒，全文回读有界轮询，失败/取消/CDP 异常统一清场并诚实区分 dirty/composer-gone。
- [x] 3c.3 Native 定向测试、全量 Rust/Edge 回归、Native 构建与生产边界验证。 <!-- aidcp-edge e2cec6d；Rust 定向 publish 19/19、全量 102/102、clippy -D warnings；Edge 定向 15/15、acceptance 30 pass / 1 gated skip、全量 2429 pass / 1 skip、typecheck；Native release artifact SHA-256 4ee4bf59072b25f5963017df96c34f49f4962f32e38b27a96304fbcf049c8f5f；dist reachable=79 / removed=63、legacy_page_rules=absent、source_maps=absent，desktop build input 验证通过；已集成并推送 origin/master -->

## 4. 真机验收（登记入 backlog，簇：Facebook dev 环境）

- [ ] 4.1 probe P1（长正文逐字）：dev + tom 分组 FB 环境，用**生产的**逐字逻辑打一篇 400–500 字真实形状正文（含标点、空行、URL、emoji），逐字符 diff 回读、记录实测 ms/char，观察打字途中有无 typeahead / 链接预览抢焦点。产出用于**校准每字 250ms 这个占位常数**，并给出这条路线的 go/no-go。**不提交**。
- [ ] 4.2 probe P2（清场语义）：全选 + Backspace 后回读文本**并确认图片缩略图是否仍在**；带脏 composer 触发 `Page.navigate`，观察是否弹出原生 beforeunload 对话框——edge 全仓**零处**处理 `Page.javascriptDialogOpening`，若 FB 注册了 beforeunload，下一篇稿的导航会把整个 tab 卡死（边缘看着在线、浏览器驱不动）。
- [ ] 4.3 端到端：一篇 300–500 字真实洗稿正文在 dev 上从头走通到真提交，正文逐字符核对无缺失。

## 5. 后续（不在本批，单列以免与并行 FB change 撞热点文件）

- [ ] 5.1 FB 评论路径用的是同一条无界逐字循环（`comment-executor.ts`）：云端虽已按长度算等待窗口（18s + 220ms/字，上限 90s），但**边缘侧仍无截止时刻**——长评论同样会留下孤儿打字循环。把 deadline 一并传下去。
- [ ] 5.2 **edge 生命周期层：给逐字输入接「取消令牌」**（复审存活项 3b.7）。今天的预算是自我计时——云端 WS 断连时边缘 reset 租约、恢复浏览循环，而打字循环仍在有界地跑，两个写者短暂共用同一个 CDP 页面。彻底消灭要让租约 / 连接 epoch 在 `reset()` / `finishActive()` 时自增，逐字循环在每个字符间与 `deadlineAt` 一并检查。属 `edge-task-coordinator` / `main.ts` 热点，单列串行做。
- [x] 5.3a Facebook 专用 prompt 的正文目标改为「全文 100–350 字（Facebook 最佳阅读区间）」，并补回归断言锁住新文案、排除旧 100–500 与 80–600 提示。 <!-- aidcp-cloud 3d28b48 初次改为 100–500；794cda9 收紧为 100–350。content-creator 7/7；acceptance 123/123；全量 3401 pass / 11 skip；typecheck pass；OpenSpec strict pass。2026-07-26 15:42 CST 部署 dev，备份 cloud.bak.20260726-074153Z.tar.gz + cloud.env.bak.20260726-074153Z；远端 prompt 哈希与 master 一致，service active / NRestarts=0 / 8787 / 8090 / 8091 / PostgreSQL / 三属主 schema 契约门 / 自动化写者锁 / 飞书 onReady / 内外 health 全绿，isales 未触碰 -->
- [ ] 5.3b 该规则仍是模型软提示，**正文无任何确定性长度校验**（只 clamp 标题）。`content_too_long` 是诚实闸、不是解法——真正该收的是生成侧。
- [ ] 5.4 Native 同类输入语义另行归属 `native-page-engine-production-cutover`：Facebook 评论仍经 `replace_focused_text` 一次性整段 `Input.insertText`（且评论 deadline 仍见 5.1）；小红书搜索仍一次性写入关键词，违反 `comment-search-command` 的逐字契约；Native 验证码文本仍使用 `Input.insertText`，违反 `captcha-incident-handling` 明确要求的真实 keyDown/keyUp。三者涉及不同提交/取消边界，MUST 拆分修复和验收，不与本次发帖修复混写。
