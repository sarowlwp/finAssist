class MockModelAdapter:
    """Mock LLM model adapter for testing"""

    def __init__(self):
        pass

    async def chat(self, messages, **kwargs):
        """Mock chat completion"""
        return "This is a mock response from the LLM"

    async def analyze(self, context, **kwargs):
        """Mock analysis function"""
        return {
            "ticker": "AAPL",
            "analysis": "Mock analysis",
            "confidence": 0.85
        }

    def validate_provider(self, provider: str):
        """Mock provider validation"""
        return provider in ["openrouter", "openai", "grok", "gemini", "dashscope"]

    def validate_api_key(self, provider: str):
        """Mock API key validation"""
        return True

    def get_supported_providers(self):
        """Mock supported providers list"""
        return ["openrouter", "openai", "grok", "gemini", "dashscope"]

    def get_default_model(self, provider: str):
        """Mock default model"""
        return "anthropic/claude-3.5-sonnet"
