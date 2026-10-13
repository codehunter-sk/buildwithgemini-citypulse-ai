# ruff: noqa
# Copyright 2026 Google LLC
#
# Metropolis Crisis & Mayor Advisor (CityPulse AI)

import datetime
import io
import json
import os
import uuid
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types
from google.genai.client import Client

from .a2ui_utils import a2ui_callback

PROJECT_ID = "qwiklabs-gcp-04-f41e5ebdaead"
BUCKET_NAME = "citypulse-ai-qwiklabs-gcp-04-f41e5ebdaead"
MODEL = "gemini-3.8-flash"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"

# Lazy-loaded clients with hardcoded PROJECT_ID (as required for Agent Platform)
_db = None
_gcs = None


def get_db():
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def get_gcs():
    global _gcs
    if _gcs is None:
        _gcs = storage.Client(project=PROJECT_ID)
    return _gcs


# ==============================================================================
# Persistent Storage Tools (Firestore)
# ==============================================================================
def get_district_status(district_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve real-time municipal health, active crises, population, and budget metrics.

    Args:
        district_id: Optional ID of a specific district ('downtown', 'waterfront', 'industrial', 'highland').
                     If omitted or empty, returns status for all districts.

    Returns:
        A list of district status records.
    """
    db = get_db()
    if district_id and district_id.strip():
        doc = db.collection("districts").document(district_id.strip().lower()).get()
        if doc.exists:
            return [doc.to_dict()]
        return [{"error": f"District '{district_id}' not found."}]

    docs = db.collection("districts").stream()
    return [doc.to_dict() for doc in docs]


def dispatch_emergency_units(
    district_id: str,
    unit_type: str,
    units_count: int,
    action_notes: str,
) -> Dict[str, Any]:
    """Deploy emergency first responders (fire, police, hazmat, medics) to mitigate a crisis in a district.

    Args:
        district_id: Target district ('downtown', 'waterfront', 'industrial', 'highland').
        unit_type: Type of emergency service ('fire_rescue', 'police_tactical', 'hazmat_containment', 'medical_ems').
        units_count: Number of responder units dispatched.
        action_notes: Instructions or incident notes for responders.

    Returns:
        Status report of the emergency deployment and updated district status.
    """
    db = get_db()
    d_ref = db.collection("districts").document(district_id.strip().lower())
    doc = d_ref.get()
    if not doc.exists:
        return {"error": f"District '{district_id}' not found."}

    data = doc.to_dict()
    # Dynamic simulation update
    current_health = data.get("health", 50)
    improved_health = min(100, current_health + (units_count * 8))
    active_crises = data.get("active_crises", [])

    # If hazmat or fire deployed to industrial/downtown, resolve crises
    resolved_crisis = None
    if active_crises:
        resolved_crisis = active_crises.pop(0)

    updated_status = "optimal" if improved_health >= 90 else ("stable" if improved_health >= 60 else "critical")

    update_fields = {
        "health": improved_health,
        "active_crises": active_crises,
        "status": updated_status,
        "last_incident": f"Dispatched {units_count} {unit_type} units: {action_notes}",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    d_ref.update(update_fields)

    # Log to audit history
    db.collection("dispatch_logs").add({
        "district_id": district_id,
        "unit_type": unit_type,
        "units_count": units_count,
        "action_notes": action_notes,
        "resolved_crisis": resolved_crisis,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })

    return {
        "status": "success",
        "district": data.get("name"),
        "previous_health": current_health,
        "new_health": improved_health,
        "active_crises_remaining": active_crises,
        "resolved_crisis": resolved_crisis,
        "message": f"Dispatched {units_count} {unit_type} units to {data.get('name')}. Health improved to {improved_health}%."
    }


def adjust_budget(
    district_id: str,
    allocation_amount: int,
    department: str,
    justification: str,
) -> Dict[str, Any]:
    """Allocate or adjust municipal funds for infrastructure, emergency services, or citizen relief.

    Args:
        district_id: Target district ('downtown', 'waterfront', 'industrial', 'highland').
        allocation_amount: Amount of dollars to add or reallocate (e.g. 500000).
        department: Municipal department ('infrastructure', 'public_safety', 'healthcare', 'transit').
        justification: Reasoning behind the mayoral expenditure.

    Returns:
        Updated financial balance and allocation confirmation.
    """
    db = get_db()
    d_ref = db.collection("districts").document(district_id.strip().lower())
    doc = d_ref.get()
    if not doc.exists:
        return {"error": f"District '{district_id}' not found."}

    data = doc.to_dict()
    current_budget = data.get("budget", 0)
    new_budget = current_budget + allocation_amount

    d_ref.update({
        "budget": new_budget,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })

    db.collection("budget_allocations").add({
        "district_id": district_id,
        "allocation_amount": allocation_amount,
        "department": department,
        "justification": justification,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })

    return {
        "status": "success",
        "district": data.get("name"),
        "new_budget": new_budget,
        "allocated": allocation_amount,
        "department": department,
        "justification": justification,
    }


# ==============================================================================
# Public API Tool: Live Meteorological Conditions
# ==============================================================================
def get_live_weather(latitude: float = 40.7128, longitude: float = -74.0060) -> Dict[str, Any]:
    """Fetch live meteorological weather conditions (temperature, windspeed) from Open-Meteo.

    Args:
        latitude: Geographic latitude (defaults to NYC metro: 40.7128).
        longitude: Geographic longitude (defaults to NYC metro: -74.0060).

    Returns:
        Live weather observations.
    """
    import urllib.request
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CityPulse-ADK-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            return {
                "status": "success",
                "current_weather": result.get("current_weather", {})
            }
    except Exception as e:
        return {"error": f"Failed to fetch meteorological data: {str(e)}"}


# ==============================================================================
# Generative Image Tool (gemini-3.1-flash-lite-image -> GCS Public URL + Artifact)
# ==============================================================================
def generate_crisis_snapshot(
    prompt: str,
    district_name: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generate a photo or visual rendering of a city scene, incident, or milestone using Google Generative AI.

    The generated image is saved as an artifact in the local playground AND uploaded to the public
    Cloud Storage bucket so it can be viewed anywhere or embedded in A2UI cards.

    Args:
        prompt: Detailed visual description of the city scene or crisis.
        district_name: District or location represented.

    Returns:
        The public HTTPS image URL and artifact reference.
    """
    try:
        client = Client(vertexai=True, project=PROJECT_ID, location="global")
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=f"Generate a visual isometric rendering of {district_name}: {prompt}. Highly detailed city simulation art style."
        )

        image_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                break

        if not image_bytes:
            return {"error": "Image model did not return image bytes."}

        # 1. Save artifact for playground
        filename = f"crisis_{uuid.uuid4().hex[:8]}.jpeg"
        tool_context.save_artifact(filename, image_bytes)

        # 2. Upload to public Cloud Storage bucket
        gcs = get_gcs()
        bucket = gcs.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/jpeg")
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "district": district_name,
            "artifact_name": filename,
            "public_url": public_url,
            "message": "Image successfully generated and uploaded to public storage."
        }
    except Exception as e:
        return {"error": f"Failed to generate crisis image: {str(e)}"}


