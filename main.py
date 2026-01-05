from flask import Flask, render_template, request
from flask import render_template
import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"]
)

client = genai.Client()

def _non_empty_lines(text):
    return [l.strip() for l in text.splitlines() if l.strip()]


def parse_debate_response(response_text):
    """Parse debate critique output into structured components robustly.

    Tries labeled extraction first (e.g., "Score:", "Verdict:", "Summary:").
    Falls back to positional extraction when labels are missing.
    """
    text = response_text or ""
    lines = _non_empty_lines(text)

    parsed = {
        'score': None,
        'verdict': None,
        'summary': None,
        'missing_evidence': None,
        'counter_arguments': None
    }

    # Score: look for numeric score like '25/100' or 'Score: 25' or 'Feasibility/Originality Score: 25/100'
    m = re.search(r'(?i)(?:feasibility|strength|score)[^\d\n]{0,20}([0-9]{1,3})(?:\s*/\s*100)?', text)
    if m:
        parsed['score'] = m.group(1)
    else:
        # fallback: if first token on first line is numeric
        if lines:
            first_tok = lines[0].split()[0]
            if re.match(r'^\d{1,3}$', first_tok):
                parsed['score'] = first_tok
            else:
                # try to capture after a literal 'Score:' even if non-numeric
                m2 = re.search(r'(?i)score\s*:\s*(.+)', lines[0])
                if m2:
                    parsed['score'] = m2.group(1).strip()

    # Verdict
    m = re.search(r'(?i)verdict\s*:\s*(.+)', text)
    if m:
        parsed['verdict'] = m.group(1).strip()
    elif len(lines) > 1:
        parsed['verdict'] = lines[1]

    # Summary
    m = re.search(r'(?i)summary\s*:\s*(.+)', text)
    if m:
        parsed['summary'] = m.group(1).strip()
    elif len(lines) > 2:
        parsed['summary'] = lines[2]

    # Missing evidence / edge cases
    # look for lines that contain keywords
    for i, ln in enumerate(lines):
        low = ln.lower()
        if any(k in low for k in ('missing evidence', 'edge case', 'forgotten', 'missing')):
            # take the remainder of this line (after ':' if present) or next line(s)
            parts = ln.split(':', 1)
            if len(parts) > 1 and parts[1].strip():
                parsed['missing_evidence'] = parts[1].strip()
            else:
                # next line if exists
                if i + 1 < len(lines):
                    parsed['missing_evidence'] = lines[i + 1]
            break

    # Counter-arguments: look for explicit label then fallback to remaining lines
    m = re.search(r'(?i)(?:counter-?arguments|counter arguments|counter-?arguments|direct counter-arguments)\s*:\s*(.+)', text, flags=re.S)
    if m:
        parsed['counter_arguments'] = m.group(1).strip()
    else:
        # fallback: join anything after the first 4 logical sections
        if len(lines) > 4:
            parsed['counter_arguments'] = '\n'.join(lines[4:])

    return parsed

def parse_hackathon_response(response_text):
    """Parse hackathon critique output into structured components robustly."""
    text = response_text or ""
    lines = _non_empty_lines(text)

    parsed = {
        'score': None,
        'verdict': None,
        'summary': None,
        'scope_creep': None,
        'technical_issues': None
    }

    # Score: try numeric patterns first
    m = re.search(r'(?i)(?:feasibility|originality|score)[^\d\n]{0,20}([0-9]{1,3})(?:\s*/\s*100)?', text)
    if m:
        parsed['score'] = m.group(1)
    else:
        if lines:
            first_tok = lines[0].split()[0]
            if re.match(r'^\d{1,3}$', first_tok):
                parsed['score'] = first_tok
            else:
                # sometimes the model prints 'Feasibility/Originality Score: 25/100' with extra text
                m2 = re.search(r'(?i)score\s*:\s*([^\n]+)', text)
                if m2:
                    parsed['score'] = m2.group(1).strip()

    # Verdict
    m = re.search(r'(?i)verdict\s*:\s*(.+)', text)
    if m:
        parsed['verdict'] = m.group(1).strip()
    elif len(lines) > 1:
        parsed['verdict'] = lines[1]

    # Summary
    m = re.search(r'(?i)summary\s*:\s*(.+)', text)
    if m:
        parsed['summary'] = m.group(1).strip()
    elif len(lines) > 2:
        parsed['summary'] = lines[2]

    # Scope creep: look for "Scope Creep" label or lines mentioning 'scope creep'
    for i, ln in enumerate(lines):
        low = ln.lower()
        if 'scope creep' in low or 'scope-creep' in low:
            parts = ln.split(':', 1)
            if len(parts) > 1 and parts[1].strip():
                parsed['scope_creep'] = parts[1].strip()
            elif i + 1 < len(lines):
                parsed['scope_creep'] = lines[i + 1]
            break

    # Technical issues: try to find 'Technical Issues' or fall back to final lines
    m = re.search(r'(?i)(?:technical issues|technical problems|technically impossible)\s*:\s*(.+)', text, flags=re.S)
    if m:
        parsed['technical_issues'] = m.group(1).strip()
    else:
        # fallback: anything after the 4th line
        if len(lines) > 4:
            parsed['technical_issues'] = '\n'.join(lines[4:])

    return parsed

