#!/usr/bin/env python

import argparse
import base64
import httplib2
import oauth2client.client
import os
import sys
import smtplib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='count', help='add debug output')
    parser.add_argument('-u', '--username', required=True, help='SMTP username')
    parser.add_argument('-t', '--tokenFile', help='OAuth token file')
    parser.add_argument('-r', '--recipients', required=True,
                        help='recipient address[es], separated by commas')
    parser.add_argument('-s', '--subject', required=True, help='email subject')
    parser.add_argument('-b', '--body', required=True, help='message body')
    args = parser.parse_args()
    return(args)

def gmailLogin(username, tokenFile=None, debug=0):
    m = smtplib.SMTP_SSL('smtp.gmail.com')
    if debug:
        print('about to log in')
        m.set_debuglevel(debug) # setting to 4 seems quite verbose
    if tokenFile:
        with open(tokenFile, 'r') as f:
            credentials = oauth2client.client.Credentials.new_from_json(f.read())
        if credentials.access_token_expired:
            if debug: print('access token expired, refreshing')
            credentials.refresh(httplib2.Http())
        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, credentials.access_token)
        if debug: print(auth_string)
        m.ehlo()
        m.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(auth_string))
    else:
        password = os.getenv('GoogleDocsPassWord')
        if password == None:
            print('set the GoogleDocsPassWord environment variable')
            sys.exit(1)
        m.login(username, password)
    if debug: print('just logged in')
    return(m)

def gmailLogout(m, debug=0):
    if debug: print('about to log out')
    m.quit()
    if debug: print('just logged out')

def gmailSend(m, fromaddr, toaddrs, subject, body, debug=0):
    msg = 'From: {}\r\nTo: {} \r\nSubject: {}\r\n\r\n{}'.format(
        fromaddr, toaddrs, subject, body)
    m.sendmail(fromaddr, toaddrs, msg)

if '__main__' == __name__:
    args = parseArgs()
    m = gmailLogin(args.username, args.tokenFile, debug=args.debug)
    gmailSend(m, args.username, args.recipients, args.subject, args.body)
    gmailLogout(m, debug=args.debug)
