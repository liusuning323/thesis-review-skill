---
name: thesis-review
description: >
  学术论文多轮审核自动化流程。适用于系统性文献综述(SLR)从初稿到终稿的完整校改流程，
  支持 LaTeX + xelatex + APA 7th + NZ English + 中英混排。触发词: 论文审核, thesis review,
  多轮校改, SLR, Biesta framework, LaTeX 编译, 引用检查, 章节字数。
version: 2.2
target_audience: 研究生(硕士/博士)、学术写作辅导人员、需要多轮审核的论文作者
prerequisites: Claude Code 或兼容多Agent环境, LaTeX (xelatex), Python 3.x
token_cost: ~2.5M tokens (完整5轮) 或更少(使用隔离策略)
---

# 学术论文多轮审核自动化流程 v2.1

## 目录
1. [适用场景](#1-适用场景)
2. [架构原则](#2-架构原则)
3. [Token 管理策略](#3-token-管理策略)
4. [完整流程](#4-完整流程)
5. [Agent Prompt 模板](#5-agent-prompt-模板)
6. [关键检查清单](#6-关键检查清单)
7. [常见问题与解决方案](#7-常见问题与解决方案)
8. [工具链](#8-工具链)

---

## 1. 适用场景

- 学术论文（特别是系统性文献综述 SLR）从初稿到终稿的完整流程
- 需要多理论视角审核（如哲学家 Biesta、教育学者 Sturm、AI 专家 Ng）
- 英文学术写作，APA 7th / New Zealand English
- LaTeX + xelatex 编译，涉及中英混排
- 需要最终邮件交付 PDF + 分析报告

---

## 2. 架构原则

### 2.1 审核与修复分离

审核 Agent 和修复 Agent **角色不合并**：
- **审核 Agent**: 只读文件 → 输出编号发现 + 行号 + 修改建议（写入 `.md` 报告）
- **修复 Agent**: 读取审核报告 → 执行修改 → 写入 `.tex` 文件
- 禁止同一个 Agent 同时做审核和修复

### 2.2 并行边界

- 每个 Agent 最多编辑 **1 个文件**，避免写冲突
- 审核 Agent 可以并行读取多个文件（无写冲突）
- 文件组装由单一 Python 脚本完成

### 2.3 章节分文件管理

```
thesis/
├── main.tex              # Preamble + Ch1-3 + \input{} statements
├── chapter4.tex          # Findings
├── chapter5_discussion.tex  # Discussion
├── chapter6_conclusion.tex  # Conclusion
└── expanded/
    └── review_round*.md     # 审核报告
```

首选 `\input{}` 方式引入章节，而非在主文件中内联复制所有内容。

### 2.4 Prompt 中必须原文粘贴的内容

以下内容**禁止 Agent 自行表述**，必须在 Prompt 中提供原文：
- **研究问题 (RQ)**: "Use EXACTLY this wording: What educational purposes..."
- **核心术语**: "Use ONLY 'three educational purposes' — never 'three domains' or 'three functions'"
- **引用格式示例**: 提供 1-2 个正确示例，Agent 会模仿

### 2.5 冲突解决协议

当多个审核 Agent 的建议矛盾时，按以下优先级裁决：

1. **理论一致性 > 可操作性** — 框架 Agent 的修改优先于实践 Agent
2. **结构正确性 > 修辞优化** — RQ 一致性、数字准确性的修复优先于措辞改进
3. **论文核心论点 > 边缘补充** — 优先保留最贴近论文核心论点的版本
4. **当两个 Agent 修改同一段时** — 先应用结构修复，再叠加内容增强

### 2.6 故障恢复

每次 Agent 修改后：
```bash
# 1. 变更范围验证
git diff --stat  # 确认只改了预期文件

# 2. 重大修改前自动备份
cp thesis.tex thesis.tex.bak.$(date +%Y%m%d_%H%M)

# 3. 编译验证
xelatex thesis.tex | grep -E "Error|Warning"
```

Agent 重试协议：最多 2 次。每次重试在 Prompt 中提供更具体的指令和当前文件的精确行号。两次失败后，改用手动修复。

---

## 3. Token 管理策略

这是整个流程中**最关键的工程约束**。以下策略将主会话 Token 消耗控制在可管理范围。

### 3.1 核心策略：子 Agent 上下文隔离

重型任务全部 fork 到独立子 Agent 中执行。**主会话只接收压缩后的审核报告**（~100-200 行），而非论文全文（1500+ 行）。

```
主会话上下文 (~5K tokens)          子Agent上下文 (隔离，~100K tokens)
┌──────────────────┐              ┌──────────────────────────┐
│ 审核报告摘要      │  ←────────  │ 读取论文全文(1500行)      │
│ 执行决策          │              │ 逐条分析                  │
│ 组装脚本          │              │ 编写审核报告(200行)       │
│ 编译验证          │              └──────────────────────────┘
└──────────────────┘
```

**Token 节省比**: 约 1:20（主会话只看到 5% 的内容）

### 3.2 grep 诊断代替全文阅读

每次修改前用 `grep` 精确锁定问题位置：

```bash
grep -n "three functions\|three domains"  → 术语漂移检测
grep -c "supplemented by related"         → 重复计数
grep -n "Deng.*2025"                      → 未引用文献定位
```

单次 grep 消耗 ~200 tokens，通读同段内容消耗 ~5,000 tokens。**节省比约 1:25**。

### 3.3 Python 脚本做机械劳动

引用转换、文件组装、字数统计全部用 Python 脚本，而非 Agent 逐行编辑。

```python
# 一次脚本执行处理整个文件的引用转换
# Token 消耗固定（脚本 ~100 行），与论文长度无关
# vs Agent 逐行编辑: 每行 10-50 tokens × 数百行
```

| 方式 | Token 消耗 |
|------|-----------|
| Agent 逐行编辑 | ~15,000-50,000 |
| Python 脚本 | ~2,000（脚本 + 执行输出） |
| **节省比** | **~10:1** |

### 3.4 审核报告结构化压缩

每个 Agent 的输出强制格式化为 **"编号发现 + 行号 + 修复建议"**，禁止自由叙述：

```markdown
### Finding 1 — RQ mismatch in Ch4
**Priority: HIGH**
**Line:** 781
**Fix:** Replace with: "RQ1 asks: What educational purposes..."
```

5 轮审核 × 4 个 Agent = 20 份报告，每份 ~150 行结构化文本，总计在主会话中仅占 ~3,000 行。

### 3.5 run_in_background 避免中间输出污染

```python
Agent(run_in_background=True)  # 后台执行
# 主会话不接收 Agent 的中间工具调用日志
# 只收到完成通知: "Agent completed"
# 节省: ~50,000-200,000 tokens/Agent
```

### 3.6 第 1 轮前先跑自动化检查

在启动 Agent 审核之前，先跑一遍机械检查脚本：

```bash
# 这些检查 0 Token 消耗（读文件不算 LLM Token）
grep -c "重复短语" → 重复统计
grep -n "RQ" → RQ 一致性
diff <(grep cited references) <(grep reference list) → 引用匹配
```

机械问题不浪费 Agent Token。Agent 应该只做**语义分析**（理论深度、论证质量、逻辑一致性）。

### 3.7 停止标准（何时可以提前结束）

满足**任一**条件即可提前结束审核循环：
1. 连续两轮无 HIGH 优先级发现
2. 最新一轮发现 < 5 个（且全部为 LOW）
3. 审核报告 > 80% 条目标记为 PASS（验证性检查）

反之，如果最新一轮仍有 HIGH 优先级发现，则**必须继续下一轮**。

### 3.8 Token 消耗估算（本轮实际经验）

| 操作 | 消耗范围 | 频率 |
|------|---------|------|
| 审核 Agent | 80K-130K/次 | ×20 次 = ~2M |
| 修复 Agent | 30K-70K/次 | ×8 次 = ~400K |
| 主会话指挥 | 5K-15K/轮 | ×5 轮 = ~50K |
| Python 脚本 | ~2K/次 | ×4 次 = ~8K |
| grep 诊断 | ~200/次 | ×30 次 = ~6K |
| **总计** | | **~2.5M tokens** |

> 如果不使用隔离策略，主会话需要承载所有 20 次审核的全部内容，预估消耗 **8M-12M tokens**，远超上下文窗口限制。

---

## 4. 完整流程

### Phase 0: 启动准备

**核心原则: 验收标准先于执行。** 先定义"什么叫好"，再开始改论文。

```
# Step 0: 定义验收标准（必须先做）
[ ] 创建 test-prompts.json（3 个典型 prompt + expected 描述）
      - Prompt 1: 最典型使用场景（happy path）
      - Prompt 2: 复杂/歧义场景
      - Prompt 3: 常见错误场景
[ ] 从 Ch1 提取 RQ 原文（用于后续所有 Agent Prompt）
[ ] 建立术语表（核心术语的标准表述 + 禁止替代词）

# Step 1: 环境验证
[ ] 确认论文初稿存在于指定路径
[ ] 确认目标格式要求（字数、引用格式、语言标准）
[ ] 首次编译测试（确认编译环境正常）
[ ] 列出所有依赖文件（图片、附录、bib 文件）
[ ] 检查图片文件大小（< 10KB 可能是占位图）

# Step 2: 自动化预检（0 Agent Token）
[ ] bash scripts/preflight_check.sh thesis.tex
[ ] grep -c 检查关键短语重复
[ ] python scripts/citation_matcher.py thesis.tex

# Step 3: Darwin 基线评估
[ ] 阅读论文全文（确认内容完整性）
[ ] 按 Darwin 8 维度建立基线分数
[ ] 记录到 baseline_evaluation.md
[ ] 识别最弱维度，作为后续审核优先级
```

**反模式（不要这样做）:**
- ❌ 先启动 Agent 审核，后补验收标准 → test-prompts 必须在 Phase 0 创建
- ❌ 跳过预检直接审核 → 机械问题浪费 Agent Token
- ❌ 没有基线就开始改 → 不知道改好还是改坏了

### Phase 1: 第 1 轮 — 理论基础审核

并行启动 3 个 Agent：
```
Agent 1: 理论视角（如 Biesta 哲学框架审核）
Agent 2: 结构视角（RQ 一致性、重复、术语、交叉引用）
Agent 3: 批判分析（语境深度、逻辑错误、证据充分性）
```

**目标**: 找出框架使用错误、结构性缺陷、逻辑漏洞
**修复方式**: 通常 <15 个问题，主会话直接修复（不启动子 Agent）

### Phase 2: 第 2 轮 — 多维度理论视角

并行启动 3 个 Agent：
```
Agent 1: 学者 A 视角（如 Sean Sturm — 特定理论深度）
Agent 2: 学者 B 视角（如 Andrew Ng — 实践/行业视角）
Agent 3: 综合审核（对比第 1 轮修复结果）
```

**目标**: 深化理论分析、发现第 1 轮未覆盖的盲区
**修复方式**: 通常 15-30 个问题，启动 2-3 个修复 Agent 并行

### Phase 3: 第 3 轮 — 深度理论介入

并行启动 4 个 Agent：
```
Agent 1: 学者 A 深度（理论章节新增/扩展建议）
Agent 2: 学者 B 深度（实践框架、可操作性）
Agent 3: 理论框架深度（框架哲学基础、不足）
Agent 4: 结构深度（引用格式、章节组织）
```

**目标**: 新增理论章节、跨文化汇合、实践框架
**修复方式**: 通常需要新增内容，3 个修复 Agent 分别编辑 Ch4/Ch5/Ch6

### Phase 4: 验证

```
单 Agent（全面验证）
检查所有第 2-3 轮修复是否已正确应用
发现 5-20 个遗留问题
修复漏洞后重新编译
```

### Phase 5: 最终审核 + 交付

```
单 Agent（全面终审）
    ↓
修复优先级最高的问题（错别字、APA 格式、引用顺序）
    ↓
最终 xelatex 两遍编译
    ↓
章节字数统计 + 分析报告
    ↓
macOS Mail.app 邮件发送
```

---

## 5. Agent Prompt 模板

### 5.1 理论审核 Agent

```
You are [Scholar Name], [role/background].
Review this thesis for:
1. [Theory check 1 — e.g., Accurate use of framework]
2. [Theory check 2 — e.g., Proper understanding of key concepts]
3. [Theory check 3 — e.g., Cross-cultural application]
...

Read these files:
- [Path to main thesis]
- [Path to chapter files]

Write your review to: [Path to output .md]
Format: 
  - Numbered findings with HIGH/MEDIUM/LOW priority
  - SPECIFIC line references (use grep to find exact lines)
  - Concrete fix suggestions (not abstract comments)
  - Maximum 200 lines
```

### 5.2 结构审核 Agent

```
Review this thesis for structural and methodological issues:

1. RQ consistency across ALL chapters (Ch1/Ch4/Ch6) — exact text alignment required
2. Repetition of phrases or ideas (>3 occurrences in different chapters)
3. Self-reference consistency ("the author" vs "this study" vs "I")
4. Chapter transition paragraphs (every chapter boundary)
5. APA 7th citation compliance
6. Table/figure formatting and cross-reference resolution
7. NZ English spelling consistency
8. Abbreviation definitions on FIRST use (not just in list)
9. Logical errors or unsupported claims
10. Synthesis quality (analytical vs merely descriptive)

For EACH finding provide:
- Priority (CRITICAL / MEDIUM / LOW)
- Exact line number
- Current text (5-10 words for context)
- Proposed fix
```

### 5.3 修复 Agent

```
You must edit the file [Path] to implement the following fixes.
Read the file first, then make ALL edits listed below.

## Fixes to apply:
1. [Line XX] Change "A" to "B"  (verify exact current text before editing)
2. [Line XX] Add paragraph: "..."

## DO NOT:
- DO NOT paraphrase research questions — use EXACT text provided
- DO NOT create new terms — use ONLY terms from the glossary below
- DO NOT delete any content not explicitly listed for deletion
- DO NOT change citation format — use EXACT format shown in examples
- DO NOT edit lines outside the specified line ranges
- DO NOT add commentary or explanations in the file

## Rules:
- Keep ALL existing content not specifically changed
- Use the EXACT citation format: Author (Year) or (Author, Year)
- Before editing line N, verify the current text matches the "Change FROM" instruction
- If current text does not match, STOP and report the mismatch

## Context:
- This is a thesis about [topic]
- The theoretical framework is [framework]
- These are the exact RQs: [paste RQ text]
- These are the key terms: [paste glossary]
```

---

## 6. 关键检查清单

### 6.1 自动化检查（Phase 0，0 Agent Token）

```bash
# RQ 一致性
grep -n "Research Question\|RQ1:\|RQ2:" main.tex

# 重复短语
grep -c "关键短语" main.tex  # >3 需关注

# 术语漂移
grep -n "three domains\|three functions\|three purposes" main.tex

# PRISMA 数字
grep -n "894\|2,354\|PRISMA" main.tex

# 引用匹配（需 Python 脚本）
```

### 6.2 LaTeX 编译检查

```
[ ] xelatex 两遍编译，0 Error
[ ] 0 undefined references (grep "??" in PDF log)
[ ] CJK 字体配置正确（xeCJK + Songti SC 或等效）
[ ] PRISMA 图存在且文件大小 >100KB（非占位图）
[ ] 所有 \ref{} 解析（非 ??）
[ ] 无 overfull/underfull hbox 警告
```

### 6.3 引用检查（Phase 5 必须）

```
[ ] 正文中的每个 Author (Year) 在参考文献列表中
[ ] 参考文献列表中的每一条在正文中被引用
[ ] 同姓同年作者引用已消歧（添加名缩写）
[ ] 参考文献按 APA 7th 字母顺序排列
[ ] 每条参考文献 DOI 完整（如期刊有 DOI）
[ ] 格式统一: \noindent\hangindent=0.5in\hangafter=1
```

### 6.4 内容检查

```
[ ] Ch1 和 Ch4/Ch6 的 RQ 文本完全一致（逐字比对）
[ ] 所有统计数字与 PRISMA 宏/图表一致
[ ] 核心术语全文统一（建立术语表并在 Phase 0 发布）
[ ] 无夸大语言（"remarkably", "cries for", "most important finding" 等）
[ ] 同一短语全文出现 ≤3-4 次
[ ] 缩略词在正文首次出现处有全称（不依赖缩略词表）
[ ] British/NZ English 拼写全文一致
```

---

## 7. 常见问题与解决方案

| # | 问题 | 根因 | 解决 | 预防 |
|---|------|------|------|------|
| 1 | Agent 生成的章节使用 BibTeX 命令，主文件使用手动 APA | Agent 默认使用 `\citet{}` | Python 脚本转换 citation key → 手动 APA 映射 | Prompt 中明确 "Use manual APA format: (Author, Year)" |
| 2 | 内联章节与独立文件重复 | 早期组装脚本未清理 | 提取主文件 Ch1-3 + `\input{}` 引入后续章节 | 始终使用 `\input{}` 而非内联复制 |
| 3 | 中文在 PDF 中显示为空白 `()` | 未配置 CJK 字体 | `\usepackage{xeCJK}` + `\setCJKmainfont{Songti SC}` | 含中文的 xelatex 项目必须检查字体配置 |
| 4 | PRISMA 图是占位符 | 项目缺少真实图文件 | 用户提供真实 PNG 替换 | Phase 0 检查所有依赖图片文件大小 |
| 5 | 各章节 RQ 文本不一致 | Agent 各自表述 RQ | 手动对齐到 Ch1 版本 | Prompt 中粘贴 Ch1 RQ 原文 |
| 6 | 限定短语重复 ~13 次 | 各章节 Agent 各自重复 | 保留在摘要/RQ/首次定义（≤4 次），其余删除 | 第 1 轮结构审核必须做重复计数检查 |
| 7 | 统计数字矛盾（2,354 vs 894） | Agent 混淆了原始命中数与去重数 | 修正为与 PRISMA 宏一致的数字 | 审核清单包含"验证统计数字与图表一致" |
| 8 | 术语漂移（domains/functions/purposes） | 不同 Agent 不同译法 | 统一为 "three educational purposes" | Phase 0 建立并发布术语表 |
| 9 | 引用键大小写不匹配 | Agent 使用不同大小写约定 | 统一映射到手动 APA 格式 | 手动 APA 论文完全避免使用引用命令 |
| 10 | 参考文献排列顺序错误 | 手动添加时未检查字母顺序 | 按 APA 7th 重新排列 | Phase 5 逐条验证参考列表顺序 |
| 11 | 未被引用的文献 + 缺失的文献 | 添加/删除内容时未同步参考文献 | 交叉验证脚本双向检查 | Phase 5 必须跑引用匹配脚本 |
| 12 | 同姓同年作者引用歧义 | "Gao et al. (2024)" 指代两篇不同论文 | 添加更多作者名消歧（APA 规则） | 审核清单包含"检测同姓同年作者" |

---

## 8. 工具链

| 工具 | 用途 | Token 消耗 |
|------|------|-----------|
| `grep -n/-c` | 精确定位 + 统计 | ~200/次 |
| `scripts/citation_converter.py` | 引用格式转换 | ~2,000/次 |
| `scripts/citation_matcher.py` | 引用双向检查 | ~500/次 |
| `scripts/word_counter.py` | 章节字数统计 | ~500/次 |
| `scripts/preflight_check.sh` | Phase 0 预检 | 0 LLM Token |
| 子 Agent | 重型审核和修改 | 30K-130K/次 |
| `xelatex` | PDF 编译 | 0 LLM Token |
| Mail.app AppleScript | 邮件发送 | 0 LLM Token |

### 核心 Python 脚本

所有脚本位于 `scripts/` 目录，可直接运行：

| 脚本 | 用途 | 用法 |
|------|------|------|
| `scripts/citation_converter.py` | natbib → 手动 APA 格式转换 | `python scripts/citation_converter.py thesis.tex --map citation_map.json` |
| `scripts/word_counter.py` | 章节字数统计 | `python scripts/word_counter.py thesis.tex --json` |
| `scripts/citation_matcher.py` | 引用↔参考文献双向检查 | `python scripts/citation_matcher.py thesis.tex` |
| `scripts/preflight_check.sh` | Phase 0 自动化预检 | `bash scripts/preflight_check.sh thesis.tex` |

自定义引用映射文件 `citation_map.json` 格式：
```json
{
  "biesta2020": {"text": "Biesta (2020)", "paren": "Biesta, 2020"}
}
```

---

## 9. CI/CD 自动化验证

每次 `git push` 自动运行结构审计：

### GitHub Actions 工作流

`.github/workflows/skill-audit.yml`:
```yaml
name: Skill Quality Audit
on: [push, pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run structural audit
        run: bash scripts/preflight_check.sh
      - name: Verify test prompts exist
        run: |
          if [ ! -f test-prompts.json ]; then
            echo "::warning::Missing test-prompts.json — create before merging"
          fi
      - name: Validate frontmatter
        run: |
          head -1 skill_thesis_review.md | grep -q "^---$" || exit 1
          grep -q "^name:" skill_thesis_review.md || exit 1
          grep -q "^description:" skill_thesis_review.md || exit 1
```

### 本地 Git Hook（可选）

`.git/hooks/pre-commit`:
```bash
#!/bin/bash
# 每次 commit 前自动跑预检
bash scripts/preflight_check.sh thesis.tex
python scripts/citation_matcher.py thesis.tex
```

### Darwin 质量闸门

合并 PR 前必须满足：
1. `preflight_check.sh` 全绿
2. `citation_matcher.py` 无 unmatched
3. `test-prompts.json` 存在
4. Darwin 总分 ≥ 上次评测分数（取 `baseline_evaluation.md` 中的记录）

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-04-30 | 初版，基于某教育学硕士论文 5 轮审核流程验证 |
| v2.0 | 2026-04-30 | 新增 Token 管理策略章节、问题解决表、工具链对比 |
| v2.1 | 2026-04-30 | Darwin 进化: 冲突解决协议、故障恢复、停止标准、负面 Prompt 指令、YAML frontmatter、可执行脚本 |
| v2.2 | 2026-04-30 | 工作流重构: test-prompts 提前到 Phase 0 第一步、CI/CD 自动化验证、Darwin 基线前置 |

## 相关文件

- `retrospective.md` — 完整项目复盘，包含 12 个具体问题的深度分析和 19 条经验教训
- `README.md` — 仓库概览和快速开始
