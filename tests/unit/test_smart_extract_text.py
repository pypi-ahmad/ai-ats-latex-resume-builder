from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import Image


class FakeUpload:
    def __init__(self, name, data):
        self.name = name
        self._data = data
        self._cursor = 0

    def seek(self, pos):
        self._cursor = pos

    def read(self):
        return self._data


def make_png_bytes():
    image = Image.new("RGB", (2, 2), color=(255, 255, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class TestSmartExtractText:
    def test_raw_text_passthrough_target_app_py(self, app_ctx):
        config = {"provider": "Ollama", "vision_provider": "Same as LLM"}
        result = app_ctx.app.smart_extract_text("raw resume", False, config)
        assert result == "raw resume"

    def test_txt_file_decode_target_app_py(self, app_ctx):
        uploaded = FakeUpload("resume.txt", "hello world".encode("utf-8"))
        config = {"provider": "Ollama", "vision_provider": "Same as LLM"}
        result = app_ctx.app.smart_extract_text(uploaded, True, config)
        assert result == "hello world"

    def test_pdf_native_text_short_circuits_target_app_py(self, app_ctx):
        class Page:
            def get_text(self):
                return "A" * 80

        fake_doc = [Page()]
        uploaded = FakeUpload("resume.pdf", b"%PDF-mock")
        config = {"provider": "Ollama", "vision_provider": "Same as LLM"}

        with patch.object(app_ctx.app.fitz, "open", return_value=fake_doc):
            result = app_ctx.app.smart_extract_text(uploaded, True, config)

        assert len(result.strip()) >= 80

    def test_pdf_scanned_paddle_none_result_target_app_py(self, app_ctx):
        class Pix:
            width = 1
            height = 1
            samples = b"\x00\x00\x00"

        class Page:
            def get_text(self):
                return ""

            def get_pixmap(self):
                return Pix()

        class Doc:
            def __iter__(self):
                yield Page()

            def __len__(self):
                return 1

            def __getitem__(self, idx):
                return Page()

        uploaded = FakeUpload("scan.pdf", b"%PDF-mock")
        config = {"provider": "Ollama", "vision_provider": "PaddleOCR"}

        with patch.object(app_ctx.app.fitz, "open", return_value=Doc()):
            with patch.object(app_ctx.app, "PADDLE_AVAILABLE", True):
                ocr = MagicMock()
                ocr.ocr.return_value = None
                with patch.object(app_ctx.app, "_get_paddle_ocr", return_value=ocr):
                    result = app_ctx.app.smart_extract_text(uploaded, True, config)

        assert result == "PaddleOCR: No text detected in image."

    def test_png_openai_missing_key_target_app_py(self, app_ctx):
        uploaded = FakeUpload("resume.png", make_png_bytes())
        config = {
            "provider": "OpenAI",
            "vision_provider": "Same as LLM",
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
        }
        result = app_ctx.app.smart_extract_text(uploaded, True, config)
        assert result == "Vision Error: Missing OpenAI API Key."

    def test_png_openai_exception_path_target_app_py(self, app_ctx):
        uploaded = FakeUpload("resume.png", make_png_bytes())
        config = {
            "provider": "OpenAI",
            "vision_provider": "Same as LLM",
            "api_key": "sk-test",
            "base_url": "https://api.openai.com/v1",
        }

        app_ctx.app.OpenAI = MagicMock(side_effect=RuntimeError("api down"))
        result = app_ctx.app.smart_extract_text(uploaded, True, config)
        assert result.startswith("OpenAI Vision Error:")

    def test_unsupported_file_returns_failure_message_target_app_py(self, app_ctx):
        uploaded = FakeUpload("resume.xyz", b"binary")
        config = {"provider": "Ollama", "vision_provider": "Same as LLM"}
        result = app_ctx.app.smart_extract_text(uploaded, True, config)
        assert result == "Failed to extract text or convert document to image."
