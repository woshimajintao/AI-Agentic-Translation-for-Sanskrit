# AI-Agentic-Translation-for-Sanskrit

EDA初步数据探索：
https://colab.research.google.com/drive/1SUnIbyEYOYf7zD-yYq8i0GDouECWW2a0#scrollTo=xLNmlK641F6j

AI Agent 的 pipeline是成这样的：

输入：一条新的梵文 shloka（Devanagari / IAST / SLP1 都行，先统一成 SLP1）

Baseline 翻译：用 Hugging Face / LLM 先翻一遍英语

调用三本“工具书”：

👉 Itihāsa：

很完整的梵语英语对齐数据集，这个是作为初始输入语料的）

👉 Monier-Williams：

对长尾词 / 生词逐个查释义、词性，看看 baseline 有没有误译

👉 ambuda-dcs：

如果遇到不确定的词形或复杂结构，查一查类似的句子是怎么被 DCS 解析的（语法助手）

用格/时态/依存关系帮你判断“谁修饰谁，谁是主语宾语”

Agent 做“第二版翻译”：

把：
原文 + baseline 译文 + 例句 + 词典释义 +（可选）语法解析结果
一起交给一个 LLM / 规则系统，让它输出更精细、更有根据的译文。

对比和分析：

在一个 test 集上，对比 baseline vs agent：
自动评分（BLEU 等），人工看几个长尾例子，写进报告。
