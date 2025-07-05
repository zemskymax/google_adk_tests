from typing import Dict, List, Any

def split_order(user_request: str, available_agents: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Determines how to split an order across multiple restaurant agents.

    For now, this is a simple strategy that sends the entire order to the first available agent.
    In the future, this could be expanded to parse the user's request and split it into sub-orders
    for different restaurants based on their menus.
    """
    if not available_agents:
        return []

    # Simple strategy: send the full request to the first agent that sounds relevant
    # A more advanced strategy would parse the request and match items to specific restaurant menus
    first_agent_name = list(available_agents.keys())[0]
    return [{"agent_name": first_agent_name, "task": user_request}]
