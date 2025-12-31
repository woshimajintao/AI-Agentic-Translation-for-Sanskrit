The datasets were from Sāmayik: A Benchmark and Dataset for English-Sanskrit Translation.

Please put the testsets folder under the data folder.https://github.com/woshimajintao/AI-Agentic-Translation-for-Sanskrit/tree/main/Agentic_system/data


https://github.com/ayushbits/Saamayik/tree/master/data

To evaluate the performance of our proposed Sanskrit-English translation agent, we utilized standard parallel corpora including [Itihasa, MKB, Bible, gitasopanam, spoken-tutorials]. 

Given the significant computational overhead inherent in the agentic workflow—which involves multiple iterations of tool invocation (dictionary lookup, morphological analysis) and LLM reasoning per sentence—evaluating on the full test sets (containing thousands of sentence pairs) was computationally infeasible. 

Therefore, following common practices in LLM-based evaluation~\cite{touvron2023llama}, we performed stratified random sampling to select a representative subset of $N=100$ instances from each dataset for our ablation studies. We fixed the random seed to ensure that all baseline and experimental models were evaluated on the identical set of samples, ensuring a fair and consistent comparison.

