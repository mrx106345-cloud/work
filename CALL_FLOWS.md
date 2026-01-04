# Call Flows and Conversation Logic

## Main Call Flow

```
1. Call Received
    ↓
2. Greeting & Purpose Check
    ↓
3. Intent Classification
    ↓
4. Response Generation
    ↓
5. Escalation Check
    ↓
6. Response Delivery
    ↓
7. Continue or End Call
```

## Detailed Call Flows

### 1. General Information Flow
```
Customer: "What time do you open?"
    ↓
AI: Recognizes "hours" intent
    ↓
AI: Retrieves opening hours from knowledge base
    ↓
AI: Responds with "We are open from 10 AM to 10 PM every day."
    ↓
AI: Asks "Is there anything else I can help you with?"
```

### 2. Order Request Flow (Escalation Required)
```
Customer: "I want to order biryani."
    ↓
AI: Recognizes "ordering" intent
    ↓
AI: Trigger escalation rule
    ↓
AI: "Sure. I'll connect you with our staff to help you place the order."
    ↓
AI: Initiates call transfer to human staff
```

### 3. Reservation Request Flow (Escalation Required)
```
Customer: "I'd like to make a reservation for tonight."
    ↓
AI: Recognizes "reservation" intent
    ↓
AI: Trigger escalation rule
    ↓
AI: "I'd be happy to connect you with our host who can assist with reservations."
    ↓
AI: Initiates call transfer to human staff
```

### 4. Complaint Flow (Escalation Required)
```
Customer: "My order was cold and arrived late!"
    ↓
AI: Recognizes "complaint" sentiment/intent
    ↓
AI: Trigger escalation rule
    ↓
AI: "I understand your concern. Let me connect you to our manager right away."
    ↓
AI: Initiates call transfer to human staff
```

### 5. Unclear Speech Flow
```
STT: Returns unclear text or empty response
    ↓
AI: "I'm sorry, I couldn't hear that clearly. Could you please repeat?"
    ↓
If repeated unclear speech → Trigger escalation
    ↓
AI: "Let me connect you with our staff who can better assist you."
```

### 6. Angry Customer Flow
```
Customer: Repeated negative sentiment or explicit anger
    ↓
AI: Detects anger pattern
    ↓
AI: "I understand this is frustrating. Let me connect you to our manager."
    ↓
AI: Immediate escalation to human staff
```

### 7. Closing Flow
```
Customer: "That's all, thanks."
    ↓
AI: Generate call summary
    ↓
AI: "Thank you for calling [Restaurant Name]. Have a great day!"
    ↓
AI: End call gracefully
```

## Intent Classification

### Primary Intents
1. **INFORMATION_REQUEST**
   - Hours of operation
   - Location/address
   - Menu categories
   - Delivery policy

2. **ORDER_REQUEST** (Escalation Required)
   - Food ordering
   - Special requests for orders

3. **RESERVATION_REQUEST** (Escalation Required)
   - Table reservations
   - Event bookings

4. **COMPLAINT** (Escalation Required)
   - Food quality issues
   - Service complaints
   - Delivery problems

5. **GENERAL_GREETING**
   - Initial greetings
   - Polite conversation starters

6. **CLOSING_INTENT**
   - Ending conversation
   - Thank you messages

## Escalation Rules

### Automatic Escalation Conditions
- Intent is ORDER_REQUEST, RESERVATION_REQUEST, or COMPLAINT
- Customer repeats themselves twice (unclear communication)
- Customer expresses anger or frustration
- STT returns empty/unclear results twice consecutively
- LLM processing timeout (more than 10 seconds)
- Explicit request to speak to manager/human

### Manual Escalation Options
- Customer requests to speak to human
- Question outside knowledge base scope
- Complex special requests

## Conversation State Management

### Active States
1. **GREETING** - Initial call response
2. **INFORMATION_GATHERING** - Collecting caller needs
3. **RESPONSE_PROVIDING** - Delivering information
4. **ESCALATION_PENDING** - Preparing to transfer
5. **CALL_CLOSING** - Ending the conversation

### Context Variables
- `caller_name` - Customer name if provided
- `caller_phone` - Customer phone if provided
- `current_intent` - Current identified intent
- `conversation_history` - Last 3 exchanges
- `escalation_triggered` - Flag for transfer need
- `call_duration` - Time elapsed in call

## Error Handling Flows

### STT Failure
```
If STT fails or returns unclear text:
    ↓
AI: "I'm sorry, I couldn't hear that clearly. Could you please repeat?"
    ↓
If failure continues → Escalate to human
```

### LLM Timeout
```
If LLM response takes >10 seconds:
    ↓
AI: "I apologize for the delay. Let me connect you to our staff."
    ↓
Escalate to human
```

### Service Unavailable
```
If any service (STT, LLM, TTS) is unavailable:
    ↓
AI: "I'm experiencing technical difficulties. Let me transfer you to our team."
    ↓
Escalate to human
```

## Call Summary Generation

### Summary Components
- **Caller Info**: Name, phone (if provided)
- **Call Intent**: Primary reason for call
- **Issues Discussed**: Main topics covered
- **Escalation**: Whether call was transferred
- **Action Items**: Follow-up needed by staff
- **Sentiment**: Positive/Neutral/Negative

### Summary Format
```
Call Summary:
- Caller: [NAME or "Unknown"]
- Intent: [PURPOSE]
- Issues: [BRIEF DESCRIPTION]
- Escalated: [YES/NO]
- Actions: [STAFF ACTIONS NEEDED]
- Sentiment: [POSITIVE/NEUTRAL/NEGATIVE]
```