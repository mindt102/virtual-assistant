from google.auth.transport.requests import Request
from google.auth.exceptions import OAuthError
from google.auth import identity_pool
# from modules import utils
from utils.logging_utils import setup_logger
from config import *
import google.auth
import requests
import pickle
import json
import os

logger = setup_logger(__name__)
# Obtain a credential from the trusted identity provider.


def request_auth0_token():
    # if not os.path.exists(AUTH0_TOKEN_PATH):
    auth0_payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": AUTH0_AUDIENCE,
        "grant_type": "client_credentials",
    }

    auth0_headers = {'content-type': "application/json"}

    auth0_res = requests.post(
        f"{AUTH0_DOMAIN}/oauth/token", auth0_payload, auth0_headers)

    auth0_token = auth0_res.json()
    with open(AUTH0_TOKEN_PATH, "w") as f:
        json.dump(auth0_token, f)
    logger.info("Auth0 ID token created")

# Exchange the credential for a token from the Security Token Service.
# Use the token from the Security Token Service to obtain a short-lived Google access token
# Use the access token to impersonate a service account and call Google APIs


def get_googleapi_credentials():
    SCOPES = ["https://www.googleapis.com/auth/cloud-platform",
              "https://www.googleapis.com/auth/youtube.readonly",
              "https://www.googleapis.com/auth/calendar.events"]

    if not os.path.exists(AUTH0_TOKEN_PATH):
        request_auth0_token()

    credentials: identity_pool.Credentials = None
    if os.path.exists(GOOGLEAPI_TOKEN_PATH) and os.path.getsize(GOOGLEAPI_TOKEN_PATH) > 0:
        with open(GOOGLEAPI_TOKEN_PATH, "rb") as f:
            credentials = pickle.load(f)

    if not credentials or not credentials.valid:
        logger.info("Refreshing auth0 token")
        request_auth0_token()
        if credentials and credentials.expired:
            logger.info("Refreshing credentials")
            credentials.refresh(Request())
            # try:
            # except OAuthError:
            #     credentials.refresh
        else:
            credentials, project = google.auth.default(scopes=SCOPES)
            # try:
            # except OAuthError:
            #     logger.info("Refreshing auth0 token")
            #     request_auth0_token()
            #     credentials, project = google.auth.default(scopes=SCOPES)
        with open(GOOGLEAPI_TOKEN_PATH, "wb") as f:
            pickle.dump(credentials, f)
    return credentials
