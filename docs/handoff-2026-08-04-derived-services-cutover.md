# 交接：派生三服务上 dev（2026-08-04）

> 对象 = change `deploy-derived-services-to-dev`。**这份只写「现在是什么状态」与「下一拍怎么切」**。
> 数字都是当天实测，但 fleet 每天在动，接手先自己重跑一遍第 0 节那几条。

---

## 0. 一句话现状

**api 与 content 两个派生服务已经在 dev 上真跑起来了**（这是五个派生仓第一次在任何机器上跑起来），
与单体并存、不推进任何周期业务。**automation 没跑过**——它跟单体并存不了，见 §2。

```bash
ssh -i ~/codes/dev-0722.pem root@121.89.85.150 'systemctl is-active aidcp-{api,content,automation} aidcp-cloud; ss -ltnp | grep -E ":8787|:8090|:8091|:8092|:8093|:8094"'
```

| 进程 | 端口 | 状态（2026-08-04 10:00） |
| --- | --- | --- |
| 单体 `aidcp-cloud` | 8787 边-云 / 8090 面板 / 8091 客户鉴权 | 现役，**全程没停过** |
| 派生 `aidcp-api` | 8093（回环） | 跑着；面板与客户鉴权口**未启用**（端口有意留空）；业务入口 **blocked** |
| 派生 `aidcp-content` | 8092（回环） | 跑着；12 族路由全注册 |
| 派生 `aidcp-automation` | 8094 内部 / 8797 边-云（并存期） | **从未启动过** |

api 的业务入口 blocked 是**设计**：它的同步读要问 automation（没起）⇒ 就绪度 not_ready ⇒
排期心跳与飞书入口都不放行。并存期因此天然不会有两处同时推进。

---

## 1. 这一批真正修掉的东西（都是「只有真跑起来才现形」那一类）

| # | 现象 | 根因 | 修在哪 |
| --- | --- | --- | --- |
| 1 | 派生 api 启动即失败 `interaction_scope_config_schema_missing_run_0048` | api 属主池上的存储顺带断言了一列 **automation 属主表**的列。三域同库时恒成立，物理拆库后永远为假 | `aidcp-cloud@71f41cb`（事实源）+ 新门禁 AC-OWN-07 |
| 2 | 派生 api 启动即失败「缺 75 个对象」，而那些对象**一个不缺** | 手写组装根里那份形状探测只查表、`columns`/`indexes` **恒返回空集合** | `aidcp-api@3f31bde`（改用共享包那份真探测） |
| 3 | 面板 API 与客户鉴权 API **零调用点** | 实现随属主搬进 api 仓，手写 main() 从没调用过它们 | `aidcp-api@5ed39a3` |
| 4 | 六族路由客户端都在、对面一条都没注册 | automation 的 main() 只注册了 8 族 | `aidcp-automation@65af812` |
| 5 | api 与 content 没有可执行入口 / 没有 schema 门 / 失败不真退出 | 见 change tasks 2.1–2.4 | `aidcp-api@6218573`、`aidcp-content@a22a8a9` |

**第 1、2 条的共同形状**：它们都不是「少一个功能」，而是**进程根本起不来**，且错误文案把排查
方向指向数据库。两条都只在物理拆库之后才可能发生，单体侧永远看不见。

---

## 2. 为什么 automation 不能跟单体并存（这条决定了切换只能是原子的）

自动化写者锁**按 target 单实例**，且在**构造期**就抢（远早于业务放行），抢不到就 fail-closed
退出。dev 那把锁在单体手里 ⇒ 派生 automation 起不来。这是设计，不是缺陷：两个实例同时持写权，
合计放行的真实平台动作会翻倍。

⇒ **不存在「先让 automation 陪跑一阵子」这个选项**。要么不动，要么切。

---

## 2.5 切流演练做过一次了（2026-08-04 10:18–10:20，已回滚）

**结果：三个进程确实同时起来过，但边缘一台都没连上。** 逐条如实记：

| 进程 | 起来了 | 链路 |
| --- | --- | --- |
| content | ✅ | 12 族路由全注册、探活答得上 |
| api | ✅ | 内部口答得上；**面板 / 客户鉴权两个对外口没验到**（还没重启到带端口那一版就先回滚了） |
| automation | ✅ 写者锁单体一停就拿到了 | **业务入口未放行 ⇒ 8787 从未监听 ⇒ 边缘全程连不上** |

**卡住 automation 的两条**（就绪度 not_ready，两条流都不就绪）：

1. **`facebook_operation_policy` 没有任何进程在服务**。接口进程的注册清单比属主源那份少一条
   （手抄的第二份漂了）。**已修**（`aidcp-cloud@…` 抽成唯一清单 + `aidcp-api` 从它取 + 用例改按引用断）。
