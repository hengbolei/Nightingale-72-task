# Nightingale 72 小时任务：项目防偏题指南

> 本文件是项目实施期间的“北极星”和验收清单。每次设计、开发、测试和录制 Demo 前后，都应回到这里确认没有偏离题目。后续还需补充实际项目的安装、运行、测试、架构与性能测量说明。

## 1. 一句话目标

构建一个诊所级、单患者单页的共享纵向 Care Note Web 应用：把患者提供的信息、员工与临床人员笔记、任务以及三类 AI 记录整合成一个可协作、可追溯、可审计且严格按角色隔离的可靠记录，并让临床人员在 10 秒内从 Glance/Top Card 看懂最重要且可行动的信息。

这不是一个通用 Notion 页面，也不只是 AI 摘要工具。产品核心是：

1. 用纵向记录解决跨就诊信息碎片化；
2. 用协作能力让不同角色围绕同一患者记录工作；
3. 用来源引用、版本历史和冲突规则建立信任；
4. 用服务端权限与脱敏流程保障安全；
5. 用克制的优先级逻辑降低临床认知负担。

## 2. 最高优先级的产品体验

### 2.1 Glance / Top Card

必须让 clinician 或 staff 在 10 秒内读懂并采取行动，至少呈现：

- 最重要的临床信息；
- 未完成行动，例如待开化验单、待护士跟进；
- 关键风险或警示；
- 每个 highlight 的简短 `risk_reason`；
- 每个 highlight 的 `provenance_pointer`；
- 点击 highlight 后跳转到 Timeline 中的准确来源 entry/span。

设计判断标准：少而重要、可解释、可操作，不用大量卡片制造“信息很丰富”的假象。

### 2.2 Longitudinal Timeline

为每位患者提供按时间排序的连续上下文流，补充传统 EHR 的结构化快照。必须清楚区分：

- patient / AI patient session summary；
- AI doctor-patient consult summary；
- AI nurse-patient consult summary；
- staff 手工笔记或编辑；
- clinician 手工笔记或编辑；
- system event。

每条 Entry 至少要有：

- `author_role`：patient / staff / clinician / system；
- `author_id`：AI 生成时可为 system；
- `timestamp`；
- `type`；
- `provenance_pointer`：指向原始消息、会话或具体来源。

三类 AI-scribed note 必须是独立 Timeline Entry，不能伪装成 clinician/staff 手工笔记：

- `ai_doctor_consult_summary`；
- `ai_nurse_consult_summary`；
- `ai_patient_session_summary`。

### 2.3 协作、版本与审计

必须支持：

- 笔记内协作编辑与批注；
- threaded comments，并有 resolve/unresolve 状态；
- 可以实现 `@mention` 与 assignment；
- 每次编辑产生完整版本快照或 diff；
- 查看自某版本以来的变化；
- 回退至任意历史版本；
- audit log 能回答谁在何时改了什么，但日志只保存必要 metadata，不能泄漏敏感正文；
- 不同角色并发编辑不同 section 时互不覆盖；
- 同一 section 冲突时采用可重复、可解释的确定性策略。

## 3. 信任与来源是硬要求

任何重要信息，尤其是 highlight，都必须可引用、可点击并可追溯到 Timeline 的具体 entry/span。原始 Entry 是 source of truth。

冲突处理必须明确：

- clinician 的后续判断优先于此前的 AI/patient memory；或
- 系统明确标记冲突并要求人工审核。

AI 内容必须始终显示其系统来源和原会话引用。不要让 UI 暗示 AI 结论已经得到临床确认。建议用状态区分：AI suggested、clinician confirmed、rejected/needs review。

## 4. RBAC 与数据隔离（必须服务端执行）

角色与最低权限：

| 角色 | 可以 | 不可以 |
| --- | --- | --- |
| Patient | 查看面向患者的摘要和医嘱 | 查看内部 staff/clinician comments；查看 raw AI-scribed notes |
| Staff | 查看和新增 staff notes；在本诊所范围协作 | 访问其他诊所患者；写入或覆盖 clinician notes |
| Clinician | 查看/编辑 clinician sections；查看 staff notes 与全部 AI notes | 访问其他诊所患者；覆盖 staff notes |
| Admin | 在所属诊所范围内监督患者数据 | 跨越其 clinic scope |

不可只通过隐藏按钮实现权限。所有读取、写入、修改和跨 clinic 查询必须由 RLS、middleware 或 backend checks 强制验证。尤其要证明：clinician 不能以 staff 身份改笔记，staff 不能覆盖 clinician section，patient 无法通过 API 获得内部内容。

