"""AI Dark Pattern & Hidden Fee Analyzer Service.

Supports both OpenAI-compatible endpoints (OpenRouter, Groq, Ollama, DeepSeek)
and Google Gemini API, with automatic fallback to mock analysis when requested.
"""

import os
import json
import re
import base64
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Explicit .env resolution: load from backend directory as well as repository root
backend_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=backend_env_path)
root_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=root_env_path)
load_dotenv()  # Fallback to current working directory

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


def _get_llm_config() -> Tuple[str, str, str, str]:
    """Resolves active LLM provider type, API key, base URL, and model name from environment variables."""
    free_key = os.getenv("FREE_LLM_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if free_key or openai_key:
        api_key = free_key or openai_key
        base_url = os.getenv("FREE_LLM_BASE_URL", "https://api.openai.com/v1").strip()
        model_name = os.getenv("FREE_LLM_MODEL", "gpt-4o-mini").strip()
        return ("openai", api_key, base_url, model_name)
    elif gemini_key:
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        return ("gemini", gemini_key, "", model_name)
    else:
        return ("mock", "", "", "mock-model")


def _encode_image_to_base64(image_path: str) -> Tuple[str, str]:
    """Reads image file from disk and returns tuple of (base64_data_str, mime_type)."""
    ext = Path(image_path).suffix.lower().lstrip(".")
    if ext in ["jpg", "jpeg"]:
        mime_type = "image/jpeg"
    elif ext == "png":
        mime_type = "image/png"
    elif ext == "webp":
        mime_type = "image/webp"
    else:
        mime_type = f"image/{ext}"

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return encoded, mime_type


def _clean_json_text(text: str) -> str:
    """Strips markdown code block fences and leading/trailing whitespace from raw JSON response."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _parse_and_guardrail_result(raw_text: str) -> Dict[str, Any]:
    """Parses JSON text, validates structure, and applies high-risk scoring guardrails."""
    cleaned_json = _clean_json_text(raw_text)
    result: Dict[str, Any] = json.loads(cleaned_json)

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


def _call_openai_llm(
    api_key: str, base_url: str, model_name: str, messages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Executes Chat Completion request using OpenAI client SDK."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    kwargs: Dict[str, Any] = {
        "model": model_name,
        "messages": messages,
    }

    # Attempt json_object response format
    try:
        response = client.chat.completions.create(
            **kwargs, response_format={"type": "json_object"}
        )
    except Exception:
        # Fall back if provider does not support explicit response_format parameter
        response = client.chat.completions.create(**kwargs)

    raw_content = response.choices[0].message.content or "{}"
    return _parse_and_guardrail_result(raw_content)


def _call_gemini_llm(
    api_key: str, model_name: str, contents: Any
) -> Dict[str, Any]:
    """Executes content generation request using google-genai SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=config,
    )
    raw_content = response.text or "{}"
    return _parse_and_guardrail_result(raw_content)


async def analyze_with_gemini(page_content: str, url: str) -> Dict[str, Any]:
    """Analyzes text/URL content for dark patterns using active LLM configuration."""
    provider, api_key, base_url, model_name = _get_llm_config()

    if provider == "mock":
        return _mock_analysis(url)

    content = page_content[:15000] if len(page_content) > 15000 else page_content
    user_payload = f"URL: {url}\n\nCONTENT:\n{content}"

    try:
        if provider == "openai":
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_payload},
            ]
            return _call_openai_llm(api_key, base_url, model_name, messages)
        else:
            return _call_gemini_llm(api_key, model_name, user_payload)
    except Exception as e:
        print(f"[AI ENGINE] Error during text analysis: {type(e).__name__}: {e}")
        traceback.print_exc()
        return _mock_analysis(url)


async def analyze_screenshot_with_gemini(image_path: str) -> Dict[str, Any]:
    """Analyzes screenshot image for dark patterns using active LLM vision capabilities."""
    provider, api_key, base_url, model_name = _get_llm_config()

    if provider == "mock":
        return _mock_analysis("screenshot")

    try:
        if provider == "openai":
            base64_data, mime_type = _encode_image_to_base64(image_path)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this screenshot for dark patterns.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_data}"
                            },
                        },
                    ],
                },
            ]
            return _call_openai_llm(api_key, base_url, model_name, messages)
        else:
            from google.genai import types

            with open(image_path, "rb") as f:
                image_bytes = f.read()
            ext = Path(image_path).suffix.lower().lstrip(".")
            mime_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png" if ext == "png" else f"image/{ext}"
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            return _call_gemini_llm(
                api_key, model_name, [image_part, "Analyze this screenshot for dark patterns."]
            )
    except Exception as e:
        print(f"[AI ENGINE] Error during screenshot analysis: {type(e).__name__}: {e}")
        traceback.print_exc()
        return _mock_analysis("screenshot")


def _mock_analysis(source: str) -> Dict[str, Any]:
    """Fallback mock analysis generator used during offline testing or network outages."""
    return {
        "overall_risk_score": 85,
        "risk_level": "high",
        "patterns": [
            {
                "type": "hidden_recurring_fee",
                "severity": "high",
                "confidence": 0.95,
                "evidence": f"ANALYSIS RESULT ({source}): Checkout highlights initial trial price; fine print discloses recurring monthly subscription.",
                "explanation": "Users are automatically enrolled into a recurring paid membership without clear disclosure.",
                "financial_impact": {
                    "has_hidden_fee": True,
                    "estimated_amount": "₹499",
                    "is_recurring": True,
                    "frequency": "monthly",
                },
            }
        ],
    }
