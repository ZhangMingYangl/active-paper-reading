# 主动阅读论文：先闭卷写，再让 AI 纠错

> 一篇 PDF、一份笔记、一个 AI。PDF 是证据源，笔记留下你自己的理解，AI 只负责解释、追问和校验，不替你读。

**状态：v0.6 试用版。** 目前只在作者本人读论文时用过，效果还没有在更多人身上验证。欢迎试用后[提交阅读复盘](../../issues/new?template=reading-review.md)，母版会按大家的复盘继续修改。

[English summary](#english-summary)

## 为什么要这样读

常见的读法是：看一句、问一次 AI、复制回答。笔记写了很多，合上论文却讲不清楚。

研究生的正式反馈集中在开题、中期和答辩，间隔太长。这套方法把每次读论文变成一次高频反馈训练：

```text
预测 → 阅读 → 合上论文自己写 → 回原文找错 → AI 依据原文核对 → 只把核实过的修正写回笔记
```

## 两步开始

1. **拿到母版。** 下载 [`templates/论文阅读-主动思考模板.md`](templates/论文阅读-主动思考模板.md)，每读一篇论文就复制一份。Obsidian、Typora、VS Code 都能打开。
2. **交给 AI。** 写好阅读目的和“我的基础”这四行后，把你为这篇论文建的笔记（就是那个 .md 文件）和论文 PDF 一起上传给任意 AI（ChatGPT、Claude、Kimi 等），说一句：**请按这篇笔记开头“给 AI 的说明”做。** 论文信息、论文类型、章节表格和背景概念这些杂活 AI 都会填好，你只管读和想；它会等你合上论文写完，再依据原文核对。

剩下的照着笔记从上往下填就行。第一次用可以看 [新手操作教程](docs/01-新手操作教程.md)，真实例子见 [示范](examples/示范-一章的反馈循环.md)。

**想在 Obsidian 里一键插入母版？** 把下面这句话发给 Claude Code、Codex、Cursor 等能操作电脑文件的 AI，它会问你知识库在哪、先预演给你看，你同意后才安装：

```text
请按 https://github.com/ZhangMingYangl/active-paper-reading 里 AGENTS.md 的说明，把这个论文阅读母版装进我的 Obsidian 知识库。
```

也可以自己运行 `python setup.py --vault "<知识库路径>"`，详见 [让 AI 自动部署](docs/02-让AI自动部署.md)。

**以后怎么更新？** 已经写好的笔记不受影响。要让以后新建的笔记用新版，对 AI 说“按 AGENTS.md 把论文阅读母版更新到最新版”，或运行 `python setup.py --vault "<知识库路径>" --update`；你改过的文件会先备份。在仓库页面点 **Watch → Custom → Releases**，有新版时会收到通知。

## 仓库结构

```text
templates/
  论文阅读-主动思考模板.md   每篇论文复制一份的笔记骨架
docs/
  00-快速上手.md             10 分钟上手说明
  01-新手操作教程.md         从零开始的分步教程
  02-让AI自动部署.md         交给 AI 一键安装到 Obsidian
  论文阅读-使用说明.md       规则、概念学习闭环、AI 提问模板
  论文阅读-类型模块.md       8 类论文的补充检查问题（待试用）
examples/
  示范-一章的反馈循环.md     “原答 → AI 核对 → 修正”的真实片段
prompts/
  AI开场指令.md              发给 AI 的顺序约束指令
  概念预填指令.md            让 AI 按章节预填概念解释
setup.py                     安装和更新脚本（复制文件、开启 Obsidian 模板插件、--update 更新）
VERSION                      当前版本号
AGENTS.md                    给 AI 助手看的部署说明
```

**Obsidian 用户**：把整个文件夹放进库里，母版中的 `[[双链]]` 和折叠块（`> [!info]-`）都能直接用。
**其他编辑器**：Typora、VS Code 或任何 Markdown 编辑器都能打开；折叠块会显示成普通引用块，“本章新概念”不会自动收起，要自己先写完闭卷三问再往下看。

## 依据与相关项目

这套方法的各个环节都有研究依据，组合方式是新的：

- **预测、提问、澄清、总结**：Palincsar 和 Brown（1984）的[交互式教学](https://readingrockets.org/articles/researchbytopic/4956)。
- **读之前先作答**：预测试效应，即使先答错，事后看到正确答案，记忆效果往往更好（[Pan & Rivers, 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC9839203)）。
- **AI 只做校验者**：一项高中数学随机实验发现，无限制使用 GPT-4 的学生考试成绩比对照组低 17%，加了“不直接给答案”护栏后基本消除了负面影响（[Bastani 等, PNAS 2025](https://ideas.repec.org/a/nas/journl/v122y2025pe2422633122.html)）。

相近的项目和工具，各有侧重：[Feynman-Reader](https://github.com/HachikoJ/Feynman-Reader)（面向书籍，先写讲解再由 AI 评分）、[iTELL](https://ceur-ws.org/Vol-4010/itb25_s1s2.pdf)（智能教材，分块作答与总结）、ChatGPT Study Mode 和 Claude 学习模式（对话式引导）。本项目的侧重点是：**专门读科研论文、逐章先预测再闭卷作答、AI 在你写完之前不给本章解读、母版按论文类型分模块并靠复盘迭代**。

## 参与改进

最有用的贡献是**真实的阅读复盘**：读完一篇论文后，[新建一个“阅读复盘” Issue](../../issues/new?template=reading-review.md)，写清哪些栏目空着、哪些问题真的有用、用了多久。其他方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

本项目文档采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh-hans) 许可：可以自由使用、修改和再分发，但需注明出处。全文见 [LICENSE](LICENSE)。安装脚本 `setup.py` 是代码，单独采用 [MIT](LICENSE-MIT) 许可。

---

## English summary

A Markdown/Obsidian workflow for reading research papers actively: **write first with the paper closed, then check against the paper and let an AI correct you.** It includes a per-chapter note skeleton (predict → closed-book three questions → correct against the source → feedback log), a one-week delayed recall check, a usage guide, question modules for 8 paper types (method, benchmark, attack/defense, mechanism, systems, dataset, survey, theory), a real worked example, and a prompt that keeps the AI from explaining a chapter before you have written your own answers. Status: v0.6, tested by the author only. Content is in Chinese; feedback via issues is welcome.
