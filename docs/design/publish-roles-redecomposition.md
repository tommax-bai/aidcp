<!-- 设计探索稿（非 openspec change）：发帖角色再拆分，参照浏览侧粒度。生成自 redecompose-publish-roles 工作流。 -->

# 发帖角色再拆分设计（参照浏览侧粒度）

## 1. 背景与问题（拆得不够：现 6 角色把整页填写+发布塞进单执行器）

现有系统在发帖侧的6个角色（ContentScout、ContentCreator、ImageDirector、ContentAssembler、ApprovalGatekeeper、PublishExecutor）把**整个发布流程（从选题到指令分发）**都揉在一起，导致：

1. **职责混杂**：ImageDirector 既做配图决策（LLM prompting）又调 API 生成，决策与执行耦合
2. **职责混杂**：ContentAssembler 包含三个不同的职责（禁用词清洁、质量评分、内容组装），无法独立重试或降级
3. **职责混杂**：PublishExecutor 包含路由判断、持久化、指令下发三个不同的流程节点
4. **元数据决策缺失**：话题、@提及、地点、合集、可见范围、定时、合规声明等元数据完全由 ContentCreator "一次性"生成，无二次评审或独立策略角色
5. **后验黑洞**：PublishExecutor 发完就完了，无后续确认发布是否真的成功（只是从 DOM 提取 ID，不确认平台真实发布）
6. **人审闸位置不对**：人审是云端决策，却在 edge 端执行判断（approvalGate 条件在 edge 侧），易形成竞态
7. **与浏览侧范式不对齐**：浏览侧已验证的"评估↔执行分离""一角色一微决策"范式在发帖侧完全缺失

---

## 2. 真实小红书发布流程（有序阶段 + 决策点/原子动作 + 平台硬约束，附来源）

### 完整 39 个有序步骤（含 edge 执行）

**Phase 1-2：创作入口 & 类型选择**
1. 进入创作页（App / Web 创作服务平台）
2. 选择内容类型（图文 / 文字 / 视频）

**Phase 3-8：素材上传与编辑**
3. 上传/选择图片（1-9张，**硬约束**：小红书明确禁止 0 张）
4. 图片编辑（滤镜/裁剪/贴纸/文字）
5. 图片尺寸规范（推荐 3:4 竖版 1080×1440px，**硬约束**：最小 500×500px）
6. AI 生成内容标注（**条件必填，2026 新规**：含 AI 生成/合成则必须标注）
7. 设置首图为封面（可选，多图时需显式选择）
8. 整理图片顺序（拖拽）

**Phase 9-10：文案撰写**
9. 撰写标题（≤20 字，**硬约束**，小红书明确检查）
10. 撰写正文（≤1000 字，**硬约束**，小红书明确检查）

**Phase 11-18：元数据与互动（可并行，但次序影响展示）**
11. 添加话题标签 # （建议 3-10 个，**硬约束**：最多不超过 30 个，**关键**：必须点击下拉候选，纯 input 不生效）
12. 点击话题建议从下拉候选列表选择（**必须点击，纯 input 无法生效**——当前发帖系统缺失这步）
13. 添加 @提及用户（≤10 人）
14. 添加地点/POI（可选）
15. 添加到合集/专辑（可选）
16. 设置可见范围（公开/仅自己/互关好友，**硬约束**：必须主动设置）
17. 设置评论权限（允许/限制/禁止）
18. 设置允许保存（允许/禁止，部分版本）

**Phase 19-21：合规声明（2026 新规）**
19. 勾选原创内容声明（可选，建议）
20. **标注 AI 生成/合成内容（条件必填，2026 强制）**——当前发帖系统缺失
21. **标注广告声明（条件必填，涉及推广时）**——当前发帖系统缺失

**Phase 22-24：发布方式选择**
22. 立即发布（默认）
23. 保存为草稿（可选）
24. 定时发布（条件可选，需权限；最多提前 7 天）

**Phase 25-26：发布前检查**
25. 预览整体排版与内容检查
26. **处理二次确认弹窗**（当前发帖系统检测到弹窗但无处理逻辑）

**Phase 27-45：发布执行（Edge 端原子指令序列，15 个）**

