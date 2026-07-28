# Tasks

## 1. aidcp-cloud — 模板正文走"运营手写"校验通道

- [x] 1.1 `facebook-comment-validators.ts`：新增 `operatorAuthored` 上下文开关；开启时在结构闸之后直接放行，跳过链接 / 联系方式 / @提及 / 垃圾短语 / 相关性五条内容政策校验。 <!-- aidcp-cloud 61bd113 -->
- [x] 1.2 `comment-scheduler.ts`：模板模式（`cfg.commentMode === 'template'`）启用该通道；生成式路径逐字不变。 <!-- aidcp-cloud 61bd113 -->
- [x] 1.3 单测：模板带电话/链接/@/营销词 → 通过；相关性零重叠 → 通过；生成文同内容 → 仍拒；模板空/过短/过长 → 仍拒。 <!-- aidcp-cloud 61bd113 -->
- [x] 1.4 并发 change `facebook-rule-mode-two-tier-cadence` 新加的「规则批次 + 模板违禁内容 → 先拒」用例改用**超长正文**触发，守住原不变量（校验先拒、绝不提交、绝不报成功），并补一条「模板带链接/电话照发」对照。 <!-- aidcp-cloud 14263aa -->
- [x] 1.5 `npm run test:acceptance`（162 绿）→ `npm test`（3773 / 3762 绿 0 失败；集成时在 rebase 后的 3838 项上复跑亦全绿）→ `npm run typecheck` 全过。 <!-- aidcp-cloud 14263aa -->

## 2. aidcp-console — 模板编辑框按 `------` 分块

- [x] 2.1 新增 `src/utils/commentTemplates.ts`：按"只含 6+ 连字符的整行"分块，块内换行原样保留，去空去重；回填用 `\n------\n`。 <!-- aidcp-console a95dd82 -->
- [x] 2.2 账号评论模板编辑器改用该工具 + 提示文案同步。 <!-- aidcp-console a95dd82 -->
- [x] 2.3 区域通用模板编辑器改用该工具 + 提示文案同步。 <!-- aidcp-console a95dd82 -->
- [x] 2.4 单测：多行块=一条；`------` 分隔=两条；6+ 连字符与首尾空白同样生效、行内连字符不算分隔；空块/重复块丢弃；round-trip 等价。两个页面的既有用例同步改为块语义。 <!-- aidcp-console a95dd82 -->
- [x] 2.5 `npm test`（40 文件 / 272 项全绿）/ `npm run typecheck` / `npm run build` 全过。 <!-- aidcp-console a95dd82 -->

## 3. 部署与数据

- [x] 3.1 cloud 部署 dev：备份 → rsync `src/` → restart → healthcheck（active / 8787+8090 监听 / 飞书长连接 / 0 error）；ECS 标志物 `operatorAuthored` 两文件各 2 处。 <!-- 2026-07-28 deployed -->
- [x] 3.2 console 构建并部署 dev：备份并保留最近 10 份 → rsync `dist/` → index.html 引用的 css/js 资产逐个存在 → `http://127.0.0.1:8088/` 200。 <!-- 2026-07-28 deployed -->
- [ ] 3.3 **现存 5 条区域配置仍是 13 段碎片**（全国 / 北宁 / 北宁北江 / 北江 / 河南，内容相同），需合并为整段一条，否则仍随机发单行。
      两条路径任选：① 运营在后台把整段广告重新粘一次保存（新分隔符下即为一条）；② 直接改库合并
      （本次尝试被安全策略拦下，需用户明确授权）。

## 4. 验收

- [ ] 4.1 后台粘贴整段广告 → 保存 → 回填仍是整段（不被拆行）。
- [ ] 4.2 触发一次模板评论，`facebook_comment_audit` 的 `text_length` 接近整段长度（约 431）而非单行长度（如 26）。

## 5. 已知边界

- 模板长度上限仍是 500 字（`FB_COMMENT_PROFILE.maxCommentLength`）。用户当前广告 431 字可过但余量不大；
  再长会被 `too_long` 拒——这不是政策而是物理：边端拟人逐字输入，真机实测 431 字约 17.6 秒，
  平台步预算封顶 90 秒并预留 12 秒提交，过长必然打字超时而非发出去。
