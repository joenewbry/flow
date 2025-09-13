import json
import requests
from typing import Optional, Dict, Any
from langflow import CustomComponent
from langflow.field_typing import Data
from pydantic import Field


class MCPSummaryComponent(CustomComponent):
    """
    Custom Langflow component that integrates with the MCP Summary Server
    to provide screen activity summaries.
    """
    
    display_name: str = "MCP Summary Tool"
    description: str = "Get screen activity summaries from the MCP server"
    
    # Component configuration
    mcp_server_url: str = Field(
        default="http://localhost:3000",  # Adjust this to your MCP server's HTTP endpoint
        description="URL of the MCP server HTTP endpoint"
    )
    
    # Tool selection
    tool_name: str = Field(
        default="get_daily_summary",
        description="MCP tool to use",
        options=[
            "get_daily_summary",
            "get_time_range_summary", 
            "get_last_hours_summary",
            "get_hourly_summary"
        ]
    )
    
    # Input fields based on tool
    date: Optional[str] = Field(
        default=None,
        description="Date in YYYY-MM-DD format (for daily summary)"
    )
    
    start_time: Optional[str] = Field(
        default=None,
        description="Start time in ISO 8601 format (for time range summary)"
    )
    
    end_time: Optional[str] = Field(
        default=None,
        description="End time in ISO 8601 format (for time range summary)"
    )
    
    hours: Optional[int] = Field(
        default=8,
        description="Number of hours to look back (for last hours summary)"
    )
    
    hour: Optional[str] = Field(
        default=None,
        description="Hour in YYYY-MM-DD-HH format (for hourly summary)"
    )
    
    def build_config(self):
        return {
            "mcp_server_url": {"display_name": "MCP Server URL"},
            "tool_name": {"display_name": "Tool Name"},
            "date": {"display_name": "Date"},
            "start_time": {"display_name": "Start Time"},
            "end_time": {"display_name": "End Time"},
            "hours": {"display_name": "Hours"},
            "hour": {"display_name": "Hour"}
        }
    
    def build(self) -> Data:
        """Execute the MCP tool and return results"""
        
        # Prepare the request payload based on the selected tool
        payload = self._prepare_payload()
        
        try:
            # Make request to MCP server
            response = requests.post(
                f"{self.mcp_server_url}/tools/{self.tool_name}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return Data(
                    value=result,
                    metadata={
                        "tool_name": self.tool_name,
                        "mcp_server": self.mcp_server_url,
                        "status": "success"
                    }
                )
            else:
                error_msg = f"MCP server error: {response.status_code} - {response.text}"
                return Data(
                    value={"error": error_msg},
                    metadata={
                        "tool_name": self.tool_name,
                        "mcp_server": self.mcp_server_url,
                        "status": "error"
                    }
                )
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to connect to MCP server: {str(e)}"
            return Data(
                value={"error": error_msg},
                metadata={
                    "tool_name": self.tool_name,
                    "mcp_server": self.mcp_server_url,
                    "status": "error"
                }
            )
    
    def _prepare_payload(self) -> Dict[str, Any]:
        """Prepare the payload based on the selected tool"""
        
        if self.tool_name == "get_daily_summary":
            return {"date": self.date} if self.date else {}
            
        elif self.tool_name == "get_time_range_summary":
            if not self.start_time or not self.end_time:
                raise ValueError("start_time and end_time are required for time range summary")
            return {
                "startTime": self.start_time,
                "endTime": self.end_time
            }
            
        elif self.tool_name == "get_last_hours_summary":
            return {"hours": self.hours}
            
        elif self.tool_name == "get_hourly_summary":
            if not self.hour:
                raise ValueError("hour is required for hourly summary")
            return {"hour": self.hour}
            
        else:
            raise ValueError(f"Unknown tool: {self.tool_name}")


# Register the component
if __name__ == "__main__":
    # This allows the component to be imported by Langflow
    pass 