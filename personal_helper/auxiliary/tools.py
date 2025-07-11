from collections.abc import Callable
import httpx
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    SendMessageRequest,
    SendMessageResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    MessageSendParams,
    SendMessageSuccessResponse,
    TextPart,
)
from google.adk.tools.tool_context import ToolContext
import uuid
from typing import List, Dict, Any
import logging
from datetime import datetime
import re
import json

logger = logging.getLogger(__name__)

def get_daily_cash_balance(tool_context: ToolContext) -> str:
    """Returns the user's daily cash balance."""
    balance = tool_context.state.get('daily_balance', 25.00)
    return f"${balance:.2f}"

def subtract_from_daily_balance(amount_str: str, tool_context: ToolContext) -> str:
    """Subtracts an amount from the user's daily cash balance. Expects a string like '$10.50' or '10.50'."""
    logger.info(f"Attempting to subtract '{amount_str}' from balance.")
    
    try:
        # Remove any non-numeric characters except for the decimal point
        amount_str = re.sub(r"[^0-9.]", "", amount_str)
        amount = float(amount_str)
    except (ValueError, TypeError):
        logger.error(f"Could not parse amount from: {amount_str}")
        return "Invalid amount format. Please provide a number."

    balance = tool_context.state.get('daily_balance', 25.00)
    
    if amount > balance:
        logger.warning(f"Insufficient funds. Balance ${balance:.2f}, order ${amount:.2f}.")
        return f"Insufficient funds. Current balance is ${balance:.2f}, but order costs ${amount:.2f}."
    
    new_balance = balance - amount
    tool_context.state['daily_balance'] = new_balance
    logger.info(f"Subtracted ${amount:.2f} from balance. New balance: ${new_balance:.2f}")
    return f"Successfully subtracted ${amount:.2f}. New balance is ${new_balance:.2f}."

def get_current_date():
    """Returns the current date."""
    return datetime.now().strftime("%Y-%m-%d")


TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]

class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        self._httpx_client = httpx.AsyncClient(timeout=30)
        self.agent_client = A2AClient(
            self._httpx_client, agent_card, url=agent_url
        )
        self.card = agent_card

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(
        self, message_request: SendMessageRequest
    ) -> SendMessageResponse:
        return await self.agent_client.send_message(message_request)

def create_send_message_payload(text: str, task_id: str | None = None, context_id: str | None = None) -> dict[str, any]:
    """Create a payload for sending a message to the remote agent."""
    payload: dict[str, any] = {
        'message': {
            'role': 'user',
            'parts': [TextPart(text=text)],
            'messageId': uuid.uuid4().hex,
        },
    }
    if task_id:
        payload['message']['taskId'] = task_id
    if context_id:
        payload['message']['contextId'] = context_id
    return payload

def list_remote_agents(host_agent):
    """List the available remote agents you can use to delegate the task."""
    if not host_agent.cards:
        return []

    remote_agent_info = []
    for card in host_agent.cards.values():
        remote_agent_info.append({"name": card['name'], "description": card['description']})

    logger.info(f"List of all the remote agents: {remote_agent_info}")
    return remote_agent_info

def get_user_address():
    """Returns the user's delivery address."""
    return "123 Main St, Anytown, USA 12345"

def get_user_phone_number():
    """Returns the user's phone number."""
    return "555-123-4567"

