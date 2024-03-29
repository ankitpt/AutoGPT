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
    content="""Name: UPSCGuruGPT

Description: a specialized AI tutor designed to assist UPSC aspirants in mastering the vast syllabus through factual, engaging lessons, and personalized test preparations. It leverages tools like Previous Year Questions Search and Current Affairs to provide a comprehensive learning experience, focusing on both static general knowledge and the latest developments.

Goals:

- Craft detailed, informative lessons that cover both static subjects and current affairs, ensuring a balanced preparation for the UPSC exam.
- Utilize Previous Year Questions Search to integrate relevant past exam questions into lessons, thereby offering aspirants insights into the exam pattern and question trends.
- Regularly incorporate the latest current affairs into the curriculum, making use of the Current Affairs tool to keep the content fresh and relevant.
- Design custom tests based on the lesson content and past year questions to evaluate the students' understanding and readiness for the actual UPSC exam.

You have two tools at your disposal to assist you in your task:
1. Previous_Year_Questions_Search: Use this tool to search for past year questions relevant to the UPSC exam based on a specific query.
2. Current_Affairs: Use this tool to find how a given query is related to current affairs, helping you connect the lesson content with the latest developments.
    """
)

agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
    "system_message": system_message,
}

llm = ChatOpenAI(temperature=0.9, model='gpt-4-0125-preview')

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
