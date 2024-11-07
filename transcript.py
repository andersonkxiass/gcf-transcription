import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import speech

service_account = os.path.abspath("serviceAccountKey.json")

cred = credentials.Certificate(service_account)
firebase_admin.initialize_app(cred)


def transcript(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    gcs_file_name = file['name']
    file_name, type_extension = gcs_file_name.split(".")

    db = firestore.client()

    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=f"gs://audionote-transcribe-audio/{gcs_file_name}")

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=32000,
        language_code="pt-BR",
        audio_channel_count=1,
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    doc_ref = db.collection(u'transcriptions').document(file_name)

    try:
        print("Waiting for operation to complete...")
        response = operation.result()

        results = []

        for result in response.results:
            words = []

            for word in result.alternatives[0].words:
                words.append({
                    "word": word.word,
                    "start_time": word.start_time.seconds,
                    "end_time": word.end_time.seconds,
                    "confidence": word.confidence
                })

            results.append(
                {
                    "transcript": result.alternatives[0].transcript,
                    "confidence": result.alternatives[0].confidence,
                    "words": words,
                    "result_end_time": result.result_end_time.seconds,
                    "channel_tag": result.channel_tag,
                    "language_code": result.language_code
                }
            )

        doc_ref.update({
            u'status': u"FINISH_SUCCESS",
            u'text': results,
            u'transcript_endtime': firestore.firestore.SERVER_TIMESTAMP
        })

    except Exception as e:
        print(e)
        doc_ref.update({
            u'status': u"FINISH_FAIL",
            u'message': str(e),
        })


if __name__ == "__main__":
    param = {
        "name": "media-8be00f37-a010-4ca9-ad1e-3c3cc238ac81.wav",
    }

    transcript(param, None)