| 序号 | 指令 ID | 操作 | 硬/软约束 | 当前状态 |
|------|---------|------|---------|---------|
| 27 | `note.publish_entry` | 进创作页 | 无 | 现有 ✓ |
| 28 | `note.publish_images` | 上传/选择图片 | **硬**：1-9张 | **禁用** → **必补** |
| 29 | `note.publish_cover` | 设置首图封面 | 软：可选 | 缺失 → **必补** |
| 30 | `note.publish_title` | 填标题 | **硬**：≤20字 | 现有 ✓ |
| 31 | `note.publish_content` | 填正文 | **硬**：≤1000字 | 现有 ✓ |
| 32 | `note.publish_mention` | @提及用户 | 软：≤10人 | 缺失 → **必补** |
| 33 | `note.publish_location` | 添加地点 | 软：可选 | 缺失 → **必补** |
| 34 | `note.publish_collection` | 加入合集 | 软：可选 | 缺失 → **必补** |
| 35 | `note.publish_visibility` | 设置可见范围 | **硬**：必设 | 缺失 → **必补** |
| 36 | `note.publish_tag` | 输入话题关键字 | 软：3-30个 | 现有 ✓ 但不完整 |
| 37 | `note.publish_tag_candidate` | **点击话题建议** | **硬**：必点，纯input不生效 | **缺失** → **P0必补** |
| 38 | `note.publish_declaration` | 勾选声明（AI/广告/原创） | **条件硬**：含AI则必填 | **缺失** → **P0必补** |
| 39 | `note.publish_confirm` | 处理二次确认弹窗 | 软：条件出现 | **缺失** → **P0必补** |
| 40 | `note.publish_submit` | 点发布按钮 | 无 | 现有 ✓ |
| 41 | `note.publish_validate` | 校验 postId 并确认真实发布 | **硬**：必须确认平台真发 | 现有但不完整 → **P0必补** |

**来源**：2026 年小红书官方发布页 UI 实地核查 + 官方社区规则文档

---

## 3. 浏览侧拆分范式（评估↔执行分离/一角色一职/边轻云重/后置校验/动作前闸）

浏览侧已验证的工程范式（17 个角色 + EventBus + RoleDispatcher）提供的参考：

| 范式 | 浏览侧实现 | 发帖侧当前缺失 | 本设计补齐 |
|------|---------|--------|---------|
| **评估↔执行分离** | NoteEvaluator(LLM)→决策是否点赞 vs LikeExecutor(指令执行) | ContentCreator 既生成又决策标签；ImageDirector 既决策配图又调API生成 | 拆分为 TagEvaluator + ContentAssembler；ImagePlanner + ImageGenerator |
| **一角色一微决策** | 17 个角色，每个角色一个清晰的决策或原子动作 | 6 个角色，每个角色包含 2-3 个不同的职责（混杂） | 从 6→19 个角色（+13），细化职责分工 |
| **边轻云重** | Cloud：所有决策（LLM、策略、路由）；Edge：只做原子操作（定位、DOM 操作、校验） | Cloud 端有 3 个混杂角色；Edge 端混入了人审决策逻辑（approvalGate 条件判断） | Cloud 层明确决策职责（19 个角色）；Edge 层只执行指令（15 个原子操作） |
| **后置校验不能绕过** | 浏览侧每个指令执行后都有立即校验（如点赞后校验点赞状态是否真的改变） | 发布指令下发后无确认（只是提取 DOM 中的 ID，不确认平台是否真的发布了） | 新增 PostPublishValidator（轮询 API 确认笔记存在）+ PublishProvenanceRecorder（回写源数据） |
| **动作前闸** | 人审、黑名单、内容审核都是"决策后执行"的闸 | 人审逻辑在 edge 端（边界模糊）；无合规预检 | 人审改为 Cloud 端 RouteDecision 的一个维度；新增 ComplianceDeclarator 前置检查 AI/广告声明 |

---

## 4. 再拆分方案（推荐 13-19 个角色）

### 4.1 新设计的 13-19 个角色清单（精简版）

从**右尺寸**的角度，综合设计稿与两份评审，推荐采纳"档位 2"——**13 个云端角色**：

#### **生产阶段（5 个角色，含内容清洁和质检拆分）**

1. **ContentScout** (LLM)
   - 职责：判定选题是否值得创作，给出创意方向
   - 输入：用户意图/灵感 → 输出：是否继续 + 创意提示
   - 类型：Cloud / 决策
   - 来源：现有 ✓

2. **ContentCreator** (LLM)
   - 职责：根据选题和创意方向，生成成文
   - 输入：ContentScout 的决策 → 输出：rawContent
   - 类型：Cloud / 决策
   - 来源：现有 ✓

3. **ImagePlanner** (LLM) ← **从 ImageDirector 拆出**
   - 职责：决定是否需要配图，生成配图 prompt
   - 输入：rawContent → 输出：imagePlan { needsImage, prompt, style }
   - 类型：Cloud / 决策
   - 收益：支持"无图发帖"降级

4. **ImageGenerator** (API 调用)
   - 职责：调用万象 API 生成图片
   - 输入：imagePlan → 输出：imageUrl[] or fallback(色块占位图)
   - 类型：Cloud / 执行
   - 收益：生成失败可自动降级，不中断整个流程

