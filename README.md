# AI ATS LaTeX Resume Builder

Streamlit application that ingests resume input (file or raw text), performs optional OCR/vision extraction for scanned content, enriches input with market-trend snippets, generates LaTeX through a selected LLM provider, validates/sanitizes the LaTeX, and compiles a downloadable PDF.

## 1) Project Overview

### What the system does
- Collects target role, optional job description, and resume input in a 2-step UI flow.
- Extracts text from `pdf`, `docx`, `txt`, `png`, `jpg` sources using native parsing first, then OCR/vision fallback.
- Fetches role-specific market trend snippets using DuckDuckGo (`ddgs`).
- Generates LaTeX resume content using one of: Ollama, OpenAI, Google Gemini, Anthropic.
- Cleans LLM output and validates it against blocked LaTeX patterns before compilation.
- Compiles LaTeX via `pdflatex` and exposes PDF/source download buttons.

### Key capabilities (implemented)
- Session-scoped artifact naming via `generated_resume_<session_id>.tex/.pdf`.
- Cached model/service operations (`@st.cache_data`, `@st.cache_resource`) for key repeated calls.
- Persistent Streamlit session state across reruns for workflow continuity.
- Explicit error surfacing for extraction, provider, and compile failures.

### Problem solved
- Reduces manual effort of tailoring resumes to a target role by combining extraction, trend context, and LLM-driven LaTeX generation in a single UI workflow.

## 2) Architecture Overview

> Source of truth: `app.py` (single-module runtime). No `backend.py` exists in this repository.

| Component | File | Responsibility |
|---|---|---|
| UI layer | `app.py` (`main`) | Renders Streamlit UI, controls step transitions, stores session state, displays outputs/errors |
| Logic + integrations | `app.py` (helpers) | OCR/vision extraction, market research, LLM calls, LaTeX cleaning/safety checks, compile orchestration |
| Resume template | `template.tex` | Prompt-injected LaTeX scaffold used during generation |
| Tests | `tests/` | Unit + integration validation for parser, config, generation and workflow behaviors |

### Workflow/agent system
- There is no explicit agent graph or workflow engine module.
- Workflow is implemented as imperative branch logic in `main()` and helper functions.

## 3) System Flow

### Step-by-step execution
1. App starts and renders sidebar config via `get_llm_config()`.
2. Step 1 captures `target_role`, optional `job_desc`, and input source (`File Upload` or `Raw Text`).
3. On **Analyze Profile**:
    - `smart_extract_text()` extracts text (native first, vision fallback if needed).
    - `get_market_research()` fetches top DuckDuckGo snippets.
    - On success, state is saved and workflow advances to Step 2.
4. Step 2 displays editable `extracted_text` and `research`.
5. On **Draft Resume (Generate LaTeX)**:
    - `template.tex` is loaded.
    - Provider-specific LLM call generates LaTeX.
    - Output is checked for emptiness, then passed through `clean_latex_code()` and `validate_latex_safety()`.
    - Session-scoped `.tex` file is written and compiled by `compile_latex()`.
6. On compile success, PDF/TEX bytes are stored in session state and download buttons are shown.
7. On failure, compile/generation log is shown and source debug download is offered when file exists.

```mermaid
flowchart TD
     A[Start app.py / main] --> B[get_llm_config]
     B --> C[Step 1 Input: role + resume source]
     C --> D{Analyze Profile clicked}
     D -->|No| C
     D -->|Yes| E[smart_extract_text]
     E --> F{Extraction valid?}
     F -->|No| G[Show error and stop current action]
     F -->|Yes| H[get_market_research]
     H --> I[Save state and move to Step 2]
     I --> J[Review/edit extracted_text + research]
     J --> K{Draft Resume clicked}
     K -->|No| J
     K -->|Yes| L[Load template.tex]
     L --> M[Call selected LLM provider]
     M --> N[clean_latex_code]
     N --> O[validate_latex_safety]
     O --> P{Safe + non-empty?}
     P -->|No| Q[Set generation_error]
     P -->|Yes| R[Write session-scoped .tex]
     R --> S[compile_latex (2 passes)]
     S --> T{Compile success?}
     T -->|Yes| U[Store PDF/TEX bytes in session state]
     U --> V[Show download buttons]
     T -->|No| W[Show error log + debug source download]
```

## 4) Workflow Logic

