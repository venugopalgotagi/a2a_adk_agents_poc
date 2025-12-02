import logging
import os
from typing import Any, Coroutine
import json

import a2a.types
import dotenv
from google.adk.tools import BaseTool

dotenv.load_dotenv()
from google.adk.models.lite_llm import LiteLlm

from utils.callbacks import (
    logger_before_agent_callback,
    logger_after_agent_callback,
    logger_on_model_error_callback
)

from a2a.types import AgentCard

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset,SseConnectionParams,McpToolsetConfig
import dotenv

dotenv.load_dotenv()

class HostAgent:

    def __init__(self,):
        self.tools = []
        self.agents = []

    async def get_tools_async(self) -> list[BaseTool]:
            try:
                sse_params = SseConnectionParams(
                    url="http://localhost:8181/sse",  # URL of the MCP server supporting SSE
                    timeout=30  # Connection timeout in seconds
                )

                # Define the MCP configuration including the SSE connection parameters
                mcp_config = McpToolsetConfig(
                    sse_connection_params=sse_params
                )

                # Create the MCPToolset from the configuration
                return await McpToolset.from_config(config=mcp_config, config_abs_path="").get_tools()


            except Exception as e:
                logging.error(f"Error in mcp_tool_set initialization: {type(e).__name__}: {str(e)}", exc_info=True)
                raise

    async def get_agents(self) -> list[dict]:
        if len(self.tools) == 0:
            self.tools = await self.get_tools_async()
        tool = [tool for tool in self.tools if tool.name == 'list_registered_agents'][0]
        try:
            agents = await tool.run_async(args={}, tool_context=None)
            agents = json.loads(agents['content'][0]['text'])
            return agents
        except Exception as e:
            ...


    async def execute_agent(self,content: bytes, agent_name:str, agent_uri:str, mime_type:str):
        logging.info(f"Executing agent {agent_name} {agent_uri} {mime_type}")
        
        # Ensure tools are loaded
        if not self.tools:
            self.tools = await self.get_tools_async()
            
        tools_list = [tool for tool in self.tools if tool.name == 'agent_executor']
        
        if not tools_list:
            # Refresh tools and try again
            logging.info("Tool 'agent_executor' not found, refreshing tools list...")
            self.tools = await self.get_tools_async()
            tools_list = [tool for tool in self.tools if tool.name == 'agent_executor']
            
        if not tools_list:
            available_tools = [t.name for t in self.tools]
            error_msg = f"Tool 'agent_executor' not found. Available tools: {available_tools}"
            logging.error(error_msg)
            return {"error": error_msg}
            
        tool = tools_list[0]
        try:
            result = await tool.run_async(args={'content':content,'agent_url':agent_uri,'mime_type':mime_type}, tool_context=None)
            if 'content' in result and len(result['content']) > 0:
                parsed_result = json.loads(result['content'][0]['text'])
                return parsed_result
        except Exception as e:
            logging.error(f"Error executing agent {agent_name}: {e}")

    def root_instruction(self) -> str:
        return f"""
        You are a root orchestrator agent. Your role is to coordinate and delegate tasks to each of the agents.
        
        Available Tools:
        - get_agents: Retrieve list of specialized agents.
        - execute_agent: Execute a specific specialized agent.
        
        Follow this execution plan strictly:
        1. Call the 'get_agents' tool to retrieve the list of all available specialized agents only once.
        2. For EACH agent returned by 'get_agents':
           - Call the 'execute_agent' tool.
           - Pass the agent's 'name' and 'uri' from the list.
           - Pass 'mime_type' as {{mime_type}}.
           - Pass 'content' as {{file_path}}.
           - Execute each agent EXACTLY ONCE.
        3. Finally, return the consolidated report to the user.
        
        CRITICAL: Do NOT repeat this process. Once all agents have been executed, generate the report and STOP.
        """

    llm_model = LiteLlm(
        model=os.getenv('LLM_MODEL'),
    )

    async def create_agent(self):
        #await self.get_agents()
        root_agent = Agent(
            model=self.llm_model,
            instruction=self.root_instruction(),
            description="You are a root orchestrator agent. Your role is to coordinate and delegate tasks to each of the ",
            name="root_agent",
            before_agent_callback=[logger_before_agent_callback],
            after_agent_callback=[logger_after_agent_callback],
            #before_tool_callback=[logger_before_tool_callback],
            #after_tool_callback=[logger_after_tool_callback],
            #on_tool_error_callback=[logger_on_tool_error_callback],
            on_model_error_callback=[logger_on_model_error_callback],
            tools=[
                self.get_agents,
                self.execute_agent,
            ]
        )
        return root_agent

    agent_skil= a2a.types.AgentSkill(
        name="Video_Risk_Hazard_Analyser_Skill",
        description="Video_Raisk_analyser_skil",
        tags=[
            "Video Risk Analyser",
            "VRA",
            "EHS Risk Analyser"
        ],
        id= "6efd02c5-8a22-4437-8138-08c90d38b53a",


    )

    def create_agent_card(self):
        root_agent_card = AgentCard(
            capabilities=a2a.types.AgentCapabilities(streaming=True,push_notifications=True),
            default_input_modes=['video','text'],
            default_output_modes=["pdf", "html", "text", "json"],
            description="Expert in analysing image or video/image/text for possible risks or hazards related to environment, health and safety",
            name="Video_Risk_Hazard_Analyser",
            preferred_transport='JSONRPC',
            version="1.0.0",
            skills=[self.agent_skil],
            supports_authenticated_extended_card=True,
            protocol_version="2.0",
            url="htp://localhost:8080"

        )


        return root_agent_card


