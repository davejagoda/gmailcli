#!/usr/bin/env python3

# https://developers.google.com/gmail/api/quickstart/python

import argparse
import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

def validateToken(clientSecrets, tokenFile, verbose):
    # If modifying these scopes, delete the tokenFile.
    SCOPES = ['https://mail.google.com/']
    creds = None
    # The tokenFile stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(tokenFile):
        if verbose:
            print('reading tokenFile')
        creds = Credentials.from_authorized_user_file(tokenFile, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            if verbose:
                print('refreshing token')
            creds.refresh(Request())
        else:
            if verbose:
                print('requesting user permissions')
            flow = InstalledAppFlow.from_client_secrets_file(
                clientSecrets, SCOPES)
            creds = flow.run_local_server(port=8000)
        # Save the credentials for the next run
        with open(tokenFile, 'w') as f:
            json.dump(json.loads(creds.to_json()), f, indent=4, sort_keys=True)
            f.write('\n')

if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='show verbose output')
    parser.add_argument('clientSecrets',
                        help='file containing clientSecrets in JSON format')
    parser.add_argument('tokenFile',
                        help='file containing token in JSON format')
    args = parser.parse_args()
    validateToken(args.clientSecrets, args.tokenFile, args.verbose)
