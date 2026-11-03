"""
SocialIQ – AI Social Media Analyzer
Run with: streamlit run app.py
Python 3.10+
"""
from __future__ import annotations

import base64
import json
import os
import re
from datetime import date, timedelta
from io import BytesIO
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image, UnidentifiedImageError

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ----------------------------- Configuration -----------------------------
APP_TITLE = "SocialIQ – AI Social Media Analyzer"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
      h1, h2, h3 { font-family: 'Manrope', sans-serif; letter-spacing: -0.035em; }
      .hero { padding: 1.35rem 1.55rem; border-radius: 18px; margin-bottom: 1rem;
              background: linear-gradient(115deg, #18243b 0%, #253c60 55%, #356b78 100%);
              color: white; }
      .hero h1 { color: white; margin: 0; font-size: 2.25rem; }
      .hero p { color: #dce8f5; margin: .35rem 0 0 0; font-size: 1rem; }
      .muted { color: #8290a5; font-size: .88rem; }
      .metric-card { border: 1px solid rgba(128,145,170,.25); border-radius: 14px;
                     padding: 1rem 1.1rem; min-height: 112px; }
      .metric-label { color: #8290a5; font-size: .82rem; font-weight: 600; }
      .metric-value { font-size: 1.8rem; font-weight: 800; margin-top: .25rem; }
      .section-kicker { color: #319b9b; font-size: .75rem; font-weight: 800;
                        letter-spacing: .12em; text-transform: uppercase; }
      div[data-testid="stMetric"] { border: 1px solid rgba(128,145,170,.22);
        padding: 13px 15px; border-radius: 13px; }
      .stButton>button { border-radius: 9px; font-weight: 650; }
      [data-testid="stSidebar"] { border-right: 1px solid rgba(128,145,170,.18); }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------- Session state -----------------------------
DEFAULT_STATE = {
    "poster_result": None,
    "caption_result": None,
    "engagement_result": None,
    "hashtag_result": None,
    "sentiment_result": None,
    "generated_content": None,
    "poster_name": None,
    "caption_text": "",
    "hashtags_text": "",
    "comments_text": "",
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ----------------------------- AI utilities -----------------------------
def get_api_key() -> str | None:
    """Read a key from Streamlit secrets first, then environment variables."""
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret_key = None
    return secret_key or os.getenv("OPENAI_API_KEY")


def get_client() -> OpenAI | None:
    key = get_api_key()
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key)


def ai_available() -> bool:
    return get_client() is not None


def extract_json(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating Markdown fences and surrounding text."""
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise ValueError("The AI response was not valid JSON. Please try again.")
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("The AI response format was unexpected.")
    return data


def call_ai(prompt: str, image: Image.Image | None = None, temperature: float = 0.4) -> dict[str, Any]:
    """Call OpenAI Responses API. Returns a parsed JSON object."""
    client = get_client()
    if client is None:
        raise RuntimeError("AI mode requires an OPENAI_API_KEY. Select Demo mode to explore without a key.")
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    if image is not None:
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="JPEG", quality=88)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{encoded}"})
    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=[{"role": "user", "content": content}],
        temperature=temperature,
    )
    output = getattr(response, "output_text", "")
    if not output:
        raise RuntimeError("The AI service returned an empty response.")
    return extract_json(output)


def run_analysis(prompt: str, demo_data: dict[str, Any], image: Image.Image | None = None) -> dict[str, Any]:
    """Run AI analysis or deterministic demo analysis according to sidebar mode."""
    if st.session_state.get("demo_mode", False):
        return demo_data
    return call_ai(prompt, image=image)


def as_list(value: Any, fallback: list[str] | None = None) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value]
    return fallback or []


def safe_score(value: Any, default: int = 70) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return default


# ----------------------------- Analysis functions -----------------------------
def analyze_poster(image: Image.Image, demo: bool) -> dict[str, Any]:
    prompt = """
Analyze this uploaded social media poster as a professional art director and content strategist.
Inspect layout, visual hierarchy, contrast, color harmony, typography, readability, spelling/text clarity
(where legible), and CTA. Do not invent text that cannot be read. Return ONLY JSON:
{"score":0-100,"summary":"...","strengths":["..."],"issues":["..."],
"spelling_or_text_notes":["..."],"design_breakdown":{"hierarchy":"...","colors":"...",
"typography":"...","readability":"...","cta":"..."},"recommendations":["..."]}
Scores should be evidence-based and suggestions practical.
"""
    demo_data = {
        "score": 78,
        "summary": "The poster has a clear focal point and a recognizable event-promotion structure. A few refinements could improve scanability.",
        "strengths": ["Main message is visually prominent", "The layout has a clear central focus", "The design uses a consistent visual direction"],
        "issues": ["Some supporting text may be difficult to read at mobile size", "Spacing between secondary elements could be more consistent"],
        "spelling_or_text_notes": ["Demo mode does not perform OCR; manually verify names, dates, venue and contact details."],
        "design_breakdown": {
            "hierarchy": "Make the event title the strongest element, followed by date, venue and registration details.",
            "colors": "Keep the palette focused and ensure text/background contrast is strong.",
            "typography": "Use no more than two complementary type families and avoid very small weights.",
            "readability": "Check the poster at phone-screen size before publishing.",
            "cta": "Use one clear action such as Register Now or Contact Us."
        },
        "recommendations": ["Increase contrast for small text", "Group date, time and venue into one information block", "Give the CTA more visual emphasis"]
    }
    return run_analysis(prompt, demo_data, image=image)


def analyze_caption(caption: str, demo: bool) -> dict[str, Any]:
    prompt = f"""
Analyze the social media caption below. Assess grammar, readability, tone, clarity, unnecessary wording,
engagement potential and CTA. Keep the original intent and facts; do not invent event details.
Return ONLY JSON with keys: score (0-100), tone, clarity, grammar_notes (array), strengths (array),
improvements (array), unnecessary_wording (array), cta_feedback, improved_caption,
versions (object with professional, creative, formal, short strings).
CAPTION:
{caption}
"""
    demo_data = {
        "score": 76,
        "tone": "Informative and promotional",
        "clarity": "The core message is understandable. A more direct opening and a specific CTA would improve it.",
        "grammar_notes": ["Review punctuation and sentence length before posting."],
        "strengths": ["The caption communicates a purpose", "It can be adapted for a student or brand audience"],
        "improvements": ["Lead with the most important information", "Break long sentences into shorter lines", "End with one specific action"],
        "unnecessary_wording": ["Remove repeated introductory phrases if they do not add meaning."],
        "cta_feedback": "Add a direct CTA such as Register now, Share your thoughts, or Send us a message.",
        "improved_caption": f"{caption.strip()}\n\nTell us what you think in the comments!",
        "versions": {
            "professional": f"{caption.strip()}\n\nStay connected for updates and further details.",
            "creative": f"Big ideas deserve the spotlight! ✨\n\n{caption.strip()}",
            "formal": f"{caption.strip()}\n\nFor further information, please follow our official updates.",
            "short": (caption.strip()[:140] + ("…" if len(caption.strip()) > 140 else ""))
        }
    }
    return run_analysis(prompt, demo_data)


def analyze_hashtags(caption: str, hashtags: str, demo: bool) -> dict[str, Any]:
    prompt = f"""
Review the hashtags against the caption/topic. Identify irrelevant, duplicate, overly generic or excessively
broad tags. Suggest relevant alternatives, grouped by category. Do not claim access to live hashtag volume.
Return ONLY JSON: {{"summary":"...","issues":["..."],"relevant":["..."],
"suggestions":{{"niche":["..."],"community":["..."],"topic":["..."],"broad":["..."]}},
"recommended_set":["..."]}}
CAPTION/TOPIC: {caption}
USER HASHTAGS: {hashtags}
"""
    parsed = re.findall(r"#?[\w]+", hashtags.lower())
    unique = list(dict.fromkeys("#" + tag for tag in parsed if tag))
    duplicates = len(parsed) - len(set(parsed))
    demo_data = {
        "summary": "Hashtags are assessed for topical fit and variety only; demo mode does not access platform trend data.",
        "issues": (["Repeated hashtags were found."] if duplicates else []) + (["Avoid relying only on very broad tags such as #socialmedia."] if any(x in unique for x in ["#socialmedia", "#love", "#instagood"]) else []),
        "relevant": unique[:8],
        "suggestions": {
            "niche": ["#ContentStrategy", "#DigitalCreativity"],
            "community": ["#StudentCommunity", "#CreativeCommunity"],
            "topic": ["#SocialMediaTips", "#ContentCreation"],
            "broad": ["#DigitalMedia", "#Community"]
        },
        "recommended_set": list(dict.fromkeys(unique[:4] + ["#ContentCreation", "#DigitalMedia", "#CreativeCommunity"]))[:10]
    }
    return run_analysis(prompt, demo_data)


def analyze_sentiment(comments: list[str], demo: bool) -> dict[str, Any]:
    prompt = """
Classify each supplied comment as Positive, Negative, or Neutral. Also identify common topics and concise
audience feedback. Be cautious with sarcasm/ambiguous comments and classify them Neutral when uncertain.
Return ONLY JSON: {"items":[{"comment":"...","sentiment":"Positive|Negative|Neutral","reason":"..."}],
"topics":["..."],"summary":"...","actions":["..."]}.
Comments:
""" + "\n".join(f"- {c}" for c in comments)
    if demo:
        labels = []
        positive_words = {"love", "great", "excellent", "amazing", "good", "helpful", "awesome", "thanks"}
        negative_words = {"bad", "poor", "boring", "late", "confusing", "disappointed", "worst"}
        for comment in comments:
            words = set(re.findall(r"\w+", comment.lower()))
            pos, neg = len(words & positive_words), len(words & negative_words)
            sentiment = "Positive" if pos > neg else "Negative" if neg > pos else "Neutral"
            labels.append({"comment": comment, "sentiment": sentiment, "reason": "Keyword-based demo classification; context may change the meaning."})
        counts = pd.Series([x["sentiment"] for x in labels]).value_counts().to_dict()
        demo_data = {
            "items": labels,
            "topics": ["Content quality", "Event information", "Audience questions"],
            "summary": f"Demo keyword scan classified {counts.get('Positive', 0)} positive, {counts.get('Negative', 0)} negative and {counts.get('Neutral', 0)} neutral comments.",
            "actions": ["Respond to questions promptly", "Thank users for constructive feedback", "Review recurring complaints before the next post"]
        }
        return demo_data
    return call_ai(prompt)


def generate_content(kind: str, topic: str, platform: str, audience: str, tone: str, extra: str, demo: bool) -> dict[str, Any]:
    prompt = f"""
Create social media content. Request type: {kind}. Topic: {topic}. Platform: {platform}.
Target audience: {audience}. Tone: {tone}. Additional direction: {extra}.
Do not invent dates, prices, claims, links or factual details. Use placeholders where details are missing.
Return ONLY JSON: {{"title":"...","caption":"...","ideas":["..."],"hashtags":["..."],
"cta":["..."],"calendar":[{{"day":"...","format":"...","idea":"..."}}]}}.
For a content calendar provide a practical 7-day plan. For other requests, still return useful ideas.
"""
    demo_data = {
        "title": f"{topic.title()} — Ideas Worth Sharing",
        "caption": f"Discover more about {topic}. What would you like to learn or see next? Share your thoughts below!",
        "ideas": [f"An introductory carousel about {topic}", f"Three useful tips related to {topic}", f"A behind-the-scenes post about {topic}"],
        "hashtags": ["#ContentCreation", "#DigitalCommunity", "#SocialMediaTips", "#CreativeIdeas"],
        "cta": ["Share your thoughts", "Save this post for later", "Send us a message"],
        "calendar": [
            {"day": "Monday", "format": "Carousel", "idea": f"Introduce {topic} with 5 key points"},
            {"day": "Tuesday", "format": "Story", "idea": "Ask an audience poll or question"},
            {"day": "Wednesday", "format": "Short video", "idea": "Share one practical tip"},
            {"day": "Thursday", "format": "Static post", "idea": "Highlight a useful fact or reminder"},
            {"day": "Friday", "format": "Carousel", "idea": "Answer frequently asked questions"},
            {"day": "Saturday", "format": "Behind the scenes", "idea": "Show the people or process"},
            {"day": "Sunday", "format": "Community post", "idea": "Invite feedback and suggestions"}
        ]
    }
    return run_analysis(prompt, demo_data)


def calculate_engagement(likes: int, comments: int, shares: int, saves: int, reach: int, impressions: int) -> dict[str, Any]:
    interactions = likes + comments + shares + saves
    rate_reach = (interactions / reach * 100) if reach else 0.0
    rate_impressions = (interactions / impressions * 100) if impressions else 0.0
    return {
        "interactions": interactions,
        "rate_reach": rate_reach,
        "rate_impressions": rate_impressions,
        "summary": (
            f"{interactions:,} total interactions. Engagement by reach is {rate_reach:.2f}%"
            + (f" and engagement by impressions is {rate_impressions:.2f}%." if impressions else ".")
        ),
        "recommendations": [
            "Use a specific question or CTA to encourage meaningful comments.",
            "Create save-worthy content such as checklists, guides or step-by-step tips.",
            "Compare posts with similar formats and audience sizes rather than judging one post alone."
        ]
    }


# ----------------------------- UI helpers -----------------------------
def show_list(title: str, values: Any, empty: str = "No items to display.") -> None:
    st.markdown(f"**{title}**")
    items = as_list(values)
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption(empty)


def score_metric(label: str, score: int) -> None:
    st.metric(label, f"{safe_score(score)}/100")


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.caption(subtitle)


def render_dashboard() -> None:
    page_header("Your workspace", "A clear view of the analyses completed in this session.")
    results = [
        ("Poster", st.session_state.poster_result),
        ("Caption", st.session_state.caption_result),
        ("Engagement", st.session_state.engagement_result),
        ("Hashtags", st.session_state.hashtag_result),
        ("Sentiment", st.session_state.sentiment_result),
    ]
    completed = sum(result is not None for _, result in results)
    a, b, c = st.columns(3)
    a.metric("Analyses completed", completed, "This session")
    b.metric("AI mode", "Demo" if st.session_state.demo_mode else "Live AI")
    c.metric("Model", "Local sample" if st.session_state.demo_mode else DEFAULT_MODEL)
    st.subheader("Analysis overview")
    cols = st.columns(5)
    for col, (name, result) in zip(cols, results):
        with col:
            if result is None:
                st.metric(name, "—", "Not analyzed")
            else:
                value = result.get("score")
                if value is not None:
                    st.metric(name, f"{safe_score(value)}/100")
                elif name == "Engagement":
                    st.metric(name, f"{result['rate_reach']:.2f}%", "By reach")
                elif name == "Sentiment":
                    st.metric(name, f"{len(result.get('items', []))} comments")
                else:
                    st.metric(name, "Complete")
    st.divider()
    st.subheader("Get started")
    st.write("Choose an analyzer from the sidebar. Results remain available in the comprehensive report for this session.")
    st.info("SocialIQ does not connect to social accounts or fetch live platform analytics. Enter your own metrics or analyze content you upload.")


def render_poster() -> None:
    page_header("AI Post & Poster Analyzer", "Upload a creative and review its design, readability and call-to-action.")
    uploaded = st.file_uploader("Upload poster", type=["jpg", "jpeg", "png"], key="poster_upload")
    if uploaded:
        try:
            image = Image.open(uploaded)
            image.verify()
            uploaded.seek(0)
            image = Image.open(uploaded).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError):
            st.error("This image could not be opened. Please upload a valid JPG or PNG.")
            return
        left, right = st.columns([1, 1.2])
        with left:
            st.image(image, caption=uploaded.name, use_container_width=True)
        with right:
            st.write(f"**File:** {uploaded.name}")
            st.write(f"**Dimensions:** {image.width} × {image.height}px")
            st.write("Check important text at mobile-screen size before publishing.")
            if st.button("Analyze poster", type="primary", use_container_width=True):
                with st.spinner("Reviewing poster design..."):
                    try:
                        result = analyze_poster(image, st.session_state.demo_mode)
                        st.session_state.poster_result = result
                        st.session_state.poster_name = uploaded.name
                        st.success("Poster analysis complete.")
                    except Exception as exc:
                        st.error(f"Poster analysis failed: {exc}")
    result = st.session_state.poster_result
    if result:
        st.divider()
        score_metric("Poster quality score", result.get("score", 0))
        st.write(result.get("summary", ""))
        c1, c2 = st.columns(2)
        with c1:
            show_list("What works well", result.get("strengths"))
            show_list("Text / spelling notes", result.get("spelling_or_text_notes"))
        with c2:
            show_list("Issues to review", result.get("issues"))
            show_list("Recommended improvements", result.get("recommendations"))
        st.subheader("Design breakdown")
        breakdown = result.get("design_breakdown", {})
        for key, value in breakdown.items():
            with st.expander(key.replace("_", " ").title()):
                st.write(value)


def render_caption() -> None:
    page_header("AI Caption Analyzer", "Improve clarity, tone, grammar and engagement potential.")
    caption = st.text_area("Paste your caption", value=st.session_state.caption_text, height=180,
                           placeholder="Write or paste your social media caption here...")
    st.session_state.caption_text = caption
    if st.button("Analyze caption", type="primary", disabled=not caption.strip()):
        with st.spinner("Analyzing caption..."):
            try:
                st.session_state.caption_result = analyze_caption(caption.strip(), st.session_state.demo_mode)
                st.success("Caption analysis complete.")
            except Exception as exc:
                st.error(f"Caption analysis failed: {exc}")
    result = st.session_state.caption_result
    if result:
        st.divider()
        score_metric("Caption quality score", result.get("score", 0))
        st.write(f"**Tone:** {result.get('tone', '—')}")
        st.write(result.get("clarity", ""))
        c1, c2 = st.columns(2)
        with c1:
            show_list("Strengths", result.get("strengths"))
            show_list("Grammar notes", result.get("grammar_notes"))
        with c2:
            show_list("Improvements", result.get("improvements"))
            show_list("Unnecessary wording", result.get("unnecessary_wording"))
        st.write(f"**CTA feedback:** {result.get('cta_feedback', '—')}")
        st.subheader("Improved caption")
        st.text_area("Recommended version", result.get("improved_caption", ""), height=130)
        st.subheader("Alternative tones")
        versions = result.get("versions", {})
        for tone in ["professional", "creative", "formal", "short"]:
            if versions.get(tone):
                with st.expander(tone.title()):
                    st.write(versions[tone])


def render_engagement() -> None:
    page_header("Engagement Analyzer", "Calculate performance from metrics you provide.")
    st.caption("Enter post-level insights from your platform. These values are not fetched automatically.")
    with st.form("engagement_form"):
        cols = st.columns(3)
        likes = cols[0].number_input("Likes", min_value=0, step=1, value=250)
        comments = cols[1].number_input("Comments", min_value=0, step=1, value=32)
        shares = cols[2].number_input("Shares", min_value=0, step=1, value=18)
        cols2 = st.columns(3)
        saves = cols2[0].number_input("Saves", min_value=0, step=1, value=45)
        reach = cols2[1].number_input("Reach", min_value=0, step=1, value=5000)
        impressions = cols2[2].number_input("Impressions", min_value=0, step=1, value=7200)
        submitted = st.form_submit_button("Calculate engagement", type="primary")
    if submitted:
        if reach == 0 and impressions == 0:
            st.error("Enter reach or impressions greater than zero to calculate an engagement rate.")
        else:
            st.session_state.engagement_result = calculate_engagement(
                int(likes), int(comments), int(shares), int(saves), int(reach), int(impressions)
            )
    result = st.session_state.engagement_result
    if result:
        st.divider()
        a, b, c = st.columns(3)
        a.metric("Total interactions", f"{result['interactions']:,}")
        b.metric("Engagement by reach", f"{result['rate_reach']:.2f}%")
        c.metric("Engagement by impressions", f"{result['rate_impressions']:.2f}%")
        st.info("Engagement by reach = (likes + comments + shares + saves) ÷ reach × 100. Engagement by impressions uses impressions as the denominator.")
        counts = pd.DataFrame({"Interaction": ["Likes", "Comments", "Shares", "Saves"],
                               "Count": [int(likes), int(comments), int(shares), int(saves)]})
        fig = px.bar(counts, x="Interaction", y="Count", color="Interaction",
                     title="Interaction breakdown", text="Count")
        fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)
        st.write(result["summary"])
        show_list("Ways to improve", result["recommendations"])


def render_hashtags() -> None:
    page_header("Hashtag Analyzer", "Check relevance and build a balanced hashtag set.")
    caption = st.text_area("Post caption or topic", key="hashtag_caption", height=100,
                           placeholder="Describe what the post is about...")
    hashtags = st.text_input("Your hashtags", value=st.session_state.hashtags_text,
                             placeholder="#University #Technology #Event")
    st.session_state.hashtags_text = hashtags
    if st.button("Analyze hashtags", type="primary", disabled=not (caption.strip() or hashtags.strip())):
        with st.spinner("Reviewing hashtags..."):
            try:
                st.session_state.hashtag_result = analyze_hashtags(caption, hashtags, st.session_state.demo_mode)
                st.success("Hashtag review complete.")
            except Exception as exc:
                st.error(f"Hashtag analysis failed: {exc}")
    result = st.session_state.hashtag_result
    if result:
        st.divider()
        st.write(result.get("summary", ""))
        show_list("Potential issues", result.get("issues"))
        show_list("Relevant hashtags detected", result.get("relevant"))
        st.subheader("Suggested hashtags by category")
        suggestions = result.get("suggestions", {})
        cols = st.columns(2)
        for i, (category, values) in enumerate(suggestions.items()):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{category.replace('_', ' ').title()}**")
                    st.write(" ".join(as_list(values)))
        recommended = " ".join(as_list(result.get("recommended_set")))
        st.text_area("Recommended hashtag set", recommended, height=90)
        if recommended and st.button("Copy-ready set"):
            st.code(recommended)


def render_generator() -> None:
    page_header("AI Content Generator", "Create platform-ready ideas, captions, hashtags and content plans.")
    with st.form("generator_form"):
        kind = st.selectbox("What would you like to create?", ["Social media caption", "Post ideas", "7-day content calendar", "Hashtag set", "Post title and CTA"])
        topic = st.text_input("Topic or campaign", placeholder="e.g. university tech event, product launch")
        cols = st.columns(2)
        platform = cols[0].selectbox("Platform", ["Instagram", "Facebook", "LinkedIn", "TikTok", "X", "Any platform"])
        audience = cols[1].text_input("Target audience", value="Students and young professionals")
        tone = st.selectbox("Tone", ["Professional", "Friendly", "Creative", "Formal", "Energetic"])
        extra = st.text_area("Additional direction (optional)", placeholder="Mention key points, word limit, language, or style...")
        submitted = st.form_submit_button("Generate content", type="primary", disabled=not topic.strip())
    if submitted:
        with st.spinner("Creating content..."):
            try:
                st.session_state.generated_content = generate_content(kind, topic, platform, audience, tone, extra, st.session_state.demo_mode)
                st.success("Content generated.")
            except Exception as exc:
                st.error(f"Content generation failed: {exc}")
    result = st.session_state.generated_content
    if result:
        st.divider()
        st.subheader(result.get("title", "Generated content"))
        if result.get("caption"):
            st.text_area("Caption", result["caption"], height=150)
        show_list("Post ideas", result.get("ideas"))
        show_list("Suggested hashtags", result.get("hashtags"))
        show_list("Calls to action", result.get("cta"))
        if result.get("calendar"):
            st.subheader("7-day content calendar")
            st.dataframe(pd.DataFrame(result["calendar"]), use_container_width=True, hide_index=True)


def render_sentiment() -> None:
    page_header("Audience Sentiment Analyzer", "Understand audience reactions from comments you paste.")
    comments_text = st.text_area("Paste comments (one comment per line)", value=st.session_state.comments_text,
                                 height=200, placeholder="This was really helpful!\nCan you share more details?\nThe information was confusing.")
    st.session_state.comments_text = comments_text
    comments = [line.strip() for line in comments_text.splitlines() if line.strip()]
    if st.button("Analyze audience comments", type="primary", disabled=not comments):
        if len(comments) > 200:
            st.error("Please analyze up to 200 comments at a time.")
        else:
            with st.spinner("Analyzing audience feedback..."):
                try:
                    st.session_state.sentiment_result = analyze_sentiment(comments, st.session_state.demo_mode)
                    st.success("Sentiment analysis complete.")
                except Exception as exc:
                    st.error(f"Sentiment analysis failed: {exc}")
    result = st.session_state.sentiment_result
    if result:
        st.divider()
        items = result.get("items", [])
        df = pd.DataFrame(items)
        if not df.empty:
            counts = df["sentiment"].value_counts().reindex(["Positive", "Neutral", "Negative"], fill_value=0).rename_axis("Sentiment").reset_index(name="Comments")
            total = len(df)
            cols = st.columns(3)
            for col, sentiment in zip(cols, ["Positive", "Neutral", "Negative"]):
                count = int(counts.loc[counts.Sentiment == sentiment, "Comments"].iloc[0])
                col.metric(sentiment, count, f"{count / total * 100:.1f}%")
            fig = px.pie(counts, names="Sentiment", values="Comments", hole=.52, title="Sentiment distribution")
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("Comment-level results")
            st.dataframe(df, use_container_width=True, hide_index=True)
        st.write(result.get("summary", ""))
        show_list("Common topics", result.get("topics"))
        show_list("Recommended actions", result.get("actions"))


def render_report() -> None:
    page_header("Comprehensive AI Report", "A consolidated view of the analyses completed in this session.")
    poster = st.session_state.poster_result
    caption = st.session_state.caption_result
    engagement = st.session_state.engagement_result
    hashtags = st.session_state.hashtag_result
    sentiment = st.session_state.sentiment_result
    available_scores = [safe_score(x.get("score")) for x in [poster, caption] if x]
    overall = round(sum(available_scores) / len(available_scores)) if available_scores else None
    if overall is None:
        st.info("Run a poster or caption analysis to calculate an overall content score. Other modules will appear below as you complete them.")
    else:
        st.metric("Overall content score", f"{overall}/100", "Average of completed poster and caption scores")
    st.caption("The overall score is a simple average of available poster and caption scores; it is not a platform ranking.")
    st.divider()
    sections = [
        ("Poster analysis", poster, ["summary", "strengths", "issues", "recommendations"]),
        ("Caption analysis", caption, ["tone", "clarity", "strengths", "improvements", "improved_caption"]),
        ("Engagement analysis", engagement, ["summary", "recommendations"]),
        ("Hashtag recommendations", hashtags, ["summary", "issues", "recommended_set"]),
        ("Audience sentiment", sentiment, ["summary", "topics", "actions"]),
    ]
    for title, data, fields in sections:
        with st.expander(title, expanded=bool(data)):
            if not data:
                st.caption("Not completed yet.")
                continue
            if "score" in data:
                st.write(f"**Score:** {safe_score(data['score'])}/100")
            for field in fields:
                value = data.get(field)
                if value:
                    st.markdown(f"**{field.replace('_', ' ').title()}**")
                    if isinstance(value, list):
                        for item in value:
                            st.markdown(f"- {item}")
                    else:
                        st.write(value)
    report = {
        "overall_content_score": overall,
        "poster_analysis": poster,
        "caption_analysis": caption,
        "engagement_analysis": engagement,
        "hashtag_analysis": hashtags,
        "audience_sentiment": sentiment,
        "notice": "Only user-provided content and metrics are included. No social platform account is connected."
    }
    st.download_button(
        "Download report as JSON",
        data=json.dumps(report, indent=2, ensure_ascii=False, default=str),
        file_name="socialiq_analysis_report.json",
        mime="application/json",
        use_container_width=False,
    )


# ----------------------------- Main app -----------------------------
def main() -> None:
    with st.sidebar:
        st.markdown("## 📊 SocialIQ")
        st.caption("Analyze. Understand. Optimize. Grow.")
        st.divider()
        page = st.radio(
            "WORKSPACE",
            ["Dashboard", "Poster Analyzer", "Caption Analyzer", "Engagement", "Hashtags", "Content Generator", "Audience Sentiment", "Comprehensive Report"],
            label_visibility="collapsed",
        )
        st.divider()
        st.markdown("**Analysis mode**")
        st.toggle("Demo mode (no API key required)", value=True, key="demo_mode")
        if st.session_state.demo_mode:
            st.success("Demo mode is active. Results use sample or local rule-based analysis.")
        elif not get_api_key():
            st.warning("No API key found. Add OPENAI_API_KEY in Streamlit secrets or environment variables.")
        else:
            st.success(f"Live AI ready · {DEFAULT_MODEL}")
        with st.expander("API configuration"):
            st.code('OPENAI_API_KEY = "your-api-key"', language="toml")
            st.caption("For Streamlit Cloud, add the key under App settings → Secrets. Locally, set the OPENAI_API_KEY environment variable.")
        st.divider()
        st.caption("SocialIQ · Session workspace")
    st.markdown(
        '<div class="hero"><h1>SocialIQ</h1><p>Analyze. Understand. Optimize. Grow.</p></div>',
        unsafe_allow_html=True,
    )
    pages = {
        "Dashboard": render_dashboard,
        "Poster Analyzer": render_poster,
        "Caption Analyzer": render_caption,
        "Engagement": render_engagement,
        "Hashtags": render_hashtags,
        "Content Generator": render_generator,
        "Audience Sentiment": render_sentiment,
        "Comprehensive Report": render_report,
    }
    pages[page]()


if __name__ == "__main__":
    main()
