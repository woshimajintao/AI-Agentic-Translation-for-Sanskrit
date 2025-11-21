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


最终idea：


0. 准备：先固定好数据切分

Itihāsa 已经有 train / dev / test：

-train：模型训练、建检索索引

dev：调参数、选方案（模型大小、Agent 设计）

-test：最后一次性评估，拿来写报告

1. 做 baseline（只用模型，不用 Agent）

1.2 用 dev 集 调 baseline

在 dev 上跑翻译 → 算 BLEU / chrF 等；

这里可以尝试：

不同最大长度、beam size

甚至不同模型（比如两个 HF 模型比一比）

目的：选出你觉得“还 OK”的 baseline 设置。

✅ 到这一步为止：

你已经有了一个“确定下来的 baseline 系统”。

1.3 用 test 集 得到 baseline 最终成绩

用刚刚确定好的 baseline，在 test 上跑一遍；

记录指标：

BLEU_base_test和
chrF_base_test

这组数以后不能再改（否则就相当于用 test 调参了）。

3. 设计并实现 Agent 版本（用三种资源）

这一步你在 代码层面 搭“增强版翻译”：

输入：同样是一句 Sanskrit

内部流程：
-调 baseline 模型粗翻
-用 ambuda-dcs 做形态/格/结构分析（或者用你提前从里边学到的规则）
-用 MW 字典 查长尾词 / 多义词
-用 Itihāsa (train) 做语义检索，找相似例句

综合这些信息，产出 Agent 的最终译文

这一步只写代码，还没评测；就像先造好一辆车。

4. 先在 dev 上比较：baseline vs agent

在 dev 集 上，对每个句子同时输出：

baseline 翻译和
agent 翻译

各自算一遍 BLEU / chrF：

BLEU_base_dev vs BLEU_agent_dev

你可以在 dev 上调整 Agent 的细节：

语义检索相似度阈值（多少算“太不像”就不用）

查 MW 的策略（只查罕见词还是所有词？）

prompt 结构（给 LLM 的上下文怎么组织？）

在 dev 上调到你满意为止。

5. 最后一步：在 test 上做“终极对比”

当你觉得 Agent 的设计已经定型了：

在 test 集 上再次跑：

baseline → BLEU_base_test（已算过，可复用）

agent → BLEU_agent_test

看最终差别：
是否整体提升

也可以只看“困难样本子集”（例如长句、含特定术语），做局部分析

这些 test 上的结果就是你报告里要写的：

“在 Itihāsa test 集上，Agent 相比 baseline：
BLEU 从 X 提升到 Y，chrF 从 A 提升到 B；
在几个 long-tail 句子上有如下定性改进……”

6. 顺带做一点误差分析：
   
在 dev/test 里找几条典型句子：

baseline 明显翻错 / 翻得很平

agent 利用字典 / 语义检索 / 语法信息做得更好

把这些例子整理到报告的一节里，特别加一段文字说明：
Agent 查了什么
改动了哪一部分
为什么更符合原文
一句话帮你串起来
baseline 的流程是：
train（训练）→ dev（挑模型/参数）→ test（给出最终分数）
Agent 的流程也是：
在 baseline 固定后，用三种资源扩展出一个 Agent，
先在 dev 上调好 Agent 的细节，
最后在 test 上和 baseline 做正式对比，写进报告。
