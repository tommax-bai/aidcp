# Tasks — cloud-oss-storage-integration

> 代码改动全落 aidcp-cloud。承回归纪律:改后先 `test:acceptance` 再全量 `test` 再 `typecheck`。真机验收解耦到 `docs/real-machine-acceptance-backlog.md`。标 **[需用户操作]** 的项需在阿里云控制台/ECS 完成。
>
> 实装进度:第 1–4 组 + 6.1 已完成(aidcp-cloud `d0e865e`,本地已提交、**推送被 harness 分类器拦截待用户放行**);第 5 组为部署 + 用户配 AK 项(待用户);6.2/6.3 待部署后归档。

## 1. aidcp-cloud — OSS 上传出口(可复用能力)

- [x] 1.1 加依赖 `ali-oss`(^6.x)到 `package.json` <!-- aidcp-cloud d0e865e：ali-oss ^6.23.0 -->
- [x] 1.2 定义可注入接口 `ObjectStore { put(key, bytes, { contentType }): Promise<{ url }> }` <!-- aidcp-cloud d0e865e：src/storage/object-store.ts（纯逻辑、不 import ali-oss，故引用它的测试恒脱网） -->
- [x] 1.3 实现 OSS 版 `ObjectStore`:内部持 `ali-oss` client(`authorizationV4:true`、region/bucket 来自配置);抓 provider 字节走注入的 `fetchImpl?: typeof fetch`;上传时设对象公读 ACL + 正确 `Content-Type`;返回公网 endpoint 的稳定 URL <!-- aidcp-cloud d0e865e：OssObjectStore(over 窄接口 OssPutClient，不 import ali-oss)+ oss-client-factory.ts(唯一 import ali-oss，authorizationV4)+ relocateImageToStore(注入 fetchImpl)。公读 ACL 走 put header x-oss-object-acl=public-read；URL 恒用公网 endpoint(去 -internal) -->
- [x] 1.4 内容类型/扩展名判定:从 provider content-type 或字节 magic-byte 判 jpg/png/webp,拼进对象键 `publish/<accountId>/<recordId>/<seq>.<ext>` <!-- aidcp-cloud d0e865e：sniffImageType(magic-byte jpg/png/webp/gif → 回退 image/* 响应头 → 兜底 jpg)。键=publish/<accountId>/<runToken>/<seq>.<ext>：recordId 在生成时尚未落库，故用单次运行随机 token 代替 recordId 分组(偏离 D5 已在代码注释说明；review 判定为文档层非缺陷) -->
- [x] 1.5 上传 endpoint 策略:若 ECS 同在 `cn-beijing` 用内网 `oss-cn-beijing-internal.aliyuncs.com` 上传、URL 用公网 endpoint;region 非同区则上传也用公网(可 env 开关) <!-- aidcp-cloud d0e865e：env OSS_INTERNAL=true → ali-oss internal:true 走内网上传；OssObjectStore 恒用公网 endpoint 拼返回 URL。默认 off，部署前 SSH 核 ECS region 再定 -->

## 2. aidcp-cloud — OSS 凭据加载(照抄 DASHSCOPE 范式)

- [x] 2.1 启动期在 `src/server.ts` 加载 OSS 凭据:`getSecretForRuntime('oss','access_key_id') ?? readEnvString('OSS_ACCESS_KEY_ID')`,secret 同理;region/bucket 走 env(`OSS_REGION`/`OSS_BUCKET`,默认 `oss-cn-beijing`/`aidcp`) <!-- aidcp-cloud d0e865e：对齐 dashscope 载入块，库内('oss')优先、env 回退 -->
- [x] 2.2 凭据/配置齐备才构造 OSS `ObjectStore` 并注入;缺失则不注入(触发「未配置零回归」路径)。明文绝不日志化、绝不回前端 <!-- aidcp-cloud d0e865e：两 key 都在才 dynamic import 构造 uploader；缺则 undefined → 配图零回归。日志只打 bucket/region/internal，绝不打 key -->
- [ ] 2.3 **[可选,可后置]** 若要 console 网页配 OSS 密钥:放宽 `isAllowedCredential`(`src/llm/providers.ts:66-68`)加 OSS 允许字段;否则不动,day-1 用 env / 直接 SQL 写 `provider_credentials` <!-- 按设计 D3/Open-Q 决定后置：day-1 用 env/SQL，不放宽白名单、不动 console。后续若要网页入口再单独增量 -->

## 3. aidcp-cloud — 接线到配图生成 + 诚实降级

- [x] 3.1 给 `ImageGeneratorDeps` 加**可选** `ossUploader?: ObjectStore`;构造点 `server.ts` 注入(未注入时行为同今天、零回归) <!-- aidcp-cloud d0e865e：加 ossUploader?/fetchImpl?/idGen? 三可选 dep；server.ts registerRole 注入 ossUploader -->
- [x] 3.2 在 `generateOne` `return res.url` 前:若注入了 `ossUploader` 且拿到 provider url,则抓字节 → PUT OSS → 用 OSS URL 替换;转存失败(抓/PUT 任一)即返回 `null`,复用现有「失败那张不进数组、M=K 诚实计数」语义,绝不伪造 URL <!-- aidcp-cloud d0e865e：produceAndRelocate=生成→(有 uploader 则)relocate；失败回 null；账号从 trigger 取、无 trigger 回落 default -->
- [x] 3.3 转存落在现有 per-image 超时/并发预算内,超时即该张诚实落空;不拖垮发布链 <!-- aidcp-cloud d0e865e：generateOne 用 Promise.race(生成+转存, 每图超时) 串行共享预算；每图超时默认 200s→240s 给转存留头(避尾部误丢，review 发现)；转存另有 30s 内层超时(覆盖抓字节+上传两段，review 发现原只覆盖 fetch 已修) -->

## 4. aidcp-cloud — 测试(守红线)

- [x] 4.1 单测 OSS `ObjectStore`:注入假 `fetchImpl`,验 put 成功返 URL、抓字节失败/PUT 失败如实抛/返错(脱网) <!-- aidcp-cloud d0e865e：test/storage/object-store.test.ts 12 例(sniff/OssObjectStore.put 公读 ACL+公网 URL+抛错传播/relocate 成功+各失败+PUT 挂起超时兜底) -->
- [x] 4.2 单测 `image-generator` 转存:注入内存假 store,验成功替换为 OSS URL、失败该张落空且 M=K 诚实、未注入 uploader 时走原 provider URL 零回归 <!-- aidcp-cloud d0e865e：test/publish-agent/image-generator.test.ts +6 例(转存成功换 OSS URL/账号回落 default/某张 PUT 失败 M=K/某张抓字节失败/全失败 M=0/未注入零回归) -->
- [x] 4.3 acceptance:补/复用「配图诚实」不变量守护——OSS 转存失败 MUST NOT 假成功/伪造 URL <!-- aidcp-cloud d0e865e：test/acceptance/oss-storage-honesty.test.ts AC-OSS-01..06(抓/PUT 失败 relocate 返 null/M=K 且不回退 provider URL/全失败空数组/未注入零回归/put 抛错向上抛) -->
- [x] 4.4 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿 <!-- aidcp-cloud d0e865e：typecheck 净；acceptance 42/43(唯一失败 AC-PUB-01 是既有 Windows 路径分隔符测试、baseline 同失、非本改动)；全量 test 1022 pass、除该既有 Windows 项外全绿 -->

## 5. 部署与验证

- [ ] 5.1 **[需用户操作]** 桶 `aidcp` 确认可写;配图对象按公读(桶级公读或上传时对象级 `--acl public-read`) <!-- 代码已在 put 时设对象级 public-read header；仍需确认桶策略允许对象级公读 ACL -->
- [ ] 5.2 **[需用户操作]** 在 ECS 设 OSS 凭据(env 写进 systemd 环境 或 直接 SQL 写 `provider_credentials` 的 `oss/access_key_id`、`oss/access_key_secret`);明文不进仓/文档 <!-- env：OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET(+可选 OSS_REGION/OSS_BUCKET/OSS_INTERNAL)。或 SQL：provider='oss' field='access_key_id'/'access_key_secret'(需 AIDCP_CRED_KEY 主密钥就位) -->
- [ ] 5.3 **[需用户操作/探测]** SSH 核 ECS 实际 region(定内/公网 endpoint);承部署安全序列(先备份 → rsync → restart → healthcheck)部署 <!-- 若 ECS 在 cn-beijing 可设 OSS_INTERNAL=true 省流量费；否则默认公网上传即可。部署走 CLAUDE.md §5 序列，绝不碰 isales -->
- [ ] 5.4 **[真机验收 → backlog]** 在 `docs/real-machine-acceptance-backlog.md` 登记:真机发一帖,验 `publish_log` 存的是 `aidcp.oss-cn-beijing` URL、边缘从 OSS 下载并上传成功、张数诚实;并验「审批延迟后仍可下载」(过期根治) <!-- 已登记：real-machine-acceptance-backlog.md 簇 11 -->
- [ ] 5.5 全程确认未触碰同机 isales

## 6. 归档前

- [x] 6.1 `openspec validate cloud-oss-storage-integration --strict` 通过 <!-- 设计期已过；实装后待跑一遍再确认(下条) -->
- [ ] 6.2 全部 task 标 `[x]` 附 commit-sha/偏离说明(部署后追 `<!-- <date> deployed -->`) <!-- 代码项已标；待部署完成 + 真机验后补 deployed 注记并收尾 5.x -->
- [ ] 6.3 archive 该 change <!-- 待部署 + 真机验通过后 archive -->