## 5. 隐私、安全与性能硬约束

- 只使用 synthetic data，绝不使用真实 PHI；
- 所有发给 LLM 的数据流，必须先脱敏姓名、IC/ID 号码和手机号；
- 文档原文中的 “No PHI Redaction Pipeline” 结合后文要求，应理解为“不得向 LLM 泄漏 PHI，必须有 PHI redaction pipeline”；
- TLS in transit；
- encryption at rest；
- 日志保持干净，不写入敏感正文；
- warm path 加载 consult Glance View 的 P95 必须 `<= 300 ms`；
- Technical Brief 中必须说明性能测量或估算方法、数据量、环境和结果。

## 6. Highlight / Importance Logic

基础优先级建议至少结合：

- recency；
- 显式 `risk_level`；
- 临床实体，例如药物、主诉、过敏；
- unresolved tasks；
- clinician-confirmed 内容应高于未经确认的 AI 建议。

必须保证：

- 建议可快速 accept/reject；
- 每条建议有短 `risk_reason`；
- 每条建议有可解析的 `provenance_pointer`；
- 排序结果可解释，避免黑箱式“AI 认为重要”。

### 加分：Self-Learning

根据 clinician/staff 的 pin、highlight、edit、comment、accept/reject 等交互，逐步提高相似主题、关键词或 AI note section 的未来优先级。实现时应保留反馈证据和可解释权重，避免模型绕开人工确认自动改变临床事实。

### 加分：Hybrid Storage / Data Decay

为旧数据设计压缩或分层存储策略，但不能破坏版本、审计和 provenance。旧且低价值内容可以降级或摘要化；高风险、被确认、未完成任务以及引用源不能因“衰减”而丢失。

## 7. 自动化微测试：交付前必须全部通过

文件名应与要求一致，并在最终 README 中写明运行方式。

### `test_rbac_scope.py`

- staff 与 clinician 不能以对方身份写入或修改笔记；
- patient 无法访问 internal comments 或 raw AI-scribed notes；
- 建议额外覆盖跨 clinic 读取与写入拒绝。

### `test_revision_history.py`

- 编辑后版本号递增；
- revert 后正文恢复到目标历史状态；
- audit log 包含变更人和变更 metadata。

### `test_highlight_provenance.py`

- 可从人工与 AI-scribed entries 生成 highlights；
- 每条 highlight 都有 `provenance_pointer`；
- pointer 能解析到 Timeline 中实际存在的 entry/span。

### `test_concurrent_edits.py`

- 两个角色并发编辑不同 sections 时不会相互覆盖；
- 同一 section 冲突时结果符合既定的确定性解决策略。

### 加分：`test_self_learning_importance.py`

- 模拟用户 pin 一个 AI note highlight；
- 相似内容后续建议的 priority 可观察地提高；
- 若只做概念测试，要明确输入、反馈信号、权重变化和预期输出。

## 8. 必需交付物

### Git Repository

- 可运行应用；
- 规定的自动化测试；
- 清晰 commit history；
- README：安装、启动、测试、脱敏发生位置、RBAC 服务端执行方式、性能测试方法。

### 2–3 页 Technical Brief

- 架构图与说明；
- 完整数据 schema；
- 清楚展示 `Entries ↔ Comments ↔ Versions ↔ Highlights ↔ Provenance ↔ AI_Scribed_Notes` 的关系；
- 如实现学习机制，说明 feedback 与 importance logic 的连接；
- assumptions、first-principles reasoning、trade-offs 和主动缩减的 scope；
- P95 Glance 性能测量/估算。

### 其他

- `ATTRIBUTION.txt`：外部 libraries、models 及其 licenses；
- Demo Video：清晰展示选定场景；
- Resume；
- WhatsApp number；
- WeChat ID。

## 9. Demo 必须形成的故事线

### Scenario A：Glance 与 AI Scribe

1. Staff 打开患者页；
2. 10 秒内理解 Top Card；
3. 点击一条来自 AI-scribed note 的 highlight；
4. 准确跳到 Timeline 的来源 entry/span。

### Scenario B：协作、审计与学习

1. Staff 添加 note 和带 `@clinician` 的 comment；
2. Clinician 手动 highlight AI note 中的短语；
3. Clinician 编辑患者 plan section；
4. 展示版本 diff 和 audit trail；
5. 执行一次 revert；
6. 如实现自学习，展示这次交互如何改变相似内容的未来优先级。

