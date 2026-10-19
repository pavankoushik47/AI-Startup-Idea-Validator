"""Streamlit UI. Run: streamlit run app.py"""
import json
import streamlit as st
from orchestrator import run_pipeline, validate_input

st.set_page_config(page_title="AI Startup Idea Validator", layout="wide")
st.title("AI Startup Idea Validator")

with st.form("idea_form"):
    description = st.text_area("Idea description *", height=120, placeholder="Describe your idea in 2-3 lines")
    industry = st.selectbox("Industry *", ["", "EdTech", "HealthTech", "AgriTech", "FinTech", "E-commerce", "SaaS", "Other"])
    customers = st.text_input("Target customers *")
    details = st.text_area("Additional details (optional)", height=80)
    submitted = st.form_submit_button("Validate idea")

if submitted:
    form = {"description": description, "industry": industry, "target_customers": customers, "details": details}
    errors = validate_input(form)
    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("Extracting idea and searching the web..."):
            out = run_pipeline(form)
        for e in out["errors"]:
            st.warning(e)
        if out["structured_idea"]:
            st.subheader("Structured idea")
            st.json(out["structured_idea"])
        if out["search_results"]:
            st.subheader("Search results")
            for category, items in out["search_results"].items():
                st.markdown(f"### {category}")
                for r in items:
                    st.markdown(f"**[{r.get('title', 'No title')}]({r.get('url', '#')})**")
                    st.caption(r.get("content", ""))
        st.download_button("Download JSON", json.dumps(out, indent=2, ensure_ascii=False), "validation_output.json")
