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
import asyncio
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

RETRY_COUNT=3
RETRY_WAIT_SECONDS = 5

from datetime import datetime
class JSONEncoderWithBytes(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        # Add support for encoding datetime.datetime (or Timestamp) objects
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert to ISO formatted string
        return super().default(obj)



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
        self.model_name = "gpt-3.5-turbo"

    async def create_task(self, task_request: TaskRequestBody) -> Task:
        """
        The agent protocol, which is the core of the Forge, works by creating a task and then
        executing steps for that task. This method is called when the agent is asked to create
        a task.

        We are hooking into function to add a custom log message. Though you can do anything you
        want here.
        """
        task = await super().create_task(task_request)
        self.messages=[]
        LOG.info(
            f"📦 Task created: {task.task_id} input: {task.input[:40]}{'...' if len(task.input) > 40 else ''}"
        )
        return task

    async def execute_step_half_baked(self, task_id: str, step_request: StepRequestBody) -> Step:
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
        task = await self.db.get_task(task_id)
        step = await self.db.create_step(
            task_id=task_id, input=step_request,
        )

        system_kwargs = {
                "abilities": self.abilities.list_abilities_for_prompt(),}
        
        prompt_engine=PromptEngine(model=self.model_name)
        
        system_prompt = prompt_engine.load_prompt("system-format", **system_kwargs)
        self.messages = [{"role": "system", "content": system_prompt}]
        
        task_kwargs = {"task": task.input}
        task_prompt = prompt_engine.load_prompt("task-step", **task_kwargs)
        self.messages.append({"role": "user", "content": task_prompt})

#        step_input = 'None'
 #       if step.input:
  #          step_input = step.input[:19]
   #     message = f'	🔄 Step executed: {step.step_id} input: {step_input}'
    #    if step.is_last:
     #       message = (
      #          f'	✅ Final Step completed: {step.step_id} input: {step_input}'
       #     )
        #LOG.info(message)

       # artifact=await self.db.create_artifact(
        #    task_id=task_id,
         #   step_id=step.step_id,
          #  file_name="output.txt",
           # relative_path="",
            #agent_created=True,
        #)

        #LOG.info(f'Received input for task {task_id}: {step_request.input}')
        #step.output = customstep(step_request.input)
        
        return step

    async def execute_step_tutorial(self, task_id: str, step_request: StepRequestBody) -> Step:
        # Firstly we get the task this step is for so we can access the task input
        task = await self.db.get_task(task_id)

        # Create a new step in the database
        step = await self.db.create_step(
            task_id=task_id, input=step_request, is_last=False
        )

        # Log the message
        LOG.info(f"\t✅ Final Step completed: {step.step_id} input: {step.input[:19]}")

        # Initialize the PromptEngine with the "gpt-3.5-turbo" model
        prompt_engine = PromptEngine("gpt-3.5-turbo")

        # Load the system and task prompts
        system_prompt = prompt_engine.load_prompt("system-format")

        # Initialize the messages list with the system prompt
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        # Define the task parameters
        task_kwargs = {
            "task": task.input,
            "abilities": self.abilities.list_abilities_for_prompt(),
        }

        # Load the task prompt with the defined task parameters
        task_prompt = prompt_engine.load_prompt("task-step", **task_kwargs)

        LOG.info(f"Task prompt {task_prompt}")
        # Append the task prompt to the messages list
        messages.append({"role": "user", "content": task_prompt})

        try:
            # Define the parameters for the chat completion request
            chat_completion_kwargs = {
                "messages": messages,
                "model": "gpt-3.5-turbo",
            }
            # Make the chat completion request and parse the response
            chat_response = await chat_completion_request(**chat_completion_kwargs)
            answer = json.loads(chat_response["choices"][0]["message"]["content"])

            # Log the answer for debugging purposes
            LOG.info(pprint.pformat(answer))

        except json.JSONDecodeError as e:
            # Handle JSON decoding errors
            LOG.error(f"Unable to decode chat response: {chat_response}")
        except Exception as e:
            # Handle other exceptions
            LOG.error(f"Unable to generate chat response: {e}")

        # Extract the ability from the answer
        ability = answer["ability"]

        # Run the ability and get the output
        # We don't actually use the output in this example
        #output = await self.abilities.run_action(
         #   task_id, ability["name"], **ability["args"]
        #)

        # Set the step output to the "speak" part of the answer
        step.output = answer["thoughts"]["speak"]

        # Return the completed step
        return step

    async def execute_step(self, task_id: str, step_request: StepRequestBody) -> Step:
        
        task=await self.db.get_task(task_id)
        step=await self.db.create_step(task_id=task_id, input=step_request,is_last=False)

        current_files = self.workspace.list(task_id, ".")

        if len(self.messages) < 2:
            prompt_engine = PromptEngine(self.model_name)
            system_kwargs = {
                "abilities": self.abilities.list_abilities_for_prompt(),
                "current_files": current_files
            }
            task_kwargs = {"task": task.input}
            system_prompt = prompt_engine.load_prompt("system-format", **system_kwargs)
            self.messages = [{"role": "system", "content": system_prompt}]
            task_prompt = prompt_engine.load_prompt("task-step", **task_kwargs)
            self.messages.append({"role": "user", "content": task_prompt})


        LOG.debug(f"\n\n\nSending the following messages to the model: {pprint.pformat(self.messages)}")

        for retry_attempt in range(RETRY_COUNT):
            try:
                # Chat completion request
                chat_completion_kwargs = {
                    "messages": self.messages,
                    "model": self.model_name,
                    "temperature": 0
                }
                chat_response = await chat_completion_request(**chat_completion_kwargs)

                answer_content = chat_response["choices"][0]["message"]["content"]

                # Check if the content is already a dictionary (JSON-like structure)
                if isinstance(answer_content, dict):
                    answer = answer_content
                else:
                    try:
                        # If answer_content is bytes, decode it
                        if isinstance(answer_content, bytes):
                            answer_content = answer_content.decode('utf-8')
                        
                        # Attempt to parse the content as JSON
                        answer = json.loads(answer_content)
                        LOG.debug(f"\n\n\nanswer: {pprint.pformat(answer)}")

                    except json.JSONDecodeError:
                        LOG.error(f"Unable to decode chat response: {chat_response}")
                        answer = None

                # Ability Sequence Execution
                ability_sequence = answer.get("abilities_sequence")
                previous_output = None

                for ability_item in ability_sequence:
                    ability = ability_item.get("ability", {})
                    LOG.debug("\n\nin the sequence %s", ability)

                    if "name" in ability and "args" in ability:
                        if previous_output and ability["name"] != "finish":
                            ability["args"].update({"input": previous_output})

                        output = await self.abilities.run_action(
                            task_id, ability["name"], **ability["args"]
                        )

                        LOG.debug("\n\nGot Output for %s : %s", ability["name"], output)

                        if isinstance(output, bytes):
                            output_str = output.decode('utf-8')
                        else:
                            output_str = output

                        if ability["name"] == "finish" or "File has been written successfully" in output_str:
                            step.is_last = True
                            step.status = "completed"

                        previous_output = output

                step.output = answer.get("speak","")
                if previous_output and isinstance(previous_output, str):
                    answer["final_output"] = previous_output

                # If everything is successful, break out of the retry loop
                LOG.info("\n\aanswer final %s", answer)
                break
            

            except Exception as e:
                if retry_attempt < RETRY_COUNT - 1:
                    LOG.warning(f"Error occurred in attempt {retry_attempt + 1}. {str(e)}")
                    await asyncio.sleep(RETRY_WAIT_SECONDS)
                else:
                    LOG.error(f"Error occurred in the final attempt {retry_attempt + 1}. Giving up.")
                    raise

        stringified_answer = json.dumps(answer, cls=JSONEncoderWithBytes)
        self.messages.append({"role": "assistant", "content": stringified_answer})

        if len(self.messages) >= 4:
            step.is_last = True

        return step