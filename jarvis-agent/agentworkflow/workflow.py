from agents import Agent, WebSearchTool, ModelSettings, Runner, RunResult
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

default_model = "gpt-4o-2024-08-06"

conversation_agent = Agent(
    name="Conversation Agent",
    instructions="""Your name is Jarvis. You are the last agent in a workflow. Your job is to take information and return a speakable text response.
    You will refer to the user as Sir. You will be polite and concise with your responses.""",
    model=default_model
)

web_search_agent = Agent(
    name="Web Search Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    Search the web for information regarding the query. Then handoff results to the Conversation Agent.""",
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
        web_search_agent
    ]
)

async def run_workflow(query: str) -> RunResult:
    result = await Runner.run(triage_agent, query)
    return result