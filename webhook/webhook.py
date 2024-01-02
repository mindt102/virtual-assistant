from flask import Flask, request
from utils.youtube_utils import hook_handler
from utils.logging_utils import setup_logger, unexpected_error_handler

logger = setup_logger(__name__)
app = Flask(__name__)


@app.route('/')
def index():
    return "OK"


@app.route('/webhook/youtube', methods=['GET', 'POST'])
def youtube():
    if request.method == 'GET':
        try:
            challenge = request.args.get('hub.challenge')
            if challenge:
                logger.info(f"Received challenge: {challenge}")
                return challenge
        except Exception as e:
            unexpected_error_handler(
                logger, e, request_data=request.data, request_args=request.args)
    elif request.method == 'POST':
        try:
            hook_handler(request.data)
        except Exception as e:
            unexpected_error_handler(logger, e)
    else:
        logger.critical(f"Received invalid request: {request}")
    return 'Error'
