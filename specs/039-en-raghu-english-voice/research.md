# Research: en-raghu English Voice

The current voice CLI uses IndicF5 for every profile. Its released model card lists Indian-language support, while the owner requested English-only cloning. The previously reviewed local comparison used Chatterbox Turbo successfully with the same two reference takes and one English line. The model is available under an MIT license and accepts a short audio prompt without an exact reference transcript.

The tested local environment used `chatterbox-tts==0.1.7`, CPU `torch==2.6.0`, and `setuptools==80.10.2`. The older `perth` watermark package needs `pkg_resources`; pinning `setuptools<81` supplied it. Model files were held outside Git and loaded through `ChatterboxTurboTTS.from_local`.

Primary sources: [Chatterbox repository](https://github.com/resemble-ai/chatterbox), [Chatterbox Turbo model](https://huggingface.co/ResembleAI/chatterbox-turbo), [IndicF5 model](https://huggingface.co/ai4bharat/IndicF5).