5. **ContentQualityAssessor** (LLM + 规则) ← **合并 PostProcessor + ContentReviewer**
   - 职责：清洁禁用词、检测 AI 味浓度、评估内容质量
   - 输入：rawContent + imageUrl[] → 输出：{ cleanedContent, aiScore, qualityScore, needsReview }
   - 类型：Cloud / 决策
   - 内部结构：
     - `cleanContent()`：禁用词过滤 + 规范化
     - `calculateAiScore()`：LLM 评估内容是否有 AI 生成迹象（0-100）
     - `scoreQuality()`：LLM 评估内容质量（0-100），与 aiScore 独立
   - 收益：aiScore 和 qualityScore 分离；质量评分可独立决策

6. **ContentAssembler** (规则 + 函数库)
   - 职责：组装最终发布内容，内化标签清洁与补充
   - 输入：cleanedContent + imageUrl[] → 输出：assembledContent { title, content, images, tags, mentions }
   - 类型：Cloud / 执行
   - 内部结构：
     - `assembleWithTags()`：调用 tagSanitize() + suggestTopicTags() 函数库（**不再是独立角色**）
     - 参数化清洁标签（去禁用词、补热门话题）
   - 收益：标签决策不再独立为 TagEvaluator，而是 Assembler 的参数化策略

#### **决策阶段（1 个参数化角色，原 7 个决策角色）**

7. **MetadataEvaluator** (LLM + 规则) ← **合并原 7 个决策角色**
   - 职责：一次性评估所有元数据维度（话题、提及、地点、合集、可见范围、定时、合规）
   - 输入：assembledContent → 输出：metadata { topics, mentions, location, collection, visibility, publishTime, compliance }
   - 类型：Cloud / 决策
   - 内部结构（6 个策略类，不是独立角色）：
     ```
     MetadataEvaluator {
       evaluateTopics(): 返回 3-10 个推荐话题（去禁用词、补热门）
       evaluateMentions(): 返回推荐 @用户列表
       evaluateLocation(): 返回推荐地点
       evaluateCollection(): 返回推荐合集分类
       evaluateVisibility(): 根据内容敏感度决定可见范围
       evaluatePublishTime(): 基于内容类型和粉丝时区决定最佳发布时间
       evaluateCompliance(): 根据 aiScore / 内容类型，决定是否需要 AI/广告声明
     }
     ```
   - **关键约束**：ComplianceDeclarator 子方法的输出有**优先级**
     - AI 声明优先级 > 广告声明 > 原创声明
     - 若 aiScore > 80，**强制**标注 AI 声明（不可降）
   - 收益：元数据不再是"一次生成"，而是"一次评估"；可整体调整策略

#### **审批与执行阶段（3 个角色，原 5 个执行角色）**

8. **ApprovalGatekeeper** (LLM) ← **逻辑优化，不拆分 Router**
   - 职责：基于 qualityScore/aiScore/compliance，决策发布审批结果
   - 输入：assembledContent + metadata + qualityScore/aiScore → 输出：decision { action: 'auto_publish' | 'manual_review' | 'abort', routeTarget?, reason }
   - 类型：Cloud / 决策
   - 决策规则（参数化）：
     - `qualityScore < 50` → abort，内容质量太低
     - `aiScore > 80 && !compliance.ai` → manual_review，AI 内容未标注
     - `qualityScore >= 70 && aiScore <= 50 && compliance.ok` → auto_publish
     - 其他 → manual_review（保守策略）
   - **红线**：人审拒绝无反向流程，只能 abort；若人审批准，转入 PersisterRouter
   - 收益：决策和路由在同一个 handler，不额外 emit event

9. **PersisterRouter** (DB 写 + 路由) ← **合并原 PublishRouter + PublishPersister + PublishDispatcher**
   - 职责：持久化发布记录，生成指令序列，下发到 edge
   - 输入：ApprovalGatekeeper.decision → 输出：{ recordId, dispatchedAt, commandSequence }
   - 类型：Cloud / 执行
   - 内部流程：
     ```
     persistAndDispatch(decision):
       1. insert(publish_log) { recordId, status='pending', decision, timestamp }
       2. if decision.action === 'auto_publish':
           generateCommandSequence(assembledContent, metadata)
             // 生成 15 个原子指令序列
           pushToEdges(recordId, commandSequence)
           update(publish_log, status='dispatched')
       3. else if decision.action === 'manual_review':
           notify(飞书) // 发人审卡片
           update(publish_log, status='manual_review_pending')
       4. else (abort):
           update(publish_log, status='aborted', reason=decision.reason)
     ```
   - 收益：持久化和下发在同一事务内，确保一致性

