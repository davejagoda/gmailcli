#!/usr/bin/env python

import os, sys, imaplib, argparse
import oauth2client.client
import httplib2

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='add debug output', action='store_true')
    parser.add_argument('-c', '--count', help='provide counts', action='store_true')
    parser.add_argument('-t', '--tokenFile', help='OAuth token file')
    parser.add_argument('-u', '--username', required=True, help='IMAP username')
    args = parser.parse_args()
    return(args)

def gmailLogin(username, tokenFile=None, debug=False):
    m = imaplib.IMAP4_SSL('imap.gmail.com')
    if debug:
        print('about to log in')
        m.debug = 4
    if tokenFile:
        with open(tokenFile, 'r') as f:
            credentials = oauth2client.client.Credentials.new_from_json(f.read())
        if credentials.access_token_expired:
            if debug: print('access token expired, refreshing')
            credentials.refresh(httplib2.Http())
        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, credentials.access_token)
        if debug:
            print(auth_string)
        m.authenticate('XOAUTH2', lambda x: auth_string)
    else:
        password = os.getenv('GoogleDocsPassWord')
        if password == None:
            print('set the GoogleDocsPassWord environment variable')
            sys.exit(1)
        m.login(username, password)
    if debug: print('just logged in')
    return(m)

def countMessages(m, debug=False):
    status, response = m.select(readonly=True)
    assert 'OK' == status
    m.close()
    if debug: print(response)
    return(response[0])

def gmailLogout(m, debug=False):
    if debug: print('about to log out')
    m.logout()
    if debug: print('just logged out')

if '__main__' == __name__:
    args = parseArgs()
    m = gmailLogin(args.username, args.tokenFile, args.debug)
    if args.count:
        messageCount = countMessages(m, debug=args.debug)
        print('{}'.format(messageCount))
    gmailLogout(m, debug=args.debug)
