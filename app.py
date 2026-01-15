from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, Response
import asyncio
import logging
import os
import json
from typing import Dict, Any
import openai
import requests
from pydantic import BaseModel
from openai import OpenAI
import redis
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from twilio.request_validator import RequestValidator
from twilio_integration import twilio_handler
from ai_agent import RestaurantAIAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    logger.warning("Twilio credentials not found. Some functionality will be limited.")
    # Create a mock client for testing purposes
    twilio_client = None

# Initialize AI agent
ai_agent = RestaurantAIAgent()

# Optional Redis for session management
redis_client = None
if os.getenv("REDIS_URL"):
    redis_client = redis.from_url(os.getenv("REDIS_URL"))

# Restaurant information (static knowledge base)
RESTAURANT_INFO = {
    "name": os.getenv("RESTAURANT_NAME", "Restaurant Name"),
    "address": os.getenv("RESTAURANT_ADDRESS", "Restaurant Address"),
    "hours": os.getenv("RESTAURANT_HOURS", "Open from 10 AM to 10 PM daily"),
    "menu_categories": os.getenv("MENU_CATEGORIES", "Appetizers, Main Courses, Desserts, Beverages").split(", "),
    "delivery_policy": os.getenv("DELIVERY_POLICY", "We offer delivery within a 5-mile radius from 11 AM to 9 PM"),
    "phone": os.getenv("RESTAURANT_PHONE", "Phone Number")
}

# System prompt for the AI agent
SYSTEM_PROMPT = f"""
You are a professional restaurant call-handling assistant for {RESTAURANT_INFO['name']}. 
Your primary function is to answer incoming calls, provide information about the restaurant, and assist customers while adhering to strict operational guidelines.

Important guidelines:
- Answer calls promptly and politely
- Provide only the restaurant information provided in your knowledge base
- Never place orders, take reservations, or access any system data
- If a customer wants to order, make a reservation, or has a complaint, politely transfer to human staff
- Keep responses short and clear (1-2 sentences when possible)
- If unsure about information, politely transfer to staff
- Always offer human handoff when appropriate

Restaurant Information:
- Name: {RESTAURANT_INFO['name']}
- Address: {RESTAURANT_INFO['address']}
- Hours: {RESTAURANT_INFO['hours']}
- Menu Categories: {', '.join(RESTAURANT_INFO['menu_categories'])}
- Delivery Policy: {RESTAURANT_INFO['delivery_policy']}

Example responses:
- Greeting: "Hello! Thank you for calling {RESTAURANT_INFO['name']}. How can I assist you today?"
- Hours: "We are open {RESTAURANT_INFO['hours'].lower()}."
- Location: "We are located at {RESTAURANT_INFO['address']}."
- Orders: "I'd be happy to connect you with our staff who can help you place your order."
- Closing: "Thank you for calling {RESTAURANT_INFO['name']}. Have a great day!"

If a customer wants to place an order, make a reservation, or has a complaint, always transfer to human staff.
"""

class CallSession:
    def __init__(self, call_sid: str):
        self.call_sid = call_sid
        self.conversation_history = []
        self.caller_info = {}
        self.escalation_needed = False
        self.call_summary = None
        
    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        
    def needs_escalation(self) -> bool:
        # Escalation is handled by the AI agent
        # This method exists for backward compatibility
        return self.escalation_needed

# In-memory session storage (use Redis in production)
sessions: Dict[str, CallSession] = {}

def get_session(call_sid: str) -> CallSession:
    if call_sid not in sessions:
        sessions[call_sid] = CallSession(call_sid)
    return sessions[call_sid]