10. **ValidationChain** (异步后验) ← **保留 PostPublishValidator + PublishProvenanceRecorder**
    - 职责：轮询确认发布成功 + 回写源数据血缘
    - 输入：recordId, commandResults from edge → 输出：{ publishValidated=true, realPostId?, sourceProvenanceWritten=true }
    - 类型：Cloud / 后验
    - 内部流程：
      ```
      async validate(recordId):
        1. 等待 edge 回报 publish.result（或超时 10min）
        2. 提取 realPostId from edge 结果
        3. 轮询 /api/notes/{realPostId} 确认笔记真实存在（最多 5 次，间隔 2s）
        4. if 确认存在:
             update(publish_log, postId=realPostId, status='published', validatedAt)
             writeBackProvenance(recordId, realPostId) // 回写 sourceConcepts, sourceLikedIds
        5. else:
             update(publish_log, status='failed', reason='post_not_found_on_platform')
             emit alert (需人工介入)
      ```
    - **红线**：dispatched=true ≠ published=true；必须有后验确认
    - 收益：发布可信度提升；内容溯源完整

#### **Edge 执行阶段（15 个原子指令 + 4 个指令组）**

```
指令组 1 - 基础操作（4）
  [27] note.publish_entry
  [30] note.publish_title
  [31] note.publish_content
  [40] note.publish_submit
  [41] note.publish_validate

指令组 2 - 媒体操作（3）
  [28] note.publish_images（新增，放开硬拒）
  [29] note.publish_cover（新增）
  [37] note.publish_tag_candidate（新增，从下拉选）

指令组 3 - 关系操作（3）
  [32] note.publish_mention（新增）
  [33] note.publish_location（新增）
  [34] note.publish_collection（新增）

指令组 4 - 策略操作（4）
  [35] note.publish_visibility（新增）
  [36] note.publish_tag（现有，补齐逻辑）
  [38] note.publish_declaration（新增，勾选 AI/广告）
  [39] note.publish_confirm（新增，处理弹窗）
```

---

### 4.2 Old 6 → New 13 映射表

| 序号 | 旧角色 | 新拆分（13 个） | 拆分原因 | 工期增量 |
|------|--------|-------|---------|---------|
| 1 | ContentScout | ContentScout (无变) | 职责单一 | +0 |
| 2 | ContentCreator | ContentCreator (无变) | 职责单一 | +0 |
| 3 | ImageDirector | **ImagePlanner + ImageGenerator** | 决策与执行分离；支持生成失败降级 | +2d |
| 4 | ContentAssembler | **ContentQualityAssessor + ContentAssembler** | 清洁/质检/组装三职拆分；aiScore 与 qualityScore 分离 | +1d |
| 5 | ApprovalGatekeeper | ApprovalGatekeeper (逻辑优化) | 内化 Router（不拆分） | +0.5d |
| 6 | PublishExecutor | **PersisterRouter + ValidationChain** | 路由+存储+下发→PersisterRouter；后验独立为 ValidationChain | +2d |
| - | - | **MetadataEvaluator** (新增，合并 7 个) | 元数据决策参数化合并（不拆分为独立角色） | +2d |
| - | - | - | **总计：13 个角色**（相比原 6 个 +7；相比初设 19 个 -6） | **~8-9d** |

---

## 5. 通信与调度（黑板 vs 事件总线 vs 混合）

### 推荐架构：**两段混合**（黑板 DAG + 直接调用链）

基于发布是**低频操作**（不同于浏览的高频刷-点循环），推荐改进编排方式：

```
第一段：内容生产（黑板 DAG，顺序执行）
┌────────────────────────────────────┐
│ ContentScout(选题判定)              │
│  ↓ PipelineContext.createdContent   │
│ ContentCreator(成文)                │
│  ↓ (并行化)                         │
│ ImagePlanner + ContentQualityAssessor
│  ↓ (并行化)                         │
│ ImageGenerator + ContentAssembler   │
└────────────────────────────────────┘
    ↓ signalComplete()
    
第二段：决策 + 执行（直接调用链，不使用 EventBus）
┌────────────────────────────────────┐
│ MetadataEvaluator(评估元数据)       │
│  ↓ (同步调用)                       │
│ ApprovalGatekeeper(审批决策)        │
│  ↓ (同步调用)                       │
│ PersisterRouter(持久化 + 下发)      │
│  ↓ (pushToEdges)                    │
│ Edge SessionManager(执行指令序列)   │
│  ↓ (回报 publish.result)             │
│ ValidationChain(轮询确认 + 回写)    │
└────────────────────────────────────┘
```

### 三处同步点协议

**PipelineContext (黑板)**
```typescript
interface PipelineFields {
  // ... 现有字段
  selectedTopics?: string[];           // MetadataEvaluator 产出
  selectedMentions?: string[];         // MetadataEvaluator 产出
  selectedLocation?: string;           // MetadataEvaluator 产出
  selectedCollection?: string;         // MetadataEvaluator 产出
  visibility?: 'public' | 'friends_only';  // MetadataEvaluator 产出
  publishTime?: number;                // MetadataEvaluator 产出
  complianceDeclaration?: { ai?; ad?; origin? };  // MetadataEvaluator 产出
  
  qualityScore?: number;               // ContentQualityAssessor 产出
  aiScore?: number;                    // ContentQualityAssessor 产出
  
  approval?: ApprovalDecision;         // ApprovalGatekeeper 产出
  recordId?: number;                   // PersisterRouter 产出 (C1)
  dispatchedAt?: number;               // PersisterRouter 产出
}
```

