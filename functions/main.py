# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
from firebase_functions import firestore_fn, https_fn
from firebase_admin import initialize_app, firestore
import google.cloud.firestore
from flask import jsonify
import os
from openai import OpenAI
import logging

app = initialize_app()


@https_fn.on_request()
def addmessage(req: https_fn.Request) -> https_fn.Response:
    """Take the text parameter passed to this HTTP endpoint and insert it into
    a new document in the messages collection."""
    # Grab the text parameter.
    original = req.args.get("text")
    if original is None:
        return https_fn.Response("No text parameter", status=400)

    firestore_client: google.cloud.firestore.Client = firestore.client()

    # Push the new message into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("messages").add({"original": original})

    # Send back a message that we've successfully written the message
    return https_fn.Response(f"Message with ID {doc_ref.id} added.")

@https_fn.on_request()
def ask_OpenAI(req: https_fn.Request) -> https_fn.Response:
    inputMsg = req.args.get("input")
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
                {"role": "user", "content": inputMsg}
            ]
        )
        # # OpenAI API 호출 (예: text-davinci-003 모델 사용)
        # response = openai.Completion.create(
        #     engine="text-davinci-003",
        #     prompt=inputMsg,
        #     max_tokens=50,
        #     n=1,
        #     stop=None,
        #     temperature=0.7,
        # )
        # # 응답에서 텍스트 추출
       
        # content = completion["choices"][0]["message"]["content"]
        # return jsonify({"result": content})
        return jsonify({"result": completion.choices[0].message.content})
    
    except Exception as e:
        # 에러 발생 시 에러 메시지 반환
        logging.exception("Error occurred in ask_OpenAI")
        return (f"Error occurred: {str(e)}", 500)




@firestore_fn.on_document_created(document="messages/{pushId}")
def makeuppercase(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    """Listens for new documents to be added to /messages. If the document has
    an "original" field, creates an "uppercase" field containg the contents of
    "original" in upper case."""

    # Get the value of "original" if it exists.
    if event.data is None:
        return
    try:
        original = event.data.get("original")
    except KeyError:
        # No "original" field, so do nothing.
        return

    # Set the "uppercase" field.
    print(f"Uppercasing {event.params['pushId']}: {original}")
    upper = original.upper()
    event.data.reference.update({"uppercase": upper})



#     cd functions

# # Activate your local venv if you have one
# source venv/bin/activate

# # Check if openai is indeed installed
# pip show openai