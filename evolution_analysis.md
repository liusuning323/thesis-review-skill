# 达尔文进化分析: thesis-review-skill v2.0

## 方法论
逐段审视 v2.0 的基因，识别**缺失的器官**（该有但没有）、**退化的结构**（有但弱）、**适应性不足**（在真实环境中会失败）。

---

## 一、缺失的器官（该有但没有）

### 1.1 「不适用场景」声明
**严重度: HIGH**

v2.0 只说了"适用场景"，没有反向界定。这会导致误用：
- 5 页短文不适合（5 轮审核过度工程化）
- 单作者独立写作不适合（需要多 Agent 并行交互的上下文）
- 非结构化论文（无 LaTeX 无严格章节）不适合（自动化脚本依赖于可解析的结构）

**进化建议**: 新增 `## 0. 不适用场景` 章节

### 1.2 Agent 失败恢复机制
**严重度: HIGH**

整个文档假设 Agent 总是成功。现实中：
- Agent 可能编辑了错误的行
- Agent 可能误解了修复指令
- Agent 生成的内容可能引入了新错误

当前没有任何回滚/重试/验证机制描述。

**进化建议**: 新增 `## 9. 故障恢复` 章节，包含：
- 每次 Agent 修改后自动 `diff` 验证变更范围
- 重大修改前 `cp file.tex file.tex.bak`
- Agent 重试协议（最多 2 次，每次提供更具体的指令）
- 修复 Agent 的 prompt 中必须包含 "Before editing, verify the exact current text at line N"

### 1.3 审核冲突解决协议
**严重度: MEDIUM**

4 个审核 Agent 可能给出矛盾建议。例如：
- Sturm Agent 说"subjectification 应该是集体的"
- Ng Agent 说"subjectification 太抽象，需要更实操"
- 两个建议同时执行可能产生逻辑断裂

当前文档没有描述如何裁决。

**进化建议**: 新增 `## 2.5 冲突解决`：
```
理论 Agent 的修改优先于实践 Agent（框架一致性 > 可操作性）
结构 Agent 的修改优先于内容 Agent（RQ 一致性 > 修辞优化）
当两个 Agent 修改同一段时，优先保留更接近论文核心论点的版本
```

### 1.4 可执行代码
**严重度: MEDIUM**

文档 7 次提到 Python 脚本，但仓库中没有一行可运行代码。用户需要自己从头写。

**进化建议**: 添加 `tools/` 目录，包含：
```
tools/
├── citation_converter.py    # 引用格式转换
├── assemble_thesis.py       # 多文件组装
├── word_counter.py          # 章节字数统计
├── citation_matcher.py      # 引用双向检查
└── preflight_check.sh       # Phase 0 自动化检查
```

### 1.5 评审质量度量
**严重度: MEDIUM**

没有标准来判断一轮审核是"好"还是"坏了"。5 轮从何而来？如果第 3 轮后只剩 2 个低优先级问题，第 4-5 轮是否浪费？

**进化建议**: 新增停止标准：
```
STOP 条件（满足任一即可提前结束）:
1. 连续两轮无 HIGH 优先级发现
2. 最新一轮发现 < 5 个（全为 LOW）
3. 审核 Agent 的压缩报告中，>80% 的条目被标记为 PASS
```

### 1.6 术语表文件模板
**严重度: LOW**

文档提到"Phase 0 建立术语表"但未给出模板。

**进化建议**: 添加 `templates/glossary.md`：
```markdown
# 术语表 — 所有 Agent 必须遵守
| 正确术语 | 禁止替代 | 说明 |
|----------|---------|------|
| three educational purposes | three domains, three functions | Biesta 框架的标准表述 |
| subjectification-adjacent | near-subjectification, proxy subjectification | 本论文的创新分析类别 |
| HVET | vocational education (首次出现后) | 缩略词，首次使用必须全称 |
...
```

---

## 二、退化的结构（有但弱）

### 2.1 Token 管理策略：缺乏量化基准
**当前**: 提供了估算数字（~2.5M tokens），但这是基于一次实际运行的经验数据
**退化点**: 换一篇论文（不同长度/不同 Agent 模型/不同 Prompt 长度），数字可能偏差 2-5 倍
**进化**: 提供计算公式而非固定数字，让用户可以根据自己的论文参数估算

```
Token 估算公式:
总 Token ≈ N_agents × (avg_paper_tokens × 0.3 + prompt_overhead) × N_rounds

其中:
- avg_paper_tokens = 论文总字数 × 1.3 (LaTeX overhead)
- prompt_overhead = ~2,000 tokens/agent (指令 + 报告模板)
- 0.3 = Agent 不会逐字处理全文的有效读取比
```

### 2.2 Agent Prompt 模板：缺少负面示例
**当前**: Prompt 模板只说了"要做什么"
**退化点**: Agent 最容易犯的错误没有在 Prompt 中被预防
**进化**: 在每个 Prompt 模板中添加 "DO NOT:" 部分

