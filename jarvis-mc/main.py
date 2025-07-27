import os
import subprocess
import threading
import time
import signal
import sys
import re

import httpx
import json
import asyncio

# Constants
SERVER_PATH = "~/Documents/fabric_server/"
AI_NAME = "Jarvis"

# Globals
process = None
event_loop = asyncio.new_event_loop()

def shutdown_server(process):
    print("Stopping server...")
    process.stdin.write(b"stop\n")
    process.stdin.flush()

def signal_handler(sig, frame):
    global process
    shutdown_server(process)
    time.sleep(10)
    process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

async def ask_llm(process, query, history = []):
    proxy_url = "https://jarvis-api.com/proxy/text-query"
    data = {
        "query": f"If asking about information that could change over time, use tools for the following query: \n{query}.",
        "history": json.dumps(history),
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(proxy_url, data=data)

        data = response.json()
        print(f"\nJarvis response: {data}")
        llm_response = data["response"]["LLM_response"]
        command = f"say {llm_response}"
    except Exception as e:
        command = f"say Error accessing Jarvis. Is he awake?"
    write_input(process, command)
    return llm_response

def write_input(process, input_text):
    process.stdin.write(input_text.encode() + b"\n")
    process.stdin.flush()

def clean_input_line(input_line):
    match = re.search(r"]:\s<[^>]+>\s(.+)", input_line)
    if match:
        message = match.group(1)
        return message
    return False

def read_output(process, loop):
    for line in iter(process.stdout.readline, b""):
        output_line = line.decode().strip()
        print(output_line)
        if AI_NAME.lower() in output_line.lower() and "[Server]".lower() not in output_line.lower():
            cleaned_line = clean_input_line(output_line)
            if cleaned_line:
                asyncio.run_coroutine_threadsafe(
                    ask_llm(process, cleaned_line, []),
                    loop
                )

def main():
    global process

    threading.Thread(target=event_loop.run_forever, daemon=True).start()

    abs_server_path = os.path.expanduser(SERVER_PATH)
    command = ["java", "-Xmx12G", "-jar", "server.jar", "nogui"]

    process = subprocess.Popen(
        command,
        cwd=abs_server_path, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
    )

    threading.Thread(target=read_output ,args=(process, event_loop), daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
