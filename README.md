# Business Idea Validator Agent

## Introduction

This project provides an AI agent built with Python and the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) that validates business ideas or pain points by searching the internet for relevant information. The agent uses the built-in Google Search tool to assess the viability of the provided ideas based on factors such as market demand, competition, and existing solutions. It is designed to help entrepreneurs quickly evaluate the potential of their ideas by leveraging real-time web data and AI-driven analysis.

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.9 or higher** installed on your system.
- A **Google Cloud account** with access to the [Google AI Studio](https://aistudio.google.com/apikey) to obtain an API key.
- Basic knowledge of Python and command-line interfaces.

## Installation

1. **Create a virtual environment:**

   ```bash
   python -m venv .venv
   ```

2. **Activate the virtual environment:**

   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows:
     ```bash
     .venv\Scripts\activate.bat
     ```

3. **Install the Google Agent Development Kit (ADK):**

   ```bash
   pip install google-adk
   ```

## Configuration

1. **Obtain an API key:**

   - Go to [Google AI Studio](https://aistudio.google.com/apikey) and generate an API key.

2. **Set up the `.env` file:**

   - Create a file named `.env` in the project directory with the following content:
     ```
     GOOGLE_GENAI_USE_VERTEXAI=FALSE
     GOOGLE_API_KEY=your_api_key_here
     ```
   - Replace `your_api_key_here` with the API key you obtained.

## Running the Agent

1. **Navigate to the parent directory:**

   - Ensure you are in the directory that contains the `business_validator` folder.

2. **Run with the web UI:**

   - Execute the following command:
     ```bash
     adk web
     ```
   - Open your web browser and go to `http://localhost:8000`.
   - Select `business_validator` from the dropdown menu.
   - Enter your business idea in the input field and submit.

3. **Run via the terminal:**

   - Execute the following command:
     ```bash
     adk run business_validator
     ```
   - When prompted, enter your business idea.

## Usage Examples

Here are some examples of how to use the agent:

- **Input:**
  ```
  Validate the business idea of a subscription box for eco-friendly pet products.
  ```

- **Expected Output:**
  - A summary of findings, such as existing competitors, market demand, and potential challenges.
  - A viability assessment (e.g., low, medium, high).
  - Recommendations for next steps.

- **Input:**
  ```
  Assess the pain point of long wait times for restaurant reservations.
  ```

- **Expected Output:**
  - Information on existing solutions, customer feedback, and market trends.
  - An assessment of whether this pain point represents a viable business opportunity.
  - Suggestions for further research or potential solutions.

## Limitations

- The agent can only use one built-in tool (e.g., Google Search) per agent.
- The effectiveness of the agent depends on the quality of the search results and the model's ability to interpret them.
- If the search results are insufficient, the agent may not provide a conclusive assessment.

## Troubleshooting

- **Issue:** The agent fails to find relevant information.
  - **Solution:** Try rephrasing the business idea or using different keywords in your input.

- **Issue:** Errors related to API key configuration.
  - **Solution:** Ensure that the `.env` file is correctly set up with the API key and that the key has the necessary permissions.

## Further Resources

For more information and advanced usage, refer to the following resources:

- [Agent Development Kit (ADK) Documentation](https://google.github.io/adk-docs/)
- [ADK Python GitHub Repository](https://github.com/google/adk-python)
- [Google AI Studio for API Key](https://aistudio.google.com/apikey)
- [ADK Tools Documentation](https://google.github.io/adk-docs/tools/)
- [ADK Built-in Tools Documentation](https://google.github.io/adk-docs/tools/built-in-tools/)