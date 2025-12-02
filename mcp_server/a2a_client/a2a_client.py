import json
import sys
import uuid

import a2a.types
import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import SendMessageRequest, SendMessageResponse, SendMessageSuccessResponse, Task

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class A2aClient:

    def __init__(self, agent_url: str):
        self.agent_url = agent_url
        self.client: A2AClient = None
        self.httpx_client: httpx.AsyncClient = None

    async def initialize(self):
        try:
            logger.info(f"Initializing A2A client for: {self.agent_url}")

            # Create async HTTP client
            self.httpx_client = httpx.AsyncClient(timeout=30.0)

            # Get agent card
            card_resolver = A2ACardResolver(
                httpx_client=self.httpx_client,
                base_url=self.agent_url
            )
            card = await card_resolver.get_agent_card()
            logger.info(f"Successfully retrieved agent card: {card.name}")

            # Create A2A client
            self.client = A2AClient(
                httpx_client=self.httpx_client,
                agent_card=card
            )
            logger.info("A2A client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize A2A client: {type(e).__name__}: {str(e)}")
            raise

    async def send_file(self, mime_type:str, content: bytes, prompt: str = "Analyze this and revert-back with hazards in json format"):
        try:

            logger.info(f"Prompt: {prompt}")

            # Create message ID
            message_id = str(uuid.uuid4())
            payload = {
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "blob",
                            "text": f"{prompt}\n\nFile: {content}\nMIME Type: {mime_type}"
                        }
                    ],
                    "message_id": message_id
                }
            }

            message_request = SendMessageRequest(
                id=message_id,
                params=a2a.types.MessageSendParams.model_validate(payload)
            )

            logger.info("Sending message to agent...")
            send_response: SendMessageResponse = await self.client.send_message(message_request)

            logger.info(f"Response type: {type(send_response)}")
            logger.info(f"Response: {send_response}")

            # Check response
            if not isinstance(send_response, SendMessageSuccessResponse):
                logger.warning(f"Response is not SendMessageSuccessResponse. Type: {type(send_response)}")
                logger.warning(f"Response content: {send_response}")
                # Try to extract any useful information from the response
                if hasattr(send_response, 'model_dump'):
                    response_dict = send_response.model_dump(exclude_none=True)
                    logger.info(f"Response as dict: {response_dict}")
                    return response_dict
                return None

            if not isinstance(send_response.result, Task):
                logger.warning(f"Response result is not a Task. Type: {type(send_response.result)}")
                logger.warning(f"Result content: {send_response.result}")
                # Still try to return the response
                if hasattr(send_response, 'model_dump'):
                    response_dict = send_response.model_dump(exclude_none=True)
                    return response_dict
                return None

            # Convert response to JSON
            response_content = send_response.model_dump_json(exclude_none=True)
            json_content = json.loads(response_content)

            logger.info("Response received successfully")
            return json_content

        except Exception as e:
            logger.error(f"Error executing agent: {type(e).__name__}: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client"""
        if self.httpx_client:
            await self.httpx_client.aclose()
            logger.info("HTTP client closed")


async def delegate_to_agent(content: bytes, agent_url:str, mime_type:str):
    """Main function to demonstrate A2A client usage"""
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Analyze this for hazards"

    # Create and initialize client
    client = A2aClient(agent_url=agent_url)

    try:
        # Initialize the client
        await client.initialize()

        # Send file and get response
        response = await client.send_file(mime_type, content, prompt)

        # Display response
        print("\n" + "="*80)
        print("RESPONSE FROM  HAZARD AGENT")
        print("="*80)
        print(json.dumps(response, indent=2))
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"Error in main: {type(e).__name__}: {str(e)}")
        sys.exit(1)
    finally:
        # Clean up
        await client.close()
