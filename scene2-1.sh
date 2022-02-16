#!/usr/bin/env bash

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