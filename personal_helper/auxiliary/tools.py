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
)
from google.adk.tools.tool_context import ToolContext
import uuid

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
            'parts': [{'type': 'text', 'text': text}],
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

    print(f"List of all the remote agents: {remote_agent_info}")
    return remote_agent_info

async def send_message(host_agent, agent_name: str, task: str, tool_context: ToolContext):
    """Send a message to the remote agent."""
    print("-- send_message --")
    if agent_name not in host_agent.remote_agent_connections:
        print(f"LLM tried to call '{agent_name}' but it was not found. Available agents: {list(host_agent.remote_agent_connections.keys())}")
        raise ValueError(f"Agent '{agent_name}' not found.")

    state = tool_context.state
    state['active_agent'] = agent_name
    client = host_agent.remote_agent_connections[agent_name]

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