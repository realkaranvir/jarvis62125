import json
from agents import Agent, WebSearchTool, ModelSettings, Runner, RunResult
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from . import agent_utils
from .session_impl import PostgreSQLSession

default_model = "gpt-4o-2024-08-06"

conversation_agent = Agent(
    name="Conversation Agent",
    instructions="""
    Your job is to take information and return a speakable text response.
    This means no code blocks, no markdown, no special characters, just plain text.
    Your name is Jarvis. You will refer to the user as Sir. You will be polite and concise with your responses.""",
    model=default_model
)

web_search_agent = Agent(
    name="Web Search Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Search the web for information regarding the query. Then handoff a summary (MAX 2 SENTENCES) of the results to the Conversation Agent.""",
    tools=[
        WebSearchTool()
    ],
    model=default_model,
    model_settings=ModelSettings(tool_choice=WebSearchTool().name),
    handoffs=[
        conversation_agent
    ]
)

triage_agent = Agent(
    name="Triage agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Handoff to the correct tool agent based on the user query. If no tool agent is required, handoff to Conversation Agent""",
    model=default_model,
    handoffs=[
        conversation_agent,
        web_search_agent,
    ]
)

# Ensures that the final output is in a format suitable for text-to-speech (TTS) engines.
speakable_agent = Agent(
    name="Speakable Agent",
    instructions="""
    Your job is to take the given agent output and return a response that a TTS engine can read out loud.
    This means no code blocks, no markdown, no special characters, converting things like lbs to pounds, and so on. Besides the reformatting,
    you should not change the words or meaning of the response.""",
    model=default_model
)

async def run_workflow(query: str, session_id: str) -> RunResult:

    workflow_result = await Runner.run(starting_agent=triage_agent, input=query, session=PostgreSQLSession(session_id)) # type: ignore
    final_output = workflow_result.final_output_as(str)

    # Need to format as assistant message so LLM doesn't think user is talking to it
    speakable_output = await Runner.run(speakable_agent, agent_utils.format_as_assistant_message(final_output))

    return speakable_output