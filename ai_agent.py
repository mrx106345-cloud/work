import os
import json
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RestaurantAIAgent:
    """
    AI agent for handling restaurant-related conversations
    """
    
    def __init__(self):
        # Get OpenAI API key from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=self.api_key) if self.api_key else None
        
        # Check if OpenAI is available
        self.has_openai = self.openai_client is not None
        
        # Restaurant information
        self.restaurant_info = {
            "name": os.getenv("RESTAURANT_NAME", "Your Restaurant Name"),
            "address": os.getenv("RESTAURANT_ADDRESS", "123 Restaurant Street, City, State 12345"),
            "hours": os.getenv("RESTAURANT_HOURS", "Open from 10 AM to 10 PM daily"),
            "menu_categories": os.getenv("MENU_CATEGORIES", "Appetizers, Main Courses, Desserts, Beverages").split(", "),
            "delivery_policy": os.getenv("DELIVERY_POLICY", "We offer delivery within a 5-mile radius from 11 AM to 9 PM"),
            "phone": os.getenv("RESTAURANT_PHONE", "Phone Number")
        }
        
        # System prompt
        self.system_prompt = f"""
        You are a professional restaurant call-handling assistant for {self.restaurant_info['name']}. 
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
        - Name: {self.restaurant_info['name']}
        - Address: {self.restaurant_info['address']}
        - Hours: {self.restaurant_info['hours']}
        - Menu Categories: {', '.join(self.restaurant_info['menu_categories'])}
        - Delivery Policy: {self.restaurant_info['delivery_policy']}

        Example responses:
        - Greeting: "Hello! Thank you for calling {self.restaurant_info['name']}. How can I assist you today?"
        - Hours: "We are open {self.restaurant_info['hours'].lower()}."
        - Location: "We are located at {self.restaurant_info['address']}."
        - Orders: "I'd be happy to connect you with our staff who can help you place your order."
        - Closing: "Thank you for calling {self.restaurant_info['name']}. Have a great day!"

        If a customer wants to place an order, make a reservation, or has a complaint, always transfer to human staff.
        """
    
    def analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Analyze the intent of the user's message
        """
        # Define possible intents
        intent_keywords = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "hours_inquiry": ["open", "close", "hours", "time", "when", "what time", "what are your hours"],
            "location_inquiry": ["where", "address", "location", "find", "direction", "located"],
            "menu_inquiry": ["menu", "food", "what do you", "what's on", "offer", "have"],
            "order_request": ["order", "place", "buy", "get", "delivery", "takeout", "take out"],
            "reservation_request": ["reservation", "book", "table", "seat", "reserve"],
            "complaint": ["problem", "issue", "wrong", "not", "complaint", "angry", "upset", "terrible", "bad"],
            "delivery_inquiry": ["delivery", "takeout", "take out", "pickup", "pick up", "carryout"],
            "closing": ["bye", "goodbye", "thanks", "thank you", "that's all", "see you", "later"],
            "contact_staff": ["speak", "talk", "manager", "human", "staff", "person", "someone"]
        }
        
        # Convert message to lowercase for matching
        message_lower = user_message.lower()
        
        # Find matching intents
        detected_intents = []
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    if intent not in detected_intents:
                        detected_intents.append(intent)
        
        # If no specific intent detected, default to general inquiry
        if not detected_intents:
            detected_intents = ["general_inquiry"]
        
        # Determine primary intent
        primary_intent = detected_intents[0] if detected_intents else "general_inquiry"
        
        # Check if escalation is needed based on detected intents
        escalation_intents = ["order_request", "reservation_request", "complaint", "contact_staff"]
        escalation_needed = any(intent in escalation_intents for intent in detected_intents)
        
        return {
            "primary_intent": primary_intent,
            "all_detected_intents": detected_intents,
            "escalation_needed": escalation_needed
        }
    
    def generate_response(self, user_message: str, conversation_history: List[Dict], intent_analysis: Dict[str, Any] = None) -> str:
        """
        Generate a response to the user's message
        """
        if intent_analysis is None:
            intent_analysis = self.analyze_intent(user_message)
        
        primary_intent = intent_analysis["primary_intent"]
        
        # Handle different intents with appropriate responses
        if primary_intent == "greeting":
            return f"Hello! Thank you for calling {self.restaurant_info['name']}. How can I assist you today?"
        
        elif primary_intent == "hours_inquiry":
            return f"We are {self.restaurant_info['hours'].lower()}."
        
        elif primary_intent == "location_inquiry":
            return f"We are located at {self.restaurant_info['address']}."
        
        elif primary_intent == "menu_inquiry":
            categories = ", ".join(self.restaurant_info['menu_categories'])
            return f"We offer {categories}. For more details, please speak with our staff."
        
        elif primary_intent in ["order_request", "reservation_request", "complaint"]:
            return "I'd be happy to connect you with our staff who can help you with that."
        
        elif primary_intent == "delivery_inquiry":
            return f"{self.restaurant_info['delivery_policy']}."
        
        elif primary_intent == "closing":
            return f"Thank you for calling {self.restaurant_info['name']}. Have a great day!"
        
        elif primary_intent == "contact_staff":
            return "I'll connect you with our staff who can better assist you."
        
        else:
            # For testing purposes, always use mock responses to avoid API delays
            # In production, you can enable OpenAI by removing this override
            return self._generate_mock_response(user_message, primary_intent)
                    
            # Original OpenAI code (commented out for testing):
            # if self.has_openai:
            #     try:
            #         # Prepare conversation history for context
            #         messages = [
            #             {"role": "system", "content": self.system_prompt}
            #         ]
            #         
            #         # Add conversation history
            #         for msg in conversation_history:
            #             messages.append({"role": msg["role"], "content": msg["content"]})
            #         
            #         # Add current user message
            #         messages.append({"role": "user", "content": user_message})
            #         
            #         # Get response from OpenAI
            #         response = self.openai_client.chat.completions.create(
            #             model="gpt-4o-mini",  # Using a more cost-effective model
            #             messages=messages,
            #             max_tokens=150,
            #             temperature=0.7
            #         )
            #         
            #         return response.choices[0].message.content.strip()
            #     except Exception as e:
            #         # If OpenAI fails, return a default response
            #         return f"I'm experiencing technical difficulties. {self.restaurant_info['name']} is {self.restaurant_info['hours'].lower()}.
            # else:
            #     # If OpenAI is not available, return a mock response
            #     return self._generate_mock_response(user_message, primary_intent)
    
    def _generate_mock_response(self, user_message: str, primary_intent: str) -> str:
        """
        Generate a mock response when OpenAI is not available
        """
        if "open" in user_message.lower() or "hour" in user_message.lower():
            return f"We are {self.restaurant_info['hours'].lower()}."
        elif "where" in user_message.lower() or "address" in user_message.lower():
            return f"We are located at {self.restaurant_info['address']}."
        elif "menu" in user_message.lower() or "food" in user_message.lower():
            categories = ", ".join(self.restaurant_info['menu_categories'])
            return f"We offer {categories}."
        elif "order" in user_message.lower() or "delivery" in user_message.lower():
            return "I'd be happy to connect you with our staff who can help you place your order."
        else:
            return f"Thank you for calling {self.restaurant_info['name']}. We are {self.restaurant_info['hours'].lower()}."
    
    def needs_escalation(self, user_message: str, conversation_history: List[Dict], intent_analysis: Dict[str, Any] = None) -> bool:
        """
        Determine if the conversation needs to be escalated to a human
        """
        if intent_analysis is None:
            intent_analysis = self.analyze_intent(user_message)
        
        # Escalate if any of these intents are detected
        escalation_intents = ["order_request", "reservation_request", "complaint", "contact_staff"]
        
        return intent_analysis["escalation_needed"]