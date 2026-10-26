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

## Milestone 1: Integrated workflow (Task 5)

Flow: Streamlit form -> `orchestrator.run_pipeline` -> Gemini extraction (`idea_extractor.py`) -> Tavily search (`tavily_search.py`) -> results shown in the UI.

### Setup
1. `pip install -r requirements.txt`
2. Create a `.env` file (never commit it):
   ```
   GEMINI_API_KEY=your_gemini_key
   TAVILY_API_KEY=your_tavily_key
   ```

### Run
- UI: `streamlit run app.py`
- Tests (3 industries + error handling): `python test_workflow.py` (writes `test_results.json`)

### Error handling covered
Missing form fields, empty/invalid LLM JSON, missing JSON keys, missing API keys, Tavily failure or empty results.
