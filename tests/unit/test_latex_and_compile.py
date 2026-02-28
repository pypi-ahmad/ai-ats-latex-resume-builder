from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestValidateLatexSafety:
    """Tests for the expanded validate_latex_safety function."""

    def test_safe_document_passes(self, app_ctx):
        safe_tex = r"\documentclass{article}\begin{document}Hello\end{document}"
        ok, msg = app_ctx.app.validate_latex_safety(safe_tex)
        assert ok is True
        assert msg == ""

    def test_blocks_write18(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety(r"\write18{rm -rf /}")
        assert ok is False

    def test_blocks_openout(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety(r"\openout\myfile=output.txt")
        assert ok is False

    def test_blocks_read(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety(r"\read16 to \myline")
        assert ok is False

    def test_blocks_shellesc_package(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety(r"\usepackage{shellesc}")
        assert ok is False

    def test_blocks_input_pipe(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety(r"\input{|\"cat /etc/passwd\"}")
        assert ok is False

    def test_blocks_catcode(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety(r"\catcode`\@=11")
        assert ok is False

    def test_blocks_csname(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety(r"\csname write\endcsname")
        assert ok is False

    def test_blocks_shell_escape_flag(self, app_ctx):
        ok, _ = app_ctx.app.validate_latex_safety("% --shell-escape trick")
        assert ok is False

    def test_no_shell_escape_in_compile_cmd(self, app_ctx):
        """Ensure the pdflatex command never includes --shell-escape."""
        import inspect
        src = inspect.getsource(app_ctx.app.compile_latex)
        assert "--shell-escape" not in src


class TestLatexHelpers:
    def test_escape_ampersands_outside_tabular_target_app_py(self, app_ctx):
        body = (
            "Plain R&D line\n"
            "\\begin{tabularx}{\\textwidth}{X r}\n"
            "Name & Value \\\\n"
            "\\end{tabularx}\n"
            "Another A&B line"
        )
        result = app_ctx.app._escape_ampersands_outside_tabular(body)
        assert "R\\&D" in result
        assert "A\\&B" in result
        assert "Name & Value" in result

    def test_clean_latex_code_strips_fences_and_preserves_tabular_target_app_py(self, app_ctx):
        src = (
            "```latex\n"
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "R&D\n"
            "\\begin{tabularx}{\\textwidth}{X r}\n"
            "A & B \\\\n"
            "\\end{tabularx}\n"
            "\\end{document}\n"
            "```"
        )
        result = app_ctx.app.clean_latex_code(src)
        assert "```" not in result
        assert "R\\&D" in result
        assert "A & B" in result


class TestCompileLatex:
    def test_compile_latex_pdflatex_missing_target_app_py(self, app_ctx):
        with patch.object(app_ctx.app.subprocess, "run", side_effect=FileNotFoundError):
            success, msg = app_ctx.app.compile_latex("resume.tex")
        assert success is False
        assert "pdflatex" in msg.lower()

    def test_compile_latex_runs_two_passes_target_app_py(self, app_ctx):
        with patch.object(app_ctx.app.subprocess, "run") as run_mock:
            run_mock.side_effect = [
                MagicMock(returncode=0),
                MagicMock(returncode=0, stdout="", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            success, msg = app_ctx.app.compile_latex("resume.tex")

        assert success is True
        assert msg == "Compilation successful."
        compile_calls = [
            c for c in run_mock.call_args_list
            if c.args and c.args[0] == ["pdflatex", "-interaction=nonstopmode", "resume.tex"]
        ]
        assert len(compile_calls) == 2

    def test_compile_latex_returns_log_on_failure_target_app_py(self, app_ctx):
        with patch.object(app_ctx.app.subprocess, "run") as run_mock:
            run_mock.side_effect = [
                MagicMock(returncode=0),
                MagicMock(returncode=1, stdout="latex error", stderr="fatal"),
            ]
            success, msg = app_ctx.app.compile_latex("resume.tex")

        assert success is False
        assert "latex error" in msg
        assert "fatal" in msg
