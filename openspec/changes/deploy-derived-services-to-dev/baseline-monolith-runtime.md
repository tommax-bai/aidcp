# dev 单体运行事实基线（任务 0.3）

> 采于 **2026-08-04 08:30 CST**，源 = dev ECS 上正在跑的 `aidcp-cloud.service`
> （`ActiveEnterTimestamp=2026-08-03 16:47:57 CST`，MainPID 1067809）。
> 第 6 组切换周期任务时要对着这份关；第 8 组回滚演练时要对着这份验「回到今天的状态」。
>
> **这份是快照，不是契约**：单体每天在部署，读的时候先自己重跑一遍那三条命令。

## 1. 监听端口

| 端口 | 绑定 | 谁 | 用途 |
| --- | --- | --- | --- |
| 8787 | `0.0.0.0` | aidcp-cloud | 边-云 WebSocket（边缘客户端连这里） |
| 8090 | `127.0.0.1` | aidcp-cloud | 面板 API（console 经 Nginx 8088 的 `/api` 与 `/ws` 反代） |
| 8091 | `127.0.0.1` | aidcp-cloud | 客户鉴权 API（桌面客户端 `/login` `/my-environments`） |
| 80 / 443 / 8088 | `0.0.0.0` | nginx | 8088 = console 静态 + 反代；80/443 另有用途 |
| 4310 / 8990 | — | **非 aidcp** | 同机 isales，**一根手指都不碰** |

复现：`ss -ltnp | grep -E "node|nginx"`。

## 2. 周期任务清单（单体启动日志里自报的）

按启动日志出现顺序，全部由单体这一个进程持有：

| 任务 | 周期 / 触发 | 日志锚点 |
| --- | --- | --- |
| 配置镜像失效信号中继 | 兜底轮询 2000ms | `[config-mirror] 失效信号中继已启动` |
| 配置镜像刷新器 | `T_poll=5000ms` | `[config-mirror] 刷新器已启动` |
| `llm_token_usage` 保留清理 | 24h（保留 45d） | `[retention] llm_token_usage 保留清理已启动` |
| `interaction_feed` 保留清理 | 24h（保留 30d） | `[retention] interaction_feed 保留清理已启动` |
| `risk_counters` 保留清理 | 24h（保留 7d） | `[retention] risk_counters 保留清理已启动` |
| `event_outbox` 保留期剪裁 | 常驻 | `event_outbox 保留期剪裁已启动（monolith）` |
| 风控记账 outbox | 常驻（启动回收在途行=0） | `风控记账 outbox 已就绪` |
| 风控计数对账 | 常驻（偏差非零即告警） | `风控计数对账已启动` |
| 内容排期心跳 | **每分钟** | `[content-scheduler] 已启动（每分钟心跳）` |
| ContentScheduler（按账号错峰） | **每分钟** | `ContentScheduler 已启动` |
| DelegatedTaskWorker | automatic priority，并发=3 | `DelegatedTaskWorker 已启动` |
| CommentScheduler | 飞书 `/comment` 触发 | `CommentScheduler 已就绪` |
| PublishScheduler | 手动 `/publish` 触发 | `PublishScheduler 已就绪` |
| MOCK publish 触发 | 文件触发 | `MOCK publish 触发已开启` |
| PacingSaturationAlerter | 常驻 | `PacingSaturationAlerter 已就绪` |

复现：`journalctl -u aidcp-cloud.service --since "<ActiveEnterTimestamp>" | head -160`。

## 3. 飞书长连接

**一条**（`[aidcp-cloud] 飞书长连接已建立（WSClient onReady）`）。
飞书命令作用域未启用（`FEISHU_MANAGEMENT_CHAT_IDS` 为空 ⇒ 放行全部命令）。

## 4. 单写者与状态

- 自动化写者锁：**单体持有**（`自动化写者锁已持有（target=dev）`）。
  ⇒ 派生 automation 进程在单体不停的前提下**起不来**（构造期抢锁、抢不到即拒启）。这是设计，不是缺陷。
- 账号归属条件写：`enforce`；冷启动配额爬坡：已禁用。
- schema 契约门：`enforce`，三个属主库全过（content 0069 / automation 0106 / api 0109）。

## 5. 边缘在线情况（采样时刻）

12 条边缘连接（sess-1…sess-12），各自 `welcome 后业务运行时已激活`。
⇒ 任何让单体重启的动作都会让这 12 条断连重连。
