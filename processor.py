# processor.py

import os
import json
from typing import Optional, List
from google import genai
from pydantic import BaseModel, ValidationError


## ---------------- Pydantic Schemas ---------------- ##
class PartyDetails(BaseModel):
    shipowner_name: Optional[str]
    charterer_name: Optional[str]
    port_agent_name: Optional[str]
    confidence: Optional[float]


class CargoDetails(BaseModel):
    operation_type: Optional[str]
    cargo_type: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    confidence: Optional[float]


class Signatory(BaseModel):
    role: Optional[str]
    name: Optional[str]
    date_signed: Optional[str]


class DocumentDetails(BaseModel):
    document_source: Optional[str]
    date_of_document: Optional[str]
    port_name: Optional[str]
    vessel_name: Optional[str]
    voyage_number: Optional[str]
    parties: Optional[PartyDetails]
    cargo: Optional[CargoDetails]
    confidence: Optional[float]


class Event(BaseModel):
    event_id: Optional[int]
    event_type: Optional[str]
    start_date: Optional[str]
    start_time: Optional[str]
    end_date: Optional[str]
    end_time: Optional[str]
    duration_hours: Optional[float]
    weather_conditions: Optional[str]
    remarks: Optional[str]
    confidence: Optional[float]


class LaytimeNotes(BaseModel):
    free_time_periods_identified: Optional[str]
    suspension_periods_identified: Optional[str]
    remarks_on_interruptions_or_delays: Optional[str]
    confidence: Optional[float]


class SoFSchema(BaseModel):
    """The overall schema for a Statement of Facts document."""
    document_details: DocumentDetails
    events: List[Event]
    laytime_notes: LaytimeNotes
    approvals: Optional[List[Signatory]]


## ---------------- Extraction Function ---------------- ##
def get_structured_data(sof_text: str) -> dict:
    """
    Takes raw text and returns structured JSON using Gemini 2.5 Flash's JSON Mode.
    Requires GOOGLE_API_KEY to be set in environment variables.
    """

    # Debug check: make sure text isn’t empty
    print(f"\n[DEBUG] Extracted text length: {len(sof_text)} characters")
    print("[DEBUG] Text preview >>>")
    print(sof_text[:500], "...\n")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=api_key)

        # Define generation configuration
        config = {
            "response_mime_type": "application/json",
            "response_schema": SoFSchema,
            "temperature": 0.0,
        }

        # Improved Prompt
        prompt = f"""
        You are given a Statement of Facts (SOF) document.
        Extract its details into the provided schema (SoFSchema).

        IMPORTANT:
        - Do not leave fields null if the information is explicitly in the text.
        - If start and end times are present, calculate duration_hours.
        - Capture weather remarks, delays, tug usage, approvals, and laytime notes.
        - Only use null if information is truly missing.

        --- DOCUMENT TEXT ---
        {sof_text}
        --- END DOCUMENT ---
        """

        # Generate content
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )

        # Debug: print raw Gemini output before parsing
        print("[DEBUG] Gemini raw output >>>")
        print(response.text, "\n")

        try:
            # Try schema-validated parsing
            parsed: SoFSchema = response.parsed
            return parsed.model_dump()

        except ValidationError as ve:
            # If schema validation fails, fall back to raw JSON
            print("[WARNING] Schema validation failed. Falling back to raw JSON.")
            return json.loads(response.text)

    except Exception as e:
        raw_output = getattr(locals().get("response", None), "text", "No response text available.")
        raise ValueError(
            f"AI data extraction failed. Reason: {e}\n\nRaw Model Output:\n{raw_output}"
        ) from e
