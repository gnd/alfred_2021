#!/usr/bin/env bash

export OKC_TRANSLATE_FROM_MAIN=
export OKC_MAIN_HAS_FULLSCREEN=yes
export OKC_TRANSLATION_FULLSCREEN=yes

cd text-display/

export OKC_DISPLAY_PORT=3000
python3 display.py &
DISPLAY_1_PID=$!

export OKC_DISPLAY_PORT=5000
python3 display.py &
DISPLAY_2_PID=$!

cd ..

cd speech-loop/

export OKC_DISPLAY_PORT=3000
python3 rt-translation.py &
TRANSLATION_PID=$!

export OKC_DISPLAY_PORT=5000
python3 se.py


kill -9 $TRANSLATION_PID
kill -9 $DISPLAY_1_PID
kill -9 $DISPLAY_2_PID


cd ..