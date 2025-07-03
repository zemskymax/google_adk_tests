"""This module contains the menu data structure for the Pizza House application.

It defines a comprehensive menu of pizzas, crusts, toppings, sides, drinks, and combo meals
with their respective prices. This data is used throughout the application for order processing,
price calculations, and menu display.
"""

MENU = {
    "pizzas": {
        "Medium Pizza": 12.99,
        "Large Pizza": 16.99,
        "Extra-Large Pizza": 19.99,
    },
    "crusts": {
        "Thin": 0.00,
        "Regular": 0.00,
        "Deep Dish": 2.00,
    },
    "toppings": {
        "Extra Cheese": 1.50,
        "Pepperoni": 2.00,
        "Olives": 1.00,
        "Mushrooms": 1.00,
        "Jalapeños": 1.00,
        "Bacon": 2.50,
        "Pineapple": 1.00,
        "Chicken": 2.00,
        "Vegan Cheese": 2.00,
    },
    "sides": {
        "Garlic Bread": 4.99,
        "Cheese Sticks": 5.99,
        "Side Salad (Caesar or Greek)": 6.50,
        "Calzone": 8.99
    },
    "drinks": {
        "2-liter Coca-Cola": 3.50,
        "2-liter Pepsi": 3.50,
        "Bottled Water": 1.50,
        "Canned Soda (Coke, Sprite, Pepsi)": 1.50,
        "Iced Tea / Lemonade": 2.00,
    },
    "combos": {
        "Pizza & Wings Combo (1 Large Pizza + 6 Wings + 2-Liter Drink)": 24.99,
        "Family Feast (2 Large Pizzas + Garlic Bread + 2-Liter Drink)": 36.99,
        "Lunch Special (1 Medium Pizza + Soda)": 13.50, # (11am–2pm)
    },
}