### UI workflow nodes
- **Node 1 (Input/Analysis):** collects user input and runs extraction + market research.
- **Node 2 (Review/Generate):** allows editing extracted content, then generates/compiles resume.

### State transitions
- `step = 1` → initial input stage.
- `step = 2` → review/generation stage.
- Transition occurs only after successful analysis action.
- Back navigation in Step 2 resets to `step = 1`.

### Conditional routing (implemented)
- Input method: file upload vs raw text.
- Extraction branch by file type (`pdf`, `docx`, `txt`, image types).
- Vision branch by selected provider (`Same as LLM`, `PaddleOCR`, `Google Gemini (Free Tier)`, `Local Ollama Vision`).
- LLM generation branch by provider (`Ollama`, `OpenAI`, `Google Gemini`, `Anthropic`).

### Retry mechanisms
- No explicit retry loop for network/provider calls.
- `compile_latex()` intentionally executes two pdflatex passes for reference resolution, not as an error retry.

## 5) Data Model / State Structure

### Sidebar config object (`get_llm_config`)

| Key | Type | Purpose |
|---|---|---|
| `provider` | `str` | Selected LLM provider |
| `model` | `str` | Selected/entered model name |
| `api_key` | `str | None` | Provider API key (where required) |
| `base_url` | `str | None` | OpenAI-compatible base URL |
| `vision_provider` | `str` | Vision/OCR mode |
| `vision_api_key` | `str` (optional) | Separate key when Gemini vision is used with non-Gemini LLM |
| `vision_model` | `str` (optional) | Ollama vision model selection |

### Session state keys (`main`)

| Key | Type | Purpose |
|---|---|---|
| `step` | `int` | Current workflow stage (`1` or `2`) |
| `extracted_text` | `str` | Parsed/edited profile content |
| `research` | `str` | Market trend snippets |
| `target_role` | `str` | User-specified role |
| `job_desc` | `str` | Optional job description |
| `generated_success` | `bool` | Last generation success flag |
| `generated_pdf_data` | `bytes | None` | Compiled PDF bytes for download |
| `generated_tex_data` | `bytes | None` | Generated TEX bytes for download |
| `generation_error` | `str | None` | Error message/log for UI display |
| `session_id` | `str` | UUID hex token for per-session artifact filenames |

## 6) Core Modules Breakdown

| Function | Purpose | Input | Output | Behavior |
|---|---|---|---|---|
| `_escape_ampersands_outside_tabular(body)` | Escape bare `&` only outside tabular environments | `str` | `str` | Splits around `tabular/tabularx/tabular*` blocks and escapes non-escaped `&` in non-tabular sections |
| `clean_latex_code(text)` | Normalize LLM LaTeX output | `str` | `str` | Removes markdown fences; applies context-aware ampersand escaping in document body |
| `validate_latex_safety(text)` | Pattern-based LaTeX safety filter | `str` | `(bool, str)` | Rejects blocked patterns (`\write18`, `\openout`, `\read`, `\catcode`, `\csname`, pipe-input, etc.) |
| `compile_latex(tex_filename)` | Compile `.tex` to PDF | `str` path | `(bool, str)` | Checks `pdflatex` availability once per process; runs two compile passes; returns success or logs |
| `get_market_research(role)` | Fetch role trends | `str` | `str` | Uses DDGS search query and returns bullet summary; cached for 1 hour |
| `get_ollama_models()` | Enumerate local Ollama models | none | `list[str]` | Handles object/dict response shapes; returns fallback list on errors; cached 60s |
| `get_llm_config()` | Build sidebar config | none | `dict` | Renders provider-specific fields and vision options; supports `GOOGLE_API_KEY` fallback |
| `_get_paddle_ocr()` | Create OCR engine | none | `PaddleOCR` instance | Cached resource factory (`use_angle_cls=True`, `lang='en'`, `show_log=False`) |
| `smart_extract_text(input_data, is_file, config)` | Unified parser | file/text + config | `str` | Native parse first; fallback image conversion; provider-specific OCR/vision extraction; returns extracted text or error string |
| `main()` | End-to-end UI orchestration | none | none | Two-step flow with state handling, generation pipeline, compile handling, and download UI |

## 7) Security Model

Implemented protections:

1. **Generated LaTeX validation**
    - Blocks specific dangerous primitives/patterns before writing/compiling.
    - Examples: `\write18`, `\openout`, `\read`, `\catcode`, `\csname`, `\input{|...}`, `--shell-escape`.

