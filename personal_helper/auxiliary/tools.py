"""
This module contains tools for discovering available food options.
These functions provide hardcoded data for the initial version of the agent system.
"""

def get_available_cuisines() -> list[str]:
    """
    Returns a list of available food cuisines.

    Returns:
        list[str]: A list of cuisine names.
    """
    return ["Italian", "Greek", "Chinese"]

def get_foods_for_cuisine(cuisine: str) -> list[str]:
    """
    Returns a list of food items for a specific cuisine.

    Args:
        cuisine (str): The name of the cuisine to look up.

    Returns:
        list[str]: A list of food items. Returns an empty list if the cuisine is not found.
    """
    # Hardcoded data mapping cuisines to specific food items.
    food_map = {
        "Italian": ["Pizza", "Pasta"],
        "Greek": ["Gyro", "Souvlaki"],
        "Chinese": ["General Tso's Chicken", "Dumplings"]
    }
    # Return the list of foods for the given cuisine, case-insensitively.
    return food_map.get(cuisine.capitalize(), [])
