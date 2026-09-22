import os
import json
import re
import traceback
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import types

# Explicit .env resolution: load from backend directory as well as repository root
backend_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=backend_env_path)
root_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=root_env_path)
load_dotenv()  # Fallback to current working directory

# Verified default active model
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[AI ENGINE] GEMINI_API_KEY is missing or empty in environment.")
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY missing or invalid")
    try:
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        print(f"[AI ENGINE] Error initializing genai.Client: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Gemini client initialization error: {type(e).__name__}: {str(e)}",
        )


SYSTEM_PROMPT = """You are an expert consumer protection analyst specializing in identifying dark patterns—deceptive UI/UX design techniques used by websites to trick consumers into unwanted purchases or subscriptions.

Analyze the provided website content or screenshot and identify specific deceptive patterns.

TAXONOMY TO CHECK:
1. hidden_fee - Unexpected charges added late in the checkout or onboarding process.
2. hidden_recurring_fee - A subscription or recurring charge that is visually de-emphasized or hidden.
3. subscription_trap - Making it easy to sign up but extremely hard or confusing to cancel, or locking users into recurring payments.
4. preselection - Opt-in checkboxes ticked by default for add-ons, tips, or subscriptions.
5. sneak_into_basket - Additional items or services added to cart automatically without explicit request.
6. misleading_pricing - Showing a deceptively low headline price while concealing mandatory fees.
7. forced_continuity - Free or discounted trials that silently auto-renew into full-price paid plans.
8. difficult_cancellation - Forcing users to call phone numbers or navigate convoluted menus to cancel.
9. fake_urgency - Fabricated countdown timers or artificial time limits.
10. fake_scarcity - Fabricated 'only 1 left' or artificial inventory pressure messages.
11. confirmshaming - Emotional manipulation or guilt-trip language for declining an offer.
12. disguised_advertising - Sponsored advertisements formatted to mimic organic interface elements.

CRITICAL INSTRUCTION FOR FINANCIAL IMPACT & FREE TRIALS:
- If the page advertises a 'Free Trial', '₹0 today', '$0 due now', or 'First month free', you MUST actively search the small print, footnotes, or fine print for the future recurring charge that will hit the user's card after the trial ends (e.g., '₹1,400/month thereafter', '$29.99/mo after 14 days').
- If a future automatic charge exists (Forced Continuity / Subscription Trap), you MUST set financial_impact.has_hidden_fee to true, is_recurring to true, and set estimated_amount to the FUTURE billed amount (not the ₹0 trial amount).
- Check for real monetary costs (e.g., "$9.99", "₹499", "€15", "₹1400").
- Identify whether the charge is recurring (subscriptions, memberships, auto-renewals, post-trial continuity).
- Determine billing frequency (e.g., "monthly", "yearly", "weekly", "quarterly").
- Set has_hidden_fee to true if extra or recurring fees are disguised, delayed, or unexpected, including delayed post-trial charges.

Return ONLY this JSON structure:
{
  "overall_risk_score": 85,
  "risk_level": "high",
  "patterns": [
    {
      "type": "forced_continuity",
      "severity": "high",
      "confidence": 0.95,
      "evidence": "Exact text or visual description observed (e.g. 'Free trial today; auto-renews at ₹1,400/month after 30 days')",
      "explanation": "Why this misleads the consumer and the recurring financial charge after trial expiration",
      "financial_impact": {
        "has_hidden_fee": true,
        "estimated_amount": "₹1400",
        "is_recurring": true,
        "frequency": "monthly"
      }
    }
  ]
}

Score guide: 80-100=high, 40-79=medium, 0-39=low risk.
MANDATORY SCORING RULE: If you detect ANY hidden_fee, hidden_recurring_fee, subscription_trap, or forced_continuity, OR if you set has_hidden_fee: true, the overall_risk_score MUST be 80 or higher, and the risk_level MUST be 'high'. Do not give low risk scores to pages with subscription traps.
"""


async def analyze_with_gemini(page_content: str, url: str) -> Dict[str, Any]:
    client = get_gemini_client()
    content = page_content[:15000] if len(page_content) > 15000 else page_content
    prompt = f"URL: {url}\n\nCONTENT:\n{content}"

    return await _call_gemini(client, prompt)


