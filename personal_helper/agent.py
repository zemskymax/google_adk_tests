from google.adk.agents import Agent
from .auxiliary import tools
import uuid
import json
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
import httpx
from a2a.client import A2ACardResolver
from google.adk.tools.tool_context import ToolContext
import asyncio
from itertools import zip_longest
import logging
import re

logger = logging.getLogger(__name__)


class AgentLogic:
    """This is the agent logic class responsible for choosing which remote agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        remote_agent_addresses: list[str],
    ):
        logger.info("HostAgent instance created in memory (uninitialized).")
        self.agent_name = "AlexHelperBot"
        self.remote_agent_connections: dict[str, tools.RemoteAgentConnections] = {}
        self.cards: dict[str, dict] = {}
        self.is_initialized = False
        self.remote_agent_addresses = remote_agent_addresses
        self.health_check_interval = 600  # 10 minutes
        self.is_initialized = False

    async def _health_check(self, address: str, httpx_client: httpx.AsyncClient):
        """Performs a health check on a single agent."""
        try:
            card_resolver = A2ACardResolver(httpx_client=httpx_client, base_url=address)
            card = await card_resolver.get_agent_card()
            return address, card
        except Exception as e:
            logger.error(f"--- Health check FAILED for address: `{address}` ---")
            logger.error(f"--- Exception type is: {type(e).__name__} ---")
            logger.error(f"--- Exception details: {e} ---")
            return address, None

    async def _initialize(self):
        """
        Initializes the connections to the remote agents.
        """
        if not self.remote_agent_addresses or not self.remote_agent_addresses[0]:
            logger.critical("CRITICAL FAILURE: REMOTE_AGENT_ADDRESSES variable is empty. Cannot proceed.")
            self.is_initialized = True
            return

        timeout = httpx.Timeout(60.0, read=60.0, write=60.0, connect=10.0)
        httpx_client = httpx.AsyncClient(timeout=timeout)

        tasks = [self._health_check(address, httpx_client) for address in self.remote_agent_addresses]
        results = await asyncio.gather(*tasks)

        for address, card in results:
            if card:
                logger.info(f"--- Successfully fetched public agent card from: `{address}` ---")
                remote_connection = tools.RemoteAgentConnections(agent_card=card, agent_url=address)
                self.remote_agent_connections[card.name] = remote_connection
                self.cards[card.name] = card.model_dump()
                logger.info(f"--- Successfully stored connection for {card.name} ---")

        if self.remote_agent_connections:
            logger.info(f"--- Initialization complete. {len(self.remote_agent_connections)} agents loaded. ---")
        else:
            logger.warning("--- The remote agent list is empty. ---")

        self.is_initialized = True

    async def before_agent_callback(self, callback_context: CallbackContext):
        """Initialize a new session if one is not already active."""
        logger.info("-- before_agent_callback --")
        if not self.is_initialized:
            await self._initialize()

        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

    def root_instruction(self, context: ReadonlyContext) -> str:
        """Generate the root instruction for the orchestrator agent."""
        return """
            You are Alex, a friendly and super-efficient personal assistant for a hungry teenager. You are conversational and use a slightly casual tone, like using 'awesome' or 'gotcha'. 
            Your primary responsibility is to intelligently interpret user requests and communicate with a single restaurant. 
            From the user's perspective, they are talking to a single person who is handling their food order. You should never reveal that you are talking to a bot.

            **Core Workflow & Decision Making:**

            1.  **Analyze the User's Request:**
                * **If the user's request is specific (e.g., "I want a pizza," "Get me some noodles"),** identify the appropriate restaurant agent and proceed directly to step 3, "Executing the Order."
                * **If the user's request is general (e.g., "I'm hungry," "What's for dinner?"),** proceed to step 2, "Greeting & Cuisine Discovery."

            2.  **Greeting & Cuisine Discovery (for general requests):**
                * Start by greeting the user: "Hey there! What are you in the mood for today?"
                * Use the `list_remote_agents` tool to see the available restaurant options.
                * Present a more engaging list of options to the user. When you get the list of restaurants, remove words like 'Bot' from their names to make it sound more natural. For example, if you get 'Luigi's Pizza Bot', you can say: "We can get some delicious pizza from Luigi's Pizzeria, or some Chinese food from the Golden Dragon. What sounds good? I can tell you more about their menus if you'd like."

            3.  **Executing the Order:**
                * **Before sending the order, use the `send_message` tool to fetch the menu from the selected restaurant agent by sending the message "Send me your full menu.".**
                * **Compare the user's request with the menu to ensure the items exist. Correct any minor discrepancies (e.g., map "large" to "Large Pizza").**
                * Once the user has indicated what they want, use the `send_message` tool to delegate the task to the specified agent.
                * You will receive a response from the agent.
                * **If the agent asks if the order is for "pickup or delivery", you must use the `send_message` tool again to respond with "delivery" to that same agent.** Do not ask the user.
                * **If the agent asks for the user's address or phone number, use the `get_user_address` or `get_user_phone_number` tools and send the information to the agent.** Do not ask the user.
                * **To finalize the order, if the restaurant agent asks if there is anything else (e.g., "Anything else for you?"), and you have no more items to add from the user's request, you MUST respond with "That will be all" or a similar message to confirm the order is complete.** This is a critical step to get the final bill and confirmation.
                * For any other questions from a restaurant agent, you should try to answer them based on the initial user request. Only ask the user for clarification if the information is not available in the conversation history.

            4.  **Consolidating and Responding:**
                * **Once an order is confirmed and you have the total cost from the restaurant agent, use the `subtract_from_daily_balance` tool to deduct the order total from the user's balance.**
                * After confirming the order, if the user asked about the delivery time, you can now ask the restaurant for an ETA.
                * Consolidate all the information (confirmation, ETA, etc.) into a single, coherent, and friendly message to the user. For example: "Alright, your pizza is on its way and should be there in about 30 minutes!" **Do not mention the restaurant name unless it's necessary for pickup.**

            5.  **Closing the Loop:**
                * After confirming the order with the user, end the conversation cheerfully.
            """

# In a real-world scenario, this would come from a config file or service discovery
REMOTE_AGENT_ADDRESSES = ["http://localhost:10003", "http://localhost:10004"]

agent_logic = AgentLogic(remote_agent_addresses=REMOTE_AGENT_ADDRESSES)

# --- Tool Wrappers ---
# These wrappers have simple signatures that the ADK can parse automatically.
# They capture the agent_logic instance in a closure.

def list_remote_agents():
    """List the available remote agents you can use to delegate the task."""
    return tools.list_remote_agents(agent_logic)

def get_user_address():
    """Returns the user's delivery address."""
    return tools.get_user_address()

