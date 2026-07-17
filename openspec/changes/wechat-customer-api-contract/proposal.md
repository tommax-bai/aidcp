## Why

客户 API 的草稿保存路径在云端 100% 返回 404：冻结契约、契约文档与 Electron 客户端三方一致地使用五段路径 `PUT /environments/:envKey/replies/:jobId/draft`，云端只实现了四段版本，五段请求落到路由末尾报「接口不存在。」。后果是**人工改稿链路完全不可达**——客户编辑草稿点保存必失败，「改了稿再批准」会先内部触发保存、一并失败，只剩「原样批准」和「重新生成」两条路。云端是漂移方。

同一文件还把最长可达 180 秒的模型调用整个包在授权数据库事务里，全程持有授权行的共享锁，阻塞边缘状态上报与环境解绑；并发 regenerate 可打满默认 10 连接的共享池，令**全部租户**的互动接口一起超时。

更重要的是根因：**手工维护的双份 HTTP 契约 + 零路径级契约测试 = 主路径 100% 坏掉而测试全绿**。同一根因已中两次（客户端详情请求多带分页参数，主干 `4c45e48` 已修；本次草稿路径）。现有 customer-api 测试虽然起了真 HTTP server，却只覆盖列表与消息两条路径，其余冻结路径无人验证 URL 组装。不补一条覆盖全部冻结路径的契约测试，必有第三次。

## What Changes

- 修 `PUT /environments/:envKey/replies/:jobId/draft`：云端按冻结契约实现五段路径；**不放宽客户端**、不保留四段别名（四段从未在任何契约里出现）。
- 补一条**路径级契约测试**：对冻结契约里全部客户 API 路径，真拼 URL、打真 HTTP、断言 2xx（或契约规定的 409/422），任一路径退化成「接口不存在」即失败。这是本 change 的最高价值产出。
- 把冻结契约的路径清单落成一份机器可读的 `route-inventory.json`（控制仓契约目录为权威源，云端测试 fixture 镜像），让契约测试由清单驱动而非散落的 assert。
- 拆授权事务边界：授权事务只做鉴权与快速查询，**不得包住模型调用与外部往返**；长耗时业务在事务外执行，落库前用新的短事务复核 scope 并以 `expectedVersion` CAS 提交。
- 鉴权路径区分「结构上无权」与「暂时无法判定」：后者不得洗成 404「资源不存在」。
- 订正台账：`wechat-channels-interaction-management` 任务 3.6「完全按冻结契约实现客户 API」标了 `[x]` 属台账不实，本 change 一并订正。

本批 8 个 change 均不触碰 CLAUDE.md 列的四个热点文件（两份 protocol.ts、command-bridge 动作映射、RoleName+role-catalog、risk-state-machine.ts），故可全并行开发；集成仍串行（合回前 rebase + `test:acceptance` + `typecheck`）。

## Capabilities

### Modified Capabilities

- `client-customer-auth`: 客户 API 路径必须与冻结契约逐条一致并由契约测试覆盖；授权事务不得包住模型调用；鉴权失败必须区分结构性无权与暂时不可判定。