async def get_restaurant_menu(host_agent, agent_name: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Fetches the menu from a specified restaurant agent."""
    logger.info(f"-- get_restaurant_menu for {agent_name} --")
    # Use the send_message tool to ask for the menu
    task_response = await send_message(host_agent, agent_name, "Send me your full menu.", tool_context)

    if not task_response or not hasattr(task_response, "id"):
        logger.error(f"Error: Could not get a task ID from {task_response}.")
        return {"error": f"Could not get a task ID from {agent_name}."}

    client = host_agent.remote_agent_connections[agent_name].agent_client

    # The send_message function returns a Task object. The agent's reply is in the parts.
    if task_response and hasattr(task_response, "artifacts") and task_response.artifacts:
        # We expect the restaurant agent to reply with the menu in a text part.
        for part in task_response.artifacts[-1].parts:
            if isinstance(part.root, TextPart):
                # The pizza bot might return the raw JSON from its get_full_menu tool,
                # or it might return a conversational text description of the menu.
                # We can try to parse it as JSON first.
                try:
                    menu_data = json.loads(part.root.text)
                    # The get_full_menu tool returns a dict with a "menu" key.
                    if "menu" in menu_data:
                        return menu_data
                except json.JSONDecodeError:
                    # If it's not JSON, it's conversational text.
                    # The helper agent's LLM can work with this.
                    return {"menu": part.root.text}
                # Fallback in case the JSON doesn't have a "menu" key.
                return {"menu": part.root.text}
    return {"error": f"Could not retrieve the menu from {agent_name}."}

async def send_message(host_agent, agent_name: str, task: str, tool_context: ToolContext):
    """Send a message to the remote agent."""
    logger.info("-- send_message --")
    if agent_name not in host_agent.remote_agent_connections:
        logger.error(f"LLM tried to call '{agent_name}' but it was not found. Available agents: {list(host_agent.remote_agent_connections.keys())}")
        raise ValueError(f"Agent '{agent_name}' not found.")

    state = tool_context.state
    state['active_agent'] = agent_name
    client = host_agent.remote_agent_connections[agent_name]

    if 'restaurant_sessions' not in state:
        state['restaurant_sessions'] = {}

    if agent_name not in state['restaurant_sessions']:
        state['restaurant_sessions'][agent_name] = {
            "context_id": str(uuid.uuid4()),
            "task_id": str(uuid.uuid4()),
        }

    session_data = state['restaurant_sessions'][agent_name]
    context_id = session_data["context_id"]
    task_id = session_data["task_id"]
    message_id = state.get('input_message_metadata', {}).get('message_id', str(uuid.uuid4()))

    payload = create_send_message_payload(task, task_id, context_id)
    payload['message']['messageId'] = message_id

    message_request = SendMessageRequest(id=message_id, params=MessageSendParams.model_validate(payload))

    try:
        async with httpx.AsyncClient() as logging_client:
            sender_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', host_agent.agent_name)
            await logging_client.post("http://localhost:10111/log", json={"agent": sender_name, "message": task})
    except httpx.RequestError as ex:
        logger.error("Could not log message to monitor: {ex}")

    send_response: SendMessageResponse = await client.send_message(message_request=message_request)

    if not isinstance(send_response.root, SendMessageSuccessResponse) or not isinstance(send_response.root.result, Task):
        return None

    if hasattr(send_response.root.result, 'id') and send_response.root.result.id:
        state['restaurant_sessions'][agent_name]["task_id"] = send_response.root.result.id

    try:
        async with httpx.AsyncClient() as logging_client:
            print("**********************************")
            # print(send_response.root.result)
            # print(send_response.root.result.artifacts)
            artifact_number = 0
            if send_response.root.result and hasattr(send_response.root.result, 'artifacts'):
                artifact = send_response.root.result.artifacts[-1]
                # for artifact in send_response.root.result.artifacts:
                for part in artifact.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        await logging_client.post("http://localhost:10111/log", json={"agent": agent_name, "message": part.root.text})
                    print(f"artifact number {artifact_number} part {part}")
                artifact_number += 1
            print("**********************************")
    except httpx.RequestError as e:
        logger.error("Could not log message to monitor: {e}")

    return send_response.root.result

async def plan_order(host_agent, user_request: str, tool_context: ToolContext) -> List[Dict[str, Any]]:
    """
    Creates a plan for ordering food, potentially splitting the order across multiple restaurants.
    """
    return await host_agent.plan_order(user_request, tool_context)
