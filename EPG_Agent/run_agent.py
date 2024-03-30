from .sigiq_tools import PreviousYearQuestionsSearchTool, CurrentAffairsTool, BookRAGTool, WikipediaSearchTool
from .sigiq_tools.anthropic_tools.tool_use_package.tool_user import ToolUser
import anthropic
import os

def main(query: str):
    tool_user = ToolUser(tools=[PreviousYearQuestionsSearchTool(),
                                CurrentAffairsTool(),
                                BookRAGTool(),
                                WikipediaSearchTool()])
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Client(api_key=anthropic_api_key)
    model = "claude-3-opus-20240229"
    
    response = tool_user.use_tool("previous_year_questions_search", query)
    print(response)