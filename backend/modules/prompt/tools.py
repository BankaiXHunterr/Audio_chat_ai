# ...existing code...
dirization_tool = {
            "name": "store_call_parameters",
            "description": "Convert a time-stamped meeting transcript into a diarized, structured transcript array with speaker identification, summary, key highlights, and action items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transcript": {
                        "type": "array",
                        "description": "Array of transcript segments, each with speaker name, timestamp (HH:MM:SS), and spoken text. Segments should be split if multiple speakers are present.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "speaker": {
                                    "type": "string",
                                    "description": "Name of the speaker (from attendee list) or 'Unknown' if not identifiable.",
                                },
                                "timestamp": {
                                    "type": "string",
                                    "description": "Start time of the segment in HH:MM:SS format.",
                                },
                                "text": {
                                    "type": "string",
                                    "description": "Spoken text for this segment.",
                                },
                            },
                            "required": ["speaker", "timestamp", "text"],
                        },
                    },
                    "summary": {
                        "type": "string",
                        "description": "Concise summary of the main topics discussed in the audio.",
                    },
                    "keyHighlights": {
                        "type": "array",
                        "description": "List of key discussion points or highlights from the meeting.",
                        "items": {
                            "type": "string",
                            "description": "A single key point or highlight.",
                        },
                    },
                    "actionItems": {
                        "type": "array",
                        "description": "List of actionable tasks discussed in the meeting, with assignee, deadline, and status if available.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string",
                                    "description": "Description of the action item or task.",
                                },
                                "assignee": {
                                    "type": "string",
                                    "description": "Name of the person responsible for the task.",
                                },
                                "deadline": {
                                    "type": "string",
                                    "description": "Deadline for the task (if mentioned), otherwise empty string.",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Current status of the task (e.g., 'pending', 'completed', etc.), or empty string if not specified.",
                                },
                            },
                            "required": ["task", "assignee", "deadline", "status"],
                        },
                    },
                },
                "required": ["transcript", "keyHighlights", "actionItems", "summary"],
            },
        }
# ...existing code...