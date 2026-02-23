from __future__ import annotations

import azure.cognitiveservices.speech as speechsdk


def create_push_stream(sample_rate: int = 16000):
    stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=sample_rate, bits_per_sample=16, channels=1)
    push_stream = speechsdk.audio.PushAudioInputStream(stream_format=stream_format)
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
    return push_stream, audio_config


def create_recognizer(
    audio_config,
    subscription: str,
    region: str,
    language: str = "en-US",
    silence_timeout_ms: str | None = None,
):
    speech_config = speechsdk.SpeechConfig(subscription=subscription, region=region)
    speech_config.speech_recognition_language = language
    if silence_timeout_ms is not None:
        speech_config.set_property(
            speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
            str(silence_timeout_ms),
        )
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    return recognizer
