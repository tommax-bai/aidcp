# Tasks — fb-publish-fill-deadline

> 背景：change `facebook-post-publish` 的 task 6.8（edge `4e466ca`）把 FB 正文从「一次性 insertText」
> 改成逐字输入（编辑器要求），但云端等待窗口仍是与长度无关的常数 30s。实测每字约 150–165ms
> （拟人节奏 + CDP 往返），正文超过约 175 字必然超时——而内容管线的设计产出区间是 200–500 字，
> 且正文无任何长度 clamp。该 change 已于 2026-07-14 归档，故本批另开 change 承载修复。
>
> 已核实**不需要**做的：身份监测体在发布期间不必挂起——FB 身份从 `c_user` cookie 读取，与编辑器
> 弹层无关，抬预算不会新增其射程（XHS 侧则由 `creator-app` 页面上下文闸豁免）。

## 1. aidcp-cloud — 按长度下发单步预算

- [x] 1.1 新增正文填写预算纯函数（`base + 每字 × 字数`，上限硬钳；字符数按码位计，与边缘 `Array.from` 同口径）。 <!-- aidcp-cloud cf6cd8c src/publish-agent/fill-budget.ts；默认 20s + 250ms/字、上限 240s。250ms/字 与 FB 评论路径既有的 220ms/字（facebook-edge-steps.ts）同源、略保守 -->
- [x] 1.2 Facebook `fill_field` 随指令下发预算；小红书全路径不带预算。 <!-- aidcp-cloud cf6cd8c src/publish-agent/platform-profile.ts；复用协议既有的 PublishCommandPayload.timeoutMs（早已声明、无人读写）→ 不改协议、不新增 MessageType、不碰主动命令白名单 -->
- [x] 1.3 等待窗口反转：带预算的指令等「预算 + 兜底余量」（默认 8s），使边缘必定先答；不带预算者逐字节沿用旧常数窗口。 <!-- aidcp-cloud cf6cd8c src/publish-agent/command-sequencer.ts -->
- [x] 1.4 正文超出预算上限可打完的长度 → 诚实 `content_too_long`，绝不截断、一条指令都不下发。 <!-- aidcp-cloud cf6cd8c src/publish-agent/command-sequencer.ts；默认上限 880 字，远高于管线 200–500 字的设计区间 -->
- [x] 1.5 预算上限按发布租约 TTL 收敛（≤0.4×），启动时钳回并告警；新增 env `AIDCP_PUBLISH_FILL_BASE_MS` / `_PER_CHAR_MS` / `_MAX_MS` / `AIDCP_PUBLISH_RESULT_SLACK_MS`，默认值逐字节复现今日行为。 <!-- aidcp-cloud cf6cd8c src/server.ts -->

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

## 4. 真机验收（登记入 backlog，簇：Facebook dev 环境）

- [ ] 4.1 probe P1（长正文逐字）：dev + tom 分组 FB 环境，用**生产的**逐字逻辑打一篇 400–500 字真实形状正文（含标点、空行、URL、emoji），逐字符 diff 回读、记录实测 ms/char，观察打字途中有无 typeahead / 链接预览抢焦点。产出用于**校准每字 250ms 这个占位常数**，并给出这条路线的 go/no-go。**不提交**。
- [ ] 4.2 probe P2（清场语义）：全选 + Backspace 后回读文本**并确认图片缩略图是否仍在**；带脏 composer 触发 `Page.navigate`，观察是否弹出原生 beforeunload 对话框——edge 全仓**零处**处理 `Page.javascriptDialogOpening`，若 FB 注册了 beforeunload，下一篇稿的导航会把整个 tab 卡死（边缘看着在线、浏览器驱不动）。
- [ ] 4.3 端到端：一篇 300–500 字真实洗稿正文在 dev 上从头走通到真提交，正文逐字符核对无缺失。

## 5. 后续（不在本批，单列以免与并行 FB change 撞热点文件）

- [ ] 5.1 FB 评论路径用的是同一条无界逐字循环（`comment-executor.ts`）：云端虽已按长度算等待窗口（18s + 220ms/字，上限 90s），但**边缘侧仍无截止时刻**——长评论同样会留下孤儿打字循环。把 deadline 一并传下去。
- [ ] 5.2 内容管线不区分平台：FB 正文走小红书形状的 prompt（「正文 200–500 字」）且**正文无任何长度 clamp**（只 clamp 标题）。`content_too_long` 是诚实闸、不是解法——真正该收的是生成侧。
