# Tasks

## 1. 规范落地（文档 / 契约）

- [x] 1.1 spec delta：`deployment-environments` 新增「发布分支改动必须回流主干」需求（含工件指针例外与「回流不成必须登记」） <!-- aidcp (本 change) -->
- [x] 1.2 `CLAUDE.md` §6 加入该铁律（与「打包 fix 必 forward-port」同处收口，指向同一失效模式） <!-- aidcp (本 change) -->
- [x] 1.3 `docs/deployment-environments.md` 同步 <!-- aidcp (本 change) -->

## 2. 清偿存量（把已经搁浅的发布分支修复全部回流）

- [x] 2.1 edge `36fe38f`（建号环境归属客户：attach 必须 await，否则刚建的环境在随后刷新可见集时看不见）→ master `3a737e6`（冲突解决：master 已有 fire-and-forget 版，取其 await 版本） <!-- aidcp-edge 3a737e6 -->
- [x] 2.2 edge `5ee9d2d`（客户端「更新人设」按钮）→ master `2f69cc9`（**重新实现**：原提交叠在 `210f386` 上，与主干新的人设三态闸 9 处冲突，机械 cherry-pick 是错的工具） <!-- aidcp-edge 2f69cc9 -->
- [x] 2.3 edge `1300f5b`（FB 联系评论确认）→ 核验**内容已在主干**（补丁空应用），弃掉、不造空提交 <!-- verified 2026-07-14 -->
- [x] 2.4 edge `210f386`（人设弹窗竞态）→ 已被主干更强的三态不变量取代（其「自动弹出的窗在权威已绑到达时自动收起」行为已折入），无需再 port <!-- superseded by aidcp-edge 9761448 -->
- [x] 2.5 cloud `e36eddd`（token 记账读 PG env，否则 OL 连错库）→ master `7bae1e5` <!-- aidcp-cloud 7bae1e5 -->
- [x] 2.6 cloud `e2e9f88`（飞书群选项从已验证存储恢复）→ master `ecefe7c`（冲突解决：与主干新增的图片上传测试为干净 union） <!-- aidcp-cloud ecefe7c -->
- [x] 2.7 console `958384f`（FB 上传 nginx 限额）→ 核验**内容已在主干**，弃掉 <!-- verified 2026-07-14 -->
- [x] 2.8 回归：edge 1183 pass + acceptance 19、cloud 1940 pass + acceptance 50、双 typecheck 干净；两次 push 撞 non-ff 均 rebase 重来（未 force） <!-- 2026-07-14 -->

## 3. 工件指针（例外条款，需人工决策，未合并）

- [ ] 3.1 edge `e5a4d1d`（`package.json` → 0.3.20）：**不可照搬**。master 现有内容已超过 0.3.20，冒充 0.3.20 会让「同版本号、不同内容」的包流出去；正解是把 master 抬到 **0.3.21**（严格高于已分发版本）。待用户确认后执行。
- [ ] 3.2 console `7a1b718` / `88ce4c8`（下载页 0.3.18 → 0.3.19 → 0.3.20）：**不可照搬**。dev 的 `/opt/aidcp/downloads/` 里只有 0.3.18 的包，master 若指向 0.3.20，console 一部署到 dev 就会给出指向不存在文件的下载链接；而 master 停在 0.3.18 又会在部署 OL 时把线上下载页回退。根因是「版本号是部署态却被写死在源码里」。两条出路：① 把 0.3.19/0.3.20 的安装包同步到 dev 后再回流版本号；② 把下载页版本改为按环境读配置（不再进源码）。待用户定。

## 4. 后续（可选）

- [ ] 4.1 给「发布分支改动必须回流主干」加机械守卫：切下一个 release 分支前跑一次 `git cherry -v origin/master origin/release/<上一个>`，凡 `+` 必须逐条给出「已回流 / 已被取代 / 工件指针」的结论。可挂进 `scripts/` 与 `task-preflight` 同级的检查位（本 change 只立法，不实现）。
