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
