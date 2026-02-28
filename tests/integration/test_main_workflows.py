from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestMainWorkflow:
    def test_main_step1_analyze_advances_to_step2_target_app_py(self, app_ctx):
        app_ctx.st.session_state.clear()
        app_ctx.st.text_input = MagicMock(return_value="Data Scientist")
        app_ctx.st.text_area = MagicMock(side_effect=["JD text", "Resume body"])
        app_ctx.st.radio = MagicMock(return_value="Raw Text")
        app_ctx.st.button = MagicMock(return_value=True)

        with patch.object(app_ctx.app, "get_llm_config", return_value={"provider": "Ollama", "vision_provider": "Same as LLM", "model": "m1", "api_key": None, "base_url": None}):
            with patch.object(app_ctx.app, "smart_extract_text", return_value="Extracted"):
                with patch.object(app_ctx.app, "get_market_research", return_value="Trends"):
                    app_ctx.app.main()

        assert app_ctx.st.session_state.step == 2
        assert app_ctx.st.session_state.extracted_text == "Extracted"
        assert app_ctx.st.session_state.research == "Trends"
        assert app_ctx.st.rerun.call_count == 1

    def test_main_step2_generate_compile_failure_sets_error_target_app_py(self, app_ctx):
        app_ctx.st.session_state.clear()
        app_ctx.st.session_state.step = 2
        app_ctx.st.session_state.extracted_text = "Profile"
        app_ctx.st.session_state.research = "Research"
        app_ctx.st.session_state.target_role = "Engineer"
        app_ctx.st.session_state.job_desc = "JD"
        app_ctx.st.text_area = MagicMock(side_effect=["Profile", "Research"])
        app_ctx.st.button = MagicMock(side_effect=[False, True])

        with patch.object(app_ctx.app, "get_llm_config", return_value={"provider": "Ollama", "vision_provider": "Same as LLM", "model": "m1", "api_key": None, "base_url": None}):
            app_ctx.app.ollama.chat.return_value = SimpleNamespace(message=SimpleNamespace(content="\\begin{document}ok\\end{document}"))
            with patch.object(app_ctx.app, "compile_latex", return_value=(False, "latex failed")):
                app_ctx.app.main()

        assert app_ctx.st.session_state.generated_success is False
        assert app_ctx.st.session_state.generation_error == "latex failed"

    def test_main_step2_generate_success_persists_download_data_target_app_py(self, app_ctx, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "template.tex").write_text("\\begin{document}X\\end{document}", encoding="utf-8")

        app_ctx.st.session_state.clear()
        app_ctx.st.session_state.step = 2
        app_ctx.st.session_state.extracted_text = "Profile"
        app_ctx.st.session_state.research = "Research"
        app_ctx.st.session_state.target_role = "Engineer"
        app_ctx.st.session_state.job_desc = "JD"
        app_ctx.st.text_area = MagicMock(side_effect=["Profile", "Research"])
        app_ctx.st.button = MagicMock(side_effect=[False, True])

        def _compile_and_emit_pdf(_tex_filename):
            with open("generated_resume.pdf", "wb") as f:
                f.write(b"%PDF-1.4 test")
            return True, "Compilation successful."

        with patch.object(app_ctx.app, "get_llm_config", return_value={"provider": "Ollama", "vision_provider": "Same as LLM", "model": "m1", "api_key": None, "base_url": None}):
            app_ctx.app.ollama.chat.return_value = SimpleNamespace(message=SimpleNamespace(content="\\begin{document}ok\\end{document}"))
            with patch.object(app_ctx.app, "compile_latex", side_effect=_compile_and_emit_pdf):
                app_ctx.app.main()

        assert app_ctx.st.session_state.generated_success is True
        assert app_ctx.st.session_state.generated_pdf_data.startswith(b"%PDF-1.4")
        assert b"\\begin{document}" in app_ctx.st.session_state.generated_tex_data
        assert app_ctx.st.download_button.call_count == 2
