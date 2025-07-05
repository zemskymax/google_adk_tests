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
from .strategies import order_splitting_strategy, budget_optimization_strategy
import logging

logger = logging.getLogger(__name__)


class HostAgent:
    """This is the agent responsible for choosing which remote agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        remote_agent_addresses: list[str],
    ):
        logger.info("HostAgent instance created in memory (uninitialized).")
        self.remote_agent_connections: dict[str, tools.RemoteAgentConnections] = {}
        self.cards: dict[str, dict] = {}
        self.is_initialized = False
        self.remote_agent_addresses = remote_agent_addresses
        self.health_check_interval = 600  # 10 minutes

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
            Your primary responsibility is to intelligently interpret user requests, create a plan, and then execute that plan by communicating with various restaurants. 
            From the user's perspective, they are talking to a single person who is handling their food order.

            **Core Workflow & Decision Making:**

            1.  **Greeting & Cuisine Discovery:**
                * Start by greeting the user: "Hey there! What are you in the mood for today?"
                * Use the `list_remote_agents` tool to see the available restaurant options and their descriptions (which include the type of food they serve).
                * Present the types of food available to the user, not the restaurant names. For example: "We can get pizza or Chinese food. What sounds good?"

            2.  **Planning the Order:**
                * Once the user has indicated what they want, use the `plan_order` tool. This tool will figure out the best way to split the order across different restaurants to be efficient.
                * The `plan_order` tool will return a list of sub-orders.

            3.  **Executing the Plan:**
                * For each sub-order in the plan, use the `send_message` tool to delegate the task to the specified agent.
                * You will receive a response from each agent.
                * **If an agent asks if the order is for "pickup or delivery", you must use the `send_message` tool again to respond with "delivery" to that same agent.** Do not ask the user.
                * **If an agent asks for the user's address or phone number, use the `get_user_address` or `get_user_phone_number` tools and send the information to the agent.** Do not ask the user.
                * For any other questions from a restaurant agent, you should try to answer them based on the initial user request. Only ask the user for clarification if the information is not available in the conversation history.

            4.  **Consolidating and Responding:**
                * **Do not** relay the individual agent responses back to the user one by one.
                * Instead, wait until you have the responses from **all** the agents in the plan.
                * Consolidate the information into a single, coherent, and friendly message. For example: "Alright, your pizza is on its way, and your Chinese food should be ready for pickup in 20 minutes." **Do not mention the restaurant names unless it's necessary for pickup.**

            5.  **Closing the Loop:**
                * After confirming the order with the user, end the conversation cheerfully.
            """

    async def plan_order(self, user_request: str, tool_context: ToolContext):
        """Creates a plan for ordering food, potentially splitting the order across multiple restaurants."""
        logger.info("-- plan_order --")
        # 1. Use the order splitting strategy to get an initial plan
        order_plan = order_splitting_strategy.split_order(user_request, self.cards)

        # 2. Use the budget optimization strategy to refine the plan
        # In a real scenario, you would pass the user's budget to this function
        optimized_plan = budget_optimization_strategy.optimize_budget(order_plan, budget=50.0)

        # 3. Store the plan in the conversation state
        state = tool_context.state
        state['order_plan'] = optimized_plan

        return optimized_plan


# In a real-world scenario, this would come from a config file or service discovery
REMOTE_AGENT_ADDRESSES = ["http://localhost:10003", "http://localhost:10004"]

host_agent_logic = HostAgent(remote_agent_addresses=REMOTE_AGENT_ADDRESSES)

# --- Tool Wrappers ---
# These wrappers have simple signatures that the ADK can parse automatically.
# They capture the host_agent_logic instance in a closure.

def list_remote_agents():
    """List the available remote agents you can use to delegate the task."""
    return tools.list_remote_agents(host_agent_logic)

def get_user_address():
    """Returns the user's delivery address."""
    return tools.get_user_address()

def get_user_phone_number():
    """Returns the user's phone number."""
    return tools.get_user_phone_number()


async def send_message(agent_name: str, task: str, tool_context: ToolContext):
    """Send a message to the remote agent."""
    return await tools.send_message(host_agent_logic, agent_name, task, tool_context)

async def plan_order(user_request: str, tool_context: ToolContext):
    """Creates a plan for ordering food, potentially splitting the order across multiple restaurants."""
    return await host_agent_logic.plan_order(user_request, tool_context)


helper_bot = Agent(
    name="AlexHelperBot",
    model="gemini-2.5-flash",
    description="A personal food ordering AI assistant that orchestrates orders with various restaurants.",
    instruction=host_agent_logic.root_instruction,
    before_agent_callback=host_agent_logic.before_agent_callback,
    tools=[
        list_remote_agents,
        send_message,
        plan_order,
        get_user_address,
        get_user_phone_number,
    ],
)

root_agent = helper_bot
