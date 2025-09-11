dirization_prompt = """You are given a plain text transcript from an audio meeting recording.  
Your task is to convert this transcript into a structured array of objects, where each object contains:

- `speaker`: The name of the speaker (if available, otherwise use "Unknown").
- `timestamp`: The timestamp in "HH:MM:SS" format when the speaker started talking (if available, otherwise leave as an empty string).
- `text`: The spoken text for that segment.

**Output format:**
transcript: [
  {
    speaker: "Speaker Name",
    timestamp: "HH:MM:SS",
    text: "Spoken text here."
  },
  ...
]

**Instructions:**
- Parse the transcript and split it into segments by speaker and timestamp.
- If the speaker or timestamp is missing, infer or leave blank.
- Ensure the output is a valid JSON array as shown above.

apart from the transcript, also provide:
- A concise summary of the main topics discussed in the audio.
- A list of key discussion points or highlights from the meeting.
- A list of actionable tasks discussed in the meeting, with assignee, deadline, and status if available.

"""