from fastapi import FastAPI, Request, status, Response, Form
from fastapi.responses import JSONResponse,  PlainTextResponse
# from twilio.twiml.voice_response import VoiceResponse, Dial
from context_compress import Compress_Context
import uvicorn
import logging_setup
# from twilio.rest import Client
# from twilio.twiml.messaging_response import MessagingResponse
import logging
# import os
# import plivo
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager


logging_setup.setup_config()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    logger.info("Application Initiated")
    app.state.call_mapping = {}
    app.state.message_mapping = {}
    app.state.call_middle = "+912268093856"
    app.state.call_agent = "" # -> agent number
    yield
    logger.info("Application Shutdown")


app = FastAPI(
    title="hive_mind",
    lifespan=lifespan
)



class History_Summarizer(BaseModel):
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use for summarization")
    temp: float = Field(default=1.0, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(default=200, description="Maximum number of tokens for summary")
    context: list = Field(..., description="Conversation content to summarize")


PLIVO_WHATSAPP_NUMBER = "whatsapp:+1234567890"



@app.post("/incoming_call")
async def incoming_call(request: Request):
    """
    handle incoming calls from users and the agent, routing them appropriately.

    workflow:
    1. if the caller is **not the agent** (i.e., a user):
       - store the user's phone number in `app.state.call_mapping["_user"]`.
       - set the call target to the agent (`app.state.call_agent`).
    2. if the caller **is the agent**:
       - retrieve the last user's number from `app.state.call_mapping["_user"]`.
       - if no user number is available, hang up the call.
       - otherwise, set the call target to the user.

    the endpoint returns a plivo-compatible xml `<response>` with a `<dial>` 
    element, specifying `callerid` as `app.state.call_middle` and the target number.

    returns:
        response: an xml response for plivo to execute the call routing.
                  - if no target is available, returns <hangup/>.
                  - otherwise, returns <dial> to the appropriate number.

    notes:
        - this endpoint relies on `app.state.call_mapping`, `app.state.call_agent`,
          and `app.state.call_middle` being initialized in the application lifespan.
        - supports one-to-one routing: agent to last user who called.
    """

    form = await request.form()
    from_number = form.get("From")

    if from_number != app.state.call_agent: # User -> Agent
        app.state.call_mapping["_user"] = from_number
        target =  app.state.call_agent
    else:
        target =  app.state.call_mapping.get("_user") # Agent -> User
        if not target:
            logger.warning("call cache not available")
            return Response("<Response><Hangup/></Response>", media_type="text/xml")

    logger.info("call triggered")
    xml = f"""
    <Response>
        <Dial callerId="{app.state.call_middle}">
            <Number>{target}</Number>
        </Dial>
    </Response>
    """
    print(target,"-------------------->")
    return Response(xml.strip(), media_type="text/xml")



# @app.post("/whatsapp", response_class=PlainTextResponse)
# async def whatsapp_webhook(
#     From: str = Form(...),
#     Body: str = Form(...),
#     To: str = Form(...)
# ):
#     """
#     Incoming message -> forward to agent
#     """

#     if From not in app.state.message_mapping:
#         target_number = "whatsapp:+1987654321"
#         app.state.message_mapping[From] = target_number
#     else:
#         target_number = app.state.message_mapping[From]

#     client.messages.create(
#         src=To,
#         dst=target_number,
#         text=Body
#     )

#     return ""


# @app.post("/whatsapp_reply", response_class=PlainTextResponse)
# async def whatsapp_reply(
#     From: str = Form(...),
#     Body: str = Form(...),
#     To: str = Form(...)
# ):
#     """
#     Agent reply -> forward back to original user
#     """

#     original_user = next(
#         (user for user, target in app.state.message_mapping.items() if target == From),
#         None
#     )

#     if original_user:
#         client.messages.create(
#             src=To,
#             dst=original_user,
#             text=Body
#         )

#     return ""


@app.post("/compress_context")
async def shorten_conversation_history(summarizer: History_Summarizer):
    try:
        compress = Compress_Context("prompt.yaml")
        condensed = compress.context_compressor_async(**summarizer.model_dump())

        if not condensed:
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                content={
                    "successful": False,
                    "summary": condensed
                }
            )
        return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "successful": True,
                    "summary": condensed
                }
            )
    except Exception as e:
        logger.error(f"error compressing context: {e}")
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "successful": True,
                    "summary": None
                }
            )

if __name__ == "__main__":
   uvicorn.run(app, host="127.0.0.1", port=8000)

