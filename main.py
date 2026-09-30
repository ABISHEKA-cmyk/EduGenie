import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google import genai


# ==========================================
# BASE PATH
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CSS_FILE = os.path.join(STATIC_DIR, "style.css")


# ==========================================
# ENV
# ==========================================

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if API_KEY and API_KEY != "YOUR_GEMINI_API_KEY":
    client = genai.Client(api_key=API_KEY)


# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(
    title="EduGenie",
    description="AI Educational Assistant",
    version="1.0.0"
)


# ==========================================
# TEMPLATES
# ==========================================

templates = Jinja2Templates(
    directory=TEMPLATES_DIR
)


# ==========================================
# STATIC FILES
# ==========================================

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# ==========================================
# DIRECT CSS ROUTE
# ==========================================

@app.get("/static/style.css")
async def get_css():

    return FileResponse(
        CSS_FILE,
        media_type="text/css"
    )


# ==========================================
# GEMINI
# ==========================================

def ask_gemini(prompt: str) -> str:

    if client is None:
        return "Gemini API key is not configured."

    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash"
    ]

    for model in models:

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response.text:
                    return response.text

                return "AI did not return an answer."

            except Exception as e:

                error_message = str(e)

                if (
                    "503" in error_message
                    or "UNAVAILABLE" in error_message
                ):

                    if attempt == 0:
                        time.sleep(5)
                        continue

                    break

                if (
                    "429" in error_message
                    or "RESOURCE_EXHAUSTED" in error_message
                ):
                    return (
                        "EduGenie AI is temporarily unavailable "
                        "because the Gemini API quota has been reached. "
                        "Please try again later."
                    )

                return f"AI Error: {error_message}"

    return (
        "EduGenie AI is temporarily busy. "
        "Please try again after a few seconds."
    )


# ==========================================
# HOME
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "EduGenie"
        }
    )


# ==========================================
# ASK AI
# ==========================================

@app.post("/ask", response_class=HTMLResponse)
async def ask_ai(
    request: Request,
    question: str = Form(...)
):

    prompt = f"""
You are EduGenie, a friendly AI educational assistant.

Answer the student's question clearly and simply.

Question:
{question}

Give:

1. Simple explanation
2. Important points
3. Example if needed

Use simple student-friendly language.
"""

    answer = ask_gemini(prompt)

    return templates.TemplateResponse(
        request=request,
        name="answer.html",
        context={
            "question": question,
            "answer": answer
        }
    )


# ==========================================
# EXPLAIN
# ==========================================

@app.post("/explain", response_class=HTMLResponse)
async def explain_topic(
    request: Request,
    topic: str = Form(...)
):

    prompt = f"""
You are EduGenie, an AI educational assistant.

Explain this topic to a college student:

{topic}

Include:

1. Definition
2. Simple explanation
3. Key points
4. Real-world example
5. Short summary

Use very simple language.
"""

    answer = ask_gemini(prompt)

    return templates.TemplateResponse(
        request=request,
        name="answer.html",
        context={
            "question": topic,
            "answer": answer
        }
    )


# ==========================================
# QUIZ
# ==========================================

@app.post("/quiz", response_class=HTMLResponse)
async def generate_quiz(
    request: Request,
    topic: str = Form(...),
    number: int = Form(5)
):

    if number < 1:
        number = 5

    if number > 20:
        number = 20

    prompt = f"""
You are EduGenie.

Create {number} multiple-choice questions
for the topic:

{topic}

For every question provide:

Question:
A)
B)
C)
D)

Correct Answer:
Explanation:

Keep it suitable for college students.
"""

    answer = ask_gemini(prompt)

    return templates.TemplateResponse(
        request=request,
        name="answer.html",
        context={
            "question": f"Quiz: {topic}",
            "answer": answer
        }
    )


# ==========================================
# LEARNING PATH
# ==========================================

@app.post("/learning-path", response_class=HTMLResponse)
async def learning_path(
    request: Request,
    topic: str = Form(...)
):

    prompt = f"""
Create a step-by-step learning path for:

{topic}

Include:

1. Beginner concepts
2. Basic concepts
3. Intermediate concepts
4. Advanced concepts
5. Practice activities
6. Mini project ideas
7. Final revision

Keep it simple and practical.
"""

    answer = ask_gemini(prompt)

    return templates.TemplateResponse(
        request=request,
        name="answer.html",
        context={
            "question": f"Learning Path: {topic}",
            "answer": answer
        }
    )


# ==========================================
# SUMMARIZE
# ==========================================

@app.post("/summarize", response_class=HTMLResponse)
async def summarize_text(
    request: Request,
    text: str = Form(...)
):

    prompt = f"""
Summarize the following educational text.

Text:

{text}

Give:

1. Short summary
2. Important points
3. Key terms
4. 5 quick revision points

Use simple language.
"""

    answer = ask_gemini(prompt)

    return templates.TemplateResponse(
        request=request,
        name="answer.html",
        context={
            "question": "Text Summary",
            "answer": answer
        }
    )


# ==========================================
# HEALTH
# ==========================================

@app.get("/health")
async def health():

    return {
        "status": "EduGenie is running",
        "gemini_configured": client is not None,
        "css_exists": os.path.exists(CSS_FILE)
    }


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )