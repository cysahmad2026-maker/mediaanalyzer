# SocialIQ – AI Social Media Analyzer

**Analyze. Understand. Optimize. Grow.**

SocialIQ is a Streamlit dashboard for creators, universities, student societies, businesses, and digital marketers. It reviews poster design and captions, calculates engagement from manually entered metrics, evaluates hashtags, generates content ideas, and classifies audience comments.

> **Important:** SocialIQ does not log in to Instagram, Facebook, TikTok, LinkedIn, or other platforms. It does not fetch live account analytics, trend volumes, or audience data. Engagement metrics must be entered by the user.

## Features

- **AI Post & Poster Analyzer:** JPG/JPEG/PNG upload, visual hierarchy, readability, color, typography, CTA feedback, improvement suggestions, and a score out of 100.
- **AI Caption Analyzer:** Grammar, clarity, tone, readability, CTA and engagement review, with professional, creative, formal, and short rewrites.
- **Engagement Analyzer:** Interactions, engagement by reach and by impressions, breakdown chart, and practical recommendations.
- **Hashtag Analyzer:** Duplicate and topical-fit review plus niche, community, topic, and broad suggestions. It does not report live hashtag popularity.
- **AI Content Generator:** Captions, post ideas, hashtags, CTAs, titles, and a 7-day calendar.
- **Audience Sentiment Analyzer:** Positive, Neutral, and Negative classification, topic summaries, and audience-feedback actions.
- **Comprehensive Report:** Consolidated results with JSON export.
- **Demo mode:** Explore the full interface without an API key. Demo analysis is illustrative and is not a substitute for live AI review.

## Screenshots

Add application screenshots here after running the app:

| Dashboard | Analyzer |
|---|---|
| `![Dashboard](screenshots/dashboard.png)` | `![Analyzer](screenshots/analyzer.png)` |

The screenshot paths above are documentation placeholders; this project intentionally contains only the three requested files.

## Technology stack

- Python 3.10+
- Streamlit
- OpenAI Python SDK (Responses API)
- Plotly
- Pillow
- Pandas

## Prerequisites

- Python 3.10 or newer
- pip
- An OpenAI API key for live AI mode (optional; demo mode works without one)

Check your Python version:

```bash
python --version
```

## Installation

### 1. Create and enter the project directory

Save `app.py`, `requirements.txt`, and `README.md` in the same directory.

```bash
cd path/to/socialiq
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## API key configuration

Demo mode is enabled by default and does not need an API key.

To use live AI analysis, configure `OPENAI_API_KEY`. Never paste a private key into source code or commit it to a public repository.

### Option A: Environment variable

**Windows PowerShell:**

```powershell
$env:OPENAI_API_KEY="your-api-key"
```

**Windows Command Prompt:**

```bat
set OPENAI_API_KEY=your-api-key
```

**macOS / Linux:**

```bash
export OPENAI_API_KEY="your-api-key"
```

### Option B: Streamlit secrets

Create `.streamlit/secrets.toml` in your local Streamlit project directory:

```toml
OPENAI_API_KEY = "your-api-key"
```

Streamlit secrets are outside the three application source files. Do not publish this file or commit it to version control. On Streamlit Community Cloud, add the same key in the app's **Settings → Secrets**.

### Model selection

The default model is `gpt-4.1-mini`, which supports image and text inputs. To choose another compatible model, set the `OPENAI_MODEL` environment variable:

```bash
export OPENAI_MODEL="gpt-4.1-mini"
```

On Windows PowerShell:

```powershell
$env:OPENAI_MODEL="gpt-4.1-mini"
```

The selected model must be available to the API key and support image input for poster analysis.

## Run the application

From the project directory, with the virtual environment activated:

```bash
streamlit run app.py
```

Streamlit will print a local URL, normally `http://localhost:8501`. Open it in your browser.

## Demo mode

1. Start the app using the command above.
2. Keep **Demo mode (no API key required)** enabled in the sidebar.
3. Try the poster and caption analyzers, enter engagement numbers, paste hashtags and comments, or generate sample content.

Demo behavior is intentionally transparent:
- Poster and caption results are illustrative sample feedback.
- Hashtag suggestions are rule-based examples and do not use live trend data.
- Sentiment classification uses a small keyword-based demonstration and can miss context, sarcasm, and nuance.
- Engagement calculations use the exact values entered by the user.
- Content generation returns a sample template.

Disable Demo mode only after configuring a valid API key to use live AI features.

## Usage guide

1. **Dashboard:** View the current session's completed analyses.
2. **Poster Analyzer:** Upload a JPG, JPEG, or PNG and select Analyze poster.
3. **Caption Analyzer:** Paste a caption and select Analyze caption.
4. **Engagement:** Enter likes, comments, shares, saves, reach, and impressions. The app calculates:
   - Total interactions = likes + comments + shares + saves
   - Engagement by reach = total interactions ÷ reach × 100
   - Engagement by impressions = total interactions ÷ impressions × 100
5. **Hashtags:** Enter the caption/topic and existing hashtags.
6. **Content Generator:** Select an output type and provide topic, platform, audience, tone, and optional direction.
7. **Audience Sentiment:** Paste up to 200 comments, one per line.
8. **Comprehensive Report:** Review available module results and download the session report as JSON.

## Privacy and security

- API keys are read from Streamlit secrets or environment variables.
- API keys are not stored in the source code or displayed in the interface.
- In live mode, the selected text and/or uploaded image are sent to the configured AI provider for processing.
- Do not submit confidential, personal, or sensitive information unless you are authorized to share it.
- Uploaded images and analysis results are held in Streamlit session state during the session; they are not saved to a project database by this application.

## Project limitations

- No direct social media account connection or automatic analytics ingestion.
- No live hashtag volume, trend, competitor, or follower-growth data.
- Engagement rates are descriptive calculations; there is no universal benchmark that applies to every platform, niche, format, and audience.
- Image text extraction and spelling checks depend on what the vision model can read; always proofread dates, names, links, and contact details manually.
- AI output can be inaccurate or biased. Review recommendations before publishing.
- Demo mode is illustrative and must not be presented as a real AI audit.
- Results are session-based; persistent user accounts, databases, and historical comparisons are not included.

## Future improvements

- Official platform API integrations with explicit user authorization.
- Historical post tracking and campaign comparisons.
- Export to PDF and branded reports.
- OCR-assisted poster text extraction and language-specific proofreading.
- Custom scoring profiles by platform and content format.
- Team workspaces, user authentication, and database-backed history.
- Scheduled content calendars and approval workflows.

## Contribution guidelines

1. Fork the repository and create a focused feature branch.
2. Keep secrets out of source control.
3. Use clear function names, type hints, and concise comments.
4. Validate user inputs and handle API/network errors gracefully.
5. Test both demo mode and live AI mode where possible.
6. Update this README when adding dependencies or changing setup instructions.
7. Submit a pull request describing the change and its testing.

## License

Choose and add a license before distributing this project publicly. Until a license is added, all rights remain with the copyright holder.
