import logging
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool
from google.adk.tools import ToolContext
from typing import Dict, Any
from google.adk.models import LlmRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

async def logger_before_agent_callback(callback_context: CallbackContext):
    logging.info(f'Agent {callback_context.agent_name} is being executed for session {callback_context.session.id} and invocation {callback_context.invocation_id}')

async def logger_after_agent_callback(callback_context: CallbackContext):
    logging.info(f'Agent {callback_context.agent_name} execution completed for session {callback_context.session.id} and invocation {callback_context.invocation_id}')

async def logger_before_tool_callback(tool:BaseTool, args:dict[str, Any], tool_context: ToolContext):
    logging.info(f"Tool {tool.name} is being executed=  by agent {tool_context.agent_name} for session {tool_context.session.id} and invocation {tool_context.invocation_id}")

async def logger_after_tool_callback(tool:BaseTool, dict:dict[str, Any], tool_context: ToolContext, response:dict):
    logging.info(f"Tool {tool.name} is  executed  by agent {tool_context.agent_name} for session {tool_context.session.id} and invocation {tool_context.invocation_id}")

async def logger_on_tool_error_callback(tool:BaseTool, dict:dict[str, Any], tool_context: ToolContext, exception:BaseException):
    logging.error(f"Exception {exception} occurred while Tool {tool.name} is  being executed by agent {tool_context.agent_name} for session {tool_context.session.id} and invocation {tool_context.invocation_id}")

async def logger_on_model_error_callback(callbackContext:CallbackContext, llm_request: LlmRequest, exception:Exception):
    logging.error(f"Exception {exception} occurred during llm-request {llm_request.contents} that is being executed by agent {callbackContext.agent_name} for session {callbackContext.session.id} and invocation {callbackContext.invocation_id}")

