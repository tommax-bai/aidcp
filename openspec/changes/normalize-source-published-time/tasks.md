## 1. Cloud 统一发布时间模型

- [x] 1.1 新增纯函数标准化模块与类型，覆盖相对时间、本地日历、跨年、非法日期、不可解析和精度语义
- [x] 1.2 重构热度帖龄计算复用标准化结果与事件观测锚，补齐 48 小时边界和 fail-closed 回归测试

## 2. Cloud 精选持久化

- [x] 2.1 为 `curated_content` 幂等新增来源发布时间五元组列，并扩展 store 输入、DB 行、内部 DTO 与原子 upsert 语义
- [x] 2.2 贯通模型准入和同访问机器人收藏补建的 `publishedAtText + event ts`，保证无新证据不擦除旧值
- [x] 2.3 扩展精选 store/evaluator/server 聚焦测试，覆盖 parsed、unparseable、历史 NULL、刷新保留与收藏补建

## 3. Cloud API 投影

- [x] 3.1 扩展面板精选 DTO 与客户鉴权列表/详情白名单投影，返回来源发布时间证据且保持账号隔离
- [x] 3.2 补齐面板 API 和 client-auth API 聚焦测试，确认旧行空值与跨账号拒绝语义

## 4. Edge 客户灵感库

- [x] 4.1 新增来源发布时间格式化 helper，让列表与详情按精度显示、不可解析显示原文、缺失显示“发布时间未知”
- [x] 4.2 更新 Electron 内容工作区测试，证明不再以 `updatedAt` 冒充原稿时间且旧 Cloud 响应兼容

## 5. Console 精选面板

- [x] 5.1 扩展 `PanelCuratedContent` 类型并在列表/详情如实展示原稿发布时间，同时保留独立更新时刻治理信息
- [x] 5.2 更新精选页面测试，覆盖日精度、不可解析原文和历史未知三态

## 6. 契约与验证

- [x] 6.1 更新 `docs/protocol.md` 的 Cloud 派生语义，确认 Edge/Cloud `NoteDetailPayload` 协议无漂移
- [x] 6.2 运行 Cloud 聚焦测试、相关安全回归、完整测试与 typecheck；运行 Edge/Console 聚焦测试与 typecheck
- [x] 6.3 回写各仓 commit、验证与偏差证据，并运行 `openspec validate normalize-source-published-time --strict`
  <!-- Cloud 618fc31: acceptance + 2764 pass / 8 gated skip + typecheck; Edge 643ae24: acceptance 28/28 + full 2129/2129 + typecheck; Console 546cd97: 35 files, 226 pass / 1 skip + typecheck + production build. Edge 真机与安装包不在本次范围。 -->

## 7. 集成与 dev 交付

- [x] 7.1 各业务仓基于最新默认分支 rebase、复验并 fast-forward 集成，提交并推送控制仓 OpenSpec
  <!-- land-change --yes fast-forward pushed Cloud 618fc31, Edge 643ae24, Console 546cd97 to origin/master; no force push. -->
- [x] 7.2 按 dev 门禁部署 Cloud 与 Console，验证 schema、HTTP 健康、服务 readiness 与静态资源；Edge 只推源码，不构建安装包
  <!-- dev deployed 2026-07-21: backups cloud.bak.20260721-073818Z.tar.gz, cloud/.env.bak.20260721-073818Z, console.bak.20260721-073818Z.tar.gz. aidcp-cloud active with NRestarts=0; 8787/8090/8091 listening; panel/client health 200 internally and publicly; all five curated source-published columns present; Feishu WS ready; console serves index-Che40Mg8.js; isales services remain active. -->