#prompts for debate and hackathon idea evaluation
DEBATE_PROMPT = """You are a World-Class Debater and ruthless logic engine. 
Your objective is to systematically deconstruct the user's argument using formal logic and empirical rigor.
Do NOT be helpful or polite; be surgical and devastating.
Identify every logical fallacy (ad hominem, straw man, circular reasoning), cognitive bias, and unsupported premise.
You are the final judge in a high-stakes debate where precision is paramount.
Assign a ruthlessly honest strength score (0-100), where 100 is an axiomatic truth and 0 is incoherent babble.

Output MUST follow this exact format with NO bolding or markdown:
Score: [Number 0-100]
Verdict: [3-5 word punchy, sarcastic judgment]
Summary: [Critical analysis of why the argument fails, exposing hidden assumptions]
Missing Evidence: [List specific data points, edge cases, or constraints ignored]
Counter-Arguments: [Direct, high-impact rebuttals and failure scenarios]"""

HACKATHON_PROMPT = """You are a cynical, battle-hardened Hackathon Judge who has seen it all.
You despise buzzwords, wrapper-apps, and solutions looking for a problem.
Your goal is to brutally stress-test this idea for feasibility in a 24-48 hour timeframe.
You must ruthlessly identify scope creep and technical impossibilities.
If it's just a CRUD app or a wrapper around an API, call it out.

Output MUST follow this exact format with NO bolding or markdown:
Score: [Number 0-100 representing feasibility and originality]
Verdict: [3-5 word punchy assessment, e.g., 'Vaporware', 'Actually Viable']
Summary: [A cynical, no-nonsense critique of the idea's value prop]
Scope Creep: [Identify specific features that will kill the team's timeline]
Technical Issues: [List specific architectural flaws, API limitations, or 'magic' assumptions]"""


# Home route
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/debate', methods=['GET', 'POST'])
@limiter.limit("1 per second;4 per minute;20 per hour")
def debate():
    output = {}
    if request.method == 'POST':
        topic = request.form['topic']
        your_stance = request.form['your_stance']
        argument = request.form['argument']
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{DEBATE_PROMPT}\n\nTopic: {topic}\nYour Stance: {your_stance}\nArgument: {argument}\nProvide a detailed critique of the argument, pointing out logical fallacies, biases, and weaknesses. Assign a strength score from 0 to 100.",
        )
        output = parse_debate_response(response.text)

    return render_template('debate.html', output=output)    

@app.route('/hackathon', methods=['GET', 'POST'])
@limiter.limit("1 per second;4 per minute;20 per hour")
def hackathon():
    output = {}
    if request.method == 'POST':
        hackathon_theme = request.form['hackathon-theme']
        idea_title = request.form['idea_title']
        idea_description = request.form['idea_description']
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{HACKATHON_PROMPT}\n\nHackathon Theme: {hackathon_theme}\nIdea Title: {idea_title}\nIdea Description: {idea_description}\nProvide constructive criticism and suggestions for improvement.",
        )
        output = parse_hackathon_response(response.text)
    return render_template('hackathon.html', output=output)

@app.route('/error')
@app.errorhandler(429)
def rate_limit_handler(e):
    return render_template(
        'error.html',
        title="Slow down",
        message="Too many requests",
        description="You’ve hit the usage limit. Please wait a moment before trying again."
    ), 429

 
@app.route('/error')   
@app.errorhandler(500)
def internal_error(e):
    return render_template(
        'error.html',
        title="Server Error",
        message="An internal server error occurred.",
        description="Either the api is flagged or the quota is exceeded.in this case you can use this by cloning to the github repo of this page and run on your machine with your own gemini api key"
    ), 500

if __name__ == '__main__':
    app.run(debug=True)
    
