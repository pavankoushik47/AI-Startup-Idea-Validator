# Task 3: Web Search Agent

## Project
AI-Based Startup Idea Validator with Market Analysis Assistance.

## Purpose
The Web Search Agent retrieves online information about a startup idea to support market research and competitor analysis.

## API
Tavily Search API.

## Python File
tavily_search.py

## Function
search_startup_idea(startup_idea, client)

## Input
A startup idea provided as a string.

## Search Categories
1. Market Demand
2. Competitor Analysis

## Output
A Python dictionary containing search results, including titles, URLs, and content summaries.

## Features
- Generates search queries from the startup idea.
- Retrieves live web search results.
- Displays results in a readable format.
- Handles search errors.
- Saves results to tavily_search_results.json.

## Setup
Install the required package:

pip install tavily-python

Set the TAVILY_API_KEY environment variable before running the script.
Never hardcode or upload the API key.

## Run
python tavily_search.py
