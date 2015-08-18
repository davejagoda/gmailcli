#!/usr/bin/python

import os, sys, imaplib, argparse

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help='add debug output', action='store_true')
    parser.add_argument('--count', help='provide counts', action='store_true')
    args = parser.parse_args()
    return(args)

def gmailLogin(debug=False):
    if debug: print('about to log in')
    u = os.getenv('GoogleDocsUserName')
    p = os.getenv('GoogleDocsPassWord')
    if u == None:
        print('set the GoogleDocsUserName environment variable')
        sys.exit(1)
    if p == None:
        print('set the GoogleDocsPassWord environment variable')
        sys.exit(1)
    m = imaplib.IMAP4_SSL('imap.gmail.com')
    m.login(u, p)
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
    m = gmailLogin(debug=args.debug)
    if args.count:
        messageCount = countMessages(m, debug=args.debug)
        print('{}'.format(messageCount))
    gmailLogout(m, debug=args.debug)