```diff
+ ## DO NOT:
+ - DO NOT paraphrase the research questions — use EXACT text from Ch1
+ - DO NOT create new terminology — use only terms from the glossary
+ - DO NOT delete content that you are not explicitly told to delete
+ - DO NOT change citation format — use the exact format shown in examples
```

### 2.3 问题解决表：缺少"如何检测"
**当前**: 12 个问题都有根因 → 解决 → 预防
**退化点**: 没有告诉用户**如何发现**这些问题。如果我不知道有中文空白问题，我怎么检测到它？
**进化**: 增加"检测方法"列

| # | 问题 | 检测方法 | 解决 |
|---|------|---------|------|
| 3 | 中文空白 | `grep -c '[\\x{4e00}-\\x{9fff}]' thesis.tex` 有中文但 PDF 中空白 | xeCJK |
| 5 | RQ 不一致 | `diff <(grep RQ1 ch1) <(grep RQ1 ch4)` | 对齐 |

### 2.4 工具链对比表：缺少选择决策树
**当前**: 工具 vs Token 消耗的静态表
**退化点**: 用户不知道**什么时候该用哪个**
**进化**: 添加决策树

```
你需要做什么？
├── 检查术语一致性 → grep
├── 转换引用格式 → Python 脚本
├── 语义分析（理论深度、论证质量） → Agent
├── 编辑 1-2 行 → 主会话直接 Edit
├── 编辑整个章节 → 修复 Agent
└── 最终格式检查 → grep + 手动
```

---

## 三、适应性不足（真实环境中的脆弱点）

### 3.1 对 macOS 的强依赖
**当前**: xelatex、Mail.app、AppleScript、Songti SC 全部是 macOS 专属
**适应性问题**: Linux/Windows 用户完全无法使用邮件和字体部分
**进化**: 为每个 macOS 专属功能提供跨平台替代方案

| 功能 | macOS | Linux | Windows |
|------|-------|-------|---------|
| 中文字体 | Songti SC | Noto Serif CJK SC | SimSun |
| 邮件发送 | Mail.app + AppleScript | mutt / sendmail | PowerShell Outlook |
| LaTeX 编译 | xelatex (相同) | xelatex | xelatex |

### 3.2 对论文类型的假设
**当前**: 整个文档基于 SLR（系统性文献综述）论文
**适应性问题**: 实证论文、理论论文、混合方法论文的审核维度和问题类型差异很大
**进化**: 第 1 节增加论文类型适配矩阵

| 论文类型 | 需要调整的审核维度 |
|----------|------------------|
| SLR | 当前配置即适用 |
| 实证研究 | 增加"方法学审核Agent"（样本量、统计方法、效度） |
| 理论论文 | 弱化"PRISMA检查"、增加"论证链完整性" |
| 混合方法 | 增加"方法间整合一致性"检查 |

### 3.3 对 Agent 能力的一致性假设
**当前**: 假设所有 Agent 的审核质量相同
**适应性问题**: Agent 模型（Haiku vs Sonnet vs Opus）的审核深度差异巨大
**进化**: Agent 模型路由建议

| 角色 | 推荐模型 | 原因 |
|------|---------|------|
| 第 1 轮结构审核 | Haiku/Sonnet | 机械检查为主，不需要深度推理 |
| 理论深度审核 | Opus | 需要理解哲学框架的细微差别 |
| 修复 Agent（简单编辑） | Haiku | 按指令逐行修改 |
| 修复 Agent（新增内容） | Opus | 需要生成学术段落 |
| 最终终审 | Opus | 需要最全面的质量判断 |

---

## 四、进化优先级

| 优先级 | 进化项 | 预期影响 |
|--------|--------|----------|
| **P0** | 故障恢复机制 (1.2) | 防止 Agent 错误修改破坏论文 |
| **P0** | 负面 Prompt 指令 (2.2) | 减少 50% 的 Agent 常见错误 |
| **P1** | 可执行代码 (1.4) | 从"方法论"变成"工具" |
| **P1** | 停止标准 (1.5) | 避免不必要的审核轮次 |
| **P1** | 审核冲突协议 (1.3) | 多 Agent 场景的必要基础 |
| **P2** | 跨平台适配 (3.1) | 扩大适用范围 |
| **P2** | 论文类型矩阵 (3.2) | 从"SLR专用"变为通用框架 |
| **P3** | 不适用场景声明 (1.1) | 防止误用 |
| **P3** | 术语表模板 (1.6) | 降低 Phase 0 启动成本 |

---

## 五、v3.0 路线图建议

**v2.1 (立即)**: P0 项 — 故障恢复 + 负面 Prompt 指令
**v2.2 (本周)**: P1 项 — 可执行代码 + 停止标准 + 冲突解决
**v3.0 (下次项目后)**: P2 项 — 跨平台 + 论文类型矩阵

---

*分析时间: 2026-04-30*
*方法论: 达尔文进化审视 — 寻找缺失器官、退化结构、适应性缺陷*
