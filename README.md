# News_sentiment_analysis_AIEAT
**Overview**

This is the sentiment Analysis project for internship at Artificial Intelligence Entrepreneur Association of Thailand.

The project made consist of new scraper module, analysis module and streamlit app.py.
Qwen2.5 3B was used to perform Name Entity Recognition, and sentiment of person mentioned in the news. 

new_scraper.py
- Receive user input news url and, optionally, person name to specify the person in new
- Output information in json and parse to news_analysis_ollama.py

news_analysis_ollama.py
- Perform sentiment analysis using predefined prompt for both user and system
- Applying name filter if user provided person name in news(case-insensitive)


issues and limitation:
- Model tend to hallucinate or fall back to their training data when summarize news that has information
  newer than its data. which can result in inaccurrate sentiment analysis 
- Entity or person in news not properly recognized

**Using this project**

Prerequisites
- Python 3.9+
- pip install -r requirement.txt
- Ollama installed and running locally
- Qwen2.5:3b model pulled(command: ollama pull qwen2.5:3b)

run app
- streamlit run app.py
