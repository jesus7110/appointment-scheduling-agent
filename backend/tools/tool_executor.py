"""
Tool execution logic - maps tool calls to actual functions.
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tool calls from the LLM."""
    
    def __init__(self):
        self.tool_map = {
            "end_conversation": self._end_conversation,
        }
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool
            
        Returns:
            Dictionary with tool execution results and any special actions
        """
        if tool_name not in self.tool_map:
            error_msg = f"Unknown tool: {tool_name}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        try:
            result = self.tool_map[tool_name](**arguments)
            return result
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            logger.error(f"{error_msg} for tool {tool_name} with args {arguments}", exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _end_conversation(self, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        End the conversation and signal to close connection.
        
        Args:
            reason: Optional reason for ending
            
        Returns:
            Dict with success flag and close_connection signal
        """
        logger.info(f"End conversation requested. Reason: {reason or 'None provided'}")
        
        return {
            "success": True,
            "action": "close_connection",
            "message": "Goodbye! Thank you for using our appointment scheduling service. Have a great day! 👋",
            "reason": reason
        }


# Global instance
_tool_executor = ToolExecutor()


def get_tool_executor() -> ToolExecutor:
    """Get the global tool executor instance."""
    return _tool_executor

