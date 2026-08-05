# Tasks

> 事实基线：2026-08-05 dev 实测。接口进程 `panelDeps` 29 键 vs 单体 49 键；七处后台功能整页失败，两项静默能力缺失。
> 分类判据见 `design.md` §2（A 纯搬运 / B 单体已有 api 分支 / C 跨属主 / D 跨多域拼装）。

## 0. 开工前

- [ ] 0.1 `git worktree list` 确认四个派生仓 canonical 都停在 `master`，本 change 的四个 worktree 已建（`../aidcp-{api,automation,content,cloud}.wt/restore-panel-capability-wiring`）。
- [ ] 0.2 各 worktree 装依赖（内网 registry 会劫 `@types` 域，用 `npm ci --userconfig /dev/null --prefer-offline`）。
- [ ] 0.3 记下开工时 dev 的实测缺口清单（本文件顶部表），收尾时逐条复打对照。

## 1. aidcp-api — A 类：本进程属主，纯搬运遗漏

- [ ] 1.1 平台配置视图：在手写组装根里就地实现 `buildModelConfigView`（读本进程的模型配置存储 + 凭据存储 + kernel 厂商登记表），装上 `panelDeps.modelConfig.getView`。**MUST NOT** 复制单体那份跨段取用闸——它包的是历史位置，不是真跨域。
- [ ] 1.2 凭据写：装上 `setCredential`（主密钥缺失时 `{ok:false}` 诚实可辨，绝不假成功）。
- [ ] 1.3 角色配置外观：构造并装上 `roleConfig`（探活口先留占位，批次 3 接真探活；**在探活可用前 MUST 让写路径诚实拒绝，MUST NOT 放行不探活的写**）。
- [ ] 1.4 分类默认外观：同 1.3，装上 `categoryConfig`。
- [ ] 1.5 热帖引流：构造存储 + 外观，装上 `hotLeadConfig`。
- [ ] 1.6 FB 群评论策略：构造存储，装上 `facebookGroupCommentPolicy`。
- [ ] 1.7 视频号权限只读总览：由本进程的面板用户表 + 授权配置直接构造，装上 `interactionPermissions`。
- [ ] 1.8 四个新构造的存储进启动 `init()` 批，并确认镜像版本推送口（`mirrorVersionBumper`）与既有三张配置表口径一致。

## 2. aidcp-api — B 类：单体已有 api 分支，照搬

- [ ] 2.1 待审稿件正文编辑 `publishDraft`：照搬单体 `mode === 'api'` 那三个方法（编辑走本进程发布台账、活版本走台账读、已决判定走审批读客户端）。
- [ ] 2.2 发布预览变更通知 `notifyPublishPreviewChanged`：照搬 api 分支（经本进程的预览产出口推送；产出口缺席时按单体口径记一行告警，不静默）。
- [ ] 2.3 客户离场卡回调 `onClientOffboardCreated`：确认其产出方在本进程，装上；确认不了则记入具名缺席表并写清后果。

## 3. aidcp-content — C 类：内容域窄口

- [ ] 3.1 模型探活窄口：内容侧注册 `POST /internal/llm/probe`，出参判别式（`ok` / `provider_key_missing` / `model_invalid`），分类与单体 `probeModelResult` 逐字同源。
- [ ] 3.2 用量成本窄口：注册用量查询 + 账单价刷新两条，形状取自面板既有两个方法。
- [ ] 3.3 精选库窄口：注册列表 / 筛选面 / 删单条 / 清空壳行 / 读单行五条（`account_id` 一律进 WHERE 防越权，跨进程后这条 MUST 由属主侧保证，MUST NOT 交给调用方自觉）。
- [ ] 3.4 FB 发帖图片窄口：注册列表 / 上传 / 重排 / 改组 / 删组五条；**上传是大载荷**（单张原图上限 10 MiB、Base64 后约 14 MiB），跨进程连接的体积上限与超时须显式设置，MUST NOT 用默认值撞上限后回一个看不出原因的失败。

## 4. aidcp-automation — C 类：自动化域窄口

