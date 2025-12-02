import os
import shutil
from contextlib import asynccontextmanager

from google.genai.types import Part, Content, FileData

import google.adk.sessions
import uvicorn
from fastapi import FastAPI, UploadFile, File
from google.adk import Runner
from google.adk.artifacts import FileArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions.database_session_service import DatabaseSessionService

from root_agent.agent import HostAgent

from typing import AsyncGenerator

from google.genai.types import Blob

# Initialize services at module level
session_service = DatabaseSessionService(db_url=os.getenv("DATABASE_URL"))
memory_service = InMemoryMemoryService()
artifacts_service = FileArtifactService(root_dir=os.getenv("ARTIFACT_DIR","artifacts"))

# Global variables for agent and runner (will be initialized in lifespan)
root_agent = None
runner : Runner

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize async components
    global root_agent, runner
    host_agent = HostAgent()
    root_agent = await host_agent.create_agent()
    runner = Runner(
        app_name=root_agent.name,
        agent=root_agent,
        session_service=session_service,
        memory_service=memory_service,
        artifact_service=artifacts_service,
    )
    yield
    # Shutdown: Clean up resources if needed
    pass

# Create the main FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

@app.post("/upload_video")
async def upload_video(user_id:str,file: UploadFile = File(...)):

    file_location = f"artifacts/{file.filename}"
    os.makedirs("artifacts", exist_ok=True)
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        session: google.adk.sessions.Session = await session_service.create_session(user_id=user_id,
                                                                                    app_name=root_agent.name, state={
                'mime_type': file.content_type,
                'file_path': file_location
            })
        response : AsyncGenerator[google.adk.events.Event] = runner.run_async(user_id=session.user_id,
                                                                                    session_id=session.id,
                                                                                    state_delta={},
                                                                                    new_message=Content(
                                                                                        role="user",
                                                                                        parts=[
                                                                                            Part(text="Analyse Video"),
                                                                                            Part(inline_data=Blob(mime_type=file.content_type, data=open(file_location,'rb').read()))
                                                                                        ]
                                                                                    )
                                                                                    )

    async for event in response:
        if event.author == root_agent.name and event.is_final_response():
            print(f'final response {event.content.parts}')
            return event.content.parts
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)