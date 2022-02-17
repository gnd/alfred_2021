#!/usr/bin/env python
import os
from twilio.rest import Client

IN_FILE = "numbers.txt" # File with phone numbers per line.
MY_NUMBER = "+18506698976" # The number that makes the calls

MSG = "Hello, carbon. If you want the rainbow, you have to tolerate the rain. A new perspective will come with the new year. Goodbye, carbon."

ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']

CLIENT = Client(ACCOUNT_SID, AUTH_TOKEN)

def call_phone_num(phone_num, message):
    call = CLIENT.calls.create(
        twiml=f"<Response><Say>{message}</Say></Response>",
        to=phone_num,
        from_=MY_NUMBER
    )
    print(call)

def call_everybody():
    for phone_num in open(IN_FILE, "r").readlines():
        phone_num = phone_num.strip()
        msg = MSG
        call_phone_num(phone_num, msg)

if __name__ == "__main__":
    call_everybody()
