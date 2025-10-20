# Schedule Analysis Tools - Documentation

## Overview

Added two new tools to the FaultCast Maintenance Agent to track and analyze scheduled maintenance tasks stored in the `maintenance-schedules/` S3 directory.

## New Tools

### 1. `count_scheduled_tasks`

Counts and analyzes maintenance tasks from S3, providing statistics and summaries.

**Parameters:**
- `machine_id` (optional): Filter by specific machine ID
- `severity_filter` (optional): Filter by severity level (critical, warning, caution, normal)

**Returns:**
```json
{
  "total_tasks": 15,
  "filters_applied": {
    "machine_id": "none",
    "severity": "none"
  },
  "summary": {
    "by_severity": {
      "critical": 3,
      "warning": 5,
      "caution": 4,
      "normal": 3
    },
    "by_machine": {
      "conveyor-A001": 5,
      "conveyor-B002": 10
    },
    "by_fault_type": {
      "ball bearing": 6,
      "pulley": 4,
      "belt slippage": 5
    },
    "total_estimated_cost_usd": 12500.50
  },
  "tasks": [
    {
      "schedule_id": "WS-conveyor-A001-20251020120000",
      "machine_id": "conveyor-A001",
      "fault_type": "ball bearing",
      "severity": "critical",
      "priority": "immediate",
      "action_required_by": "2025-10-21T12:00:00Z",
      "estimated_cost_usd": 1350.00,
      "created_at": "2025-10-20T12:00:00Z"
    }
  ],
  "timestamp": "2025-10-20T15:30:00Z"
}
```

**Features:**
- Reads all JSON files from S3 maintenance-schedules directory
- Aggregates statistics by severity, machine, and fault type
- Calculates total estimated costs
- Returns top 10 most urgent tasks (sorted by severity)
- Supports filtering by machine ID or severity level

**Example Usage:**
```python
# Count all tasks
result = count_scheduled_tasks()

# Count only critical tasks
result = count_scheduled_tasks(severity_filter="critical")

# Count tasks for specific machine
result = count_scheduled_tasks(machine_id="conveyor-A001")
```

### 2. `get_schedule_insights`

Queries the Knowledge Base for insights about scheduled maintenance tasks.

**Parameters:**
- `query` (optional): Question about scheduled tasks

**Returns:**
```json
{
  "query": "maintenance schedule critical tasks",
  "insights_found": 3,
  "insights": [
    {
      "content": "Schedule data showing critical maintenance...",
      "relevance_score": 0.85,
      "source": "s3://bucket/maintenance-schedules/..."
    }
  ],
  "timestamp": "2025-10-20T15:30:00Z"
}
```

**Features:**
- Leverages the Knowledge Base data source for maintenance-schedules
- Provides semantic search over scheduled tasks
- Returns relevant schedule information with relevance scores
- Useful for answering questions about patterns and trends

**Example Usage:**
```python
# Get general insights
result = get_schedule_insights()

# Ask specific questions
result = get_schedule_insights(query="What are the most common fault types?")
result = get_schedule_insights(query="Which machines need urgent attention?")
```

## Agent Integration

The tools are integrated into the FaultCast agent and can be invoked through natural language:

**Example Queries:**
- "How many maintenance tasks are scheduled?"
- "Show me all critical maintenance tasks"
- "What machines have scheduled maintenance?"
- "What's the total estimated cost of scheduled maintenance?"
- "Which fault types are most common in scheduled tasks?"
- "Give me insights about scheduled maintenance patterns"

## System Prompt Updates

The agent's system prompt has been updated to include:
- Tracking and analyzing scheduled maintenance tasks
- Two new tools in the capabilities list
- Guidance on when to use each tool

## Testing

Run the test suite to verify the tools work correctly:

```bash
cd agent
source ../venv/bin/activate
python test_schedule_tools.py
```

## Requirements

- AWS credentials configured (for S3 access)
- `WORK_SCHEDULE_BUCKET` environment variable set
- `WORK_SCHEDULE_PREFIX` environment variable set (default: `maintenance-schedules/`)
- Knowledge Base configured with maintenance-schedules as a data source
- `KNOWLEDGE_BASE_ID` environment variable set

## Use Cases

1. **Dashboard Statistics**: Get real-time counts and summaries for maintenance dashboards
2. **Priority Management**: Filter and view critical tasks requiring immediate attention
3. **Cost Analysis**: Track total estimated costs across all scheduled maintenance
4. **Machine Health**: See which machines have the most scheduled maintenance
5. **Trend Analysis**: Use KB insights to identify patterns in maintenance needs
6. **Resource Planning**: Understand workload distribution across machines and fault types

## Implementation Details

### count_scheduled_tasks
- Directly reads from S3 using boto3
- Parses JSON schedule files
- Aggregates statistics in-memory
- Returns structured data for programmatic use

### get_schedule_insights
- Uses Bedrock Knowledge Base Retrieve API
- Semantic search over schedule documents
- Returns natural language insights
- Better for answering "why" and "what if" questions

## Error Handling

Both tools include comprehensive error handling:
- Returns error messages if S3/KB not configured
- Gracefully handles missing or malformed schedule files
- Provides helpful error messages for troubleshooting

## Future Enhancements

Potential improvements:
- Add time-based filtering (tasks due in next 24h, week, etc.)
- Support for pagination of large result sets
- Export capabilities (CSV, PDF reports)
- Integration with notification systems
- Predictive analytics on maintenance patterns
