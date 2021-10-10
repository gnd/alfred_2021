#!/usr/bin/env python3

"""The application entrypoint.
"""

import os
import fire
import signal
import configparser

def load_config():
    config = configparser.ConfigParser(interpolation=None)
    config.read("lizzie.cfg")   # hardcoded for now
    cookies = config.get('server', 'cookies').strip(';')

def main(port=5000, public=False):
    """The application entrypoint
    
    Args:
        port: The port number on which the application will listen.
            Listens on port 5000 if not specified.
        public: Optional argument, if specified the application will
            listen on all public IPs. Otherwise, it runs only locally.
    """

    from flask_server import start_server
    # from macaque_state import MacaqueState

    signal.signal(signal.SIGINT, handle_exit)

    # state = MacaqueState(public=public, config_dir=config_dir)
    start_server(port=port, public=public)

def handle_exit(signum, frame):
    """Quits the application.
    Args:
        signum: Signal number.
        frame: Current stack frame object.
    """

    exit(0)

if __name__ == "__main__":
    fire.Fire(main)