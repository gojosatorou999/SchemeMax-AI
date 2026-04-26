import traceback
from twilio.rest import Client
from flask import current_app

def get_twilio_client():
    sid = current_app.config.get("TWILIO_ACCOUNT_SID")
    auth = current_app.config.get("TWILIO_AUTH_TOKEN")
    if not sid or not auth:
        return None
    return Client(sid, auth)

def send_whatsapp_message(to_number: str, message: str) -> dict:
    """
    Sends a WhatsApp message using Twilio Sandbox.
    to_number should be formatted like 'whatsapp:+919999999999' or '+919999999999'
    """
    try:
        client = get_twilio_client()
        if not client:
            return {"success": False, "error": "Twilio not configured"}
            
        if not to_number.startswith("whatsapp:"):
            # Ensure number has + prefix if missing (though user should provide it)
            if not to_number.startswith("+"):
                to_number = "+" + to_number
            to_number = f"whatsapp:{to_number}"
            
        from_number = "whatsapp:+14155238886"
        
        msg = client.messages.create(
            from_=from_number,
            body=message,
            to=to_number
        )
        return {"success": True, "sid": msg.sid}
    except Exception as e:
        current_app.logger.error(f"WhatsApp Error: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}
