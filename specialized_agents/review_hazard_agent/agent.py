import os

import google.adk
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent

from utils.callbacks import (
    logger_before_agent_callback,
    logger_after_agent_callback,
    logger_before_tool_callback,
    logger_after_tool_callback,
    logger_on_tool_error_callback,
    logger_on_model_error_callback
)

import dotenv

dotenv.load_dotenv()

llm_model = LiteLlm(
    model=os.getenv('LLM_MODEL'),
)

review_hazard_agent = Agent(
    model=llm_model,
    instruction="You are an expert in analysing video or image for review hazards."
                "Analyse video or image for review hazards and return the response"
                "in the user specified format only. "
                "If user does not specify return in JSON format"
                "When user greets respond in a friendly manner and introduce your self and ask for the task "
                "the user want to perform. Do only the review hazards analysis task."
                "When user asks about your self, or your capabilities or offerings please respond in a friendly manner"
                "Do not use abusive words, do not use sentence that hurts communal sentiments, do not sue words"
                "that has discrimination towards race, cast, religion, colour, gender etc",
    description="You are a review Hazard Agent, who can analyse image or video for review hazards.",
    name="review_hazard_agent",
    output_key="review_hazard_agent_response",
    tools=[],
    before_agent_callback=[logger_before_agent_callback],
    after_agent_callback=[logger_after_agent_callback],
    before_tool_callback=[logger_before_tool_callback],
    after_tool_callback=[logger_after_tool_callback],
    on_tool_error_callback=[logger_on_tool_error_callback],
    on_model_error_callback=[logger_on_model_error_callback],
)

# Alias for A2A server compatibility (expects root_agent)
root_agent = review_hazard_agent