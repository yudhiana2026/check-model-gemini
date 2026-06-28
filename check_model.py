"""Check Gemini model availability, categories, and published rate limits."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from tabulate import tabulate

load_dotenv()
_client: Optional[genai.Client] = None


def get_api_key() -> str:
    """Return the Gemini API key from the environment.

    Returns:
        The API key string.

    Raises:
        RuntimeError: If GOOGLE_API_KEY is not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set")
    return api_key


def get_client() -> genai.Client:
    """Return a lazily-initialized Gemini API client (global singleton)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_api_key())
    return _client


# ── Published Gemini API rate limits (Free Tier) ──
# Source: https://ai.google.dev/pricing
# NOTE: Actual remaining quota cannot be fetched via API.
# These are published maximum limits for reference only.
GEMINI_LIMITS = {
    "gemini-2.5-flash":                {"rpm": 30,   "tpm": 1_000_000, "rpd": 1_500},
    "gemini-2.5-flash-lite":           {"rpm": 30,   "tpm": 1_000_000, "rpd": 1_500},
    "gemini-2.5-flash-preview-tts":    {"rpm": 3,    "tpm": 10_000,    "rpd": 10},
    "gemini-3-flash-preview":          {"rpm": 30,   "tpm": 1_000_000, "rpd": 1_500},
    "gemini-3.1-flash-lite":           {"rpm": 30,   "tpm": 1_000_000, "rpd": 1_500},
    "gemini-3.1-flash-lite-preview":   {"rpm": 30,   "tpm": 1_000_000, "rpd": 1_500},
    "gemini-3.1-flash-tts-preview":    {"rpm": 10,   "tpm": 500_000,   "rpd": 500},
    "gemini-robotics-er-1.6-preview":  {"rpm": 10,   "tpm": 500_000,   "rpd": 500},
    "gemma-4-26b-a4b-it":              {"rpm": 10,   "tpm": 500_000,   "rpd": 500},
    "gemma-4-31b-it":                  {"rpm": 10,   "tpm": 500_000,   "rpd": 500},
    "gemini-flash-lite-latest":        {"rpm": 10,   "tpm": 500_000,   "rpd": 500},
    "antigravity-preview-05-2026":     {"rpm": 60,   "tpm": 100_000,   "rpd": 100},
    "deep-research-max-preview-04-2026":  {"rpm": 10,  "tpm": 500_000, "rpd": 500},
    "deep-research-preview-04-2026":      {"rpm": 10,  "tpm": 500_000, "rpd": 500},
    "deep-research-pro-preview-12-2025":  {"rpm": 10,  "tpm": 500_000, "rpd": 500},
    "gemini-embedding-001":            {"rpm": 100,  "tpm": 30_000,    "rpd": 1_000},
    "gemini-embedding-2-preview":      {"rpm": 100,  "tpm": 30_000,    "rpd": 1_000},
    "gemini-embedding-2":              {"rpm": 100,  "tpm": 30_000,    "rpd": 1_000},
    # Models with zero quota (disabled/blocked)
    "gemini-2.5-pro":                  {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-2.5-pro-preview-tts":      {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-2.0-flash":                {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-2.0-flash-lite":           {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-2.5-computer-use-preview-10-2025": {"rpm": 0, "tpm": 0,   "rpd": 0},
    "gemini-2.5-flash-image":          {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3-pro-image-preview":      {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3-pro-image":              {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3.1-pro-preview":          {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3.1-flash-image-preview":  {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3.1-flash-image":          {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3.5-flash":                {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "lyria-3-clip-preview":            {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "lyria-3-pro-preview":             {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "nano-banana-pro-preview":         {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3-pro-preview":            {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-3.1-pro-preview-customtools": {"rpm": 0, "tpm": 0,        "rpd": 0},
    "gemini-2.0-flash-001":            {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-2.0-flash-lite-001":       {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "gemini-pro-latest":               {"rpm": 0,    "tpm": 0,         "rpd": 0},
    "_default":                        {"rpm": 10,   "tpm": 500_000,  "rpd": 500},
}

# Pre-sorted keys by length descending for deterministic substring matching.
# This ensures "gemini-2.5-flash-lite" is tested before "gemini-2.5-flash".
_LIMIT_KEYS = sorted(
    (k for k in GEMINI_LIMITS if k != "_default"),
    key=len,
    reverse=True,
)


def humanize_number(n: Optional[int]) -> str:
    """Convert a number to a human-readable abbreviated format (K, M, B).

    Args:
        n: Integer value to format, or None (rendered as "-").

    Returns:
        Formatted string such as "1.5M", "30K", "0", or "-" for None.
    """
    if n is None:
        return "-"
    if n >= 1_000_000_000:
        val = n / 1_000_000_000
        return f"{val:.1f}B" if val < 10 else f"{int(val)}B"
    if n >= 1_000_000:
        val = n / 1_000_000
        return f"{val:.1f}M" if val < 10 else f"{int(val)}M"
    if n >= 1_000:
        val = n / 1_000
        return f"{val:.1f}K" if val < 10 else f"{int(val)}K"
    return str(n)


def get_published_limits_raw(model_name: str) -> dict:
    """Return the published rate limits for a model.

    Tries an exact match first, then a longest-substring fallback, and
    finally the "_default" entry.

    Args:
        model_name: Full model name (e.g. "models/gemini-2.5-flash").

    Returns:
        Dict with keys "rpm", "tpm", "rpd".
    """
    short = model_name.replace("models/", "")
    if short in GEMINI_LIMITS:
        return GEMINI_LIMITS[short]
    for key in _LIMIT_KEYS:
        if key in short:
            return GEMINI_LIMITS[key]
    return GEMINI_LIMITS["_default"]


# ── Model Accessibility Check ──
def check_model_accessibility(model_name: str) -> str:
    """Probe whether a model is accessible via a minimal generation request.

    The Gemini API does **not** return remaining quota in response headers,
    so this checks accessibility rather than quota consumption.  See:
      - https://aistudio.google.com/app/apikey  (Free Tier usage dashboard)
      - Google Cloud Console > APIs & Services > Quotas  (Vertex AI)

    Args:
        model_name: Full model name (e.g. "models/gemini-2.5-flash").

    Returns:
        One of: "ALLOWED", "QUOTA_EXCEEDED", "FORBIDDEN", "NOT_FOUND",
        "SERVER_ERROR_{code}", "ERROR_{code}", or "CHECK_FAILED".
    """
    client = get_client()
    try:
        client.models.generate_content(
            model=model_name,
            contents="hello",
            config=types.GenerateContentConfig(max_output_tokens=1),
        )
        return "ALLOWED"
    except ClientError as e:
        if e.code == 429:
            return "QUOTA_EXCEEDED"
        elif e.code == 403:
            return "FORBIDDEN"
        elif e.code == 404:
            return "NOT_FOUND"
        elif e.code == 400:
            # 400 often means the model exists but requires different input
            return "ALLOWED"
        else:
            return f"ERROR_{e.code}"
    except ServerError as e:
        return f"SERVER_ERROR_{e.code}"
    except Exception:
        # Catches network timeouts, connection errors, etc.  The exception
        # is logged so debugging information is not silently lost.
        logging.exception("Unexpected error probing model %s", model_name)
        return "CHECK_FAILED"


# ── Category Detection ──
# Priority mirrors the original implementation:
#   1. Name: robotics / robot         → Robotics
#   2. Name: computer / use           → Computer Use
#   3. Name: research                 → Deep Research
#   4. Name: aqa                      → Q&A
#   5. Name: veo                      → Video
#   6. Name: imagen                   → Image
#   7. Name: embedding                → Embedding
#   8. Action: bidiGenerateContent    → Live
#   9. Action: predict (sole action)  → Image
#  10. Action: predictLongRunning     → Video
#  11. Action: embedContent           → Embedding
#  12. Action: generateContent        → Chat
#  13. Name: audio / tts              → Audio
#  14. Name: live                     → Live
#  15. Fallback                       → Other / Unknown
CATEGORY_RULES = [
    # Agents
    ("antigravity", "Agents"),
    ("deep-research", "Agents"),

    # Live API
    ("live", "Live API"),
    ("native-audio", "Live API"),

    # Multi-modal
    ("imagen", "Multi-modal generative models"),
    ("veo", "Multi-modal generative models"),
    ("lyria", "Multi-modal generative models"),
    ("-tts", "Multi-modal generative models"),
    ("-image", "Multi-modal generative models"),
    ("nano-banana", "Multi-modal generative models"),

    # Other
    ("embedding", "Other models"),
    ("robotics", "Other models"),
    ("computer-use", "Other models"),
    ("aqa", "Other models"),

    # Default
    ("gemma", "Text-out models"),
    ("gemini", "Text-out models"),
]

def get_category(actions: Optional[list[str]], name: str) -> str:
    # print(actions, name)
    """Return a human-readable category label for a model.

    Args:
        actions: Supported API actions returned by the model listing.
        name: Model name used for heuristic matching.

    Returns:
        Category string such as "Chat", "Image", "Audio", "Robotics", etc.
    """
    name_lower = name.lower()

    for prefix, category in CATEGORY_RULES:
        if prefix in name_lower:
            return category

    # ── Fallback ──
    return "Other" if actions else "Unknown"


# ── Display helpers ──
QUOTA_DISPLAY = {
    "ALLOWED":         "✅ Accessible",
    "QUOTA_EXCEEDED":  "🔴 Quota Exceeded",
    "FORBIDDEN":       "🔴 Forbidden",
    "NOT_FOUND":       "⚠️ Not Found",
    "CHECK_FAILED":    "⚠️ Check Failed",
}


def display_quota(key: str) -> str:
    """Map an accessibility status key to its emoji-prefixed display string.

    Args:
        key: Status key such as "ALLOWED" or "QUOTA_EXCEEDED".

    Returns:
        Human-readable display string.
    """
    return QUOTA_DISPLAY.get(key, key)


# ── Main ──
def main() -> None:
    """Fetch Gemini models, probe accessibility, categorize, and print a summary table."""
    logging.basicConfig(level=logging.WARNING)

    client = get_client()

    print("Fetching model list...")
    all_models = list(client.models.list())
    print(f"Found {len(all_models)} models.\n")

    rows: list[list[str]] = []
    quota_ok = 0
    quota_fail = 0

    for model in all_models:
        name = model.name
        display_name = model.display_name
        category = get_category(model.supported_actions, name)
        has_chat = model.supported_actions and "generateContent" in model.supported_actions

        if has_chat:
            status = check_model_accessibility(name)
            status_display = display_quota(status)

            if status == "ALLOWED":
                quota_ok += 1
            else:
                quota_fail += 1

            limits = get_published_limits_raw(name)
            rpm_str = humanize_number(limits.get("rpm"))
            tpm_str = humanize_number(limits.get("tpm"))
            rpd_str = humanize_number(limits.get("rpd"))
        else:
            status_display = "-"
            rpm_str = "-"
            tpm_str = "-"
            rpd_str = "-"

        rows.append([name, display_name, status_display, category, rpm_str, tpm_str, rpd_str])

    headers = ["Model", "Name", "Status", "Category", "RPM (limit)", "TPM (limit)", "RPD (limit)"]
    print(tabulate(rows, headers=headers, tablefmt="grid", stralign="left"))

    # Summary
    print(f"\nSummary: {quota_ok} models Allowed  |  {quota_fail} models Blocked/Error")
    print()
    print("NOTE: Gemini API enforces rate limits per MINUTE, not per day.")
    print()
    print("Published limits shown are reference values (Free Tier estimates):")
    print("  Gemini 2.5 Flash:    30 RPM / 1M TPM / 1,500 RPD")
    print("  Gemini 2.5 Pro:      10 RPM / 500K TPM / 1,000 RPD")
    print("  Gemini 2.0 Flash:    30 RPM / 1M TPM / 1,500 RPD")
    print("  Other models:        10 RPM / 500K TPM / 500 RPD (default)")
    print("  RPM=Requests/min, TPM=Tokens/min, RPD=Requests/day (free)")
    print()
    print("⚠ Remaining quota CANNOT be fetched via the API.")
    print("  To check actual remaining usage, visit:")
    print("    -> https://aistudio.google.com/app/apikey  (Free Tier / Developer API)")
    print("    -> Google Cloud Console > APIs & Services > Quotas  (Vertex AI)")


if __name__ == "__main__":
    main()