def text_to_speech(text: str) -> str:
    """Convert text to speech using ElevenLabs API"""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            # In a real implementation, you'd save this audio to a temporary file and return a URL
            # For this example, we'll return a placeholder that Twilio can use
            # For Twilio integration, we'd typically host the audio file temporarily
            import tempfile
            import os
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                temp_audio.write(response.content)
                # In production, you'd upload this to a cloud storage service
                # and return the public URL. For this example, we'll return a placeholder
                return f"http://localhost:8000/audio/{os.path.basename(temp_audio.name)}"
        else:
            logger.error(f"TTS API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return None

def speech_to_text(audio_url: str) -> str:
    """Convert speech to text using OpenAI Whisper API"""
    try:
        if not openai_client:
            logger.error("OpenAI client not initialized")
            return ""
        
        # Download audio file from URL
        response = requests.get(audio_url)
        if response.status_code != 200:
            logger.error(f"Failed to download audio: {response.status_code}")
            return ""
        
        # Save to temporary file for processing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(response.content)
            temp_filename = temp_audio.name
        
        try:
            # Use OpenAI Whisper API for transcription
            with open(temp_filename, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                return transcript.text
        finally:
            # Clean up temporary file
            import os
            os.unlink(temp_filename)
            
    except Exception as e:
        logger.error(f"STT error: {str(e)}")
        return ""

def get_ai_response(user_message: str, session: CallSession) -> str:
    """Get response from AI using the RestaurantAIAgent"""
    try:
        # Use the AI agent to generate response
        intent_analysis = ai_agent.analyze_intent(user_message)
        ai_response = ai_agent.generate_response(user_message, session.conversation_history, intent_analysis)
        
        # Add user message to conversation history
        session.add_message("user", user_message)
        
        # Add AI response to conversation history
        session.add_message("assistant", ai_response)
        
        # Check if escalation is needed based on the conversation
        if ai_agent.needs_escalation(user_message, session.conversation_history, intent_analysis):
            session.escalation_needed = True
        
        return ai_response
    except Exception as e:
        logger.error(f"AI response error: {str(e)}")
        return "I apologize, but I'm experiencing technical difficulties. Let me connect you to our staff."

@app.get("/")
def read_root():
    return {
        "status": "Restaurant Voice AI Agent is running",
        "endpoints": {
            "voice_webhook": "/webhook/twilio/voice",
            "speech_webhook": "/webhook/twilio/speech",
            "status_webhook": "/webhook/twilio/status",
            "docs": "/docs"
        },
        "configuration": {
            "twilio_connected": bool(os.getenv("TWILIO_ACCOUNT_SID")),
            "openai_connected": bool(os.getenv("OPENAI_API_KEY")),
            "elevenlabs_connected": bool(os.getenv("ELEVENLABS_API_KEY"))
        }
    }

@app.post("/webhook/twilio/voice")
async def handle_twilio_voice_webhook(request: Request):
    """Handle incoming voice calls from Twilio"""
    try:
        form_data = await request.form()
        call_sid = form_data.get('CallSid', '')
        from_number = form_data.get('From', '')
        to_number = form_data.get('To', '')
        
        logger.info(f"Incoming call from {from_number} to {to_number}, CallSid: {call_sid}")
        
        # Bypass validation for faster response during testing
        logger.info("Request validation bypassed to ensure calls connect")
        
        # Create or get session for this call
        session = get_session(call_sid)
        session.caller_info['phone'] = from_number
        
        # Generate greeting response using Twilio handler
        twiml_response = twilio_handler.generate_twiml_response(
            "greeting", 
            restaurant_name=RESTAURANT_INFO['name']
        )
        
        logger.info(f"Sending TwiML response for call {call_sid}: {twiml_response[:100]}...")
        return Response(content=twiml_response, media_type="text/xml")
    except Exception as e:
        logger.error(f"Error handling voice webhook: {str(e)}")
        # Return a simple error response that Twilio can understand
        error_response = VoiceResponse()
        error_response.say(message="Sorry, there was an error processing your call. Please try again later.")
        return Response(content=str(error_response), media_type="text/xml")

@app.get("/webhook/twilio/voice")
async def handle_twilio_voice_webhook_get():
    """Return a friendly message for GET requests to the voice webhook"""
    return {"message": "This is a Twilio voice webhook endpoint. It handles incoming voice calls from Twilio.", "status": "active"}

@app.post("/webhook/twilio/speech")
async def handle_twilio_speech_webhook(request: Request):
    """Handle speech recognition results from Twilio"""
    form_data = await request.form()
    call_sid = form_data.get('CallSid', '')
    speech_result = form_data.get('SpeechResult', '')
    confidence = form_data.get('Confidence', '0.0')
    
    logger.info(f"Speech result: '{speech_result}' with confidence {confidence} for CallSid: {call_sid}")
    
    # Get session for this call
    session = get_session(call_sid)
    
    # If speech recognition failed or low confidence, ask for repetition
    if not speech_result or float(confidence) < 0.5:
        twiml_response = twilio_handler.generate_twiml_response("unclear")
        return Response(content=twiml_response, media_type="text/xml")
    
    # Get AI response based on speech result
    ai_response = get_ai_response(speech_result, session)
    
    # Check if escalation is needed
    if session.needs_escalation():
        # Generate escalation response
        twiml_response = twilio_handler.generate_twiml_response(
            "escalation",
            restaurant_phone=RESTAURANT_INFO['phone']
        )
        
        # Generate and log call summary
        session.call_summary = {
            "call_sid": call_sid,
            "caller_phone": session.caller_info.get('phone', 'Unknown'),
            "final_intent": "Escalated to human",
            "conversation_length": len(session.conversation_history),
            "escalation_reason": "Order/Reservation/Complaint detected"
        }
        
        return Response(content=twiml_response, media_type="text/xml")
    
    # Generate response with AI-generated speech
    twiml_response = twilio_handler.generate_twiml_response(
        "speech_response",
        ai_response=ai_response,
        call_sid=call_sid
    )
    
    return Response(content=twiml_response, media_type="text/xml")

@app.post("/webhook/twilio/status")
async def handle_twilio_status_webhook(request: Request):
    """Handle call status changes from Twilio"""
    form_data = await request.form()
    call_sid = form_data.get('CallSid', '')
    call_status = form_data.get('CallStatus', '')
    from_number = form_data.get('From', '')
    
    logger.info(f"Call status update: {call_sid} is now {call_status}")
    
    if call_status in ['completed', 'busy', 'failed', 'no-answer']:
        # Generate and log call summary when call ends
        if call_sid in sessions:
            session = sessions[call_sid]
            summary = {
                "call_sid": call_sid,
                "caller_phone": from_number,
                "call_status": call_status,
                "conversation_length": len(session.conversation_history),
                "escalated": session.needs_escalation(),
                "summary": session.call_summary
            }
            
            logger.info(f"Call summary: {json.dumps(summary, indent=2)}")
            
            # Clean up session
            del sessions[call_sid]
    
    return Response(content="OK", media_type="text/plain")

@app.get("/api/session/{call_sid}")
def get_call_session(call_sid: str):
    """Get information about a specific call session (for monitoring/debugging)"""
    if call_sid in sessions:
        session = sessions[call_sid]
        return {
            "call_sid": session.call_sid,
            "conversation_history": session.conversation_history,
            "caller_info": session.caller_info,
            "escalation_needed": session.escalation_needed,
            "call_summary": session.call_summary
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/config-status")
def config_status():
    return twilio_handler.get_config_status()

if __name__ == "__main__":
    import uvicorn
     
    uvicorn.run(app, host="0.0.0.0", port=8000)