def get_user_phone_number():
    """Returns the user's phone number."""
    return tools.get_user_phone_number()

def get_daily_cash_balance(tool_context: ToolContext):
    """Returns the user's daily cash balance."""
    return tools.get_daily_cash_balance(tool_context)

def subtract_from_daily_balance(amount_str: str, tool_context: ToolContext):
    """Subtracts an amount from the user's daily cash balance. Expects a string like '$10.50' or '10.50'."""
    return tools.subtract_from_daily_balance(amount_str, tool_context)

def get_current_date():
    """Returns the current date."""
    return tools.get_current_date()

async def send_message(agent_name: str, task: str, tool_context: ToolContext):
    """Send a message to the remote agent."""
    return await tools.send_message(agent_logic, agent_name, message=task, tool_context=tool_context)

helper_bot = Agent(
    name=agent_logic.agent_name,
    model="gemini-2.5-flash",
    description="A personal food ordering AI assistant that orchestrates orders with various restaurants.",
    instruction=agent_logic.root_instruction,
    before_agent_callback=agent_logic.before_agent_callback,
    tools=[
        list_remote_agents,
        send_message,
        get_user_address,
        get_user_phone_number,
        get_daily_cash_balance,
        subtract_from_daily_balance,
        get_current_date,
    ],
)

root_agent = helper_bot
