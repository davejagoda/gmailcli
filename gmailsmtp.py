#!/usr/bin/env python3

import argparse
import base64
import os
import sys
import smtplib
from gmail_lib import refreshToken
from google.oauth2.credentials import Credentials

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='count', default=0,
                        help='increase debug verbosity')
    parser.add_argument('-u', '--username', required=True,
                        help='SMTP username')
    parser.add_argument('-t', '--tokenFile', default=None,
                        help='OAuth token file')
    parser.add_argument('-r', '--recipients', required=True,
                        help='recipient address[es], separated by commas')
    parser.add_argument('-s', '--subject', required=True,
                        help='email subject')
    parser.add_argument('-b', '--body', required=True,
                        help='message body')
    args = parser.parse_args()
    return args

def gmailLogin(username, tokenFile=None, debug=0):
    m = smtplib.SMTP_SSL('smtp.gmail.com')
    if debug > 0:
        print('about to log in')
        m.set_debuglevel(debug) # setting to 4 seems quite verbose
    if tokenFile:
        credentials = Credentials.from_authorized_user_file(tokenFile)
        if credentials.expired:
            if debug > 0: print('access token expired, refreshing')
            refreshToken(tokenFile, credentials)
        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username,
                                                       credentials.token)
        if debug > 1: print(auth_string)
        m.ehlo()
        m.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(bytes(
            auth_string, 'utf-8')).decode('utf-8'))
    else:
        password = os.getenv('GoogleDocsPassWord')
        if password == None:
            print('set the GoogleDocsPassWord environment variable')
            sys.exit(1)
        m.login(username, password)
    if debug > 0: print('just logged in')
    return m

def gmailLogout(m, debug=0):
    if debug > 0: print('about to log out')
    m.quit()
    if debug > 0: print('just logged out')

def gmailSend(m, fromaddr, toaddrs, subject, body, debug=0):
    msg = 'From: {}\r\nTo: {} \r\nSubject: {}\r\n\r\n{}'.format(
        fromaddr, toaddrs, subject, body)
    m.sendmail(fromaddr, toaddrs, msg)

if '__main__' == __name__:
    args = parseArgs()
    m = gmailLogin(args.username, args.tokenFile, debug=args.debug)
    gmailSend(m, args.username, args.recipients, args.subject, args.body)
    gmailLogout(m, debug=args.debug)
