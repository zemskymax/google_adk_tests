import sys
import asyncio
import json
import uuid
from typing import List, Optional, Callable, Any

from google.genai import types
from google.adk import Agent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from remote.remote_agent_connection import (
    RemoteAgentConnections,
    TaskUpdateCallback
)
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task
)
import httpx
from .remote_agent_connection import (
    RemoteAgentConnections,
    TaskUpdateCallback,
)


def create_send_message_payload(text: str, task_id: str | None = None, context_id: str | None = None) -> dict[str, Any]:
    """Create a payload for sending a message to the remote agent."""
    payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': text}],
            'messageId': uuid.uuid4().hex,
        },
    }
    if task_id:
        payload['message']['taskId'] = task_id
    if context_id:
        payload['message']['contextId'] = context_id
    return payload

class HostAgent:
    """The orchestrate agent.
    This is the agent responsible for choosing which remote agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        remote_agent_addresses: List[str],
        task_callback: TaskUpdateCallback | None = None
    ):
        print("HostAgent instance created in memory (uninitialized).")
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''
        self.is_initialized = False

        self.remote_agent_addresses = remote_agent_addresses

    async def _initialize(self):
        """
        DIAGNOSTIC VERSION: This method will test each connection one-by-one
        with aggressive logging to force the hidden error to appear.
        """
        if not self.remote_agent_addresses or not self.remote_agent_addresses[0]:
            print("CRITICAL FAILURE: REMOTE_AGENT_ADDRESSES variable is empty. Cannot proceed.")
            self.is_initialized = True
            return

        timeout = httpx.Timeout(60.0, read=60.0, write=60.0, connect=10.0)
        httpx_client = httpx.AsyncClient(timeout=timeout)

        for i, address in enumerate(self.remote_agent_addresses):
            print(f"--- STEP 1.{i}: Attempting connection to: `{address}` ---")
            try:
                card_resolver = A2ACardResolver(httpx_client=httpx_client, base_url=address)
                card = await card_resolver.get_agent_card()
                print("Successfully fetched public agent card")

                remote_connection = RemoteAgentConnections(agent_card=card, agent_url=address)
                self.remote_agent_connections[card.name] = remote_connection
                self.cards[card.name] = card
                print(f"--- STEP 2.{i}: Successfully stored connection for {card.name} ---")

            except Exception as e:
                print(f"--- CRITICAL FAILURE at STEP 3.{i} for address: `{address}` ---")
                print(f"--- The hidden exception type is: {type(e).__name__} ---")
                print(f"--- Full exception details and traceback: ---")

        print("STEP 4: Finished attempting all connections.")
        if not self.remote_agent_connections:
            print("FINAL VERDICT: The loop finished, but the remote agent list is still empty.")
        else:
            agent_info = [json.dumps({'name': c.name, 'description': c.description}) for c in self.cards.values()]
            self.agents = '\n'.join(agent_info)
            print(f"--- FINAL SUCCESS: Initialization complete. {len(self.remote_agent_connections)} agents loaded. ---")

        self.is_initialized = True

    async def before_agent_callback(self, callback_context: CallbackContext):
        """Initialize a new session if one is not already active.

        This callback is triggered before the model processes a request. It ensures that
        a session is properly initialized by setting a unique session ID and marking
        the session as active if it's not already active.

        Args:
            callback_context: The context object containing the current state.
            llm_request: The request object being processed by the language model.
        """
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
        current_agent = self.check_active_agent(context)
        return f"""
            You are an expert AI Orchestrator. Your primary responsibility is to intelligently interpret user requests, plan the necessary sequence of actions if multiple steps are involved, and delegate them to the most appropriate specialized remote agents. You do not perform the tasks yourself but manage their assignment, sequence, and can monitor their status.

            Core Workflow & Decision Making:

            1.  **Understand User Intent & Complexity:**
                *   Carefully analyze the user's request to determine the core task(s) they want to achieve. Pay close attention to keywords and the overall goal.
                *   **Identify if the request requires a single agent or a sequence of actions from multiple agents.** For example, "Analyze John Doe's profile and then create a positive post about his recent event attendance" would require two agents in sequence.

            2.  **Agent Discovery & Selection:**
                *   Use `list_remote_agents` to get an up-to-date list of available remote agents and understand their specific capabilities (e.g., what kind of requests each agent is designed to handle and what data they output).
                *   Based on the user's intent:
                    *   For **single-step requests**, select the single most appropriate agent.
                    *   For **multi-step requests**, identify all necessary agents and determine the logical order of their execution.

            3.  **Task Planning & Sequencing (for Multi-Step Requests):**
                *   Before delegating, outline the sequence of agent tasks.
                *   Identify dependencies: Does Agent B need information from Agent A's completed task?
                *   Plan to execute tasks sequentially if there are dependencies, waiting for the completion of a prerequisite task before initiating the next one.

            4.  **Task Delegation & Management:**
                *   **For New Single Requests or the First Step in a Sequence:** Use `create_task`. Your `create_task` call MUST include:
                    *   The `remote_agent_name` you've selected.
                    *   The `user_request` or all necessary parameters extracted from the user's input, formatted in a way the target agent will understand.
                *   **For Subsequent Steps in a Sequence:**
                    *   Wait for the preceding task to complete (you may need to use `check_pending_task_states` to confirm completion).
                    *   Once the prerequisite task is done, gather any necessary output from it.
                    *   Then, use `create_task` for the next agent in the sequence, providing it with the user's original relevant intent and any necessary data obtained from the previous agent's task.
                *   **For Ongoing Interactions with an Active Agent (within a single step):** If the user is providing follow-up information related to a task *currently assigned* to a specific agent, use the `update_task` tool.
                *   **Monitoring:** Use `check_pending_task_states` to check the status of any delegated tasks, especially when managing sequences or if the user asks for an update.

            **Communication with User:**

            *   When you delegate a task (or the first task in a sequence), clearly inform the user which remote agent is handling it.
            *   For multi-step requests, you can optionally inform the user of the planned sequence (e.g., "Okay, first I'll ask the 'Social Profile Agent' to analyze the profile, and then I'll have the 'Instavibe Posting Agent' create the post.").
            *   If waiting for a task in a sequence to complete, you can inform the user (e.g., "The 'Social Profile Agent' is currently processing. I'll proceed with the post once that's done.").
            *   If the user's request is ambiguous, if necessary information is missing for any agent in the sequence, or if you are unsure about the plan, proactively ask the user for clarification.
            *   Rely strictly on your tools and the information they provide.

            **Important Reminders:**
            *   Always prioritize selecting the correct agent(s) based on their documented purpose.
            *   Ensure all information required by the chosen remote agent is included in the `create_task` or `update_task` call, including outputs from previous agents if it's a sequential task.
            *   Focus on the most recent parts of the conversation for immediate context, but maintain awareness of the overall goal, especially for multi-step requests.

            Agents:
            {self.agents}

            Current agent: {current_agent['active_agent']}
            """

    async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
        """Send a message to the remote agent."""
        print("-- send_message --")
        if agent_name not in self.remote_agent_connections:
            print(f"LLM tried to call '{agent_name}' but it was not found. Available agents: {list(self.remote_agent_connections.keys())}")
            raise ValueError(f"Agent '{agent_name}' not found.")

        state = tool_context.state
        state['active_agent'] = agent_name
        client = self.remote_agent_connections[agent_name]

        task_id = state.get('task_id', str(uuid.uuid4()))
        context_id = state.get('context_id', str(uuid.uuid4()))
        message_id = state.get('input_message_metadata', {}).get('message_id', str(uuid.uuid4()))

        payload = create_send_message_payload(task, task_id, context_id)
        payload['message']['messageId'] = message_id

        message_request = SendMessageRequest(id=message_id, params=MessageSendParams.model_validate(payload))

        send_response: SendMessageResponse = await client.send_message(message_request=message_request)

        if not isinstance(send_response.root, SendMessageSuccessResponse) or not isinstance(send_response.root.result, Task):
            return None
        return send_response.root.result

    def check_active_agent(self, context: ReadonlyContext):
        """Check the state of the session."""
        state = context.state
        if ('session_active' in state and state['session_active'] and 'active_agent' in state):
            return {"active_agent": f'{state["active_agent"]}'}
        return {"active_agent": "None"}

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.cards:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append({"name": card.name, "description": card.description})

        print(f"List of all the remote agents: {remote_agent_info}")
        return remote_agent_info

    def create_agent(self) -> Agent:
        """Create the orchestrator agent."""
        return Agent(
            model="gemini-2.5-flash",
            name="orchestrate_agent",
            instruction=self.root_instruction,
            before_agent_callback=self.before_agent_callback,
            description=("This agent orchestrates the decomposition of the user request into"
                         " tasks that can be performed by the child agents."),
            tools=[
                self.list_remote_agents,
                self.send_message,
            ],
        )