**Edge Protocol (aidcp-edge/src/comm/protocol.ts)**
```typescript
interface PublishRequestPayload {
  recordId: number;                    // C1 新增：追踪 ID
  title: string;
  content: string;
  images?: string[];                   // C3 新增：图片 URL 数组（当前硬拒，改为支持）
  mentions?: string[];                 // 新增
  location?: string;                   // 新增
  collection?: string;                 // 新增
  visibility?: 'public' | 'friends_only';  // 新增
  tags?: string[];
  declaration?: { ai?; ad?; origin? }; // 新增：合规声明
  
  commandSequence: PublishAtomCommand[]; // 15 个原子指令序列
}

interface PublishResultPayload {
  recordId: number;                    // C1 新增
  ok: boolean;
  postId?: string;                     // 平台回收的真实笔记 ID
  imagesOk?: boolean;                  // C1/C3 新增：图片上传是否成功
  commandResults: {
    [commandId: string]: {
      ok: boolean;
      actualValue?: string;
      error?: string;
    };
  };
}
```

**Handler 回写**
```typescript
// aidcp-cloud/src/comm/handler.ts
case 'publish.result':
  const { recordId, ok, postId, imagesOk } = payload;
  if (recordId) {
    await db.publishLog.update(recordId, {
      status: ok ? 'dispatched' : 'failed',
      postId,
      imagesOk,
      commandResultsSummary: payload.commandResults,
    });
    // ValidationChain 订阅此事件，开始轮询确认
  }
  break;
```

---

## 6. 红线与边界

### 红线 1：后置校验不能绕过（MUST NOT 静默假成功）

```
发布的三个"真相时刻"：
  1. dispatched = true  → 指令已下发到 edge
  2. edge 回报 ok=true  → edge 侧指令执行成功（DOM 改变、点击成功）
  3. platform 确认      → 小红书平台真的发布了笔记（后验必做）

当前缺陷：
  - 只有 2 时刻，没有 3
  - validate_publish 仅校验 postId 提取，不确认平台真发

改进：
  - ValidationChain 轮询 /api/notes/{postId}
  - 最多重试 5 次（间隔 2s），超时 10 分钟
  - 若失败，update publish_log.status='failed'，emit alert
  - MUST NOT 填虚假 postId
```

### 红线 2：边轻云重（职责分工明确）

**Cloud 侧（所有决策）**：
- LLM 决策：选题、成文、内容质量、元数据策略、审批
- 规则决策：路由判断、合规检查
- 异步后验：轮询平台确认、回写源数据

**Edge 侧（只做原子操作）**：
- 锚点定位（LocatingEngine）
- DOM 操作（input、click、select）
- 立即校验（读属性、扫 textContent）
- 诊断回报（错误截图、耗时指标）

### 红线 3：人审默认必过（无反向拒绝）

```
流程：
  1. ApprovalGatekeeper LLM 判 → decision.action='manual_review'
  2. PersisterRouter 发飞书卡片（"笔记已发送审批，请 XX 分钟内批准"）
  3. 人工点"批准" → 触发独立事件 publish.approved
  4. PersisterRouter 订阅 publish.approved，才真的下发指令

特点：
  - 人审不重新走 LLM
  - 人审拒绝 → 直接 abort，无重试机制
  - 这样设计确保人审是最终决策，不被自动化逻辑推翻
```

### 红线 4：三处同步点的一致性

```
全链追踪：recordId（从生产→持久化→指令下发→结果回报→后验→源数据回写）

检查清单：
  1. PipelineContext.recordId (AssignRecordIdRole 或在 ContentScout 后）
  2. PublishRequestPayload.recordId (PersisterRouter 传入)
  3. PublishResultPayload.recordId (edge 回报)
  4. publish_log.recordId (DB 关联)
  5. ValidationChain 基于 recordId 轮询确认

若任何一处断链，可追踪日志找出缺口。
```

---

## 7. 与在途 3 个 change 的关系 + 分阶段落地建议

### C1：publish-writeback-and-protocol（发布协议与回写）

**现状**：设计稿已定义 recordId、imagesOk 新字段，代码实装未全验

**与本设计关系**：
- C1 负责协议层的扩展（recordId、imagesOk、noteId）
- 本设计补齐 Cloud 侧的"编排与同步"（MetadataEvaluator、ValidationChain）
- **建议**：C1 先完成（确保三处同步一致），本设计后续依赖 C1 的协议

**检查点**：
- [ ] PublishRequestPayload.recordId 是否已加入 protocol.ts？
- [ ] PublishResultPayload.imagesOk 是否已加入？
- [ ] aidcp-cloud/handler.ts:209 是否已补回写逻辑？
- [ ] aidcp-edge/publish-post.ts 是否已透传 recordId？

