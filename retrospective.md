# 论文多轮审核项目完整复盘

**项目**: 某教育学硕士论文 — 生成式人工智能在中国职业教育中的系统性文献综述（匿名化处理）
**大学**: 新西兰某综合性大学, 2026
**时间**: 2026-04-29 ~ 2026-04-30
**最终成果**: 114 页 PDF, ~36,400 词, 5 轮审核, 100+ 问题修复, 0 编译错误

---

## 一、项目数据

| 指标 | 数值 |
|------|------|
| 论文总字数 | ~36,400 词 |
| PDF 页数 | 114 页 |
| 审核轮次 | 5 轮 |
| 并行 Agent 总数 | ~18 个 |
| 发现问题总数 | 100+ |
| 修复问题总数 | 100+ |
| 编译次数 | ~12 次 |
| 主要 Python 脚本 | 3 个（引用转换 + 组装 + 邮件） |
| 邮件附件 | PDF + 中文分析报告 |
| 最终状态 | READY FOR SUBMISSION |

## 二、Token 管理深度分析

### 2.1 核心矛盾

5 轮审核需要反复通读一篇 1500+ 行的论文全文。如果不做隔离，主会话上下文会被论文内容反复填充，单轮就能耗尽窗口。

### 2.2 解决方案架构

```
                    ┌─────────────────────────────┐
                    │     主会话（指挥中心）         │
                    │  Token: ~5K-15K/轮            │
                    │  - 接收审核报告摘要             │
                    │  - 做执行决策                   │
                    │  - 运行脚本                    │
                    │  - 验证编译结果                │
                    └──────┬──────────────────────┘
                           │ 并行 fork
          ┌────────────────┼──────────────────┐
          ▼                ▼                  ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ 审核Agent A   │ │ 审核Agent B   │ │ 审核Agent C   │
  │ Token: ~100K  │ │ Token: ~100K  │ │ Token: ~100K  │
  │ 在自己的上下   │ │ 在自己的上下   │ │ 在自己的上下   │
  │ 文中读取全文   │ │ 文中读取全文   │ │ 文中读取全文   │
  └──────────────┘ └──────────────┘ └──────────────┘
          │                │                  │
          ▼                ▼                  ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ 审核报告.md   │ │ 审核报告.md   │ │ 审核报告.md   │
  │ ~150 行      │ │ ~150 行      │ │ ~150 行      │
  └──────────────┘ └──────────────┘ └──────────────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           │ 汇总到主会话
                           ▼
                  ┌─────────────────┐
                  │ 修复Agent (fork) │
                  │ Token: ~50K      │
                  │ 在自己的上下文中   │
                  │ 读取报告+执行编辑  │
                  └─────────────────┘
```

### 2.3 策略详解

#### 策略 1: 子 Agent 上下文隔离（节省比 ~20:1）

重型任务全部 fork 到独立子 Agent。主会话只接收压缩后的审核报告（~100-200 行），而非论文全文（1500+ 行）。

每个审核 Agent 独立在自己的上下文中读取全文、分析、写报告。Agent 完成后返回主会话的只是一份 150 行的结构化报告。

#### 策略 2: grep 诊断代替全文阅读（节省比 ~25:1）

```bash
# 找术语漂移（200 tokens vs 读全文 5,000 tokens）
grep -n "three functions\|three domains" thesis.tex

# 统计重复次数
grep -c "supplemented by related" thesis.tex

# 定位未引用文献
grep -n "Author.*2024" thesis.tex
```

单次 grep ~200 tokens，读同段落 ~5,000 tokens。

#### 策略 3: Python 脚本做机械劳动（节省比 ~10:1）

| 任务 | Agent 方式 | Python 方式 |
|------|-----------|------------|
| 引用格式转换 | ~30,000 tokens（逐行编辑） | ~2,000 tokens |
| 文件组装 | ~15,000 tokens | ~1,000 tokens |
| 字数统计 | ~5,000 tokens | ~500 tokens |

#### 策略 4: 审核报告结构化压缩

强制格式化为 `编号 + 优先级 + 行号 + 修复文本`。禁止自由叙述。

5 轮 × 4 Agent = 20 份报告, 每份 ~150 行, 总计占主会话 ~3,000 行。

#### 策略 5: 后台执行

run_in_background=True 确保 Agent 的中间工具调用日志（通常 50K-200K tokens）不会被推到主会话上下文。

#### 策略 6: 第 1 轮前自动化预检

在启动 Agent 审核前, 先跑机械检查:
- grep 统计重复短语
- Python 脚本匹配引用
- diff RQ 文本

这些检查 0 LLM Token 消耗（grep/Python 不计 Token）。机械问题不浪费 Agent。

### 2.4 Token 消耗估算

