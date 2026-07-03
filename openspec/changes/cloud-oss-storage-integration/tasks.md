# Tasks — cloud-oss-storage-integration

> 代码改动全落 aidcp-cloud。承回归纪律:改后先 `test:acceptance` 再全量 `test` 再 `typecheck`。真机验收解耦到 `docs/real-machine-acceptance-backlog.md`。标 **[需用户操作]** 的项需在阿里云控制台/ECS 完成。

## 1. aidcp-cloud — OSS 上传出口(可复用能力)

- [ ] 1.1 加依赖 `ali-oss`(^6.x)到 `package.json`
- [ ] 1.2 定义可注入接口 `ObjectStore { put(key, bytes, { contentType }): Promise<{ url }> }`(放 `src/publish-agent/` 或 `src/storage/`,与现有 provider 抽象同层)
- [ ] 1.3 实现 OSS 版 `ObjectStore`:内部持 `ali-oss` client(`authorizationV4:true`、region/bucket 来自配置);抓 provider 字节走注入的 `fetchImpl?: typeof fetch`(默认 `globalThis.fetch`,照 `wanxiang-client.ts:82-84`);上传时设对象公读 ACL + 正确 `Content-Type`;返回公网 endpoint 的稳定 URL
- [ ] 1.4 内容类型/扩展名判定:从 provider content-type 或字节 magic-byte 判 jpg/png/webp,拼进对象键 `publish/<accountId>/<recordId>/<seq>.<ext>`
- [ ] 1.5 上传 endpoint 策略:若 ECS 同在 `cn-beijing` 用内网 `oss-cn-beijing-internal.aliyuncs.com` 上传、URL 用公网 endpoint;region 非同区则上传也用公网(可 env 开关)

## 2. aidcp-cloud — OSS 凭据加载(照抄 DASHSCOPE 范式)

- [ ] 2.1 启动期在 `src/server.ts`(对齐 :247-250)加载 OSS 凭据:`getSecretForRuntime('oss','access_key_id') ?? readEnvString('OSS_ACCESS_KEY_ID')`,secret 同理;region/bucket 走 env(`OSS_REGION`/`OSS_BUCKET`,默认 `oss-cn-beijing`/`aidcp`)
- [ ] 2.2 凭据/配置齐备才构造 OSS `ObjectStore` 并注入;缺失则不注入(触发「未配置零回归」路径)。明文绝不日志化、绝不回前端
- [ ] 2.3 **[可选,可后置]** 若要 console 网页配 OSS 密钥:放宽 `isAllowedCredential`(`src/llm/providers.ts:66-68`)加 OSS 允许字段;否则不动,day-1 用 env / 直接 SQL 写 `provider_credentials`

## 3. aidcp-cloud — 接线到配图生成 + 诚实降级

- [ ] 3.1 给 `ImageGeneratorDeps`(`src/publish-agent/roles/image-generator.ts:28-39`)加**可选** `ossUploader?: ObjectStore`;构造点 `server.ts:1277-1283` 注入(未注入时行为同今天、零回归)
- [ ] 3.2 在 `generateOne`(`image-generator.ts:106-123`)`return res.url ?? null`(:115)前:若注入了 `ossUploader` 且拿到 provider url,则抓字节 → PUT OSS → 用 OSS URL 替换;转存失败(抓/PUT 任一)即返回 `null`,复用现有「失败那张不进数组、M=K 诚实计数」语义(:85-88),绝不伪造 URL
- [ ] 3.3 转存落在现有 per-image 超时/并发预算内,超时即该张诚实落空;不拖垮发布链

## 4. aidcp-cloud — 测试(守红线)

- [ ] 4.1 单测 OSS `ObjectStore`:注入假 `fetchImpl`,验 put 成功返 URL、抓字节失败/PUT 失败如实抛/返错(脱网)
- [ ] 4.2 单测 `image-generator` 转存:注入内存假 store，验成功替换为 OSS URL、失败该张落空且 M=K 诚实、未注入 uploader 时走原 provider URL 零回归
- [ ] 4.3 acceptance:补/复用「配图诚实」不变量守护——OSS 转存失败 MUST NOT 假成功/伪造 URL
- [ ] 4.4 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿

## 5. 部署与验证

- [ ] 5.1 **[需用户操作]** 桶 `aidcp` 确认可写;配图对象按公读(桶级公读或上传时对象级 `--acl public-read`)
- [ ] 5.2 **[需用户操作]** 在 ECS 设 OSS 凭据(env 写进 systemd 环境 或 直接 SQL 写 `provider_credentials` 的 `oss/access_key_id`、`oss/access_key_secret`);明文不进仓/文档
- [ ] 5.3 **[需用户操作/探测]** SSH 核 ECS 实际 region(定内/公网 endpoint);承部署安全序列(先备份 → rsync → restart → healthcheck)部署
- [ ] 5.4 **[真机验收 → backlog]** 在 `docs/real-machine-acceptance-backlog.md` 登记:真机发一帖,验 `publish_log` 存的是 `aidcp.oss-cn-beijing` URL、边缘从 OSS 下载并上传成功、张数诚实;并验「审批延迟后仍可下载」(过期根治)
- [ ] 5.5 全程确认未触碰同机 isales

## 6. 归档前

- [ ] 6.1 `openspec validate cloud-oss-storage-integration --strict` 通过
- [ ] 6.2 全部 task 标 `[x]` 附 commit-sha/偏离说明(`<!-- <repo> <sha> 备注 -->`;部署后追 `<!-- <date> deployed -->`)
- [ ] 6.3 archive 该 change
