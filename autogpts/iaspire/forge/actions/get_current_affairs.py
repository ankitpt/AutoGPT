from forge.sdk.forge_log import ForgeLogger
import requests
from .registry import action
import json
logger = ForgeLogger(__name__)


@action(
    name="get_current_affairs",
    description="Use this to contextualize the user query with current affairs, an important part of the UPSC exam preparation.",
    parameters=[
        {
            "name": "query",
            "description": "The UPSC topic the user wants to learn about in the context of current affairs.",
            "type": "string",
            "required": True,
        }
    ],
    output_type="string",
)
async def get_current_affairs(agent, task_id:str, query:str) -> str:

    url="https://dev-ai.server.sigiq.ai/async/news-rag/"

    data = {
        "query": query,
    }    

    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers, data=json.dumps(data))

    # Checking if the request was successful
    if response.ok:
        # Parsing the JSON response
        response_data = response.json()
    else:
        print("Failed to get data from the endpoint. Status Code:", response.status_code)
    
    return response_data["response"]
