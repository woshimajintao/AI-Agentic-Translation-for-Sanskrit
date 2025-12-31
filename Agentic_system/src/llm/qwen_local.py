import os
from llama_cpp import Llama

# Dynamically get the project root directory (3 levels up from this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# GGUF model path
MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "models/Qwen2.5-7B-GGUF",
    "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
)


class QwenLocalLLM:
    def __init__(self, model_path: str = MODEL_PATH):
        print(f"Loading GGUF model from: {model_path}")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"❌ Model file not found at {model_path}.")

        try:
            # Initialize llama.cpp model
            self.llm = Llama(
                model_path=model_path,
                n_gpu_layers=-1,  # Use GPU acceleration (where available, e.g., on Mac)
                # -------------------------------------------------
                # Key setting: increase context window
                # If dictionary evidence is long, we need a large context.
                # 8192 is a safe value for a 7B model; on a 16GB MacBook Air it should be OK.
                # If you only have 8GB RAM, consider lowering to 4096 and truncating evidence harder.
                # -------------------------------------------------
                n_ctx=8192,
                n_batch=512,      # Larger batch can speed up prompt processing
                verbose=True,     # Enable logs for debugging
                chat_format="chatml",
            )
            print(f"✅ GGUF model loaded successfully! (Context window: {self.llm.n_ctx()})")
        except Exception as e:
            print(f"❌ Failed to load GGUF model: {e}")
            raise

    def generate(self, messages: list, max_new_tokens: int = 512, temperature: float = 0.2) -> str:
        """
        Generate a response from the local model.
        """
        try:
            # You could add a proactive prompt-length check here if needed.

            output = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=max_new_tokens,
                temperature=temperature,
                top_p=0.9,
                stream=False,
            )

            return output["choices"][0]["message"]["content"]

        except Exception as e:
            # Print detailed error to the terminal for debugging
            print(f"❌ Error during generation in qwen_local.py: {e}")

            # Common failure: context/token limit exceeded
            if "context" in str(e).lower() or "token" in str(e).lower():
                return "Error: Input text (dictionary evidence) is too long for the model context window."

            return f"Error: Model generation failed. Details: {str(e)}"


# Test code
if __name__ == "__main__":
    llm = QwenLocalLLM()
    print(llm.generate([{"role": "user", "content": "Hello!"}]))
