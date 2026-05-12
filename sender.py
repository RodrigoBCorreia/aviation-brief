import os
from twilio.rest import Client

WHATSAPP_MAX_CHARS = 1600  # Twilio WhatsApp message limit


def send_whatsapp(message: str) -> None:
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    from_number = os.environ["TWILIO_WHATSAPP_FROM"]   # e.g. "whatsapp:+14155238886"
    to_number = os.environ["TWILIO_WHATSAPP_TO"]        # e.g. "whatsapp:+1234567890"

    client = Client(account_sid, auth_token)

    # Split into chunks if message exceeds limit
    chunks = _split_message(message)
    for chunk in chunks:
        client.messages.create(
            body=chunk,
            from_=from_number,
            to=to_number,
        )
    print(f"  [sender] Sent {len(chunks)} WhatsApp message(s).")


def _split_message(text: str) -> list[str]:
    if len(text) <= WHATSAPP_MAX_CHARS:
        return [text]

    chunks = []
    while text:
        if len(text) <= WHATSAPP_MAX_CHARS:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, WHATSAPP_MAX_CHARS)
        if split_at == -1:
            split_at = WHATSAPP_MAX_CHARS
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks
