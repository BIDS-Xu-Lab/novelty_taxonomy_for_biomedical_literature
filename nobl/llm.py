"""GPT-4o batch requests and response parsing (Methods §2).

The paper's run used the OpenAI and Azure OpenAI Batch APIs. Credentials are read
from the environment (see .env.example):

    NOBL_LLM_PROVIDER      "openai" (default) or "azure"
    OPENAI_API_KEY         when provider = openai
    AZURE_OPENAI_API_KEY   when provider = azure
    AZURE_OPENAI_ENDPOINT  when provider = azure, e.g. https://<resource>.openai.azure.com/
"""
import json
import os
import re

SYSTEM_MESSAGE = ("You are an expert specializing in biomedical research analysis tasked with classifying "
                  "sentences from PubMed abstracts based on their novelty.")
MODEL = "gpt-4o"  # the paper used gpt-4o-2024-11-20 for 90.7% of requests; see README
AZURE_API_VERSION = "2024-12-01-preview"


def build_request(custom_id, conclusion, taxonomy, prompt_template, model=MODEL):
    """One Batch API request line for a conclusion section."""
    prompt = prompt_template.format(taxonomy=taxonomy, conclusion=conclusion)
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 1000,
        },
    }


def clean_output(raw):
    """Extract the leaf label from a model response.

    The prompt asks for "Primary Label - Sub-label - Sub-sub-label"; the most specific
    non-empty part is returned in lower case. Responses that are not valid JSON become
    "none json"; JSON without a category becomes "none category".
    """
    match = re.search(r'{.*}', raw, re.DOTALL)
    if not match:
        return "none json"

    try:
        category = json.loads(match.group(0)).get("category", "none category")
        for part in reversed(category.split('-')):
            cleaned = re.sub(r'[^a-zA-Z\s/]', '', part).strip().lower()
            if cleaned and cleaned != "none":
                return cleaned
        return "none category"
    except json.JSONDecodeError:
        return "none json"


def parse_batch_output_line(line):
    """(custom_id, label) from one line of a Batch API output file."""
    data = json.loads(line)
    content = data["response"]["body"]["choices"][0]["message"].get("content", "none content")
    return data["custom_id"], clean_output(content)


def init_client():
    from dotenv import load_dotenv
    load_dotenv()

    provider = os.getenv("NOBL_LLM_PROVIDER", "openai").lower()
    if provider == "azure":
        from openai import AzureOpenAI
        return AzureOpenAI(
            api_version=AZURE_API_VERSION,
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
        )
    from openai import OpenAI
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])
