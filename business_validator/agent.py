import dotenv
from google.adk.agents import Agent
from google.adk.tools.google_search_tool import google_search

from . import prompt

dotenv.load_dotenv()


root_agent = Agent(
    name="business_validator",
    model="gemini-2.5-flash-preview-05-20",
    description=("Validates business ideas by searching the web for relevant information."),
    instruction=prompt.ROOT_AGENT_BUSINESS_VALIDATOR_INSTR,
    tools=[google_search]
)
