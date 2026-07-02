## 1. aidcp-cloud — 探活确认厂商 thinking 参数（实装前置）

- [x] 1.1 `curl` DashScope compatible-mode 直探：确认 Qwen 系关思考键（`enable_thinking:false`）在非流式被接受、且 `enable_thinking:true` 非流式确会 400（坐实守卫前提）
- [x] 1.2 `curl` 直探 DashScope DeepSeek 系（deepseek-v4-flash）关 / 开思考的**精确参数键**（`enable_thinking` 是否通用，或需 `thinking` / `reasoning_effort`）、非流式可用性
- [x] 1.3 `curl` 火山方舟豆包直探 `thinking:{type:disabled|enabled}` 非流式可用性与返回结构（确认 `content` 干净、推理落 `reasoning_content`）
- [x] 1.4 把 1.1–1.3 结论记进本 change design.md 的 D3 翻译表（定稿参数键名）

## 2. aidcp-cloud — 存储层（role_config / category_config 加 thinking 列）

- [x] 2.1 `role-config-store.ts`：自愈加列 `thinking_mode TEXT`（`ADD COLUMN IF NOT EXISTS`，与 provider 列同模式）+ 同源 migration 文件
- [x] 2.2 `category-config-store.ts`：同样自愈加列 + 同源 migration
- [x] 2.3 两 store 的 reload / get / set 扩 `thinkingMode` 字段：读取归一（空 / 非法 → 视作未设）、写入只改传入字段、缺省不污染其它列
- [x] 2.4 store 单测：加列幂等、缺行 / 空值读为未设、写读往返、写思考模式不动 model/provider/temperature

## 3. aidcp-cloud — 解析器 + 出口翻译

- [x] 3.1 解析器新增 `getThinking(role?) → 'off' | 'on' | undefined`：role → category → undefined 两层回落，取自共享内存镜像（与 getModel 同源、热加载）
- [x] 3.2 `llm/qwen.ts`：新增纯函数 `buildThinkingParams(provider, model, mode)` → 返回要合并进请求体的附加字段；`default`/undefined → `{}`
- [x] 3.3 `buildThinkingParams` 实现 D3 规则：off（Qwen `enable_thinking:false` / DeepSeek 关键 / 豆包 disabled）；on（DeepSeek 开键 / 豆包 enabled；**Qwen+on → 空 + 告警一次**；未识别组合 on → 空，失败安全）
- [x] 3.4 `QwenClient` 构造期可选注入 `getThinking`；`chat()` 解析 mode 后合并 `buildThinkingParams` 结果进 body；**未注入 / default 时 body 与改造前逐字一致**；保持非流式 + 只读 content
- [x] 3.5 `server.ts`：把解析器的 `getThinking` 接进 QwenClient 构造（与 getModel/getProvider 并列）
- [x] 3.6 出口单测（注入假 fetch 断言 body 形状）：default 零回归；豆包 off/on；DeepSeek on；Qwen+on 兜底回落空 + 告警；未识别组合 on 失败安全

## 4. aidcp-cloud — 面板 API 读写

- [x] 4.1 `panel/types.ts`：角色目录 / 角色配置 / 分类配置读写类型加 `thinkingMode`（`'default'|'off'|'on'`）
- [x] 4.2 `role-config-facade.ts` / `category-config-facade.ts`：读回带 thinkingMode；写校验值 ∈ {default,off,on}，非法拒绝、缺省视作 default，写库成功再刷镜像
- [x] 4.3 `panel-server.ts`：对应 GET / PUT 路由透传 + 校验接线
- [x] 4.4 面板 API 单测：读回带、非法值被拒不落库、写库失败不污染镜像

## 5. aidcp-console — 前端三态控件

- [x] 5.1 `types/api.ts` + `api/queries.ts`：角色 / 分类配置类型与查询加 `thinkingMode`
- [x] 5.2 `pages/RolesPage.tsx`：每个文本角色行加思考模式三态控件（默认 / 关闭 / 开启），读写接后端
- [x] 5.3 Qwen 守卫：角色 / 分类**当前绑定 DashScope Qwen 模型**时，"开启"选项禁用 + 悬浮说明"需流式支持，暂不可用"
- [x] 5.4 分类默认页：分类级思考模式三态控件（同样带 Qwen+on 禁用逻辑）
- [x] 5.5 console `npm run typecheck` + `build` 通过

## 6. 回归 + 部署

- [x] 6.1 cloud：`npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`（安全红线 AC-PROTO/AC-PUB/AC-RISK 全过；新增 default 零回归断言必过）
- [x] 6.2 更新 `docs/protocol.md` 无关（本 change 不动协议）；确认无遗漏
- [x] 6.3 部署 cloud 走 §5 安全序列（备份 → rsync → restart → healthcheck → 失败回滚），绝不碰同机 isales
- [ ] 6.4 部署 console（发 /opt/aidcp/console，rsync 绝不 --delete）
- [x] 6.5 线上逐角色核验：设 off/on 后经 `llm_token_usage` / 日志确认翻译生效、Qwen+on 未 400；default 角色请求不变

<!-- 实装完成 2026-07-02：aidcp-cloud store/resolver/egress/panel + aidcp-console 前端全部落地；cloud npm test 1048/1048 绿、typecheck 绿；console tsc+vite build 绿。
     console 已提交并推送：aidcp-console e25e22e（api.ts + RolesPage.tsx，纯本功能两文件，干净切分）。
     参数键实测（1.1–1.3，2026-07-02 ECS curl）：DashScope `enable_thinking`（Qwen off=200；**on 非流式也=200、不报 400**——原"必须流式否则 400"假设被推翻，守卫仍 fail-safe 保留；DeepSeek off/on=200 非流式可用）；
       Ark `thinking:{type}`（豆包 off=200）。译表定稿在 llm/qwen.ts buildThinkingParams（design D3 已述）。
     部署 + 应用（6.3/6.5，2026-07-02）：cloud 从工作区 rsync 部署（连带并发 editable-account-group-label 未提交 WIP，健康检查全绿：active + 8787 + 飞书长连 + PG）；
       自愈加列 thinking_mode；写入设置——分类 browse_judge/browse_compose/publish_create/publish_gate=off、角色 publish:ContentScout/publish:ApprovalGatekeeper=on；
       线上 e2e 逐角色核验出口参数正确、全 200（curated 评估 deepseek 关思考后 685ms，原 ~30s）。回滚点 /opt/aidcp/cloud.bak.20260702-215923.tar.gz + config-backup-{cat,role}-20260702-215923.txt。
     仍未做：cloud git commit（生产领先于 git；工作区与 group-label WIP 交织，待其先提交后 thinking 再单独提交回填 sha）；6.4 console 部署（等 group-label 处理后再发）。 -->
