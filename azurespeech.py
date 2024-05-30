import azure.cognitiveservices.speech as speechsdk
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Creates an instance of a speech config with specified subscription key and service region.
# Replace with your own subscription key and service region (e.g., "westus").
speech_key = getenv("AZURE")
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region="westus")
speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"

# Creates a recognizer with the given settings
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

# print("Say something...")
ds = 0


def start_speaking(*args, **kwargs) -> None:
    global ds
    ds += 1


def done_speaking(*args, **kwargs):
    global ds
    ds = 0


# speech_synthesizer.synthesizing.connect(lambda _: print(f"Synthesizing {_}"))

speech_synthesizer.synthesis_started.connect(start_speaking)
speech_synthesizer.synthesis_completed.connect(done_speaking)


def speech_to_text() -> str | None:
    result = speech_recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return
    elif result.reason == speechsdk.ResultReason.Canceled:
        return


# def text_to_speech(text: str) -> None:
#     result = speech_synthesizer.speak_text_async(text).get()
#     if result.reason == speechsdk.ResultReason.Canceled:
#         cancellation_details = result.cancellation_details
#         print("Speech synthesis canceled: {}".format(cancellation_details.reason))
#         if cancellation_details.reason == speechsdk.CancellationReason.Error:
#             print("Error details: {}".format(cancellation_details.error_details))


def text_to_speech(text: str) -> None:
    speed = 0
    ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-CA"><voice name="{speech_config.speech_synthesis_voice_name}"><prosody rate="+{speed}%">{text}</prosody></voice></speak>"""

    try:
        result = speech_synthesizer.start_speaking_ssml_async(
            ssml
        ).get()  # TODO: be able to stop the speech mid-sentence

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
    except KeyboardInterrupt:
        speech_synthesizer.stop_speaking()


if __name__ == "__main__":
    text_to_speech("Hello! I am working.")

# Starts speech recognition, and returns after a single utterance is recognized. The end of a
# single utterance is determined by listening for silence at the end or until a maximum of 15
# seconds of audio is processed.  The task returns the recognition text as result.
# Note: Since recognize_once() returns only a single utterance, it is suitable only for single
# shot recognition like command or query.
# For long-running multi-utterance recognition, use start_continuous_recognition() instead.
# result = speech_recognizer.recognize_once()

# # Checks result.
# if result.reason == speechsdk.ResultReason.RecognizedSpeech:
#     print("Recognized: {}".format(result.text))
# elif result.reason == speechsdk.ResultReason.NoMatch:
#     print("No speech could be recognized: {}".format(result.no_match_details))
# elif result.reason == speechsdk.ResultReason.Canceled:
#     cancellation_details = result.cancellation_details
#     print("Speech Recognition canceled: {}".format(cancellation_details.reason))
#     if cancellation_details.reason == speechsdk.CancellationReason.Error:
#         print("Error details: {}".format(cancellation_details.error_details))