| 操作 | 单次消耗 | 次数 | 总计 |
|------|---------|------|------|
| 审核 Agent (读全文+分析+写报告) | 80K-130K | ×20 | ~2M |
| 修复 Agent (读报告+编辑文件) | 30K-70K | ×8 | ~400K |
| 主会话指挥 | 5K-15K | ×5 轮 | ~50K |
| Python 脚本 | ~2K | ×4 | ~8K |
| grep 诊断 | ~200 | ×30 | ~6K |
| **总计** | | | **~2.5M** |

> 对比：如果不使用隔离策略，同一会话需要载入 18 个 Agent 的全部交互内容 ≈ 8M-12M tokens。实际节省 ~4:1。

---

## 三、12 个典型问题深度分析

### 问题 1: 引用格式冲突 — BibTeX vs 手动 APA

**现象**: Agent 生成的 Ch4-6 全部使用 `\citet{}`/`\citep{}`，但主文件 Ch1-3 使用手动 APA 格式 `(Author, Year)`

**根因**: 主文件未使用 BibTeX（是手动 `\hangindent` 参考文献格式）。Agent 默认生成 BibTeX 风格的引用命令。

**解决**: Python 脚本建立 50+ 个 citation key → 手动 APA 映射表，正则替换 `\citet{key}` 和 `\citep{key}` 为文本格式。

**关键代码**:
```python
CITE_MAP = {
    'biesta2020': {'text': 'Biesta (2020)', 'paren': 'Biesta, 2020'},
    'cao2025': {'text': 'Cao and Abdullah (2025)', 'paren': 'Cao & Abdullah, 2025'},
    # ... 50+ keys
}

# \citet{key} → Author (Year)
content = re.sub(r'\\citet\{([^}]+)\}', convert_citet, content)

# \citep{key} → (Author, Year)  
content = re.sub(r'\\citep\{([^}]+)\}', convert_citep, content)
```

**预防**: 在修复 Agent Prompt 中明确: "Use manual APA format: (Author, Year). Do NOT use \citet{} or \citep{} commands."

### 问题 2: RQ 在不同章节中不一致

**现象**:
- Ch1: "What educational purposes are articulated or implied..."
- Ch4: "What does the existing literature reveal about the use of GenAI..."
- Ch6: 自行创造了三个独立问题

**根因**: 各章节由不同 Agent 独立生成，Agent 自行"表述"了 RQ 而非使用原文。

**解决**: 手动将 Ch4 和 Ch6 的 RQ 文本精确对齐到 Ch1 版本。

**预防**: Agent Prompt 中明文粘贴 Ch1 的 RQ 原文，并要求 "Use EXACTLY this wording. Do not paraphrase."

### 问题 3: 中文在 PDF 中不显示

**现象**: 论文中的中文（修身、和、深度求索、文心一言等）在 PDF 中显示为空白或空括号 `()`

**根因**: LaTeX preamble 只有 `\usepackage[T1]{fontenc}`（欧洲字体编码），无 CJK 字体配置

**解决**:
```latex
\usepackage{xeCJK}
\setCJKmainfont{Songti SC}  % macOS 系统自带宋体
```

**经验**: xelatex + xeCJK + Songti SC 是 macOS 上中英混排论文的最简方案。`T1{fontenc}` 与 CJK 无关，xeCJK 会自动处理字体。

### 问题 4: PRISMA 数字错误

**现象**: Ch5 声称 "2,354 records"，但 PRISMA 宏定义是 `\PRISMAIdentified = 894`

**根因**: Agent 可能混淆了原始数据库命中数与去重后的记录数

**解决**: 改为 894，与 PRISMA 图表和宏定义一致

**预防**: 审核清单必须包含 "验证所有统计数字与 PRISMA 宏定义一致"

### 问题 5: 文件组织混乱 — 主文件内联 vs 独立文件

**现象**: 主文件第 778 行起内联了整个 Ch4（与 chapter4.tex 相同），造成内容重复

**根因**: 早期组装脚本同时保留了内联内容和 `\input` 引用

**解决**: 重组装脚本：提取主文件 Ch1-3 + 转换后的 ch4.tex + ch5.tex + ch6.tex + 原始 References

**预防**: 始终使用 `\input{}` 方式组织多章节论文；单文件论文除外

### 问题 6: 过度重复的限定短语

**现象**: "supplemented by related Chinese tertiary/professional evidence" 重复 ~13 次

**根因**: 每个章节 Agent 都被要求"提及语料库范围限制"，各自独立重复

**解决**: 保留在 Abstract/RQ/首次定义处（≤4 次），其余删除或替换为简略引用

**预防**: 第 1 轮结构审核必须包含 `grep -c` 重复短语计数

### 问题 7: 术语漂移

**现象**: "three functions" / "three domains" / "three purposes" 三种术语混用

**根因**: 不同 Agent 使用 Biesta 框架的不同翻译习惯

**解决**: 统一为 "three educational purposes"

**预防**: Phase 0 建立术语表，在所有 Agent Prompt 中引用

### 问题 8: 参考文献双向不匹配

