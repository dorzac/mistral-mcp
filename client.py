import os
import json
import asyncio
import shutil
import subprocess
import time
from typing import Optional, Any

from dotenv import load_dotenv

from openai import AsyncOpenAI
from agents import set_tracing_disabled
from agents import Agent, Runner, Model, ModelProvider, RunConfig, OpenAIChatCompletionsModel
from agents.model_settings import ModelSettings

from agents.mcp import MCPServer, MCPServerStdio, MCPServerSse


load_dotenv() 

async def run(mcp_server: MCPServer):

    client = AsyncOpenAI(
        api_key=os.environ["MISTRAL_API_KEY"],
        base_url="https://api.mistral.ai/v1"
    )
    MODEL_NAME = "mistral-small-latest"
    set_tracing_disabled(disabled=True)

    agent = Agent(
        name="Orchestrator",
        instructions="""
            You are a helpful worker.
            Answer any question you're given.
            
            Tool Explanations:
            run_rag_pipeline tool will return relevant results from buyer documentation
            and training. It's good for theory questions, and generally returns
            qualitative data.

            The NL2SQL tool will retrieve relevant quantitative data from the data hub related
            to the supply chain, as well as global purchasing. 

            Use the weather tools to answer weather related questions.
            NEVER make up data! Always choose the best tool and call it.
            You may have to call multiple tools to get a correct answer.
        """,
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice='required'),
    )

    question = "What does SDC stand for?"
    result = await Runner.run(starting_agent=agent, input=question)
    print(result.final_output)

    question = "How many parts does buyer code 123 own?"
    result = await Runner.run(starting_agent=agent, input=question)
    print(result.final_output)

async def main():
    
    async with MCPServerStdio(
            params={
                "command": "python",
                "args": ["weather.py"],
            }
        ) as server:
            tools = await server.list_tools()
            print(tools)
            await run(server)


if __name__ == "__main__":
    asyncio.run(main())
