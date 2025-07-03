from .host_agent import HostAgent
import asyncio
import os # Import os to read environment variables
from dotenv import load_dotenv
from google.adk.agents import BaseAgent
from common.types import Task, AgentCard
import logging 
# import nest_asyncio # Import nest_asyncio
import atexit


load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def on_task_update(task: Task, agent_card: AgentCard):
    log.info(f"** Task update event: {task} **")
    log.info(f"** Agent card: {agent_card} **")

# --- Global variables ---
# Define them first, initialize as None

# --- Configuration ---
# It's better to get this from environment variables or a config file
# REMOTE_AGENT_ADDRESSES_STR = os.getenv("REMOTE_AGENT_ADDRESSES", "")
REMOTE_AGENT_ADDRESSES_STR = "http://localhost:10003,http://localhost:10004"
log.info(f"Remote Agent Addresses String: {REMOTE_AGENT_ADDRESSES_STR}")
REMOTE_AGENT_ADDRESSES = [addr.strip() for addr in REMOTE_AGENT_ADDRESSES_STR.split(',') if addr.strip()]
log.info(f"Remote Agent Addresses: {REMOTE_AGENT_ADDRESSES}")

# --- Agent Initialization ---
# Instantiate the HostAgent logic class
# You might want to add a task_callback here if needed, similar to run_orchestrator.py
host_agent_logic = HostAgent(remote_agent_addresses=REMOTE_AGENT_ADDRESSES, task_callback=on_task_update)

# Create the actual ADK Agent instance
root_agent: BaseAgent = host_agent_logic.create_agent()
log.info(f"Orchestrator root agent '{root_agent.name}' created.")