2. **Compile command constraints**
    - `compile_latex()` runs `pdflatex -interaction=nonstopmode <file>`.
    - No `--shell-escape` flag is included by the app command path.

3. **Scoped artifact naming**
    - Uses `session_id` in output filenames to reduce cross-session file collisions.

Important scope note:
- Safety validation is regex/pattern based. It is not a full LaTeX sandbox or formal parser.

## 8) LLM / Provider Integration

### Resume generation providers (`provider`)
- `Ollama` (local `ollama.chat`)
- `OpenAI` (`OpenAI` client with configurable `base_url` + model)
- `Google Gemini` (`google.genai` preferred, legacy fallback import path supported)
- `Anthropic` (`anthropic.Anthropic`)

### Vision/OCR providers (`vision_provider`)
- `Same as LLM`
- `PaddleOCR`
- `Google Gemini (Free Tier)`
- `Local Ollama Vision`

### Selection and fallback behavior
- Vision provider can be independent of generation provider.
- When Gemini is selected, API key can come from sidebar input or `GOOGLE_API_KEY` env variable.
- Ollama model list retrieval has fallback defaults on errors.
- Generation and vision paths return provider-specific error messages when calls fail.

## 9) Setup & Installation

### 1. Create and activate virtual environment

```bash
python -m venv venv
```

Windows (PowerShell):

```powershell
venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Ensure `pdflatex` is installed and on PATH
- Required by `compile_latex()`.
- If unavailable, app returns: `pdflatex not found. Please ensure MikTeX or TeX Live is installed and in your PATH.`

### 4. Optional provider prerequisites
- Local Ollama runtime (if using Ollama providers).
- API keys for OpenAI / Anthropic / Gemini as applicable.

## 10) Running the Application

Start Streamlit:

```bash
streamlit run app.py
```

Expected UI behavior:
- Sidebar with LLM + Vision configuration.
- Main page title: `🚀 AI Resume Builder`.
- Step 1: profile/target input and analysis trigger.
- Step 2: editable extracted text + market insights and generation trigger.
- On success: download buttons for `resume.pdf` and `resume.tex`.
- On failure: error display with expandable compile/generation log.

## 11) Testing

### Framework
- `pytest` (configured via `pytest.ini`, `testpaths = tests`, `addopts = -q`).

### Test suites in repository
- Unit: `tests/unit/test_latex_and_compile.py`
- Unit: `tests/unit/test_services_and_config.py`
- Unit: `tests/unit/test_smart_extract_text.py`
- Integration: `tests/integration/test_main_workflows.py`
- Additional legacy-style suite: `tests/test_app.py`

### Run tests

```bash
python -m pytest -q tests
```

### Latest local verification
- Last observed local command: `python -m pytest -q tests`
- Last observed result: exit code `0` (successful run)

Optional coverage command (example reflected in repository report usage):

```bash
python -m pytest tests/unit tests/integration --cov=app --cov-report=term-missing -q
```

Coverage insight visible in repo artifacts:
- `TEST_REPORT.md` records a full-suite run result of `52 passed` at report time.

## 12) Limitations

Code-observed constraints:

1. **No separate backend module**
    - Entire runtime logic resides in `app.py`.

2. **Pattern-based LaTeX safety only**
    - `validate_latex_safety()` blocks listed patterns but does not provide complete sandboxing.

3. **Extraction contract uses strings for both success and errors**
    - `smart_extract_text()` returns error messages as plain strings; caller relies on prefix checks.

4. **PDF image fallback is first-page only**
    - For scanned PDFs, image conversion path processes only page index `0`.

5. **External dependency sensitivity**
    - Market research requires network.
    - Provider calls require reachable services and valid keys/models.
    - PDF output requires local `pdflatex`.

6. **State/file scope model**
    - Session-scoped names are used, but files are still written to the working directory.

## 13) Future Improvements (grounded by current code)

Potential next steps directly implied by current implementation patterns:

1. Replace string-based extraction error signaling with structured result objects (e.g., `{ok, text, error}`).
2. Extend scanned-PDF OCR/vision fallback from first page to multi-page processing.
3. Add a dedicated backend module if separation of UI and business logic is desired (current code is single-file).
4. Add stronger LaTeX validation/sandboxing beyond regex pattern checks.

## License

See `LICENSE`.
