"""
Module 3: AI Validator - With automatic retry for rate limits
"""

from google import genai
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None

MODEL = "gemini-2.0-flash"

def run_ai_validation(geometry: dict, rule_violations: list) -> dict:
    if not client:
        return _fallback_response("No API key")
    
    prompt = f"""Analyze this CAD part. Return ONLY JSON:

Dimensions: {geometry.get('length_mm', 0)}x{geometry.get('width_mm', 0)}x{geometry.get('height_mm', 0)}mm
Wall: {geometry.get('min_wall_thickness_mm', 0)}mm
Watertight: {geometry.get('is_watertight', False)}
Holes: {geometry.get('hole_count', 0)}

Return: {{"part_type": "type", "part_type_confidence": "HIGH", "part_type_reasoning": "...", "ai_violations": [], "design_summary": "...", "manufacturability_score": "ACCEPTABLE", "score_deduction": 0}}"""

    return _call_with_retry(prompt)

def answer_question(question: str, context: dict) -> str:
    if not client:
        return "API not configured"
    
    geometry = context.get('geometry', {})
    prompt = f"""You are a CAD expert. Answer this question about a 3D model:

Model: {geometry.get('length_mm', '?')}mm, Watertight: {geometry.get('is_watertight', False)}
Question: {question}

Give CAD-specific advice about mesh repair using software like FreeCAD, Blender, or MeshLab. Answer briefly (2-3 sentences):"""
    
    return _call_with_retry(prompt, is_json=False)

def _call_with_retry(prompt: str, is_json: bool = True, max_retries: int = 3):
    """Call API with automatic retry on rate limits"""
    
    for attempt in range(max_retries):
        try:
            print(f"[AI] Attempt {attempt + 1}/{max_retries}...")
            response = client.models.generate_content(model=MODEL, contents=prompt)
            
            if is_json:
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()
                return json.loads(raw)
            else:
                return response.text.strip()
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s
                print(f"[AI] Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"[AI] Error: {e}")
                if is_json:
                    return _fallback_response(str(e))
                return f"Error: {str(e)}"
    
    if is_json:
        return _fallback_response("Rate limit exceeded. Please try again in a minute.")
    return "Rate limit exceeded. Please wait a minute and try again."

def _fallback_response(error: str) -> dict:
    return {
        "part_type": "Mechanical Component",
        "part_type_confidence": "MEDIUM",
        "part_type_reasoning": f"Rate limited: {error}",
        "ai_violations": [],
        "design_summary": "AI temporarily rate limited. Please try again in a minute.",
        "manufacturability_score": "ACCEPTABLE",
        "score_deduction": 0
    }