from forge.actions import ActionRegister
import json
import pprint
import requests
from forge.sdk import (
    Agent,
    AgentDB,
    Step,
    StepRequestBody,
    Workspace,
    ForgeLogger,
    Task,
    TaskRequestBody,
    PromptEngine,
    chat_completion_request,
)

import os
from dotenv import load_dotenv
from langchain import PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationSummaryBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from bs4 import BeautifulSoup
import requests
import json
from langchain.schema import SystemMessage
LOG = ForgeLogger(__name__)

load_dotenv()
open_ai_api = os.getenv('OPENAI_API_KEY')

class ForgeAgent(Agent):
    """
    The goal of the Forge is to take care of the boilerplate code, so you can focus on
    agent design.

    There is a great paper surveying the agent landscape: https://arxiv.org/abs/2308.11432
    Which I would highly recommend reading as it will help you understand the possabilities.

    Here is a summary of the key components of an agent:

    Anatomy of an agent:
         - Profile
         - Memory
         - Planning
         - Action

    Profile:

    Agents typically perform a task by assuming specific roles. For example, a teacher,
    a coder, a planner etc. In using the profile in the llm prompt it has been shown to
    improve the quality of the output. https://arxiv.org/abs/2305.14688

    Additionally, based on the profile selected, the agent could be configured to use a
    different llm. The possibilities are endless and the profile can be selected
    dynamically based on the task at hand.

    Memory:

    Memory is critical for the agent to accumulate experiences, self-evolve, and behave
    in a more consistent, reasonable, and effective manner. There are many approaches to
    memory. However, some thoughts: there is long term and short term or working memory.
    You may want different approaches for each. There has also been work exploring the
    idea of memory reflection, which is the ability to assess its memories and re-evaluate
    them. For example, condensing short term memories into long term memories.

    Planning:

    When humans face a complex task, they first break it down into simple subtasks and then
    solve each subtask one by one. The planning module empowers LLM-based agents with the ability
    to think and plan for solving complex tasks, which makes the agent more comprehensive,
    powerful, and reliable. The two key methods to consider are: Planning with feedback and planning
    without feedback.

    Action:

    Actions translate the agent's decisions into specific outcomes. For example, if the agent
    decides to write a file, the action would be to write the file. There are many approaches you
    could implement actions.

    The Forge has a basic module for each of these areas. However, you are free to implement your own.
    This is just a starting point.
    """

    def __init__(self, database: AgentDB, workspace: Workspace):
        """
        The database is used to store tasks, steps and artifact metadata. The workspace is used to
        store artifacts. The workspace is a directory on the file system.

        Feel free to create subclasses of the database and workspace to implement your own storage
        """
        super().__init__(database, workspace)
        self.abilities = ActionRegister(self)

    async def create_task(self, task_request: TaskRequestBody) -> Task:
        """
        The agent protocol, which is the core of the Forge, works by creating a task and then
        executing steps for that task. This method is called when the agent is asked to create
        a task.

        We are hooking into function to add a custom log message. Though you can do anything you
        want here.
        """
        task = await super().create_task(task_request)
        LOG.info(
            f"📦 Task created: {task.task_id} input: {task.input[:40]}{'...' if len(task.input) > 40 else ''}"
        )
        return task

    async def execute_step(self, task_id: str, step_request: StepRequestBody) -> Step:
        """
        For a tutorial on how to add your own logic please see the offical tutorial series:
        https://aiedge.medium.com/autogpt-forge-e3de53cc58ec

        The agent protocol, which is the core of the Forge, works by creating a task and then
        executing steps for that task. This method is called when the agent is asked to execute
        a step.

        The task that is created contains an input string, for the benchmarks this is the task
        the agent has been asked to solve and additional input, which is a dictionary and
        could contain anything.

        If you want to get the task use:

        ```
        task = await self.db.get_task(task_id)
        ```

        The step request body is essentially the same as the task request and contains an input
        string, for the benchmarks this is the task the agent has been asked to solve and
        additional input, which is a dictionary and could contain anything.

        You need to implement logic that will take in this step input and output the completed step
        as a step object. You can do everything in a single step or you can break it down into
        multiple steps. Returning a request to continue in the step output, the user can then decide
        if they want the agent to continue or not.
        """

        self.workspace.write(task_id=task_id, path="output.txt", data=b"IASpire preparing your lesson..")

        # An example that
        step = await self.db.create_step(
            task_id=task_id, input=step_request, is_last=True
        )

        step_input = 'None'
        if step.input:
            step_input = step.input[:19]
        message = f'	🔄 Step executed: {step.step_id} input: {step_input}'
        if step.is_last:
            message = (
                f'	✅ Final Step completed: {step.step_id} input: {step_input}'
            )
        LOG.info(message)

        artifact=await self.db.create_artifact(
            task_id=task_id,
            step_id=step.step_id,
            file_name="output.txt",
            relative_path="",
            agent_created=True,
        )

        LOG.info(f'Received input for task {task_id}: {step_request.input}')
        step.output = customstep(step_request.input)
        return step

def pyqs_search(query:str):
    # Endpoint URL
    url = 'https://dev-ai.server.sigiq.ai/async/custom-pyq-retrieval/'

    # JSON body data
    data = {
        "query": query,
        "topics": [],
        "start_year": 1993,
        "end_year": 2023
    }

    # Headers to indicate JSON content
    headers = {'Content-Type': 'application/json'}

    # Making the GET request with JSON body
    response = requests.get(url, headers=headers, data=json.dumps(data))

    # Checking if the request was successful
    if response.ok:
        # Parsing the JSON response
        response_data = response.json()
        print("Response Data:", response_data)
    else:
        print("Failed to get data from the endpoint. Status Code:", response.status_code)

    return """Q) The provisions in the Fifth Schedule and Sixth Schedule in the Constitution of India are made in order to (2015)
protect the interests of Scheduled Tribes
determine the boundaries between states
determine the powers, authorities, and responsibilities of Panchayats
protect the interests of all the border States
"""

def get_current_affairs(query):

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
        print("Response Data:", response_data)
    else:
        print("Failed to get data from the endpoint. Status Code:", response.status_code)
    
    LOG.info(f"Respohanse Data: {response_data}")
    return response_data["response"]


tools = [
    Tool(
        name="Previous_Year_Questions_Search",
        func=pyqs_search,
        description="Useful to search for past year questions for UPSC prelims to test student's learning"
    ),
    Tool(
        name="Current_Affairs",
        func=get_current_affairs,
        description="Useful to find how given query is related to current affairs"
    ),    
]

system_message = SystemMessage(
    content="""You are an expert UPSC teacher who crafts factual and engaging lessons for a UPSC aspirant query.
    You organize your lessons in a coherent manner giving static as well as current affairs information.
    You also test students' knowledge using past year questions or make your own questions on lesson content. You have 
    two tools at your disposal: Previous Year Questions Search and Current Affairs. You can use these tools to
    enhance your lesson. Use your inherent knowledge to get the static information. Compulsorily use the news search tool.
    """
)

agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
    "system_message": system_message,
}

llm = ChatOpenAI(temperature=0.9, model='gpt-3.5-turbo-16k-0613')

memory = ConversationSummaryBufferMemory(
    memory_key="memory", return_messages=True, llm=llm, max_token_limit=10000)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    agent_kwargs=agent_kwargs,
    memory=memory,
)


def customstep(query):
    result = agent({"input": query})
    return result['output']
