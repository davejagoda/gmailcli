#!/usr/bin/env python3

import json
from google.auth.transport.requests import Request

def refreshToken(tokenFile, credentials):
    credentials.refresh(Request())
    with open(tokenFile, 'r') as f:
        old_token = json.load(f)
    new_token = old_token
    new_token['token'] = credentials.token
    new_token['expiry'] = f'{credentials.expiry.isoformat()}Z'
    with open(tokenFile, 'w') as f:
        json.dump(new_token, f, indent=4, sort_keys=True)
        f.write('\n')

if '__main__' == __name__:
    print('gmail_lib called directly')