### Scenario C：纵向上下文

1. 展示多个日期的人工与 AI entries；
2. 解释 recent、unresolved、risk 与 clinician-confirmed 如何影响排序；
3. 具体解释 self-learning 的影响；
4. 加分项：解释旧数据的 decay/分层策略。

## 10. 评分导向与时间分配

基础分 20：

| 评分项 | 分值 | 开发含义 |
| --- | ---: | --- |
| Glanceability & Actionability | 6 | 优先打磨 Top Card 的信息质量和 10 秒可读性 |
| Collaboration & AI Integration | 5 | 做通评论、角色协作、版本、AI entries 的完整闭环 |
| Provenance & Trust | 4 | 每条关键信息都能回源，冲突和确认状态清晰 |
| Security & Privacy | 3 | 服务端 RBAC、clinic scope、PHI redaction、干净日志 |
| Communication | 2 | Brief 和 Demo 简洁，主动讲清 trade-offs |

另有最高 10 分 Nightingale Alignment bonus，重点是 Hybrid Storage/Data Decay 和 Self-Learning。加分项不能挤占上述硬要求。时间不足时，应先完成可运行、安全、可验证的核心闭环，再实现 bonus。

## 11. 范围边界：防止做偏

### 应优先完成

- 一个患者页面的端到端核心闭环；
- 高质量 Top Card；
- 多类型 Timeline entries；
- server-side RBAC 与 clinic scope；
- comments、versions、revert、audit；
- highlight 到来源的精确跳转；
- PHI redaction boundary；
- 四个必需微测试；
- 可演示的 synthetic longitudinal dataset。

### 不应抢占核心时间

- 通用富文本编辑器的完整复刻；
- 大而全的 EHR；
- 真实医院系统集成；
- 真实患者数据导入；
- 与评分无关的后台管理页面；
- 仅为视觉炫技、却不能提升 10 秒决策能力的动画和组件；
- 未能保留来源、审核状态和权限边界的“自动 AI 决策”。

### Bonus：有余力再做

- 基于交互反馈的 self-learning importance；
- hybrid storage / data decay；
- ambient voice capture；
- 噪声环境、diarization、overlap、code-switching、多语言医学术语、多设备录音。

## 12. 每次变更前后的防偏题检查

实现一个功能前，回答：

1. 它直接支持哪个评分项或硬约束？
2. 它是否减少临床人员在 10 秒内理解患者的成本？
3. 它的来源能否准确追溯？
4. 它是否尊重 role、clinic scope 和 section ownership？
5. 它是否可能让未经确认的 AI 内容看起来像临床事实？
6. 它能否通过自动化测试或 Demo 明确证明？

合并或录制 Demo 前，确认：

- [ ] Glance View 温路径 P95 `<= 300 ms`，且测量方法已记录；
- [ ] Top Card 在 10 秒内可理解且有明确 action；
- [ ] 所有 highlights 均有 `risk_reason` 和有效 provenance；
- [ ] AI、patient、staff、clinician 内容视觉与数据模型上均可区分；
- [ ] patient API 不返回 internal comments 或 raw AI notes；
- [ ] staff/clinician 不能覆盖对方 section；
- [ ] 跨 clinic 访问在服务端被拒绝；
- [ ] LLM 调用前已脱敏姓名、IC/ID、手机号；
- [ ] edit、diff、audit、revert 全部可演示；
- [ ] 并发编辑不会静默覆盖；
- [ ] 四个必需 test 文件全部通过；
- [ ] 只使用 synthetic data；
- [ ] README、Technical Brief、ATTRIBUTION、Demo Video 和个人联络材料齐全。

## 13. 截止与提交

- 截止：2026 年 8 月 28 日（星期五）17:30 SGT/MYT；
- 收件人：`irakumar@ntngale.com`；
- 抄送：`frank.ng@ntu.edu.sg`、`carrene.teo@ntu.edu.sg`；
- 邮件主题：`Nightingale 72HR Build — <Your Name>`；
- 提交 repo link（或 zip）、Technical Brief 以及全部交付物。

## 14. 当前建议的实施原则

用一个窄而完整的 vertical slice 赢得可信度：选择一位 synthetic patient，准备跨日期、跨角色、含三类 AI note 的数据，完整走通“Glance → 精确回源 → 评论/分配 → clinician 编辑 → 版本审计/revert → 权限拒绝 → 脱敏 → 测试”。这条链条比大量互不连通的功能更贴合题目，也更容易在短视频中证明价值。