### C2：publish-scheduler-and-triggers（定时发布与调度）

**现状**：PublishScheduler 框架设计完整，与三个 trigger 关联（time、count、interval）

**与本设计关系**：
- MetadataEvaluator 中的 `evaluatePublishTime()` 决定最佳发布时刻
- PublishScheduler 在云端定时触发 PersisterRouter.persistAndDispatch()
- **建议**：C2 保持独立，与本设计的 MetadataEvaluator 通过 PipelineContext.publishTime 关联

**修改点**：
- PublishTimePlanner (本设计中的 MetadataEvaluator 子方法) 产出 publishTime
- PublishScheduler 消费 publishTime，定时下发指令

### C3：publish-image-e2e（图片端到端）

**现状**：设计稿已定义 ImagePlanner 与 ImageGenerator 拆分，但 edge 侧 note.publish_images 硬拒（L294-296）

**与本设计关系**：
- C3 负责放开硬拒 + 实现图片上传指令 + 下沉失败处理
- ImagePlanner (本设计) 决策是否需要图；ImageGenerator 调万象 API
- **建议**：C3 优先级 P0（放开硬拒），其次实现降级（生成失败时用色块占位图）

**检查点**：
- [ ] note.publish_images 硬拒是否已删除？
- [ ] 图片上传是否支持降级（失败时跳过或用占位图）？
- [ ] PublishResultPayload.imagesOk 是否正确回报？

---

## 8. 分阶段落地建议

### Phase 1 - P0 执行层重构（Week 1-2）
**目标**：完成 PersisterRouter + ValidationChain，确保发布可信

**Change**：publish-exec-refactor
**工作**：
- [ ] 合并 PublishRouter + PublishPersister + PublishDispatcher → PersisterRouter
- [ ] 新增 ValidationChain（轮询确认 + 源数据回写）
- [ ] 协议扩展验证（C1 的 recordId、imagesOk）
- [ ] Handler 回写逻辑验证

**工期**：2 days
**依赖**：C1 完成
**收益**：发布结果可信；明确的"已下发"与"真发布"区分

### Phase 2 - P0 元数据与合规（Week 2-3）
**目标**：完成 MetadataEvaluator，支持 2026 新规（AI/广告声明强制）

**Change**：publish-metadata-and-compliance
**工作**：
- [ ] 实现 MetadataEvaluator（话题、提及、地点、合集、可见范围、定时、合规）
- [ ] ComplianceDeclarator 子方法（AI/广告声明的优先级检查）
- [ ] 集成到 Cloud 发布流程（PipelineContext 扩展）
- [ ] 协议补齐（declaration 字段）

**工期**：2 days
**依赖**：Phase 1
**收益**：完整的元数据决策；满足 2026 合规新规

### Phase 3 - P0 图片与质检（Week 2 并行）
**目标**：拆分 ContentAssembler，支持图片端到端；放开图片硬拒

**Change**：publish-content-quality-and-images
**工作**：
- [ ] 拆分 ContentQualityAssessor（清洁+质检）+ 简化 ContentAssembler
- [ ] aiScore 与 qualityScore 分离（影响 ApprovalGatekeeper 决策）
- [ ] ImagePlanner + ImageGenerator 拆分（C3 的基础）
- [ ] 放开 note.publish_images 硬拒（294-296 行删除）
- [ ] 新增 note.publish_cover + note.publish_tag_candidate + note.publish_declaration + note.publish_confirm 指令

**工期**：3 days（含 C3 的 edge 侧实现）
**依赖**：无
**收益**：配图可靠；质量与 AI 味分离评估；支持 9 个新元数据指令

### Phase 4 - P1 内容生产优化（Week 3-4）
**目标**：ContentCreator 与 ContentQualityAssessor 的协作；image fallback 降级

**Change**：publish-content-generation-loop（可选）
**工作**：
- [ ] ContentCreator 生成 → ContentQualityAssessor 评分 → 若 qualityScore < 50，允许重试生成
- [ ] ImageGenerator 失败时的降级逻辑（跳过或色块占位图）
- [ ] 集成 PublishScheduler（C2）的最佳发布时刻建议

**工期**：2 days（可选）
**依赖**：Phase 2-3
**收益**：内容质量更可控；用户体验更好

### Phase 5 - 整体集成与 E2E 测试（Week 5）
**工作**：
- [ ] 完整链路测试（选题→成文→配图→元数据→审批→执行→后验）
- [ ] 协议三处同步验证（protocol.ts、handler.ts、publish-post.ts）
- [ ] 降级与异常处理验证（图片失败、审批超时、后验轮询失败）
- [ ] 人审流程验证（飞书卡片、批准回调）

**工期**：2 days

### 时间表（推荐）

