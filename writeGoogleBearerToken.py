#!/usr/bin/env python

import os, argparse, json, webbrowser
import oauth2client.client

OAUTH2_SCOPE = 'https://mail.google.com/'

def promptForCode(clientSecrets):
    flow = oauth2client.client.flow_from_clientsecrets(clientSecrets, OAUTH2_SCOPE)
    flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
    authorize_url = flow.step1_get_authorize_url()
    webbrowser.open(authorize_url)
    code = raw_input('paste in returned code here: ')
    return(flow.step2_exchange(code))

def writeToken(token, filename):
    with open(filename, 'w') as f:
        f.write(json.dumps(token, indent=4, sort_keys=True))

if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='show verbose output')
    parser.add_argument('clientSecrets', help='file containing clientSecrets in JSON format')
    parser.add_argument('tokenFile', help='file containing token in JSON format')
    args = parser.parse_args()
    token = promptForCode(args.clientSecrets)
    if args.verbose:
        print('token={}'.format(json.dumps(json.loads(token.to_json()), indent=4, sort_keys=True)))
    writeToken(json.loads(token.to_json()), args.tokenFile)
