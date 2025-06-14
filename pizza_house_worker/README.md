# Luigi's PizzaBot

This project is a conversational AI agent that simulates a worker at a pizza house, created using the Google Agent Development Kit (ADK). The agent, "Alex," can take orders, provide menu information, handle customizations, process payments, and give order estimates.

## Features

-   **Conversational Ordering:** Natural language conversation for placing pizza orders.
-   **Menu Inquiry:** Ask for the full menu or specific categories.
-   **Order Customization:** Specify pizza size, crust, and toppings.
-   **Pickup or Delivery:** Handles both order types, collecting address information for delivery.
-   **Billing & Payment:** Calculates subtotal, tax, and total, and simulates payment processing.
-   **Order ETA:** Provides an estimated time for order readiness.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd luigis_pizzabot
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Rename or copy the `.env` file and add your Google API key.
    ```bash
    cp .env .env.local
    # Now edit .env.local and add your key:
    # GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    ```
    The ADK will automatically load variables from `.env.local`.

## Running the Agent

You can interact with Luigi's PizzaBot using the ADK's built-in web interface or directly from the command line.

### Web Interface (Recommended)

Run the following command to start the ADK web server:
```bash
adk web
```