async def analyze_screenshot_with_gemini(image_path: str) -> Dict[str, Any]:
    client = get_gemini_client()

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = Path(image_path).suffix.lower().lstrip(".")
        if ext in ["jpg", "jpeg"]:
            mime_type = "image/jpeg"
        elif ext == "png":
            mime_type = "image/png"
        elif ext == "webp":
            mime_type = "image/webp"
        else:
            mime_type = f"image/{ext}"

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    except Exception as e:
        print(
            f"[AI ENGINE] Error reading image '{image_path}': {type(e).__name__}: {e}"
        )
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=f"Error reading image file: {type(e).__name__}: {str(e)}",
        )

    return await _call_gemini(
        client, [image_part, "Analyze this screenshot for dark patterns."]
    )


async def _call_gemini(client: genai.Client, contents) -> Dict[str, Any]:
    model_name = DEFAULT_MODEL
    print(f"\n{'='*30} [AI ENGINE GEMINI REQUEST] {'='*30}")
    print(f"[AI ENGINE] Target Model: '{model_name}' (SDK: google-genai)")

    if isinstance(contents, list):
        payload_repr = []
        for item in contents:
            if hasattr(item, "inline_data") and item.inline_data:
                payload_repr.append(
                    f"<Part mime_type={item.inline_data.mime_type} bytes={len(item.inline_data.data or b'')}>"
                )
            elif hasattr(item, "size"):
                payload_repr.append(f"<PIL.Image size={item.size} mode={item.mode}>")
            else:
                payload_repr.append(str(item))
        print(f"[AI ENGINE] Request Payload: {payload_repr}")
    else:
        preview = (
            contents
            if len(contents) <= 2000
            else f"{contents[:2000]}... [truncated total {len(contents)} chars]"
        )
        print(f"[AI ENGINE] Request Payload ({len(contents)} chars):\n{preview}")
    print(f"{'='*80}\n")

    try:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        print(
            f"[AI ENGINE] Response status: SUCCESS (200 OK from model '{model_name}')"
        )
        response_text = response.text.strip() if response.text else ""
        print(f"[AI ENGINE] Response Text preview: {response_text[:300]}...\n")

        result = json.loads(response_text)

        # Ensure basic fields
        result.setdefault("overall_risk_score", 0)
        result.setdefault("risk_level", "low")
        result.setdefault("patterns", [])

        for p in result.get("patterns", []):
            fi = p.get("financial_impact")
            if not isinstance(fi, dict):
                p["financial_impact"] = {
                    "has_hidden_fee": False,
                    "estimated_amount": None,
                    "is_recurring": False,
                    "frequency": None,
                }
            else:
                fi.setdefault("has_hidden_fee", False)
                fi.setdefault("estimated_amount", None)
                fi.setdefault("is_recurring", False)
                fi.setdefault("frequency", None)

        # Enforce high-risk scoring guardrail if hidden fee or subscription trap is detected
        has_fee_or_trap = any(
            p.get("financial_impact", {}).get("has_hidden_fee", False)
            or p.get("type")
            in [
                "hidden_fee",
                "hidden_recurring_fee",
                "subscription_trap",
                "forced_continuity",
            ]
            for p in result.get("patterns", [])
        )
        if has_fee_or_trap:
            result["overall_risk_score"] = max(
                80, int(result.get("overall_risk_score", 0))
            )
            result["risk_level"] = "high"

        return result
    except Exception as e:
        print(
            f"[AI ENGINE] Response status: FAILED (Exception raised for model '{model_name}')"
        )
        print(
            f"[AI ENGINE] Exact error in client.models.generate_content(): {type(e).__name__}: {e}"
        )
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API error ({model_name}): {type(e).__name__} - {str(e)}",
        )


def _mock_analysis(source: str) -> Dict[str, Any]:
    """Retained for offline testing/reference only. Never returned as a quiet fallback."""
    return {
        "overall_risk_score": 85,
        "risk_level": "high",
        "patterns": [
            {
                "type": "hidden_recurring_fee",
                "severity": "high",
                "confidence": 0.95,
                "evidence": "DEMO DATA: Checkout highlights ₹99 trial price; footnote specifies ₹499/month recurring charge.",
                "explanation": "Consumers are automatically enrolled into a paid monthly subscription without clear prominent disclosure.",
                "financial_impact": {
                    "has_hidden_fee": True,
                    "estimated_amount": "₹499",
                    "is_recurring": True,
                    "frequency": "monthly",
                },
            }
        ],
    }
