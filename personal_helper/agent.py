from google.adk.agents import Agent
from .auxiliary import tools
import uuid
import json
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
import httpx
from a2a.client import A2ACardResolver
from google.adk.tools.tool_context import ToolContext

class HostAgent:
    """The orchestrate agent.
    This is the agent responsible for choosing which remote agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        remote_agent_addresses: list[str],
    ):
        print("HostAgent instance created in memory (uninitialized).")
        self.remote_agent_connections: dict[str, tools.RemoteAgentConnections] = {}
        self.cards: dict[str, dict] = {}
        self.agents: str = ''
        self.is_initialized = False
        self.remote_agent_addresses = remote_agent_addresses

    async def _initialize(self):
        """
        Initializes the connections to the remote agents.
        """
        if not self.remote_agent_addresses or not self.remote_agent_addresses[0]:
            print("CRITICAL FAILURE: REMOTE_AGENT_ADDRESSES variable is empty. Cannot proceed.")
            self.is_initialized = True
            return

        timeout = httpx.Timeout(60.0, read=60.0, write=60.0, connect=10.0)
        httpx_client = httpx.AsyncClient(timeout=timeout)

        for i, address in enumerate(self.remote_agent_addresses):
            print(f"--- Attempting connection to: `{address}` ---")
            try:
                card_resolver = A2ACardResolver(httpx_client=httpx_client, base_url=address)
                card = await card_resolver.get_agent_card()
                print("Successfully fetched public agent card")

                remote_connection = tools.RemoteAgentConnections(agent_card=card, agent_url=address)
                self.remote_agent_connections[card.name] = remote_connection
                self.cards[card.name] = card.model_dump()
                print(f"--- Successfully stored connection for {card.name} ---")

            except Exception as e:
                print(f"--- CRITICAL FAILURE for address: `{address}` ---")
                print(f"--- Exception type is: {type(e).__name__} ---")
                print(f"--- Exception details: {e} ---")

        if self.remote_agent_connections:
            agent_info = [json.dumps({'name': c['name'], 'description': c['description']}) for c in self.cards.values()]
            self.agents = '\n'.join(agent_info)
            print(f"--- Initialization complete. {len(self.remote_agent_connections)} agents loaded. ---")
        else:
            print("--- The remote agent list is empty. ---")

        self.is_initialized = True

    async def before_agent_callback(self, callback_context: CallbackContext):
        """Initialize a new session if one is not already active."""
        print("-- before_agent_callback --")
        if not self.is_initialized:
            await self._initialize()

        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

    def root_instruction(self, context: ReadonlyContext) -> str:
        """Generate the root instruction for the orchestrator agent."""
        return f"""
            You are Alex, a friendly and super-efficient personal assistant for a hungry teenager. You are conversational and use a slightly casual tone, like using 'awesome' or 'gotcha'. Your primary responsibility is to intelligently interpret user requests and delegate them to the most appropriate specialized restaurant agents.

            **Core Workflow & Decision Making:**

            1.  **Greeting & Cuisine Discovery:**
                * Start by greeting the user: "Hey there! What are you in the mood for today?"
                * Use the `list_remote_agents` tool to see the available restaurant options and their descriptions (which include the type of food they serve).
                * Present these options to the user.

            2.  **Agent Selection:**
                * Based on the user's choice, select the most appropriate agent. For example, if the user says they want "Pizza", you should select the `LuigisPizzaBot`.

            3.  **Task Delegation & Management:**
                * Use the `send_message` tool to delegate the user's request to the chosen agent.
                * Your `send_message` call MUST include the `agent_name` and the `task` (the user's request).

            4.  **Mediation Mode:**
                * Once delegated, you will act as a go-between.
                * For every user message, you will first get a response from the delegated agent by calling `send_message` again.
                * Relay the agent's exact response back to the user without adding any of your own commentary.
                * Continue this back-and-forth relay until the conversation with the restaurant agent is finished. The agent will indicate this by saying something like "Enjoy your meal!" or mentioning an ETA.

            5.  **Closing the Loop:**
                * After the delegated conversation is over, provide a final confirmation to the user. Say something like, "Alright, your order is all set! It should be ready in about 25-30 minutes."
                * End the conversation cheerfully.

            **Available Agents:**
            {self.agents}
            """

# In a real-world scenario, this would come from a config file or service discovery
REMOTE_AGENT_ADDRESSES = ["http://localhost:10003", "http://localhost:10004"]

host_agent_logic = HostAgent(remote_agent_addresses=REMOTE_AGENT_ADDRESSES)

# --- Tool Wrappers ---
# These wrappers have simple signatures that the ADK can parse automatically.
# They capture the host_agent_logic instance in a closure.

def list_remote_agents():
    """List the available remote agents you can use to delegate the task."""
    return tools.list_remote_agents(host_agent_logic)

async def send_message(agent_name: str, task: str, tool_context: ToolContext):
    """Send a message to the remote agent."""
    return await tools.send_message(host_agent_logic, agent_name, task, tool_context)


helper_bot = Agent(
    name="AlexHelperBot",
    model="gemini-2.5-flash-lite-preview-06-17",
    description="A personal food ordering AI assistant that orchestrates orders with various restaurants.",
    instruction=host_agent_logic.root_instruction,
    before_agent_callback=host_agent_logic.before_agent_callback,
    tools=[
        list_remote_agents,
        send_message,
    ],
)

root_agent = helper_bot