#!/usr/bin/env bash

export OKC_DISPLAY_HOST="127.0.0.1"
export OKC_DISPLAY_PORT=5000

export OKC_SPEECH_LANG="en-US"
export OKC_OUTPUT_SPEECH_LANG="cs-CZ"
export OKC_ENGINE="davinci"

export OKC_TRANSLATE_FROM_MAIN=yes
export OKC_MAIN_HAS_FULLSCREEN=

cd text-display/

python3 display.py &
DISPLAY_PID=$!

cd ..

cd speech-loop/

python3 se.py

kill -9 $DISPLAY_PID

cd ..