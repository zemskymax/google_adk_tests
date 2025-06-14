import random
from typing import Dict, Any, List
from .menu import MENU
from .order import Order, PizzaItem

TAX_RATE = 0.08

def get_full_menu() -> Dict[str, Any]:
    """Returns the entire menu with all categories and prices, which you can then present to the customer."""
    return {"menu": MENU}

def add_pizza_to_order(order: Dict[str, Any], size: str, crust: str, toppings: List[str]) -> Dict[str, Any]:
    """
    Adds a pizza with a specified size, crust, and toppings to the current order.
    Validates all items against the menu.
    """
    # Validate size
    if size not in MENU["pizzas"]:
        return {"error": f"Sorry, we don't offer '{size}'. Available sizes are: {', '.join(MENU['pizzas'].keys())}."}

    # Validate crust
    if crust not in MENU["crusts"]:
        return {"error": f"Sorry, we don't have '{crust}' crust. Available crusts are: {', '.join(MENU['crusts'].keys())}."}

    # Validate toppings
    invalid_toppings = [t for t in toppings if t not in MENU["toppings"]]
    if invalid_toppings:
        return {"error": f"Sorry, we don't have the following toppings: {', '.join(invalid_toppings)}."}

    pizza_item = PizzaItem(size=size, crust=crust, toppings=toppings)

    # Add the pizza to the order
    if 'pizzas' not in order:
        order['pizzas'] = []
    order['pizzas'].append(pizza_item.model_dump())

    order['order_status'] = "building"
    return {"updated_order": order, "confirmation_message": f"Added one {size} with {crust} crust and {', '.join(toppings) if toppings else 'no extra'} toppings."}

def add_side_to_order(order: Dict[str, Any], side: str) -> Dict[str, Any]:
    """Adds a side dish to the current order."""
    if side not in MENU["sides"]:
        return {"error": f"Sorry, we don't offer '{side}'. Available sides are: {', '.join(MENU['sides'].keys())}."}

    if 'sides' not in order:
        order['sides'] = []
    order['sides'].append(side)

    order['order_status'] = "building"
    return {"updated_order": order, "confirmation_message": f"Got it. Added {side} to your order."}

def add_drink_to_order(order: Dict[str, Any], drink: str) -> Dict[str, Any]:
    """Adds a drink to the current order."""
    if drink not in MENU["drinks"]:
        return {"error": f"Sorry, we don't have '{drink}'. Available drinks are: {', '.join(MENU['drinks'].keys())}."}

    if 'drinks' not in order:
        order['drinks'] = []
    order['drinks'].append(drink)

    order['order_status'] = "building"
    return {"updated_order": order, "confirmation_message": f"Perfect, one {drink} added."}

def calculate_total(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the subtotal, tax, and total for the current order based on the items added.
    This should be called when the customer is ready to checkout.
    """
    subtotal = 0.0

    # Calculate pizza costs
    for pizza_data in order.get("pizzas", []):
        pizza = PizzaItem(**pizza_data)
        item_price = MENU["pizzas"].get(pizza.size, 0)
        item_price += MENU["crusts"].get(pizza.crust, 0)
        for topping in pizza.toppings:
            item_price += MENU["toppings"].get(topping, 0)
        pizza.price = item_price
        subtotal += item_price

    # Calculate sides, drinks, and combos
    for side in order.get("sides", []):
        subtotal += MENU["sides"].get(side, 0)
    for drink in order.get("drinks", []):
        subtotal += MENU["drinks"].get(drink, 0)
    for combo in order.get("combos", []):
        subtotal += MENU["combos"].get(combo, 0)

    tax = subtotal * TAX_RATE
    total = subtotal + tax

    order["subtotal"] = round(subtotal, 2)
    order["tax"] = round(tax, 2)
    order["total"] = round(total, 2)

    return {"billing_summary": order}

def process_payment(order: Dict[str, Any], payment_method: str) -> Dict[str, Any]:
    """
    Processes the payment for the order. In this simulation, it confirms payment.
    It should only be called after the total has been calculated.
    """
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
    """
    Provides an estimated time of arrival (ETA) for the order.
    The ETA depends on whether the order is for delivery or pickup.
    """
    if not order or order.get('order_status') != 'confirmed':
        return "Please confirm the order and payment before I can provide an ETA."

    is_delivery = order.get("is_delivery", False)

    if is_delivery:
        eta = f"{random.randint(30, 45)} minutes"
        return f"Your delivery order should arrive in about {eta}."
    else:
        eta = f"{random.randint(15, 20)} minutes"
        return f"Your pickup order will be ready in about {eta}."
