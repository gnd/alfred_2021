#!/usr/bin/env bash

export OKC_DISPLAY_HOST="127.0.0.1"
export OKC_DISPLAY_PORT=5000

export OKC_SPEECH_LANG="en-US"
export OKC_OUTPUT_SPEECH_LANG="cs-CZ"

export OKC_TRANSLATE_FROM_MAIN=
export OKC_MAIN_HAS_FULLSCREEN=
export OKC_TRANSLATION_FULLSCREEN=

cd text-display/

python3 display.py > /dev/null 2>&1 &
DISPLAY_PID=$!

cd ..

cd speech-loop/

python3 rt-translation.py > /dev/null 2>&1 &
TRANSLATION_PID=$!

cd ../questions/

python3 questions.py

kill -9 $TRANSLATION_PID
kill -9 $DISPLAY_PID

cd ..