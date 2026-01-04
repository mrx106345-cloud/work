"""
Main entry point that combines the Restaurant Voice AI Agent API and UI interface
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import sys
from typing import Dict, Any

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main application components
from app import app as voice_agent_app
from twilio_integration import twilio_handler

# Create the main app that includes both API and UI
main_app = FastAPI(title="Restaurant Voice AI Agent - Combined Interface")

# Mount the voice agent API under a specific path
main_app.mount("/api", voice_agent_app)

@main_app.get("/", response_class=HTMLResponse)
async def ui_home(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Restaurant Voice AI Agent Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #eee;
            }
            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .status-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #007bff;
            }
            .status-card.connected {
                border-left-color: #28a745;
            }
            .status-card.disconnected {
                border-left-color: #dc3545;
            }
            .endpoints {
                margin: 20px 0;
            }
            .endpoint {
                background: #e9ecef;
                margin: 10px 0;
                padding: 15px;
                border-radius: 5px;
                font-family: monospace;
            }
            .controls {
                margin: 20px 0;
                text-align: center;
            }
            button {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin: 0 10px;
            }
            button:hover {
                background: #0056b3;
            }
            .config-section {
                margin: 20px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            .call-log {
                margin-top: 30px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            .info-box {
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🍽️ Restaurant Voice AI Agent Dashboard</h1>
                <p>Manage and monitor your restaurant's AI-powered phone system</p>
            </div>
            
            <div class="info-box">
                <strong>Note:</strong> This interface combines both the API endpoints and UI in a single server.
                The API endpoints are available under the /api/ path.
            </div>
            
            <div class="status-grid">
                <div class="status-card connected">
                    <h3>📞 Call Handling</h3>
                    <p>Active</p>
                </div>
                <div class="status-card" id="ai-status">
                    <h3>🧠 AI Processing</h3>
                    <p id="ai-status-text">Checking...</p>
                </div>
                <div class="status-card connected">
                    <h3>💬 Twilio Integration</h3>
                    <p>Connected</p>
                </div>
                <div class="status-card" id="voice-status">
                    <h3>🔊 Voice Synthesis</h3>
                    <p id="voice-status-text">Checking...</p>
                </div>
            </div>
            
            <div class="endpoints">
                <h2>📡 API Endpoints</h2>
                <div class="endpoint">
                    <strong>Twilio Voice Webhook:</strong> /api/webhook/twilio/voice
                </div>
                <div class="endpoint">
                    <strong>Twilio Speech Webhook:</strong> /api/webhook/twilio/speech
                </div>
                <div class="endpoint">
                    <strong>Twilio Status Webhook:</strong> /api/webhook/twilio/status
                </div>
                <div class="endpoint">
                    <strong>Configuration Status:</strong> /api/config-status
                </div>
                <div class="endpoint">
                    <strong>API Documentation:</strong> /api/docs
                </div>
            </div>
            
            <div class="config-section">
                <h2>⚙️ Configuration Status</h2>
                <div id="config-status">
                    <p>Loading configuration status...</p>
                </div>
            </div>
            
            <div class="controls">
                <button onclick="window.open('/api/docs', '_blank')">View API Docs</button>
                <button onclick="window.open('/api/config-status', '_blank')">View Config Status</button>
                <button onclick="window.open('https://console.twilio.com/', '_blank')">Twilio Console</button>
                <button onclick="updateStatus()">Refresh Status</button>
            </div>
            
            <div class="call-log">
                <h2>📋 Recent Calls</h2>
                <p>Connect to the API to start logging calls.</p>
            </div>
        </div>
        
        <script>
            // Function to update status indicators
            async function updateStatus() {
                try {
                    const response = await fetch('/api/config-status');
                    const config = await response.json();
                    
                    // Update AI status
                    const aiStatusText = document.getElementById('ai-status-text');
                    const aiStatusCard = document.getElementById('ai-status');
                    if (config.openai_configured) {
                        aiStatusText.textContent = 'Active';
                        aiStatusCard.className = 'status-card connected';
                    } else {
                        aiStatusText.textContent = 'Mock Responses';
                        aiStatusCard.className = 'status-card disconnected';
                    }
                    
                    // Update voice synthesis status
                    const voiceStatusText = document.getElementById('voice-status-text');
                    const voiceStatusCard = document.getElementById('voice-status');
                    if (config.elevenlabs_configured) {
                        voiceStatusText.textContent = 'Active';
                        voiceStatusCard.className = 'status-card connected';
                    } else {
                        voiceStatusText.textContent = 'Disabled';
                        voiceStatusCard.className = 'status-card disconnected';
                    }
                    
                    // Update configuration status display
                    const configDiv = document.getElementById('config-status');
                    configDiv.innerHTML = `
                        <p><strong>Twilio:</strong> <span>\${config.twilio_configured ? '✅ Configured' : '❌ Not Configured'}</span></p>
                        <p><strong>OpenAI:</strong> <span>\${config.openai_configured ? '✅ Configured' : '❌ Not Configured'}</span></p>
                        <p><strong>ElevenLabs:</strong> <span>\${config.elevenlabs_configured ? '✅ Configured' : '❌ Not Configured'}</span></p>
                        <p><strong>Restaurant Info:</strong> <span>\${config.restaurant_info_configured ? '✅ Configured' : '❌ Not Configured'}</span></p>
                        <p><strong>Redis:</strong> <span>\${config.redis_configured ? '✅ Configured' : '❌ Not Configured'}</span></p>
                    `;
                } catch (error) {
                    console.error('Error fetching config status:', error);
                    document.getElementById('config-status').innerHTML = '<p>Error loading configuration status</p>';
                }
            }
            
            // Update status on page load
            document.addEventListener('DOMContentLoaded', updateStatus);
        </script>
    </body>
    </html>
    """
    return html_content

@main_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Restaurant Voice AI Agent UI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(main_app, host="0.0.0.0", port=8000)