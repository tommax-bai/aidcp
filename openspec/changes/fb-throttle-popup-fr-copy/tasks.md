# Tasks — fb-throttle-popup-fr-copy

> 词条纪律是硬约束（误报 = 账号迁入 `restricted`、钉住恢复窗、不自动回滚、只能人工恢复；漏报 = 维持现状）。
> 实装期若要增删任何词条，先回读 design.md 决策 2。

## 1. aidcp-automation — 云端限流词库

- [x] 1.1 `src/comm/facebook-throttle-signals.ts` 的 `normalize()` 补入去变音符一步（`normalize('NFD')` + 剥离 `U+0300–U+036F`），置于小写化之后、折叠空白之前；补注释说明三条失配路径（Unicode 等价形式 / 转录损耗 / 地区变体） <!-- aidcp-automation 1aebdc5 normalize() 补 NFD + 剥离 U+0300–U+036F -->
- [x] 1.2 `FB_THROTTLE_PHRASES` 补入两条法语词条（归一后 ASCII 形式）：`controle de securite est requis`、`cette fonctionnalite nest pas disponible`；注释注明 `est requis` 是必需限定（裸短语在安全设置页是功能名）、并注明显式排除申诉话术及其理由 <!-- aidcp-automation 1aebdc5 两条法语词条 + est requis 限定说明 + 申诉话术排除理由 -->
- [x] 1.3 `test/facebook-throttle-signal.test.ts` 补测试：① 锁法语词条集合字面量（与边缘逐条一致）；② 用带完整重音与撇号的真实法语原文断言命中；③ 用去重音转录版断言同样命中；④ 申诉话术单独一句断言不命中；⑤ 不带 `est requis` 的裸短语断言不命中；⑥ 既有英文与中文用例保持全绿（归一化未改行为） <!-- aidcp-automation 1aebdc5 24/24 绿；词库形状断言扩为「含变音符即失败」 -->

## 2. aidcp-edge — 边缘遮罩分类

- [x] 2.1 `src/facebook/overlay.ts` 新增 `FB_THROTTLE_FR_PHRASES` 常量数组（与云端逐条一致）+ 归一函数（小写 → 去撇号 → 去变音符 → 折叠空白），行为与云端 `normalize()` 一致 <!-- aidcp-edge 4ad96ee FB_THROTTLE_FR_PHRASES + normalizeLatin() -->
- [x] 2.2 把法语集合接入既有阻断判据分支（`:84` 的 `if`），与既有正则、中文频率集合并列为 OR 条件；**不改既有正则**（它跑在未归一的 `textLower` 上，引入归一会改变全部既有判据的输入面） <!-- aidcp-edge 4ad96ee 接入既有阻断分支；既有正则未动；抽 matchesLatinThrottlePhrase 只归一一次且保持惰性 -->
- [x] 2.3 `test/facebook/overlay.test.ts` 补测试：① 锁法语词条集合字面量；② 真实法语原文 + 普通群页 URL → 阻断态（今天是 `none`，此为本 change 的钉子断言）；③ 去重音转录版同样为阻断态；④ 申诉话术单独一句 → `none`；⑤ 不带 `est requis` 的裸短语 → `none`；⑥ 既有英文与中文用例保持全绿 <!-- aidcp-edge 4ad96ee 28/28 绿 -->

## 3. 跨仓一致性验证

- [x] 3.1 两侧法语词条集合逐字比对一致（人工核 + 两侧测试各自锁定） <!-- 两侧集合逐字一致，各自单测锁定 -->
- [x] 3.2 端到端复核：用真实法语原文跑一遍两侧现役函数，确认边缘判阻断态、云端词库命中（对齐英文版今天的行为），且英文版行为逐字不变 <!-- 部署后在 dev ECS 上调真函数直证：法语全文 true / 申诉话术 false / 安全设置页 false / 既有英文中文 true -->

## 4. 回归闸

- [x] 4.1 aidcp-automation：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（安全红线 `AC-RISK-*` 必过） <!-- aidcp-automation acceptance 305/305、全量 2431 pass 0 fail、typecheck 绿 -->
- [x] 4.2 aidcp-edge：`npm test` → `npm run test:acceptance` → `npm run typecheck` 全绿 <!-- aidcp-edge 全量 3247 pass 0 fail、acceptance 40/40、typecheck 绿、gate:native 绿 -->
- [x] 4.3 确认零协议改动（两份 `protocol.ts` 消息总数不变）、零 DB 迁移、零风控状态机改动 <!-- 零协议改动（协议对账闸绿，56 条登记表两仓一致）、零 DB 迁移、零风控状态机改动 -->

## 5. 集成与部署

- [x] 5.1 两仓各自 rebase 到最新默认分支、解冲突、跑回归闸后 ff 合并 <!-- aidcp-edge 5ec389a ff / aidcp-automation 1aebdc5 ff；均 rebase 后过全闸 -->
- [x] 5.2 aidcp-automation 按安全序列部署 `dev`（`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck） <!-- 2026-08-09 deployed dev：备份 automation.bak.20260809-204652.tar.gz + .env.bak.20260809；rsync -c 实测生产源码仅本 change 一个文件；stop-then-start（风控单写者）；schema 门 enforce/automation 通过（账本 0116）；三服务 active、8787/8090-8094 全在、写者锁已持有 -->
- [x] 5.3 aidcp-edge 收尾只到 commit / push（出安装包属用户显式触发，不进自动收尾）；在 tasks 中记明「运营机需 pull + 重建方生效」 <!-- aidcp-edge 只到 commit/push，未出安装包（用户长期授权：打包需显式触发）。**运营机需 pull + 重建客户端方生效** -->
- [x] 5.4 tasks.md 按仓回写 commit-sha 与偏离说明，格式 `<!-- <repo> <commit-sha> 备注 -->`；部署后追加 `<!-- <date> deployed -->` <!-- 本条即台账回写 -->

## 6. 真机验收登记（不阻塞码级实装）

- [x] 6.1 法语原文逐字坐实：真机 CDP 读一次法语界面下该弹窗的 `innerText`，核对两条词条是否命中；若 Facebook 实际用词不同（例如 `vérification` 而非 `contrôle`），按真实原文校正词条。失败方向安全（不命中 = 回落今天的静默行为），故不阻塞 <!-- 登记为真机项 91.8，不阻塞（失败方向安全：不命中=回落静默现状） -->
- [x] 6.2 登记入 `docs/real-machine-acceptance-backlog.md`，与既有 Facebook 环境簇合并（勿新开孤立簇） <!-- 并入既有簇 91（中文频率那次的同一 FB 环境与同一判据模块），未新开孤立簇 -->
- [x] 6.3 在 backlog 中一并登记待查项：该环境为何是法语界面（`facebook-locale-pin-en-us` 只作用于新建号指纹层，登录后界面语言由账号服务端设置决定）——属独立工作，本 change 不接管 <!-- 登记为 91.11 -->