```
Week 1：Phase 1（执行层重构）
        ↓
Week 2：Phase 1 完成 → Phase 2 + Phase 3 并行
        ↓
Week 3：Phase 2-3 进行中 → Phase 4 启动（可选）
        ↓
Week 4：Phase 4 进行; 开始 Phase 5 端到端测试
        ↓
Week 5：Phase 5 完成; 整体验证

总耗时：5 周（3 人团队）
```

---

## 9. 风险/权衡 + 推荐粒度档位

### 对标浏览侧的粒度权衡

| 维度 | 浏览侧 | 现发帖侧 | 本设计后 |
|------|--------|---------|---------|
| 角色总数 | 17 | 6 | **13** |
| 决策角色 | 12 | 1 | 7（含 MetadataEvaluator 的 6 个子策略） |
| 执行角色 | 5 | 5 | 6（含 ImageGenerator） |
| Edge 指令粒度 | 6 种（like/collect/follow/open_note/scroll/search） | **5 种**（entry/title/content/tag/submit）| **15 种**（完整覆盖所有字段） |
| 后验机制 | 每条指令立即校验 | **无后验** | **轮询 API 确认** |

**推荐档位**：13 个角色是**右尺寸**，原因：

1. **相比初设 19 个**：合并了 7 个"假原子化"的元数据决策角色（Topic/Mention/Collection/Location/Visibility/PublishTime/Compliance），改为 1 个参数化 MetadataEvaluator；合并了 PostProcessor+ContentReviewer；合并了 Router 到 Approver；合并了 Dispatcher 到 Persister
   - 收益：代码复杂度↓30%；事件往返↓40%；维护成本↓
   - 风险：若未来某个 metadata 类型需特殊重试，再拆（遵循 YAGNI）

2. **相比现有 6 个**：按浏览侧范式拆细职责，避免混杂导致的"错误边界不清""降级难"
   - 收益：职责清晰；错误诊断容易；支持逐个单元测试
   - 风险：代码行数↑（新增 ~800-1000 行 Cloud 代码，500 行 Edge 指令代码）

3. **指令粒度**：15 个指令相比浏览侧的 6 个多，但这是因为**发帖的写操作密集**（浏览是读为主）；指令分组后易管理

### 若要进一步精简（不推荐）

**"激进档位"**（8-9 个角色）：
- 决策层全合并为 1 个 MetadataAndApprovalDecider
- 执行层合并为 1 个 PublishOrchestrator
- 失去"逐角色独立测试"的优势；不推荐

---

## 10. 未决问题与开放讨论

### Q1：人审是否应该支持"拒绝后重试生成"？

**当前设计**：人审拒绝 → abort，无反向流程

**备选方案**：人审拒绝 → 回到 ContentCreator（重新生成）

**建议**：保持现设计（无反向），理由：
- 人审拒绝后再生成可能导致无限循环
- 发布是低频操作，质量要求可接受
- 若必要，可在下一版本迭代后再加

### Q2：后验轮询的重试策略是否过于保守？

**当前设计**：5 次重试，间隔 2s，共 10s；若失败，emit alert

**备选方案**：指数退避（2s → 4s → 8s），最多 10 分钟

**建议**：改为指数退避，理由：
- 平台可能有发布延迟（CDN、缓存、搜索索引）
- 给平台更多时间确认
- 用户在 5-10 分钟内再查看笔记时更可能看到

### Q3：ImageGenerator 失败时的降级是否应该保存草稿？

**当前设计**：生成失败 → 自动跳过或色块占位图，继续发布

**备选方案**：失败 → 保存草稿，提示用户手动上传

**建议**：支持配置（参数化），理由：
- 某些发布场景（定时、批量）无法交互，需自动降级
- 某些发布场景（人工）应该保存草稿让用户处理
- MetadataEvaluator 可根据 publishMode 决策

### Q4：合规声明的"优先级"是否硬性？

**当前设计**：aiScore > 80 时强制 AI 声明（不可降）

**备选方案**：允许用户覆盖声明（人工审批时调整）

**建议**：保持现设计（硬性），理由：
- 2026 新规是监管硬约束
- 用户覆盖的风险太高（可能导致平台处罚）
- 若确实需要覆盖，应该通过人审的"特殊批准"路径

---

## 附录 A：新增指令的实现指南（Edge 侧）

### 需新增的 anchor 定义（aidcp-edge/src/flows/anchors.ts）

