from difflib import SequenceMatcher
from typing import List
import requests
import json
from .anthropic_tools.tool_use_package.tools.base_tool import BaseTool
from .utils import pyqs_to_xml, ID_TO_PYQ

class PreviousYearQuestionsSearchTool(BaseTool):
    PYQ_EXAMPLE_PATH = "EPG_Agent/data/prompts/pyq_search_example.txt"
    with open(PYQ_EXAMPLE_PATH, "r") as f:
        PYQ_EXAMPLE = f.read()
    f"""
    This tool searches for past year UPSC Prelims questions relevant to the query.
    
    Inputs:
        query: str = Query to retrieve past year questions
    Output:
        str: A sequence of questions formatted in XML in decreasing order of relevance to the query. The order of relevance may not be perfect.
    
    Examples Queries:
        - Polity
        - agriculture
        - Chola Dynasty
        - Article 14 of the Constitution        
    
    Example Usage:
        {PYQ_EXAMPLE}
    """
    
    def __init__(self):
        self.default_response = "No Questions Found."
        
        """
        Temporary limit for testing, so we don't pollute context window with too many questions.
        """
        self.max_num_questions = 5
        
        super().__init__("previous_year_questions_search", self.__doc__, [{"name": "query", "type": "str", "description": "Query to retrieve past year questions"}])
    
    def use_tool(self, query: str, topics: List[str] = [], start_year: int = 1993, end_year: int = 2023) -> str:
        # Endpoint URL
        url = 'https://dev-ai.server.sigiq.ai/async/custom-pyq-retrieval/'

        # JSON body data
        data = {
            "query": query,
            "topics": topics,
            "start_year": start_year,
            "end_year": end_year
        }

        # Headers to indicate JSON content
        headers = {'Content-Type': 'application/json'}

        # Making the GET request with JSON body
        response = requests.get(url, headers=headers, data=json.dumps(data))

        # Checking if the request was successful
        if response.ok:
            # Parsing the JSON response
            response_data = response.json()['response']
                    
            # Get all Question IDS from response_data
            question_ids = [elem[0] for elem in response_data['high_relevance_ids']] + [elem[0] for elem in response_data['low_relevance_ids_scores']]
            
            if len(question_ids) > 0:
                questions = [ID_TO_PYQ[question_id] for question_id in question_ids][:self.max_num_questions]
                
                return pyqs_to_xml(questions)
            else:
                return self.default_response
        else:
            print("Failed to get data from the endpoint. Status Code:", response.status_code)
            return self.default_response

class CurrentAffairsTool(BaseTool):
    CURRENT_AFFAIRS_EXAMPLE_PATH = "EPG_Agent/data/prompts/current_affairs_example.txt"
    with open(CURRENT_AFFAIRS_EXAMPLE_PATH, "r") as f:
        CURRENT_AFFAIRS_EXAMPLE = f.read()
    f"""
    This tool searches reliable news sources to get the latest information on the query, background information, and suggestions on how to use to information to prepare for UPSC.
    
    Inputs:
        query: str = Query to retrieve current affairs information
    Output:
        str: It returns a markdown formatted string.
    
    Example Queries:
        - What problem did Bangalore face recently due to monsoons?
        - Elephant Corridors in India
        - Electoral Bonds
    
    Example Usage:
        {CURRENT_AFFAIRS_EXAMPLE}
    """
    
    def __init__(self):
        super().__init__("news_search", self.__doc__, [{"name": "query", "type": "str", "description": "News Query"}])

    def use_tool(query: str) -> str:
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
        
        return response_data["response"]
    
class BookRAGTool(BaseTool):
    BOOK_RAG_EXAMPLE_PATH = "EPG_Agent/data/prompts/book_rag_example.txt"
    with open(BOOK_RAG_EXAMPLE_PATH, "r") as f:
        BOOK_RAG_EXAMPLE = f.read()
    
    f"""
    This tool can ask a question about a book containing UPSC relevant content and get an well informed response using information and citations from the book.
    
    The books available are:
        1. Indian Polity for Civil Services Examinations by M. Laxmikanth
        2. Brief History of Modern India by R. Ahir
        3. India after Ghandi by R. Guha
        4. Indian Art and Culture by N. Singhania
        5. Indian Economy by R. Singh
        6. PMF IAS Environment by M. Thamminidi
        
    Inputs:
        book: str = Name of the book to search. This should be the exact title that was listed.
        query: str = the question
        
    Example Queries:
        Indian Polity for Civil Services Examinations:
            - Why is Article 32 called the heart and soul of the Constitution?
            
        Brief History of Modern India:
            - Why is the revolt of 1857 considered a watershed moment in Indian independence history?
            
        India After Gandhi:
            - How various PMs shaped India’s foreign policy after independence?

        Indian Art and Culture:
            - Explore the Mughal art and architecture patronized by Mughal emperors

        Indian Economy:
            - What are WTO's norms on farm subsidies?
            
        PMF IAS Environment:
            - What is Environment Impact Assessment and its significance?
            
    Example Usage:
        {BOOK_RAG_EXAMPLE}
    """
    
    def __init__(self):
        self.book_name_2_id = {"Indian Polity for Civil Services Examinations": "polity_laxmikanth",
                               "Brief History of Modern India": "india_ahir",
                               "India After Ghandi": "democracy_guha",
                               "Indian Art and Culture": "culture_singhania",
                               "Indian Economy": "economy_singh",
                               "PMF IAS Environment": "ias_thamminidi"}
        super().__init__("ask_book", self.__doc__, [{"name": "book", "type": "str", "description": "Name of the book to search. This should be the exact title that was listed."}, 
                                                    {"name": "query", "type": "str", "description": "News Query"}])
    
    def _get_book_name(self, input_book_str: str):
        book_names = list(self.book_name_2_id.keys())
        closest_string = book_names[0]
        max_ratio = SequenceMatcher(None, input_book_str, closest_string).ratio()

        for string in book_names[1:]:
            ratio = SequenceMatcher(None, input_book_str, string).ratio()
            if ratio > max_ratio:
                max_ratio = ratio
                closest_string = string

        return closest_string
   
    def use_tool(self, book: str, query: str):
        url="https://dev-ai.server.sigiq.ai/async/book-rag/book_rag_for_agent/"
        
        book = self._get_book_name(input_book_str=book)
        data = {
            "book": self.book_name_2_id[book],
            "query": query,
        }    

        headers = {'Content-Type': 'application/json'}

        response = requests.get(url, headers=headers, data=json.dumps(data), timeout=180)

        # Checking if the request was successful
        if response.ok:
            # Parsing the JSON response
            return response
        else:
            print("Failed to get data from the endpoint. Status Code:", response.status_code)
            return response
    



current_autogpt_sys_prompt = \
"""Name: UPSCGuruGPT

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
