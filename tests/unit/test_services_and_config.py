from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestMarketResearch:
    def test_get_market_research_empty_role_target_app_py(self, app_ctx):
        assert app_ctx.app.get_market_research("") == "No role specified."

    def test_get_market_research_success_target_app_py(self, app_ctx):
        ddgs_instance = MagicMock()
        ddgs_instance.text.return_value = [
            {"title": "T1", "body": "B1"},
            {"title": "T2", "body": "B2"},
        ]
        app_ctx.ddgs.DDGS.return_value.__enter__.return_value = ddgs_instance

        result = app_ctx.app.get_market_research("Data Engineer")
        assert "- T1: B1" in result
        assert "- T2: B2" in result

    def test_get_market_research_failure_target_app_py(self, app_ctx):
        app_ctx.ddgs.DDGS.return_value.__enter__.side_effect = RuntimeError("network")
        result = app_ctx.app.get_market_research("Data Engineer")
        assert result.startswith("Market research failed:")


class TestOllamaModelFetch:
    def test_get_ollama_models_object_response_target_app_py(self, app_ctx):
        model_obj = SimpleNamespace(model="llama3:latest")
        app_ctx.ollama.list.return_value = SimpleNamespace(models=[model_obj])
        result = app_ctx.app.get_ollama_models()
        assert result == ["llama3:latest"]

    def test_get_ollama_models_dict_response_target_app_py(self, app_ctx):
        app_ctx.ollama.list.return_value = {"models": [{"name": "mistral"}]}
        result = app_ctx.app.get_ollama_models()
        assert result == ["mistral"]

    def test_get_ollama_models_fallback_target_app_py(self, app_ctx):
        app_ctx.ollama.list.side_effect = RuntimeError("down")
        result = app_ctx.app.get_ollama_models()
        assert isinstance(result, list)
        assert len(result) >= 1


class TestConfigBuilder:
    def test_get_llm_config_openai_target_app_py(self, app_ctx):
        app_ctx.st.sidebar.selectbox = MagicMock(side_effect=["OpenAI", "Same as LLM"])
        app_ctx.st.sidebar.text_input = MagicMock(
            side_effect=["sk-openai", "https://api.example/v1", "gpt-test"]
        )

        config = app_ctx.app.get_llm_config()
        assert config["provider"] == "OpenAI"
        assert config["api_key"] == "sk-openai"
        assert config["base_url"] == "https://api.example/v1"
        assert config["model"] == "gpt-test"
        assert config["vision_provider"] == "Same as LLM"

    def test_get_llm_config_gemini_env_fallback_target_app_py(self, app_ctx):
        app_ctx.st.sidebar.selectbox = MagicMock(side_effect=["Google Gemini", "Same as LLM"])
        app_ctx.st.sidebar.text_input = MagicMock(return_value="")

        with patch.dict(app_ctx.app.os.environ, {"GOOGLE_API_KEY": "env-key-1"}):
            config = app_ctx.app.get_llm_config()

        assert config["provider"] == "Google Gemini"
        assert config["api_key"] == "env-key-1"
        assert config["model"] == "gemini-2.5-flash"

    def test_get_llm_config_ollama_with_local_vision_target_app_py(self, app_ctx):
        app_ctx.st.sidebar.selectbox = MagicMock(
            side_effect=["Ollama", "m1", "Local Ollama Vision", "vision1"]
        )
        with patch.object(app_ctx.app, "get_ollama_models", return_value=["m1", "vision1"]):
            config = app_ctx.app.get_llm_config()

        assert config["provider"] == "Ollama"
        assert config["model"] == "m1"
        assert config["vision_provider"] == "Local Ollama Vision"
        assert config["vision_model"] == "vision1"


    def test_get_llm_config_anthropic_target_app_py(self, app_ctx):
        app_ctx.st.sidebar.selectbox = MagicMock(side_effect=["Anthropic", "Same as LLM"])
        app_ctx.st.sidebar.text_input = MagicMock(return_value="sk-ant-test")

        config = app_ctx.app.get_llm_config()
        assert config["provider"] == "Anthropic"
        assert config["api_key"] == "sk-ant-test"
        assert config["model"] == "claude-4-5-sonnet-latest"
        assert config["vision_provider"] == "Same as LLM"

    def test_get_llm_config_gemini_vision_cross_provider_target_app_py(self, app_ctx):
        """When vision is Gemini but LLM is OpenAI, a separate vision key is collected."""
        app_ctx.st.sidebar.selectbox = MagicMock(
            side_effect=["OpenAI", "Google Gemini (Free Tier)"]
        )
        app_ctx.st.sidebar.text_input = MagicMock(
            side_effect=["sk-openai", "https://api.example/v1", "gpt-test", "vis-gemini-key"]
        )

        config = app_ctx.app.get_llm_config()
        assert config["provider"] == "OpenAI"
        assert config["vision_provider"] == "Google Gemini (Free Tier)"
        assert config["vision_api_key"] == "vis-gemini-key"


class TestPaddleFactory:
    def test_get_paddle_ocr_constructs_with_expected_args_target_app_py(self, app_ctx):
        app_ctx.app.PaddleOCR = MagicMock(return_value="ocr-instance")
        result = app_ctx.app._get_paddle_ocr()
        assert result == "ocr-instance"
        app_ctx.app.PaddleOCR.assert_called_once_with(use_angle_cls=True, lang="en", show_log=False)
