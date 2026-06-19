import base64
import json
import re
from datetime import date, datetime
from pathlib import Path

import anthropic

from models import Cheque

_client = anthropic.Anthropic()

_SYSTEM = """You are a cheque-reading assistant. Extract fields from the cheque image and return ONLY valid JSON with these keys:
- amount (number)
- currency (string, e.g. "SAR", "USD")
- due_date (string, ISO format YYYY-MM-DD)
- payee (string or null)
- cheque_number (string or null)
- bank (string or null)

If a field is not visible, use null. Do not include any explanation outside the JSON."""


def _encode_image(path: str) -> tuple[str, str]:
    data = Path(path).read_bytes()
    b64 = base64.standard_b64encode(data).decode()
    suffix = Path(path).suffix.lower()
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/jpeg")
    return b64, media_type


def _parse_response(text: str) -> dict:
    # Extract JSON even if the model wraps it in markdown fences
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in vision response: {text!r}")
    return json.loads(match.group())


def extract_cheque(image_path: str) -> Cheque:
    b64, media_type = _encode_image(image_path)

    response = _client.messages.create(
        model="claude-opus-4-8",
        max_tokens=512,
        system=_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": "Extract all cheque fields as JSON."},
                ],
            }
        ],
    )

    raw = response.content[0].text
    data = _parse_response(raw)

    return Cheque(
        amount=float(data["amount"]),
        currency=str(data.get("currency") or ""),
        due_date=datetime.strptime(data["due_date"], "%Y-%m-%d").date(),
        payee=data.get("payee"),
        cheque_number=str(data["cheque_number"]) if data.get("cheque_number") else None,
        bank=data.get("bank"),
    )
