import json
import ollama

system_prompt = """you are an billingual Thai and English expert who is specialized in name entity recognition and analyzing sentiment

Your ONLY output is a valid JSON object — no markdown, no explanation, no extra text.

Schema:
{
  "persons": [
    {
      "name": "<full name>",
      "role": "<job title / role if mentioned, else null>",
      "sentiment": "<Positive | Negative | Neutral>",
      "reason": "<one short sentence explaining the sentiment>"
    }
  ],
  "overall_sentiment": "<Positive | Negative | Neutral>",
  "summary": "<2-3 sentence English summary of the article, focus on document in article, do not correct them with your training data>"
}

Rules:
- Only include REAL public persons (politicians, executives, celebrities, officials).
- Do NOT include fictional or anonymous people.
- If no public persons are found, return an empty persons array.
- sentiment must be exactly one of: Positive, Negative, Neutral
- If news contain information that isnt consistant with your training data, prioritize information of news
"""


def analyze(txt, filter_names=None):
    try:
        response = ollama.chat(
            model='qwen2.5:3b',
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': f"Extract public person and their sentiment from news, classify them as Positive or Negative or Neutral from this news:{txt}"
                }
            ],
            format='json'
        )

        result = json.loads(response['message']['content'])

        # Apply name filter if provided
        if filter_names and 'persons' in result:
            filter_lower = [n.lower() for n in filter_names]
            result['persons'] = [
                p for p in result['persons']
                if any(f in p['name'].lower() for f in filter_lower)
            ]

        return result

    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return {"error": str(e)}
