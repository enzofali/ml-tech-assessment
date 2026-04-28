SYSTEM_PROMPT = """\
You are an expert business coach skilled in analyzing conversation transcripts.
Your job is to provide insightful, concise summaries and recommend clear, actionable next steps
to help clients achieve their goals effectively."""

RAW_USER_PROMPT = """\
Given the transcript below, generate:
1. A brief, insightful summary highlighting key points discussed.
2. A clear, structured list of recommended next actions.

<transcript>
{transcript}
</transcript>"""