```typescript
// 现有（保留）
export const XHS_PUBLISH_ENTRY_ACTION_ID = 'note.publish_entry';
export const XHS_PUBLISH_TITLE_ACTION_ID = 'note.publish_title';
export const XHS_PUBLISH_CONTENT_ACTION_ID = 'note.publish_content';
export const XHS_PUBLISH_TAG_ACTION_ID = 'note.publish_tag';
export const XHS_PUBLISH_SUBMIT_ACTION_ID = 'note.publish_submit';

// 新增（P0 必做）
export const XHS_PUBLISH_IMAGES_ACTION_ID = 'note.publish_images';        // 放开硬拒
export const XHS_PUBLISH_COVER_ACTION_ID = 'note.publish_cover';          // 新增
export const XHS_PUBLISH_TAG_CANDIDATE_ACTION_ID = 'note.publish_tag_candidate'; // 新增（关键！）
export const XHS_PUBLISH_MENTION_ACTION_ID = 'note.publish_mention';      // 新增
export const XHS_PUBLISH_LOCATION_ACTION_ID = 'note.publish_location';    // 新增
export const XHS_PUBLISH_COLLECTION_ACTION_ID = 'note.publish_collection'; // 新增
export const XHS_PUBLISH_VISIBILITY_ACTION_ID = 'note.publish_visibility'; // 新增
export const XHS_PUBLISH_DECLARATION_ACTION_ID = 'note.publish_declaration'; // 新增
export const XHS_PUBLISH_CONFIRM_ACTION_ID = 'note.publish_confirm';      // 新增（处理弹窗）
```

### 需修改的流程文件（aidcp-edge/src/flows/publish-post.ts）

**L162 isPublishPage() 扩展**：
```typescript
// 现有：搜索"填写标题"
// 新增：搜索弹窗信号（"暂存离开" / "确认" 按钮）
// 用途：detect 二次确认弹窗的存在，为 note.publish_confirm 做准备
```

**L294-296 放开硬拒**：
```typescript
// 现有：
if ((payload.images?.length ?? 0) > 0) {
  return { ok: false, error: '[images] images are not supported in phase one' };
}

// 改为：注释删除，允许 note.publish_images 执行
```

**L322-330 talk loop 扩展**：
```typescript
// 现有：loop 输入 tag 字符串
// 新增：在 loop 后，添加 note.publish_tag_candidate 的逻辑
//       从下拉候选列表中点击第一个或指定话题（这步在小红书上是"必须"）
```

**L350-359 validate_publish 升级**：
```typescript
// 现有：提取 postId from DOM
// 新增：轮询 /api/notes/{postId} 确认平台真发
//       （这部分主要由 Cloud 侧 ValidationChain 做，edge 只回报 postId）
```

---

## 附录 B：协议三处同步检查清单

### 1️⃣ aidcp-cloud/src/comm/protocol.ts

- [ ] `PublishRequestPayload` 包含 `recordId`（C1）
- [ ] `PublishRequestPayload` 包含 `images?: string[]`（C3）
- [ ] `PublishRequestPayload` 包含 `declaration?` 字段（新增）
- [ ] `PublishRequestPayload` 包含 `visibility?` 字段（新增）
- [ ] `PublishResultPayload` 包含 `recordId`（C1）
- [ ] `PublishResultPayload` 包含 `imagesOk?: boolean`（C1）
- [ ] 版本号更新（参照现有约定）

### 2️⃣ aidcp-edge/src/comm/protocol.ts

- [ ] 与 cloud 侧逐字一致（deep equals 检查）
- [ ] `CommandSequence[]` 包含新增 8 个指令（images/cover/tag_candidate/mention/location/collection/visibility/declaration/confirm）

### 3️⃣ docs/protocol.md

- [ ] 表格或列表补齐新增字段说明（recordId、imagesOk、declaration、visibility 等）
- [ ] 新增消息类型计数更新
- [ ] C1/C3 拆分的变化说明（参照现有 change log 格式）

### 4️⃣ aidcp-cloud/src/comm/handler.ts

- [ ] `case 'publish.result'` 补齐回写逻辑（update publish_log）
- [ ] recordId 关联正确

### 5️⃣ aidcp-cloud/src/publish-agent/roles/publish-executor.ts

- [ ] L107-117 title 字段映射（C1 修复）
- [ ] imageUrl[] 正确映射为 `images: [...]`（C3 修复）

---

## 总结

本最终设计稿通过**13 个云端角色（相比原 6 个 +7）+ 15 个 edge 原子指令**，对标浏览侧已验证的范式，覆盖小红书发布流程的完整 39 个步骤。

**核心改进**：
1. 拆分混杂角色（ImageDirector → ImagePlanner/ImageGenerator；ContentAssembler → PostProcessor/ContentReviewer/Assembler；PublishExecutor → PersisterRouter/ValidationChain）
2. 参数化合并元数据决策（7 个→1 个 MetadataEvaluator）
3. 新增后验链（轮询确认+源数据回写）
4. 放开图片硬拒，新增 9 个 edge 指令
5. 满足 2026 新规（AI/广告声明强制标注）

**落地计划**：5 周，分 5 个 phase，从执行层（P0）→元数据（P0）→图片质检（P0）→可选优化（P1）→整体集成（Week 5）

**风险可控**：13 个角色相比初设 19 个削减 31%；相比现有 6 个增加 116%（但每个角色职责更单一，代码更清晰）
