# ContrAI

ContrAI is a web-based AI adversary engine that intentionally challenges user arguments and project ideas instead of agreeing. It helps users identify logical flaws, feasibility risks, and blind spots through structured, adversarial AI feedback.

## Project Overview

Most AI tools are designed to be helpful and compliant. ContrAI is designed to be the opposite: a ruthless critic. By adopting specific adversarial personas (a World-Class Debater and a Cynical Hackathon Judge), it provides high-signal feedback that exposes weaknesses in logic or project planning.

## Key Features

- **Debate Mode**: A "ruthless logic engine" that deconstructs arguments, identifies fallacies (Ad Hominem, Straw Man), and assigns a logical strength score (0-100).
- **Hackathon Judge Mode**: A "cynical judge" that stress-tests project ideas for feasibility, identifying scope creep, valid technical paths, and "vaporware" risks.
- **Structured Scoring**: Converts qualitative AI critiques into quantitative metrics (Score, Verdict, Missing Evidence).
- **Adversarial Personas**: Uses carefully prompted system instructions to ensure feedback is surgical, direct, and free of fluff.

## How It Works

1.  **Frontend**: User submits a Debate Argument or Hackathon Idea via the web interface.
2.  **Flask Backend**: Routes the input to the specific endpoint (`/debate` or `/hackathon`).
3.  **Gemini API**: The backend constructs a prompt with a specific persona (e.g., "World-Class Debater") and sends it to the `gemini-2.5-flash` model.
4.  **Structured Output Parsing**: The raw text response from Gemini—formatted systematically—is parsed using Regex to extract fields like Score, Verdict, Analysis, and Counter-arguments.
5.  **Rendering**: The parsed data is displayed as structured feedback cards on the frontend.

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python, Flask
- **AI**: Google Gemini API (`gemini-2.5-flash`)
- **Utilities**: `python-dotenv` for environment configuration, Regex for output parsing

## Running Locally

### Prerequisites
- Python 3.8+
- A Google Cloud Project with Gemini API access

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/ArcnoX1611/ContrAI.git
    cd ContrAI
    ```

2.  **Install Dependencies**
    ```bash
    pip install flask python-dotenv google-genai
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory and add your API key:
    ```env
    GOOGLE_API_KEY=your_api_key_here
    ```
4.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Application**
    ```bash
    python main.py
    ```

6.  **Access the App**
    Open your browser and navigate to `http://127.0.0.1:5000`.

## Alternatively , you can see the website deployed on  https://contrai.onrender.com/
it may take some time to load as the server is on free tier of render.com wait 60 seconds for the server to wake up.

## Design Decisions

- **Why Adversarial AI?**: Confirmation bias is a major blocker in ideation. By forcing the AI to disagree, we generate higher-quality, stress-tested ideas that stand up to scrutiny.
- **Structured Output Parsing**: Instead of asking for JSON directly (which can sometimes reduce the "natural" quality of a critique), we force the model to output a specific text format and use robust Regex parsing. This balances the need for structured UI elements with the flexibility of natural language generation.

## Limitations & Ethics

- **Parsing Sensitivity**: The system relies on the model following a strict output format. While `gemini-2.5-flash` is consistent, occasional formatting deviations may cause parsing errors.
- **Tone**: The AI is prompted to be "ruthless" and "cynical." This tone is intentional for effective stress-testing but may feel harsh to some users. It is a tool for improvement, not discouragement.

## Future Improvements

- **Multi-turn Debates**: Allow users to respond to the critique and argue back in a thread.
- **History & Export**: Save critique reports as PDFs for hackathon submissions.
- **Custom Personas**: Allow users to adjust the "ruthlessness" level or choose different judge archetypes (e.g., VC Investor, Academic Reviewer).
