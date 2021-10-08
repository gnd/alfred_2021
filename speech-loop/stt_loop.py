import fire
from google.cloud import speech

from microphone_stream import MicrophoneStream

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

def processMicrophoneStream(speech_lang, responses_cb=None):
    """Opens a microphone stream, transcribing recorder speech.
    
    Speech is transcribed using Google Cloud's Speech-to-text API.
    This function blocks as long as audio is recorded.

    Args:
        speech_lang (str): BCP-47 language code of the spoken language.
        response_cb (func): Function invoked for each response returned
            by the API. 
    
    """
    
    client = speech.SpeechClient()
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=speech_lang,
        # alternative_language_codes=alternative_language_codes - TODO: solve how to call beta API
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        # For response type details, see:
        # https://googleapis.dev/python/speech/latest/speech_v1/types.html#google.cloud.speech_v1.types.StreamingRecognizeResponse
        responses = client.streaming_recognize(streaming_config, requests)

        if not responses_cb:
            print(responses)
        else:
            responses_cb(responses)


def main(speech_lang):
    processMicrophoneStream(speech_lang)


if __name__ == "__main__":
    fire.Fire(main)