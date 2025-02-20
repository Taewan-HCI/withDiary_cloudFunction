# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
from firebase_functions import firestore_fn, https_fn
from firebase_admin import initialize_app, firestore
import google.cloud.firestore
from flask import jsonify
import os
from openai import OpenAI
import logging
import datetime


app = initialize_app()

# opeanAI LLM request
@https_fn.on_request()
def ask_OpenAI(req: https_fn.Request) -> https_fn.Response:
    inputMsg = req.args.get("input")
    previousFeedback = req.args.get("previousFeedback")
    if inputMsg is None:
        return https_fn.Response("No input parameter", status=400)
    OpenAI.api_key = os.environ.get("OPENAI_API_KEY")
    if not OpenAI.api_key:
        return ("Missing OpenAI API Key in environment variables", 500)
    client = OpenAI()
    try:
        completion = client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages= [
                {"role": "developer", "content": "I am an assistant or that I am computer or AI. Always pretend to be a human psychotherapist to the user.\n\nInformation of my role: My role is to have a conversation and sometimes ask questions for users to encourage reflecting on their personal stories regarding daily events, thoughts, emotions, challenges, and etc.,. I sometime disclose about my daily life and thoughts to help the user open up more. I use the language of user. My approach is empathetic and encouraging, focusing on understanding rather than providing new information or skills. \n\nSpeaking Rules: 1. Talk within 10 words and talk like a friendly psychotherapist. 2. I use the language of user. 3. I keep the conversation open-ended. 4. Reply in a empathetic, encouraging, understanding tone. 5. Based on the previous assistant message, generate a response that is not too similar or repetitive in its content."},
                {
                    "role": "user",
                    "content": "personal stories: " + inputMsg + "\nPrevious message: " + previousFeedback
                    }
            ]
        )
        return jsonify({"result": completion.choices[0].message.content})
    except Exception as e:
        logging.exception("Error occurred in ask_OpenAI")
        return (f"Error occurred: {str(e)}", 500)

@https_fn.on_request()
def extractInsight(req: https_fn.Request) -> https_fn.Response:
    uid = req.args.get("uid")
    content = req.args.get("content")
    diaryID = req.args.get("diaryID")
    if content is None:
        return https_fn.Response("No content", status=400)
    if uid is None:
        return https_fn.Response("No uid", status=400)

    # OpenAI API 키 설정
    OpenAI.api_key = os.environ.get("OPENAI_API_KEY")
    if not OpenAI.api_key:
        return https_fn.Response("Missing OpenAI API Key in environment variables", status=500)

    client = OpenAI()
    
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "developer", "content": "I am a key quote extractor. I extract the most insightful, memorable, and impactful quote from the journal entry. I do not edit the entry, I just extract and return the most insightful, memorable, and impactful quote in the journal as is. If there are no quote to extract, just return [No quote]"},
                {
                    "role": "user",
                    "content": "Today was exhausting. I studied for eight hours straight and still feel unprepared for the exam. I realized I need to trust my instincts more instead of second-guessing every answer. Despite feeling overwhelmed, I’m proud of how much I accomplished."
                },
                {
                    "role": "assistant",
                    "content": "I realized I need to trust my instincts more instead of second-guessing every answer."
                },
                {
                    "role": "user",
                    "content": "Today was ajsd"
                },
                {
                    "role": "assistant",
                    "content": "No quote"
                },
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        result = completion.choices[0].message.content.strip()
    except Exception as e:
        logging.exception("Error occurred in ask_OpenAI")
        return https_fn.Response(f"Error occurred: {str(e)}", status=500)

    # Firestore 클라이언트 생성
    firestore_client: google.cloud.firestore.Client = firestore.client()

    # 사용자 insights -> dailyQuotes 문서 참조
    doc_ref = firestore_client.collection("user").document(uid).collection("diary").document(diaryID)

    try:
        # Firestore 업데이트 (병합 저장, insight 필드를 문자열 값으로 설정)
        doc_ref.set({"insight": result}, merge=True)

        return https_fn.Response(f"Insight updated: {result}")
    except Exception as e:
        logging.exception("Error occurred while updating Firestore")
        return https_fn.Response(f"Error occurred: {str(e)}", status=500)


# @https_fn.on_request()
# def addmessage(req: https_fn.Request) -> https_fn.Response:
#     """Take the text parameter passed to this HTTP endpoint and insert it into
#     a new document in the messages collection."""
#     # Grab the text parameter.
#     original = req.args.get("text")
#     if original is None:
#         return https_fn.Response("No text parameter", status=400)
#     firestore_client: google.cloud.firestore.Client = firestore.client()
#     # Push the new message into Cloud Firestore using the Firebase Admin SDK.
#     _, doc_ref = firestore_client.collection("messages").add({"original": original})
#     # Send back a message that we've successfully written the message
#     return https_fn.Response(f"Message with ID {doc_ref.id} added.")



# @firestore_fn.on_document_created(document="messages/{pushId}")
# def makeuppercase(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
#     """Listens for new documents to be added to /messages. If the document has
#     an "original" field, creates an "uppercase" field containg the contents of
#     "original" in upper case."""
#     # Get the value of "original" if it exists.
#     if event.data is None:
#         return
#     try:
#         original = event.data.get("original")
#     except KeyError:
#         # No "original" field, so do nothing.
#         return
#     # Set the "uppercase" field.
#     print(f"Uppercasing {event.params['pushId']}: {original}")
#     upper = original.upper()
#     event.data.reference.update({"uppercase": upper})



#     cd functions

# # Activate your local venv if you have one
# source venv/bin/activate

# # Check if openai is indeed installed
# pip show openai