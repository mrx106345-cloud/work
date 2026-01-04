"""
Test script to verify the Restaurant Voice AI Agent application can run
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✓ FastAPI import successful")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import openai
        print("✓ OpenAI import successful")
    except ImportError as e:
        print(f"✗ OpenAI import failed: {e}")
        return False
    
    try:
        import twilio
        print("✓ Twilio import successful")
    except ImportError as e:
        print(f"✗ Twilio import failed: {e}")
        return False
    
    try:
        import requests
        print("✓ Requests import successful")
    except ImportError as e:
        print(f"✗ Requests import failed: {e}")
        return False
    
    try:
        import redis
        print("✓ Redis import successful")
    except ImportError as e:
        print(f"✗ Redis import failed: {e}")
        # This is optional, so we don't return False
    
    try:
        from ai_agent import RestaurantAIAgent
        print("✓ AI Agent import successful")
    except ImportError as e:
        print(f"✗ AI Agent import failed: {e}")
        return False
    
    try:
        from twilio_integration import twilio_handler
        print("✓ Twilio Integration import successful")
    except ImportError as e:
        print(f"✗ Twilio Integration import failed: {e}")
        return False
    
    return True

def test_environment_variables():
    """Test that required environment variables are set"""
    print("\nTesting environment variables...")
    
    required_vars = [
        'RESTAURANT_NAME',
        'RESTAURANT_ADDRESS', 
        'RESTAURANT_HOURS',
        'MENU_CATEGORIES'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Missing required environment variables: {missing_vars}")
        print("  Please set these in your .env file")
        return False
    else:
        print("✓ All required environment variables are set")
        return True

def test_ai_agent():
    """Test that the AI agent can be initialized"""
    print("\nTesting AI Agent initialization...")
    
    try:
        from ai_agent import RestaurantAIAgent
        agent = RestaurantAIAgent()
        print("✓ AI Agent initialized successfully")
        
        # Test intent analysis
        test_message = "What time do you open?"
        intent_result = agent.analyze_intent(test_message)
        print(f"✓ Intent analysis works: {intent_result['primary_intent']}")
        
        # Test response generation
        response = agent.generate_response(test_message, [])
        print(f"✓ Response generation works: {response[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ AI Agent test failed: {e}")
        return False

def test_main_app():
    """Test that the main app can be imported and run"""
    print("\nTesting main application...")
    
    try:
        from app import app
        print("✓ Main application imported successfully")
        return True
    except Exception as e:
        print(f"✗ Main application import failed: {e}")
        return False

def main():
    print("Restaurant Voice AI Agent - Readiness Test")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Run all tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_environment_variables()
    all_tests_passed &= test_ai_agent()
    all_tests_passed &= test_main_app()
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✓ All tests passed! The application is ready to run.")
        print("\nTo start the application, run:")
        print("  uvicorn app:app --reload --host 0.0.0.0 --port 8000")
        print("\nOr directly run the app:")
        print("  python app.py")
    else:
        print("✗ Some tests failed. Please fix the issues before running.")
        sys.exit(1)

if __name__ == "__main__":
    main()