2. **`account_persona` 同游标载荷漂移**：同一个游标 902，接口进程发出的载荷摘要与单体当初发的不同，
   消费方按设计拒收。**根因已定位、未修**：两个进程解析人设用的**不是同一个解析器**——
   单体用人设专用编解码器（带 try/catch，失败回 null），派生接口进程用的是通用装载器、且不带兜底。
   同一份人设文本解出两种结构 ⇒ 同游标不同摘要。
   **正确的修法是把那段纯解析提进 `aidcp-kernel`、两侧按引用共用**（本项目的规矩：同一个判断被两处用，
   必须按引用断，因为「第二份实现」在行为测试上原理不可见）。代价是一次共享包版本抬升 + 三仓重装。

另修一条演练暴露的：**干净停机在 `systemctl status` 里显示 failed**（143）。已修（关停成功显式退 0）。

---

## 3. 下一拍：把人设解析收成一份，再切（用户 2026-08-04 已拍板走切流这条）

### 3.1 切之前必须知道的三件事

1. **console 与桌面客户端登录的后端会换人**：面板 API 与客户鉴权 API 从单体挪到派生 api。
   代码已接线（§1 第 3 条），但**跨进程那几跳一次都没真跑过**。
2. **12 条边缘连接会断连重连**（单体停 → automation 起，边-云口易主）。
3. **面板有一批口今天注定答不了**：属主在 content/automation 且 `aidcp-transport` 里
   **没有现成通道**的那些（草稿精修、环境总览的当日用量、边缘 id 反查、互动客户 API、
   离职清理回调；面板侧还有素材池、验证码协助、token 用量、计费价、精选后台、精选动作）。
   它们逐路由答 503 + 具名原因，**不是白屏、也不是假数据**。清单见 change 的 backlog 登记。

### 3.2 切换步骤（预计窗口 3–5 分钟）

```bash
# ① 改两份 .env（只在切换那一刻）
#    api：加 AIDCP_PANEL_PORT=8090 / AIDCP_CLIENT_AUTH_PORT=8091 /
#         AIDCP_PANEL_JWT_SECRET / AIDCP_PANEL_USERS / AIDCP_PANEL_FORBIDDEN_PORTS /
#         AIDCP_CLIENT_JWT_SECRET / AIDCP_CLIENT_JWT_TTL_SECONDS（都从单体那份取）
#         删掉 AIDCP_FEISHU_WS_ENABLED=false（并存期为防两条长连接重复消费事件而加的）
#    automation：AIDCP_WS_PORT 8797 → 8787
# ② 停单体
systemctl stop aidcp-cloud.service
# ③ 起 automation（此刻才抢得到写者锁），再重启 api 让两个对外口生效
systemctl start aidcp-automation.service && systemctl restart aidcp-api.service
# ④ 逐条核对：三个进程 active、8787/8090/8091/8092/8093/8094 都在、
#    api 的 sync-read readiness 变 ready、业务入口 started、飞书长连接 1 条、
#    console 能登录能出数、桌面客户端能登录
```

### 3.3 回滚（演练过才算数，本批还没演练）

```bash
systemctl stop aidcp-api.service aidcp-automation.service aidcp-content.service
systemctl start aidcp-cloud.service
# 单体一起来就同时拿回 8787/8090/8091 与写者锁；数据面无残留（本批不改任何业务写路径）
```

---

## 4. 几条会让人白花时间的（都实测过）

- **`npm install <包名>` 会把 pin 规格从 `git+ssh://` 重写成 `github:`**，对账脚本从此报「未 pin」；
  且本机实测跑了 **37 分钟**。要刷新装机用 `rm -rf node_modules/<包> && npm install`（17 秒）。
- **ECS 上没有 GitHub 私钥**，但 `ssh -A` 转发可用 ⇒ 服务器上不留钥匙也能装私有共享包。
  ECS 的 npm registry 是公网 npmjs，**没有本机那个 @types 劫持问题**。
- **systemd unit 用未加引号的 heredoc 写时，正文里不能出现反引号**——会被 shell 当命令替换执行，
  实测把 `systemctl status` 的输出写进了 unit 文件，systemd 报 `Missing '='`。
- **新加的派生仓私有文件要登记进 `scripts/sync-split-repos` 的私有清单**，否则对账报「多出」、
  `--prune` 会**删掉它们**。
- **门禁写完要变异测试**：本批那道 AC-OWN-07 第一版恒绿（把数组当对象读、表全集为空），
  注入违规仍然全绿，只有变异测试才发现。

---

## 5. 指针

| 东西 | 在哪 |
| --- | --- |
| change 本体与逐条进度 | `openspec/changes/deploy-derived-services-to-dev/`（tasks.md 里每条都带实测注） |
| 单体运行事实基线 | 同目录 `baseline-monolith-runtime.md`（端口 / 15 项周期任务 / 飞书 / 写者锁 / 12 条边缘） |
| 依赖可满足性分类 | 本文 §3.1 第 3 点提到的那批；面板 54 个字段与客户鉴权 29 个字段的逐条判定见 change 的 backlog 登记 |
| 拆仓不变量 | `CLAUDE.md` §8（OVERRIDE 级） |
