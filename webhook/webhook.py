from flask import Flask, request
from utils.youtube_utils import hook_handler
from utils.logging_utils import setup_logger, unexpected_error_handler
from werkzeug.middleware.proxy_fix import ProxyFix

logger = setup_logger(__name__)
app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

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
