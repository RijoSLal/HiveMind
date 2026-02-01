# Hotelzify

## Important Notice Regarding Repository Changes

### Removal of Conversational System

Recent changes to this repository. **We have removed the conversational system component** from the codebase as it inadvertently resembled too much of Hotelzify's proprietary technology. As a company, we cannot risk exposing our core intellectual property, even in a hackathon context.

### What This Means

- ⚠️ The conversational AI engine code is no longer available in this repository
- ✅ **All remaining functionality is fully operational** and can be used without any issues
- ✅ **We have decoupled all proprietary-resembling technology** from the public repository
- ✅ **The hackathon evaluation team still has access** to interact with the complete system through our hosted demo environment

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      HIVE_MIND                                  │
└─────────────────────────────────────────────────────────────────┘

     ┌──────────┐                              ┌──────────────┐
     │ Twilio   │                              │ Web/Mobile   │
     │ Voice    │                              │ Interface    │
     └────┬─────┘                              └──────┬───────┘
          │                                           │
          │ Phone Calls                               │ Chat Messages
          ▼                                           ▼
    ┌─────────────────┐                      ┌─────────────────┐
    │      TTS        │                      │   Chat Agent    │
    │ Text-to-Speech  │                      │  (GPT-based)    │
    └────────┬────────┘                      └────────┬────────┘
             │                                        │
             ▼                                        │
    ┌────────────────────────────┐                   │
    │  Voice AI Agent            │                   │
    │  (OpenAI GPT-based)        │                   │
    └────────┬───────────────────┘                   │
             │                                        │
             └────────────┬───────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    ┌───────────┐   ┌───────────┐   ┌──────────┐
    │  Qdrant   │   │  MongoDB  │   │   TTS    │
    │ Vector DB │   │           │   │ Response │
    │ (Shared)  │   │ (Shared)  │   │          │
    └───────────┘   └───────────┘   └──────────┘
         │               │                │
         │ Retrieval     │ Storage        │
         └───────────────┴────────────────┘
```

### Architecture Components

#### 1. **Twilio Integration**
- Handles incoming and outgoing phone calls
- Manages call routing and webhook events
- Provides telephony infrastructure

#### 2. **Web/Mobile Interface**
- Provides chat-based customer interaction
- WebSocket connection for real-time messaging
- Accessible via web browsers and mobile apps

#### 3. **Voice AI Agent** *(Removed from Repository)*
- **Status**: Proprietary technology - not included in this repository
- **Function**: Processes customer queries via phone, manages conversation flow
- **Access**: Available through hosted demo for evaluation team
- Built on OpenAI GPT Agents

#### 4. **Chat Agent** *(Removed from Repository)*
- **Status**: Proprietary technology - not included in this repository
- **Function**: Processes customer queries via text chat, manages conversation flow
- **Access**: Available through hosted demo for evaluation team
- Built on OpenAI GPT Agents
- Shares the same knowledge base and data access as Voice AI Agent

#### 5. **Qdrant Vector Database** *(Shared Resource)*
- Stores hotel information, amenities, and policies as vector embeddings
- Enables semantic search for relevant information retrieval
- Used by both Voice and Chat agents for context-aware responses

#### 6. **MongoDB** *(Shared Resource)*
- Stores structured data (bookings, customer info, hotel details)
- Manages transactional records and session state
- Shared data layer for both Voice and Chat channels

---

## Data Flow

### Voice Channel
```
User Call → Twilio → Speech-to-Text → Voice AI Agent → Vector Search (Qdrant)
                                            ↓
                                      MongoDB Query
                                            ↓
                                    Response Generation
                                            ↓
                                   Text-to-Speech (OpenAI)
                                            ↓
                                        Twilio → User
```

### Chat Channel
```
User Message → Web/Mobile → Chat Agent → Vector Search (Qdrant)
                                ↓
                          MongoDB Query
                                ↓
                        Response Generation
                                ↓
                          Web/Mobile → User
```

---

## For Hackathon Evaluation Team

### Demo Access

We understand the importance of evaluating the complete system. The evaluation team has been granted access to:

1. **Hosted Demo Environment**: Fully functional instance with all features (Voice + Chat)
2. **API Documentation**: Complete API reference for integration testing
3. **Test Phone Numbers**: Twilio numbers configured for testing calls
4. **Chat Interface**: Web-based chat demo for testing text interactions

## Multi-Channel Support

HiveMind now supports **two channels** for customer interaction:

- 📞 **Voice**: Traditional phone calls via Twilio
- 💬 **Chat**: Text-based messaging via web/mobile interface

Both channels share the same:
- Knowledge base (Qdrant vector database)
- Customer data (MongoDB)
- AI processing capabilities
- Business logic and hotel information

This ensures a **consistent experience** regardless of how customers choose to interact with the system.

**Our commitment to the hackathon:**
- All promised functionality remains accessible through our hosted demo
- The evaluation team has full access to test and verify our solution (both voice and chat)

- We're happy to answer questions and provide additional documentation

## Acknowledgments

Thank you for your understanding and for the opportunity to participate in this hackathon. We believe in open collaboration while also protecting the innovations that make our business viable.

**Team Hotelzify** 🏨

