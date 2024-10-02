import os
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import Activity
from flask import Flask, request
from botbuilder.core.integration import aiohttp_error_middleware
import asyncio
import subprocess

app = Flask(__name__)

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = {
    "APP_ID": os.environ.get("MicrosoftAppId", ""),
    "APP_PASSWORD": os.environ.get("MicrosoftAppPassword", "")
}
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}")
    await context.send_activity("The bot encountered an error or bug.")

ADAPTER.on_turn_error = on_error

async def run_script(context: TurnContext):
    await context.send_activity("Starting user creation process...")
    
    # Run the user_creation.py script
    process = subprocess.Popen(['python', 'user_creation.py'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
    
    # Initialize an empty list to store the prompts
    prompts = []
    
    # Read the output line by line
    for line in process.stdout:
        # Send each line (prompt) to Teams
        await context.send_activity(line.strip())
        # Store the prompt
        prompts.append(line.strip())
        
        # Here you would typically wait for user input and send it back to the script
        # For simplicity, we're just collecting prompts here
    
    # Wait for the process to complete
    process.wait()
    
    # Check if there were any errors
    if process.returncode != 0:
        await context.send_activity("An error occurred while creating the user.")
    else:
        await context.send_activity("User creation process completed successfully.")

# Listen for incoming requests on /api/messages
@app.route("/api/messages", methods=["POST"])
def messages():
    # Main bot message handler.
    if "application/json" in request.headers["Content-Type"]:
        body = request.json
    else:
        return Response(status=415)

    async def call_run_script(turn_context):
        await run_script(turn_context)

    task = ADAPTER.process_activity(body, "", call_run_script)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
    return ""

if __name__ == "__main__":
    try:
        app.run(debug=False, port=3978)
    except Exception as e:
        raise e
