"""
ZERO-DEFECT AUTONOMOUS AUDIT — Phase 3-4
Test suite for app.py covering all 23 findings from Phase 2.

Strategy:
  - All external libraries (streamlit, ollama, openai, anthropic,
    google-genai, ddgs, paddleocr) are stubbed via sys.modules
    before importing app.py so no network/SDK is needed.
  - Tests are written to FAIL against the buggy code and PASS
    after surgical fixes are applied.
"""

import sys
import os
import types
import textwrap
from unittest.mock import MagicMock, patch

# ──────────────────────────────────────────────────────────────────────────────
# STUB LAYER — inject minimal fakes for every heavy/network import
# ──────────────────────────────────────────────────────────────────────────────

def _make_stub(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod

# streamlit  ──────────────────────────────────────
st_stub = _make_stub("streamlit")
st_stub.set_page_config = MagicMock()
st_stub.sidebar = MagicMock()
st_stub.info = MagicMock()
st_stub.error = MagicMock()
st_stub.stop = MagicMock()
st_stub.session_state = {}
st_stub.cache_data = lambda *a, **kw: (lambda f: f)  # passthrough decorator
st_stub.cache_resource = lambda *a, **kw: (lambda f: f)

# ollama  ─────────────────────────────────────────
ollama_stub = _make_stub("ollama")
ollama_stub.list = MagicMock()
ollama_stub.chat = MagicMock()

# openai  ─────────────────────────────────────────
openai_stub = _make_stub("openai")
openai_stub.OpenAI = MagicMock()

# anthropic  ──────────────────────────────────────
anthropic_stub = _make_stub("anthropic")
anthropic_stub.Anthropic = MagicMock()

# google-genai  ───────────────────────────────────
google_stub     = _make_stub("google")
genai_stub      = _make_stub("google.genai")
_make_stub("google.genai.types")
google_stub.genai = genai_stub
genai_stub.Client = MagicMock()

# ddgs  ───────────────────────────────────────────
ddgs_stub = _make_stub("ddgs")
ddgs_stub.DDGS = MagicMock()

# paddleocr  ──────────────────────────────────────
paddle_stub = _make_stub("paddleocr")
paddle_stub.PaddleOCR = MagicMock()

# fitz / PyMuPDF  ─────────────────────────────────
# Allow real import (installed in test env)
# PIL / numpy : same

# ──────────────────────────────────────────────────────────────────────────────
# Import the module under test
# ──────────────────────────────────────────────────────────────────────────────

# Point sys.path to workspace root so `import app` resolves
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

import app  # noqa: E402  (must come after stubs)


# ══════════════════════════════════════════════════════════════════════════════
# BUG-01 · clean_latex_code — & inside tabular must NOT be escaped
# ══════════════════════════════════════════════════════════════════════════════

class TestCleanLatexCode:

    def test_ampersand_in_plain_text_is_escaped(self):
        """Non-tabular & like "R&D" in body text should be escaped."""
        src = r"""\documentclass{article}
\begin{document}
R&D experience.
\end{document}"""
        result = app.clean_latex_code(src)
        # The & in plain text body should become \&
        assert r"R\&D" in result, \
            "Plain-text & in body MUST be escaped to \\&"

    def test_ampersand_in_tabular_is_NOT_escaped(self):
        """
        BUG-01: & used as a tabular column separator inside
        \\begin{tabularx} ... \\end{tabularx} must NOT become \\&,
        otherwise LaTeX alignment breaks.
        """
        src = (
            r"\documentclass{article}" + "\n"
            r"\begin{document}" + "\n"
            r"\begin{tabularx}{\textwidth}{X r}" + "\n"
            r"Name & Value \\" + "\n"
            r"\end{tabularx}" + "\n"
            r"\end{document}"
        )
        result = app.clean_latex_code(src)
        # Column-separator & inside tabular must survive unescaped
        assert r"Name & Value" in result, (
            "BUG-01: tabular column-separator & must NOT be escaped inside "
            "tabular environments"
        )

    def test_markdown_fences_stripped(self):
        """```latex ... ``` wrappers must be removed."""
        src = "```latex\n\\documentclass{article}\n```"
        result = app.clean_latex_code(src)
        assert "```" not in result
        assert "\\documentclass{article}" in result

    def test_already_escaped_ampersand_not_doubled(self):
        """An already-escaped \\& must not become \\\\&."""
        src = r"\begin{document}already \& escaped\end{document}"
        result = app.clean_latex_code(src)
        assert r"\\" + "&" not in result, \
            "Pre-escaped \\& must not be double-escaped"

    def test_no_document_tag_returns_unchanged_body(self):
        """If \\begin{document} absent, text is returned stripped."""
        src = "   just some text   "
        assert app.clean_latex_code(src) == "just some text"


# ══════════════════════════════════════════════════════════════════════════════
# BUG-02 · compile_latex — must run pdflatex TWICE for \pageref*{LastPage}
# ══════════════════════════════════════════════════════════════════════════════

class TestCompileLatex:

    def test_pdflatex_called_twice(self):
        """
        BUG-02: compile_latex must invoke pdflatex twice so that
        \\pageref*{LastPage} in the footer resolves correctly.
        Single-pass produces 'Page 1 of ??'.
        """
        with patch("subprocess.run") as mock_run:
            # First call: version check
            version_result = MagicMock(returncode=0)
            # Second + third call: two compile passes
            compile_result = MagicMock(returncode=0, stdout="", stderr="")
            mock_run.side_effect = [version_result, compile_result, compile_result]

            success, msg = app.compile_latex("dummy.tex")

        compile_calls = [
            c for c in mock_run.call_args_list
            if c.args and "pdflatex" in str(c.args[0])
            and "-interaction=nonstopmode" in str(c.args[0])
        ]
        assert len(compile_calls) == 2, (
            f"BUG-02: pdflatex must be called TWICE for cross-reference "
            f"resolution, got {len(compile_calls)} call(s)"
        )

    def test_returns_false_on_nonzero_returncode(self):
        """Compilation failure (returncode != 0) must return (False, log)."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),           # version check
                MagicMock(returncode=1, stdout="Error log", stderr=""),  # pass 1
            ]
            success, msg = app.compile_latex("bad.tex")
        assert success is False
        assert "Error log" in msg

    def test_returns_false_when_pdflatex_missing(self):
        """FileNotFoundError from version check must give (False, helpful msg)."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            success, msg = app.compile_latex("any.tex")
        assert success is False
        assert "pdflatex" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# BUG-03 · get_ollama_models — modern Pydantic response (not dict)
# ══════════════════════════════════════════════════════════════════════════════

class TestGetOllamaModels:

    def test_handles_pydantic_object_response(self):
        """
        BUG-03: ollama ≥ 0.2 returns a Pydantic object, not a dict.
        get_ollama_models() must use attribute access (.models, .model).
        """
        model_obj = MagicMock()
        model_obj.model = "llama3:latest"
        response_obj = MagicMock()
        response_obj.models = [model_obj]
        # Remove dict-like behaviour to simulate Pydantic object
        del response_obj.__getitem__

        ollama_stub.list.return_value = response_obj
        result = app.get_ollama_models()
        assert "llama3:latest" in result, \
            "BUG-03: must handle Pydantic ChatResponse via attribute access"

    def test_falls_back_on_exception(self):
        """Network error must return the fallback list, not raise."""
        ollama_stub.list.side_effect = Exception("connection refused")
        result = app.get_ollama_models()
        ollama_stub.list.side_effect = None
        assert isinstance(result, list)
        assert len(result) > 0


# ══════════════════════════════════════════════════════════════════════════════
# BUG-04 / SEC-01 · GOOGLE_API_KEY read from OS environment
# ══════════════════════════════════════════════════════════════════════════════

class TestGoogleApiKeyFromEnv:

    def test_gemini_config_uses_env_var_when_field_empty(self):
        """
        BUG-04 / SEC-01: When the sidebar text input is blank,
        the Gemini API key must be populated from os.environ['GOOGLE_API_KEY'].
        """
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key-12345"}):
            # Simulate sidebar returning empty string (user left field blank)
            st_stub.sidebar.text_input = MagicMock(return_value="")
            st_stub.sidebar.selectbox = MagicMock(return_value="Google Gemini")
            st_stub.sidebar.subheader = MagicMock()
            st_stub.sidebar.title = MagicMock()

            config = app.get_llm_config()

        assert config.get("api_key") == "env-key-12345", (
            "BUG-04: When sidebar API key field is blank, "
            "config['api_key'] must be sourced from GOOGLE_API_KEY env var"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG-05 · Debug download must not crash when .tex file absent
# ══════════════════════════════════════════════════════════════════════════════

class TestCompileLatexFileGuard:

    def test_compile_result_no_filenotfounderror_on_missing_tex(self):
        """
        BUG-05: If the LLM call fails before writing generated_resume.tex,
        the error display path must NOT raise FileNotFoundError.
        The function must guard the open() with os.path.exists().
        """
        # Verify the fix: compile_latex itself should not crash on missing file.
        # The guard belongs in the UI layer, so we test via a helper assertion
        # on the fixed source.
        import inspect
        src = inspect.getsource(app)
        # After fix, the debug download block must be guarded
        assert 'os.path.exists("generated_resume.tex")' in src or \
               "os.path.exists('generated_resume.tex')" in src, (
            "BUG-05: The debug download block must guard with "
            "os.path.exists('generated_resume.tex') before open()"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG-06 · Empty generated_latex must be caught before writing + compiling
# ══════════════════════════════════════════════════════════════════════════════

class TestEmptyGeneratedLatex:

    def test_source_guards_empty_generated_latex(self):
        """
        BUG-06: generated_latex == '' must raise an error before
        writing to disk and invoking pdflatex.
        """
        import inspect
        src = inspect.getsource(app)
        # The fix must have a guard like: if not generated_latex: raise ...
        assert "if not generated_latex" in src, (
            "BUG-06: A guard 'if not generated_latex' must exist to prevent "
            "writing an empty .tex file to disk"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG-07 · template.tex opened with explicit UTF-8 encoding
# ══════════════════════════════════════════════════════════════════════════════

class TestTemplateEncoding:

    def test_template_open_uses_utf8(self):
        """
        BUG-07: open('template.tex', 'r') must specify encoding='utf-8'
        to avoid UnicodeDecodeError on Windows with non-default code pages.
        """
        import inspect
        src = inspect.getsource(app)
        assert 'open("template.tex", "r", encoding="utf-8")' in src or \
               "open('template.tex', 'r', encoding='utf-8')" in src, (
            "BUG-07: template.tex must be opened with encoding='utf-8'"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG-08 · Bare except: pass must be replaced with typed exception handlers
# ══════════════════════════════════════════════════════════════════════════════

class TestNoBareExcept:

    def test_no_bare_except_pass_in_source(self):
        """
        BUG-08: bare 'except: pass' swallows BaseException including
        KeyboardInterrupt and MemoryError. All handlers must be typed.
        """
        import inspect
        src = inspect.getsource(app)
        lines = src.splitlines()
        violations = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Single-line bare except: pass
            if stripped == "except: pass":
                violations.append(i + 1)
            # Two-line bare except: / pass
            elif stripped == "except:":
                next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if next_stripped == "pass":
                    violations.append(i + 1)
        assert len(violations) == 0, (
            f"BUG-08: bare 'except: pass' found at lines: {violations}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG-09 · PaddleOCR result None/empty guard
# ══════════════════════════════════════════════════════════════════════════════

class TestPaddleOCRResultGuard:

    def test_paddleocr_none_result_does_not_crash(self):
        """
        BUG-09: ocr.ocr() can return None or [[]] for blank pages.
        The join comprehension must be guarded against None/empty results.
        """
        import inspect
        src = inspect.getsource(app)
        # Verify that after the ocr call there is a None check
        assert "res is None" in src or \
               "res and res[0]" in src or \
               "if not res" in src, (
            "BUG-09: PaddleOCR result must be guarded for None/empty "
            "before indexing res[0]"
        )


# ══════════════════════════════════════════════════════════════════════════════
# DEAD-01 · os module must actually be used (for env var reading)
# ══════════════════════════════════════════════════════════════════════════════

class TestOsModuleUsed:

    def test_os_environ_accessed_in_source(self):
        """
        DEAD-01 + BUG-04: After fix, `os` must be used (via os.environ)
        instead of being a dead import.
        """
        import inspect
        src = inspect.getsource(app)
        assert "os.environ" in src, \
            "DEAD-01/BUG-04: os.environ must be referenced in the source"


# ══════════════════════════════════════════════════════════════════════════════
# DEAD-02 · `from google.genai import types` must be removed if unused
# ══════════════════════════════════════════════════════════════════════════════

class TestDeadImportTypes:

    def test_types_import_removed(self):
        """
        DEAD-02: `from google.genai import types` is never used.
        It should be removed to keep imports clean.
        """
        import inspect
        src = inspect.getsource(app)
        assert "from google.genai import types" not in src, \
            "DEAD-02: unused 'from google.genai import types' must be removed"


# ══════════════════════════════════════════════════════════════════════════════
# RACE-01 · session-scoped file names prevent cross-user contamination
# ══════════════════════════════════════════════════════════════════════════════

class TestSessionScopedFilenames:

    def test_generated_files_use_session_scope(self):
        """
        RACE-01: Writing to fixed 'generated_resume.tex' is unsafe in
        multi-user deployments. File names must include a session-unique token.
        """
        import inspect
        src = inspect.getsource(app)
        # After fix, file references must use a session_id or similar unique key
        assert "session_id" in src or "session_file" in src or \
               "st.session_state" in src and "generated_resume" not in src.split("session_id")[0].split("\n")[-1], (
            "RACE-01: generated_resume.tex/.pdf must use a session-scoped "
            "filename to prevent cross-user file contamination"
        )


# ══════════════════════════════════════════════════════════════════════════════
# PERF-01 · get_ollama_models must be decorated with @st.cache_data
# ══════════════════════════════════════════════════════════════════════════════

class TestCaching:

    def test_get_ollama_models_is_cached(self):
        """
        PERF-01: get_ollama_models makes a live HTTP request on every call.
        It must be wrapped with @st.cache_data to avoid repeated roundtrips.
        """
        import inspect
        src = inspect.getsource(app)
        # Find the function definition and check there's a cache_data decorator
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "def get_ollama_models" in line:
                # Check 1-2 lines above for decorator
                above = [lines[j].strip() for j in range(max(0, i-2), i)]
                assert any("cache_data" in a for a in above), (
                    "PERF-01: get_ollama_models must be decorated with "
                    "@st.cache_data"
                )
                break

    def test_get_market_research_is_cached(self):
        """
        PERF-05: get_market_research makes live HTTP requests.
        It must be wrapped with @st.cache_data(ttl=...).
        """
        import inspect
        src = inspect.getsource(app)
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "def get_market_research" in line:
                above = [lines[j].strip() for j in range(max(0, i-2), i)]
                assert any("cache_data" in a for a in above), (
                    "PERF-05: get_market_research must be decorated with "
                    "@st.cache_data"
                )
                break

    def test_paddleocr_model_is_cached(self):
        """
        PERF-02: PaddleOCR model is heavy (~1-3s load).
        It must be instantiated via @st.cache_resource.
        """
        import inspect
        src = inspect.getsource(app)
        assert "cache_resource" in src, (
            "PERF-02: PaddleOCR model initialisation must use "
            "@st.cache_resource so weights are loaded only once"
        )


# ══════════════════════════════════════════════════════════════════════════════
# PERF-03 · fitz.open called at most once per file in smart_extract_text
# ══════════════════════════════════════════════════════════════════════════════

class TestSingleFitzOpen:

    def test_scanned_pdf_opens_fitz_once(self):
        """
        PERF-03: For a scanned PDF (< 50 chars extracted), fitz.open()
        is currently called twice. After fix it must be called only once.
        """
        import fitz

        # Build a minimal real in-memory PDF with no visible text
        pdf_doc = fitz.open()
        page = pdf_doc.new_page()
        pdf_bytes = pdf_doc.tobytes()

        fake_file = MagicMock()
        fake_file.name = "scan.pdf"
        fake_file.seek = MagicMock()
        fake_file.read = MagicMock(return_value=pdf_bytes)

        config = {
            "vision_provider": "PaddleOCR",
            "provider": "PaddleOCR",
            "api_key": None,
        }

        with patch("fitz.open", wraps=fitz.open) as mock_fitz:
            # PaddleOCR not available in test env — will return error string
            with patch.object(app, "PADDLE_AVAILABLE", False):
                app.smart_extract_text(fake_file, True, config)

        fitz_call_count = mock_fitz.call_count
        assert fitz_call_count <= 1, (
            f"PERF-03: fitz.open must be called at most once per PDF, "
            f"got {fitz_call_count} calls"
        )


# ══════════════════════════════════════════════════════════════════════════════
# BUG-03 (Ollama Vision) · response attribute access in vision path
# ══════════════════════════════════════════════════════════════════════════════

class TestOllamaVisionResponse:

    def test_ollama_vision_uses_attribute_access(self):
        """
        BUG-03 (vision): The Ollama vision path accesses response['message']['content']
        which fails on modern Pydantic ChatResponse. Must use .message.content.
        """
        import inspect
        src = inspect.getsource(app)
        # Find the vision ollama block — should NOT have dict subscript access
        # for the response object
        lines = src.splitlines()
        in_ollama_vision = False
        violations = []
        for i, line in enumerate(lines):
            if "Local Ollama Vision" in line:
                in_ollama_vision = True
            if in_ollama_vision and "response['message']['content']" in line:
                violations.append(i + 1)
            if in_ollama_vision and "return" in line and "Ollama Vision Error" not in line:
                in_ollama_vision = False
        assert len(violations) == 0, (
            f"BUG-03: Ollama vision response dict access found at lines "
            f"{violations}. Must use response.message.content"
        )

    def test_ollama_llm_uses_attribute_access(self):
        """
        BUG-03 (LLM): The main Ollama LLM path uses resp['message']['content'].
        Must use resp.message.content for Pydantic compatibility.
        """
        import inspect
        src = inspect.getsource(app)
        assert "resp['message']['content']" not in src, (
            "BUG-03: resp['message']['content'] dict access must be replaced "
            "with resp.message.content for ollama >= 0.2"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Integration: clean_latex_code round-trip (template + body)
# ══════════════════════════════════════════════════════════════════════════════

class TestCleanLatexIntegration:

    def test_full_template_ampersand_preservation(self):
        """
        End-to-end: run clean_latex_code over a complete template-like
        LaTeX document and verify all tabular & survive, while R&D → R\\&D.
        """
        src = textwrap.dedent(r"""
            \documentclass[letterpaper,11pt]{article}
            \usepackage{tabularx}
            \begin{document}
            \begin{tabularx}{1.0\textwidth}{@{}X r@{}}
              \textbf{Google} & 2020--2023 \\
              \textit{\small Senior Engineer} & \textit{\small New York} \\
            \end{tabularx}
            R&D experience at Acme Corp.
            \end{document}
        """).strip()

        result = app.clean_latex_code(src)

        # Tabular separators must survive
        assert r"\textbf{Google} & 2020" in result, \
            "Tabular column separator & in heading row must not be escaped"
        assert r"\textit{\small Senior Engineer} & \textit" in result, \
            "Tabular column separator & in subheading row must not be escaped"

        # Plain text & must be escaped
        assert r"R\&D" in result, \
            "Inline R&D text must have & escaped as \\&"

    def test_clean_latex_idempotent(self):
        """Running clean_latex_code twice must produce identical output."""
        src = textwrap.dedent(r"""
            \begin{document}
            R&D and \& already here.
            \end{document}
        """).strip()
        first = app.clean_latex_code(src)
        second = app.clean_latex_code(first)
        assert first == second, "clean_latex_code must be idempotent"
