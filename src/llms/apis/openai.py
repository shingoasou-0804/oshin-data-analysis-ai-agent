import os

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.responses import ResponseOutputRefusal
from pydantic import BaseModel

from src.llms.models.llm_response import LLMResponse


load_dotenv()

COST = {
    "gpt-4o-2024-11-20": {
        "input": 2.50 / 1_000_000,
        "output": 1.25 / 1_000_000,
    },
    "gpt-4o-mini-2024-07-18": {
        "input": 0.150 / 1_000_000,
        "output": 0.600 / 1_000_000,
    }
}


def generate_response(
    messages: list[dict],
    model: str = "gpt-4o-2024-11-20",
    response_format: BaseModel | None = None,
) -> LLMResponse:
    assert model in COST, f"Invalid model name: {model}"
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # LLM Call
    content_idx = 1 if model.startswith(("o1", "o3")) else 0
    if response_format is None:
        completion = client.responses.create(model=model, input=messages)
        content_item = completion.output[content_idx].content[0]
        if isinstance(content_item, ResponseOutputRefusal):
            refusal_reason = getattr(
                content_item, 'refusal', 'Unknown reason'
            )
            raise ValueError(f"API response was refused: {refusal_reason}")
        content = content_item.text
    else:
        completion = client.responses.parse(
            model=model,
            input=messages,
            text_format=response_format,
        )
        content_item = completion.output[content_idx].content[0]
        if isinstance(content_item, ResponseOutputRefusal):
            refusal_reason = getattr(
                content_item, 'refusal', 'Unknown reason'
            )
            raise ValueError(f"API response was refused: {refusal_reason}")
        content = content_item.parsed

    # Cost calculation
    input_cost = completion.usage.input_tokens * COST[model]["input"]
    output_cost = completion.usage.output_tokens * COST[model]["output"]

    return LLMResponse(
        messages=messages,
        content=content,
        model=model,
        created_at=completion.created_at,
        input_tokens=completion.usage.input_tokens,
        output_tokens=completion.usage.output_tokens,
        cost=input_cost + output_cost,
    )
