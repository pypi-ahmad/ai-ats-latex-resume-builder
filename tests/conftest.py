import importlib
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


class SessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _cache_passthrough(func=None, *args, **kwargs):
    if callable(func):
        return func

    def decorator(inner_func):
        return inner_func

    return decorator


@pytest.fixture
def app_ctx():
    if "app" in sys.modules:
        del sys.modules["app"]

    st_mod = types.ModuleType("streamlit")
    st_mod.set_page_config = MagicMock()
    st_mod.title = MagicMock()
    st_mod.header = MagicMock()
    st_mod.subheader = MagicMock()
    st_mod.caption = MagicMock()
    st_mod.markdown = MagicMock()
    st_mod.info = MagicMock()
    st_mod.error = MagicMock()
    st_mod.success = MagicMock()
    st_mod.code = MagicMock()
    st_mod.download_button = MagicMock()
    st_mod.rerun = MagicMock()
    st_mod.cache_data = _cache_passthrough
    st_mod.cache_resource = _cache_passthrough
    st_mod.session_state = SessionState()

    sidebar = SimpleNamespace(
        title=MagicMock(),
        subheader=MagicMock(),
        selectbox=MagicMock(side_effect=lambda _label, options, **_: options[0]),
        text_input=MagicMock(return_value=""),
    )
    st_mod.sidebar = sidebar

    st_mod.columns = MagicMock(side_effect=lambda n: [DummyContext() for _ in range(n)])
    st_mod.radio = MagicMock(return_value="Raw Text")
    st_mod.file_uploader = MagicMock(return_value=None)
    st_mod.text_input = MagicMock(return_value="")
    st_mod.text_area = MagicMock(return_value="")
    st_mod.button = MagicMock(return_value=False)
    st_mod.spinner = MagicMock(return_value=DummyContext())
    st_mod.expander = MagicMock(return_value=DummyContext())

    def _stop():
        raise RuntimeError("streamlit.stop called")

    st_mod.stop = MagicMock(side_effect=_stop)

    sys.modules["streamlit"] = st_mod

    ollama_mod = types.ModuleType("ollama")
    ollama_mod.list = MagicMock()
    ollama_mod.chat = MagicMock()
    sys.modules["ollama"] = ollama_mod

    openai_mod = types.ModuleType("openai")
    openai_mod.OpenAI = MagicMock()
    sys.modules["openai"] = openai_mod

    anthropic_mod = types.ModuleType("anthropic")
    anthropic_mod.Anthropic = MagicMock()
    sys.modules["anthropic"] = anthropic_mod

    ddgs_mod = types.ModuleType("ddgs")
    ddgs_mod.DDGS = MagicMock()
    sys.modules["ddgs"] = ddgs_mod

    paddle_mod = types.ModuleType("paddleocr")
    paddle_mod.PaddleOCR = MagicMock()
    sys.modules["paddleocr"] = paddle_mod

    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    genai_mod.Client = MagicMock()
    google_mod.genai = genai_mod
    sys.modules["google"] = google_mod
    sys.modules["google.genai"] = genai_mod

    app = importlib.import_module("app")
    app = importlib.reload(app)

    return SimpleNamespace(
        app=app,
        st=st_mod,
        ollama=ollama_mod,
        openai=openai_mod,
        anthropic=anthropic_mod,
        ddgs=ddgs_mod,
        paddle=paddle_mod,
        genai=genai_mod,
    )
