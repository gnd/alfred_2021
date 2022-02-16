#!/usr/bin/env bash

export OKC_TRANSLATE_FROM_MAIN=
export OKC_MAIN_HAS_FULLSCREEN=
export OKC_TRANSLATION_FULLSCREEN=

cd text-display/

python3 display.py &
DISPLAY_PID=$!

cd ..

cd speech-loop/

python3 rt-translation.py &
TRANSLATION_PID=$!

python3 se.py


kill -9 $TRANSLATION_PID
kill -9 $DISPLAY_PID

cd ..