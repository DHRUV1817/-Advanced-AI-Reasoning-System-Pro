"""
Application constants and enums
"""
from enum import Enum


class ReasoningMode(Enum):
    """
    🧠 RESEARCH-ALIGNED REASONING METHODOLOGIES
    Based on academic papers and proven techniques
    """
    TREE_OF_THOUGHTS = "Tree of Thoughts (ToT)"
    CHAIN_OF_THOUGHT = "Chain of Thought (CoT)"
    SELF_CONSISTENCY = "Self-Consistency Sampling"
    REFLEXION = "Reflexion + Self-Correction"
    DEBATE = "Multi-Agent Debate"
    ANALOGICAL = "Analogical Reasoning"
    SIMPLE = "Simple (Direct Response)"
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def get_description(cls, mode: 'ReasoningMode') -> str:
        """Get detailed description of reasoning mode"""
        descriptions = {
            cls.TREE_OF_THOUGHTS: "Explores multiple reasoning paths systematically before converging on the best solution.",
            cls.CHAIN_OF_THOUGHT: "Breaks down complex problems into clear, logical steps with explicit reasoning.",
            cls.SELF_CONSISTENCY: "Generates multiple independent solutions and identifies the most consistent answer.",
            cls.REFLEXION: "Solves problems, critiques reasoning, and refines solutions iteratively.",
            cls.DEBATE: "Presents multiple perspectives and synthesizes the strongest arguments.",
            cls.ANALOGICAL: "Finds similar problems and applies their solutions to the current problem.",
            cls.SIMPLE: "Direct response without structured reasoning - fastest and most natural."
        }
        return descriptions.get(mode, "Advanced reasoning mode")


class ModelConfig(Enum):
    """
    🤖 AVAILABLE GROQ MODELS
    """
    
    # === Meta / Llama Models ===
    LLAMA_70B = ("llama-3.3-70b-versatile", 70, 8000, "Best overall performance", "Meta")
    LLAMA_70B_V31 = ("llama-3.1-70b-versatile", 70, 8000, "Stable production model", "Meta")
    LLAMA_3_1_8B_INSTANT = ("llama-3.1-8b-instant", 8, 131072, "Ultra-fast responses", "Meta")
    LLAMA_4_MAVERICK_17B = ("meta-llama/llama-4-maverick-17b-128k", 17, 131072, "Llama 4 experimental", "Meta")
    LLAMA_4_SCOUT_17B = ("meta-llama/llama-4-scout-17b-16e-instruct", 17, 16384, "Llama 4 scout model", "Meta")
    LLAMA_GUARD_4_12B = ("meta-llama/llama-guard-4-12b", 12, 8192, "Content moderation", "Meta")
    LLAMA_PROMPT_GUARD_2_22M = ("meta-llama/llama-prompt-guard-2-22m", 0, 8192, "Prompt injection detection (22M)", "Meta")
    LLAMA_PROMPT_GUARD_2_86M = ("meta-llama/llama-prompt-guard-2-86m", 0, 8192, "Prompt injection detection (86M)", "Meta")
    
    # === DeepSeek Models ===
    DEEPSEEK_70B = ("deepseek-r1-distill-llama-70b", 70, 8000, "Optimized reasoning", "DeepSeek")
    
    # === Mixtral Models ===
    MIXTRAL_8X7B = ("mixtral-8x7b-32768", 47, 32768, "Long context specialist", "Mixtral")
    
    # === Google Gemma Models ===
    GEMMA_9B = ("gemma2-9b-it", 9, 8192, "Fast and efficient", "Google")
    
    # === Moonshot AI Models ===
    KIMI_K2_INSTRUCT_DEPRECATED = ("moonshotai/kimi-k2-instruct", 0, 200000, "Ultra-long context (Deprecated)", "Moonshot")
    KIMI_K2_INSTRUCT_0905 = ("moonshotai/kimi-k2-instruct-0905", 0, 200000, "Ultra-long context specialist", "Moonshot")
    
    # === OpenAI Models ===
    GPT_OSS_120B = ("openai/gpt-oss-120b", 120, 8192, "Large open source model", "OpenAI")
    GPT_OSS_20B = ("openai/gpt-oss-20b", 20, 8192, "Medium open source model", "OpenAI")
    
    # === Qwen Models ===
    QWEN3_32B = ("qwen/qwen3-32b", 32, 32768, "Qwen 3 multilingual", "Qwen")
    
    # === Groq Compound Models ===
    GROQ_COMPOUND = ("groq/compound", 0, 8192, "Groq optimized compound", "Groq")
    GROQ_COMPOUND_MINI = ("groq/compound-mini", 0, 8192, "Groq mini compound", "Groq")
    
    def __init__(self, model_id: str, params_b: int, max_context: int, description: str, provider: str):
        self.model_id = model_id
        self.params_b = params_b
        self.max_context = max_context
        self.description = description
        self.provider = provider
    
    def __str__(self) -> str:
        return f"{self.provider} - {self.model_id}"
    
    @classmethod
    def get_by_id(cls, model_id: str) -> 'ModelConfig':
        """Get model config by ID"""
        for model in cls:
            if model.model_id == model_id:
                return model
        raise ValueError(f"Model {model_id} not found")
    
    @classmethod
    def get_by_provider(cls, provider: str) -> list:
        """Get all models by provider"""
        return [model for model in cls if model.provider == provider]
    
    @classmethod
    def get_recommended(cls) -> 'ModelConfig':
        """Get recommended default model"""
        return cls.LLAMA_70B
    
    @property
    def is_long_context(self) -> bool:
        """Check if model supports long context (>16k)"""
        return self.max_context > 16384
    
    @property
    def is_fast(self) -> bool:
        """Check if model is optimized for speed"""
        return "instant" in self.model_id.lower() or self.params_b < 10
