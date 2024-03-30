from forge.sdk.forge_log import ForgeLogger

from .registry import action

logger = ForgeLogger(__name__)


@action(
    name="finish",
    description="Use this to indicate that task is complete and the program should exit with final output." 
    " This is useful when you have finished your task successfully,"
    " or when there are insurmountable problems that make it impossible"
    " for you to finish your task.",
    parameters=[
        {
            "name": "reason",
            "description": "A summary to the user of how the goals were accomplished",
            "type": "string",
            "required": True,
        },
        {
            "name": "final_output",
            "description": "The final output of the task",
            "type": "string",
            "required": True,
        }        
    ],
    output_type="string",
)
async def finish(
    agent,
    task_id: str,
    reason: str,
    final_output: str,
) -> str:
    """
    A function that takes in two strings and exits the program

    Parameters:
        reason (str): A summary to the user of how the goals were accomplished.
        final_output (str): A result string from create chat completion.
    Returns:
        A result string from create chat completion.
    """

    logger.info(reason, extra={"title": "Shutting down...\n"})
    return final_output
