# AI-Startup-Idea-Validator
The AI Startup Idea Validator helps entrepreneurs de-risk their business concepts before making  financial commitments. By submitting a simple concept description, founders receive an automated, comprehensive report detailing market demand, ideal customer profiles, competitor landscapes, unit economics feasibility, and key strategic risks.                               


## Task 2: LLM Structured Idea Extraction
This module uses Google Gemini AI to analyze startup ideas and extract:
- Problem statement
- Proposed solution
- Target customers
- Industry
- Key features
### Installation
Run `pip install -r requirements.txt`
### API Key Setup
Create a local `.env` file and add your own Gemini API key:
`GEMINI_API_KEY=your_gemini_api_key`
Do not upload your `.env` file to GitHub.
### Run the Program
Run `python idea_extractor.py` and enter a startup idea. The program returns the extracted information in JSON format.
