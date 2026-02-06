# 🚀 Universal AI Resume Builder v2.0

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange)
![LaTeX](https://img.shields.io/badge/LaTeX-Professional%20Format-green)

A professional, multi-modal AI Resume Builder that combines **Computer Vision**, **Market Research**, and **LLMs** to craft tailored, ATS-friendly LaTeX resumes.

It supports **Local LLMs (Ollama)** for zero-cost generation and **Cloud APIs** (OpenAI, Gemini, Anthropic) for maximum power.

## ✨ Key Features

*   **📄 Universal Smart Parser**: Handles EVERYTHING.
    *   Standard PDFs & DOCX files.
    *   **Images & Scanned Docs**: Uses Vision LLMs (Gemini/GPT-4o) or PaddleOCR to transcribe text from images (PNG/JPG) or flat PDFs.
*   **🧠 Intelligent Market Research**: Automatically searches the web for the latest trends and keywords for your target role using DuckDuckGo.
*   **🎨 Professional Formatting**: Generates high-quality PDFs using a structured LaTeX template.
*   **🤖 Multi-Model Support**:
    *   **Local**: Auto-detects installed **Ollama** models (Llama 3, Mistral, Gemma).
    *   **Cloud**: Support for **OpenAI** (GPT-4o), **Google Gemini** (1.5/2.5 Flash), and **Anthropic** (Claude 3.5 Sonnet).
*   **👁️ Flexible Vision Pipeline**: Choose between local OCR (Paddle/Ollama Vision) or Cloud Vision (Gemini/GPT) for extracting text from messy resumes.

## 🛠️ Prerequisites

Before running the app, ensure you have the following installed:

1.  **Python 3.9+**
2.  **LaTeX Distribution** (Required for PDF compilation):
    *   **Windows**: [MikTeX](https://miktex.org/download) (Recommended) or TeX Live.
    *   **Mac**: MacTeX.
    *   **Linux**: `sudo apt-get install texlive-full`.
3.  **Ollama** (Optional, for local privacy):
    *   Download from [ollama.com](https://ollama.com).
    *   Pull a model: `ollama pull llama3` or `ollama pull glm4`.

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/ai-resume-builder.git
    cd ai-resume-builder
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Verify LaTeX**
    Ensure `pdflatex` is in your system PATH by running:
    ```bash
    pdflatex --version
    ```

## 🏃‍♂️ How to Run

1.  Start the Streamlit application:
    ```bash
    streamlit run app.py
    ```

2.  The app will open in your browser at `http://localhost:8501`.

## 📖 Usage Guide

**Step 1: Input & Extraction**
*   **Upload**: Drag & drop your current resume (PDF, Word, or Image).
*   **Target Role**: Enter the job title you are applying for (e.g., "Senior Data Scientist").
*   **Analyze**: The app uses the "Smart Parser" to extract text and researches market trends for that role.

**Step 2: Review & Generate**
*   **Edit**: Review the extracted text and the market research summary. You can manually tweak them if needed.
*   **Select Model**: Open the sidebar to choose your LLM provider (Ollama for free local use, or enter API keys for cloud models).
*   **Draft Resume**: Click generate. The AI will write a LaTeX resume incorporating your data + market keywords.
*   **Download**: Get the compiled **PDF** or the **Source Code (.tex)**.

## 📦 Project Structure

```
├── app.py                # Main application logic
├── template.tex          # LaTeX Resume Template
├── requirements.txt      # Python dependencies
├── generated_resume.pdf  # (Ignored) Temporary output
└── README.md             # Documentation
```

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
[MIT](https://choosealicense.com/licenses/mit/)