- [ ] 4.1 验证码协助窄口：注册面板五个端点所需的方法面（含短命图像字节；**图像 MUST NOT 落日志**，跨进程后这条约束在两侧都要成立）。
- [ ] 4.2 授权前置 `preflightApprovePublish` 窄口。
- [ ] 4.3 下发在途 id `publishDispatcher.getInFlightRecordIds` 窄口；若既有同步读镜像已覆盖，改为复用镜像并在本文件记明，不新开通道。

## 5. aidcp-cloud — 派生源：跨进程三件套与契约

- [ ] 5.1 新增 `src/transport/*-http.ts`：探活 / 用量 / 精选库 / FB 发帖图片 / 验证码协助 / 发布下发前置，各含路径常量 + 服务端注册 + 类型化客户端。路径常量**只此一份**。
- [ ] 5.2 面板契约 `src/panel/types.ts` 新增运行时能力名册 `PANEL_CAPABILITY_KEYS`，并用 `Exclude<keyof PanelDeps, 名册项> extends never` 钉死完备性。
- [ ] 5.3 新增覆盖断言工具：入参为 deps 对象 + 本进程具名缺席表，缺项即抛。
- [ ] 5.4 单体自身照旧编译通过、行为不变（新增的是 api 模式装配与新窄口，单体路径不改）。
- [ ] 5.5 控制仓 `scripts/sync-split-repos` 的 `TRANSPORT_MEMBERS` 登记新增 transport 文件；跑一次不带参数的对账确认六仓全绿。

## 6. aidcp-api — 接线跨进程客户端 + 打开写路径

- [ ] 6.1 装上内容侧四族客户端：`tokenUsage`、`billingPriceRefresh`、`curatedContent`、`curatedActions`、`facebookPublishMedia`。
- [ ] 6.2 装上自动化侧：`captchaAssist`、`preflightApprovePublish`、（如未复用镜像）`publishDispatcher`。
- [ ] 6.3 把 1.3 / 1.4 的探活占位换成真探活客户端；模型配置写路径同接。**三处写共用同一个探活口，MUST NOT 各写一份分类逻辑。**
- [ ] 6.4 装上覆盖断言（5.3），填本进程具名缺席表。

## 7. rolePromptPreview — D 类：分域拼装

- [ ] 7.1 坐实三段依赖各自的属主：预览角色清单（自动化）、人设（接口）、发布 / 配图渲染闭包表（内容）。
- [ ] 7.2 各域各出一段窄口，接口侧只做拼装。**MUST NOT 把渲染闭包表复制进接口仓**——第二份实现在行为测试上原理不可见。
- [ ] 7.3 若拼装成本与收益不成比例（该页只是只读预览），改为记入具名缺席表 + 登记 backlog，并在本文件写清判断依据与用户可见后果。**不得静默留 503。**

## 8. 测试

- [ ] 8.1 覆盖断言的单测：喂一个少装一项且未具名的 deps，断言抛错并指名；喂具名缺席的，断言放行。**闸恒真通过就没人能证明它还在**——用例必须包含违规输入。
- [ ] 8.2 能力名册完备性的编译期判据用例（漏项即红）。
- [ ] 8.3 探活不可用时三处写路径均拒写、且原因可区分于「模型不合法」「密钥缺失」。
- [ ] 8.4 精选库跨进程后账号隔离仍由属主侧保证的用例。
- [ ] 8.5 三仓 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；边界门禁 `boundaries` 相关用例不退化（豁免清单只准下降）。

## 9. 集成与部署

- [ ] 9.1 四仓各自 rebase 到最新 `master`、跑完 8.5、ff 合并。
- [ ] 9.2 `scripts/sync-split-repos` 对账全绿（含两个共享包的 pin）。
- [ ] 9.3 部署 dev：三个服务按依赖序重启（内容 / 自动化先起、接口后起），逐个健康口确认。
- [ ] 9.4 **逐条复打**顶部那张缺口表：每条记 200 / 具名缺席 / 仍失败，不得用「三进程起来了」代替。
- [ ] 9.5 后台真人走一遍：设置页、角色页、用量成本、精选库、配额页热帖引流、FB 群策略、验证码协助页。真机项收拢进 `docs/real-machine-acceptance-backlog.md`。

## 10. 收尾

- [ ] 10.1 回写 `deploy-derived-services-to-dev` 的 task 6.2：指向本 change，写明它本该抓住这批。
- [ ] 10.2 `openspec validate restore-panel-capability-wiring --strict` 通过后归档。
