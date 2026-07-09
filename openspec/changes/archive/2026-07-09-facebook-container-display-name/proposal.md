# Facebook 容器一律展示群名、不展示群 id

## Why

Facebook 定向评论的「容器」（运营方自己的 / 已加入的主页或群）此前在系统里以运营方粘贴的**原始字符串**存储（通常是含群 id 的链接，如 `https://www.facebook.com/groups/1109299026882957`）。管理后台、审计、飞书回执等**需要人工识别**的场景直接展示这个字符串——**群 id 对人不具有辨识度**，运营方无法一眼认出是哪个群。

## What Changes

容器从裸字符串升级为 `{ url, name }`：`url` 是功能主键（含群 id，边缘据此站内搜索），`name` 是**真实人类可读群名**，由**边缘在站内搜索时从群页自动读出**（og:title → 群头部 h1 → 清洗后的 document.title）并回传，云端把配置里 url 匹配的容器名自动回填。所有对人展示处（console 配置弹层、审计行、飞书回执）一律展示群名（尚未识别出时显示「待识别」占位），**绝不展示群 id / url**。

- **协议**：`page.cards` 增可选 `containerName?`（复用消息、零新增类型、消息计数不变）。
- **边缘**：`FacebookCommentExecutor.searchInContainer` 读容器真名回传；读不出诚实 undefined、绝不用 id 冒充。
- **云端**：容器配置模型 `string[]` → `FacebookContainer[]`（向后兼容裸 url 字符串）；新增 `resolveContainerName` best-effort 回填；调度器审计/回执用群名。
- **console**：容器编辑器存 `{url,name}`，运营方粘链接、标签展示群名（缺则「待识别」），保存保留已识别名。

向后兼容：历史裸 url 字符串配置自动 coerce 为 `{url}`（name 待首次搜索回填）；旧云端忽略 `containerName`。

## Impact

- Specs: `facebook-scheduled-comment`（容器语义：以 url 为功能主键、以自动解析的群名对人展示）。
- Code: aidcp-edge（executor/handler/protocol）、aidcp-cloud（config store/edge-steps/scheduler/panel/protocol）、aidcp-console（api/组件）。
- 无新增消息类型；对现役小红书零影响（仅 Facebook 容器配置）。