**现象**: 
- 正文引用 Biesta (2017, 2022) 但不在参考文献列表中
- 参考文献列表有 Ng, A. (2024) 但正文未引用

**根因**: 后期添加/删除内容时未同步更新参考文献

**解决**: Phase 5 交叉验证脚本检查 citation ↔ reference 双向一致性

**预防**: 终审清单必须包含引用双向匹配检查

### 问题 9: 同姓同年作者引用歧义

**现象**:
- "Gao et al. (2024)" 同时指代 Gao, Cheah et al. (business students) 和 Gao, Wang & Wang (EFL teachers)
- "Wang et al. (2025)" 指代三个不同的 Wang 论文

**根因**: APA 规则中同年同姓作者的歧义需要额外作者名消除

**解决**: Gao, Wang, and Wang (2024) vs Gao, Cheah, et al. (2024); Wang, Wang, and Xu (2025) vs Wang, Qu, and Wong (2025)

**预防**: 审核清单包含 "检测同姓同年作者的歧义引用"

### 问题 10: 参考文献字母排序错误

**现象**: 
- Roder & Sturm (2017) 错放在 L 与 M 之间
- Selwyn (2016) 错放在 Shi 与 Shu 之间
- `\hangindent` 重复; 缺少 `\noindent`

**根因**: 手动添加条目时未检查字母顺序和格式一致性

**解决**: 按 APA 7th 字母顺序重排，统一 `\noindent\hangindent=0.5in\hangafter=1`

### 问题 11: LaTeX 编译问题

**现象**: 中文字符不显示、交叉引用显示 ??

**解决**:
- 中文字体: `\usepackage{xeCJK}` + `\setCJKmainfont{Songti SC}`
- 交叉引用: xelatex 必须执行两遍编译
- 占位图片: Phase 0 检查所有依赖文件大小

### 问题 12: 邮件发送

**现象**: 需要将 114 页 PDF + 中文分析报告发送到指定邮箱

**解决**: macOS Mail.app + AppleScript
```applescript
tell application "Mail"
    set newMessage to make new outgoing message with properties {subject:"...", content:"...", visible:true}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"user@gmail.com"}
        tell content
            make new attachment with properties {file name:"path/to/pdf"} at after the last paragraph
        end tell
    end tell
    activate
end tell
```

**条件**: Mail.app 必须已配置目标邮箱账户

---

## 四、19 条经验教训

### 架构

1. **审核-修复分离不可妥协** — 合并角色 = 自我审核 = 盲区
2. **章节分文件 + `\input{}`** — 比单文件内联干净得多
3. **Agent 并行边界**: 一个 Agent 只编辑一个文件
4. **背景 Agent 用 run_in_background** — 避免中间日志污染主会话
5. **Prompt 中原文粘贴 RQ 和术语** — 禁止 Agent 自行表述

### LaTeX / CJK

6. macOS: xelatex + xeCJK + Songti SC 最简中文方案
7. 手动 APA 格式论文（无 BibTeX）必须禁止 Agent 使用 `\citet{}`/`\citep{}`
8. xelatex 两遍编译是必须的（交叉引用）
9. Phase 0 检查所有图片文件大小 — 占位图通常 < 10KB

### Agent Prompt

10. RQ 必须原文粘贴，不能信任 Agent 的"复述"
11. 提供 1-2 个引用格式示例，Agent 会精确模仿
12. 要求具体行号（"line 781 change X to Y"），而非模糊定位（"in Section 5.4"）
13. 限制 Agent 创建新概念（"subjectification-adjacent"除外，这是论文的原创贡献）

### 审核流程

14. 第 1 轮必须包含结构审核 — RQ、术语、重复、数字逻辑是最常见错误
15. 第 3 轮是理论深度的关键窗口 — 此时结构已稳定
16. 第 5 轮只做 polish — 禁止引入新内容
17. 所有修改后必须重新编译并 grep 验证

### 工具链

18. Python 是胶水语言 — grep/Python 解决 60% 的机械问题，Agent 只做语义分析
19. 邮件用 AppleScript 在用户已登录 Mail.app 时最可靠

---

## 五、适用于类似项目的启动清单

```
[ ] 确认目标字数范围
[ ] 确认引用格式（APA/Harvard/MLA）
[ ] 确认语言标准（NZ English/British/American）
[ ] 确认编译方式（xelatex/pdflatex/lualatex）
[ ] 检查非 ASCII 字符（中文 → CJK 字体）
[ ] 列出所有依赖文件（图片/附录/bib）
[ ] 读取并理解全部现有内容
[ ] 建立术语表
[ ] 提取 RQ 原文用于 Prompt
[ ] 首次编译测试（确认环境正常）
[ ] 跑自动化预检脚本（grep/Python）
[ ] 配置邮件发送方式（如需要）
```

---

*复盘时间: 2026-04-30*
*项目原始文件: 本地论文目录（匿名化）*
