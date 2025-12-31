import os
import sys
from llama_cpp import Llama

# 动态获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# GGUF 模型路径
MODEL_PATH = os.path.join(PROJECT_ROOT, "models/Qwen2.5-7B-GGUF", "Qwen2.5-7B-Instruct-Q4_K_M.gguf")

class QwenLocalLLM:
    def __init__(self, model_path: str = MODEL_PATH):
        print(f"Loading GGUF model from: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Model file not found at {model_path}.")

        try:
            # 初始化 Llama
            self.llm = Llama(
                model_path=model_path,
                n_gpu_layers=-1,      # 使用 Mac GPU 加速
                # -------------------------------------------------
                # 【关键修复】增大上下文窗口
                # 如果 dictionary 内容很长，需要足够大的窗口来容纳
                # 8192 是 7B 模型的安全值，MacBook Air 16G 应该能扛住
                # 如果你是 8G 内存，这里可能要试着降回 4096 并严格截断字典
                # -------------------------------------------------
                n_ctx=8192,           
                n_batch=512,          # 批处理大小，提高 Prompt 处理速度
                verbose=True,         # 打开日志以便在终端看报错
                chat_format="chatml"
            )
            print(f"✅ GGUF Model loaded successfully! (Context window: {self.llm.n_ctx()})")
        except Exception as e:
            print(f"❌ Failed to load GGUF model: {e}")
            raise e

    def generate(self, messages: list, max_new_tokens=512, temperature=0.2) -> str:
        """
        生成回复
        """
        try:
            # 检查 Prompt 是否过长（简单的预估）
            # 这是一个预防性检查
            
            output = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=max_new_tokens,
                temperature=temperature,
                top_p=0.9,
                stream=False
            )
            
            return output['choices'][0]['message']['content']
            
        except Exception as e:
            # 打印详细错误到终端，方便调试
            print(f"❌ Error during generation in qwen_local.py: {e}")
            # 有可能是 Context Limit Exceeded
            if "context" in str(e).lower() or "token" in str(e).lower():
                return "Error: Input text (dictionary evidence) is too long for the model context window."
            return f"Error: Model generation failed. Details: {str(e)}"

# 测试代码
if __name__ == "__main__":
    llm = QwenLocalLLM()
    print(llm.generate([{"role": "user", "content": "Hello!"}]))