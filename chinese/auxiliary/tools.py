import random
from typing import Dict, Any, List
from .menu import MENU
from .order import Order, MainCourseItem

TAX_RATE = 0.08

def get_full_menu() -> Dict[str, Any]:
    """Returns the entire menu with all categories and prices."""
    return {"menu": MENU}

def add_item_to_order(order: Dict[str, Any], category: str, item: str) -> Dict[str, Any]:
    """Adds an item to the current order under a specified category."""
    if category not in MENU or item not in MENU[category]:
        return {"error": f"Sorry, we don't have '{item}' in the '{category}' category."}

    if category not in order:
        order[category] = []
    order[category].append(item)

    order['order_status'] = "building"
    return {"updated_order": order, "confirmation_message": f"Added {item} to your order."}

def add_main_course_to_order(order: Dict[str, Any], name: str, with_rice: str = None) -> Dict[str, Any]:
    """Adds a main course with an optional rice choice to the current order."""
    if name not in MENU["main_courses"]:
        return {"error": f"Sorry, we don't have '{name}' as a main course."}
    if with_rice and with_rice not in MENU["rice_and_noodles"]:
        return {"error": f"Sorry, we don't offer '{with_rice}'."}

    main_course = MainCourseItem(name=name, with_rice=with_rice)

    if 'main_courses' not in order:
        order['main_courses'] = []
    order['main_courses'].append(main_course.model_dump())

    order['order_status'] = "building"
    rice_confirmation = f" with {with_rice}" if with_rice else ""
    return {"updated_order": order, "confirmation_message": f"Got it. One {name}{rice_confirmation}."}


def calculate_total(order: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates the subtotal, tax, and total for the current order."""
    subtotal = 0.0

    for category, items in order.items():
        if category in MENU:
            for item in items:
                if isinstance(item, dict) and 'name' in item: # For main courses
                    main_course = MainCourseItem(**item)
                    item_price = MENU["main_courses"].get(main_course.name, 0)
                    if main_course.with_rice:
                        item_price += MENU["rice_and_noodles"].get(main_course.with_rice, 0)
                    main_course.price = item_price
                    subtotal += item_price
                elif isinstance(item, str): # For other categories
                    subtotal += MENU[category].get(item, 0)


    tax = subtotal * TAX_RATE
    total = subtotal + tax

    order["subtotal"] = round(subtotal, 2)
    order["tax"] = round(tax, 2)
    order["total"] = round(total, 2)

    return {"billing_summary": order}

def process_payment(order: Dict[str, Any], payment_method: str) -> Dict[str, Any]:
    """Processes the payment for the order."""
    if order.get("total", 0) == 0:
        return {"error": "The total has not been calculated yet. Please call `calculate_total` first."}

    valid_methods = ["credit card", "debit", "cash on delivery"]
    if payment_method.lower() not in valid_methods:
        return {"error": f"Invalid payment method. Please choose from: {', '.join(valid_methods)}."}

    order["payment_status"] = "paid"
    order["order_status"] = "confirmed"

    return {
        "confirmation_message": f"Payment of ${order['total']:.2f} via {payment_method} confirmed. Your order is placed!",
        "final_order": order
    }

def get_order_eta(order: Dict[str, Any]) -> str:
    """Provides an estimated time of arrival (ETA) for the order."""
    if not order or order.get('order_status') != 'confirmed':
        return "Please confirm the order and payment before I can provide an ETA."

    is_delivery = order.get("is_delivery", False)

    if is_delivery:
        eta = f"{random.randint(35, 50)} minutes"
        return f"Your delivery order should arrive in about {eta}."
    else:
        eta = f"{random.randint(15, 25)} minutes"
        return f"Your pickup order will be ready in about {eta}."