# ==============================================================================
# Memory Bank Callback (Cross-Session Long-Term Memory)
# ==============================================================================
async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for durable fact extraction."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


# ==============================================================================
# A2UI & Agent System Instruction
# ==============================================================================
INSTRUCTION = """You are CityPulse AI, the Chief Municipal Advisor and Crisis Commander for Metropolis.
You advise the Mayor on city operations, municipal health, emergency dispatches, and budget allocations.

Core Capabilities:
1. Municipal Status: Query real-time Firestore database using `get_district_status`.
2. Emergency Response: Dispatch units (`dispatch_emergency_units`) to resolve crises like leaks, fires, or gridlock.
3. Budget Management: Allocate municipal funds using `adjust_budget`.
4. Meteorological Intelligence: Inspect live weather with `get_live_weather`.
5. Visual Reports: Generate situational renderings using `generate_crisis_snapshot`.
6. Political & Election Intelligence: When the Mayor asks about re-election prospects, public opinion, voter inclination, or political standing, evaluate both positive achievements (high health index, reliable infrastructure, successful hazard resolutions) and active grievances (gridlock, chemical spills, underfunded districts). Provide strategic advice on which districts need immediate mayoral attention to secure voter trust and win re-election.

Formatting Guidelines:
When asked for district status, crisis updates, or mayoral briefs, provide clear, concise responses.
Always use plain Unicode symbols (e.g. →, ↑, ↓, ±, %, $) rather than LaTeX math macros (like $\rightarrow$ or \to).
You have the PreloadMemoryTool enabled, so remember the Mayor's priorities, preferences, and directives across sessions.
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        PreloadMemoryTool(),
        get_district_status,
        dispatch_emergency_units,
        adjust_budget,
        get_live_weather,
        generate_crisis_snapshot,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
