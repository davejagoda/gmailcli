#!/usr/bin/env python

import argparse
import datetime
import dateutil.parser
import email
import httplib2
import imaplib
import oauth2client.client
import os
import sys
import termios
import time
import tty

EPOCH = dateutil.parser.parse('1970-01-01 00:00:00 +0000')

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='count', help='debug output')
    parser.add_argument('-u', '--username', required=True, help='IMAP username')
    parser.add_argument('-t', '--tokenFile', help='OAuth token file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--before', help='[Gmail]/All Mail counts before CCYY-MM-DD')
    group.add_argument('-o', '--on', help='[Gmail]/All Mail counts on CCYY-MM-DD')
    group.add_argument('-s', '--since', help='[Gmail]/All Mail counts since CCYY-MM-DD')
    group.add_argument('-m', '--mailboxes', action='store_true', help='list mailboxes')
    group.add_argument('-i', '--interactiveDelete', help='ask to delete messages from this folder one by one')
    group.add_argument('-e', '--envelopes', help='print all envelope data from this folder')
    group.add_argument('-f', '--flags', help='print all flags from this folder')
    group.add_argument('-a', '--append', help='append this file to the INBOX')
    args = parser.parse_args()
    return(args)

def gmailLogin(username, tokenFile=None, debug=0):
    m = imaplib.IMAP4_SSL('imap.gmail.com')
    if debug:
        print('about to log in')
        m.debug = debug # setting to 4 seems quite verbose
    if tokenFile:
        with open(tokenFile, 'r') as f:
            credentials = oauth2client.client.Credentials.new_from_json(f.read())
        if credentials.access_token_expired:
            if debug: print('access token expired, refreshing')
            credentials.refresh(httplib2.Http())
        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, credentials.access_token)
        if debug: print(auth_string)
        m.authenticate('XOAUTH2', lambda x: auth_string)
    else:
        password = os.getenv('GoogleDocsPassWord')
        if password == None:
            print('set the GoogleDocsPassWord environment variable')
            sys.exit(1)
        m.login(username, password)
    if debug: print('just logged in')
    return(m)

def countBefore(m, before, debug=0):
    status, response = m.select('[Gmail]/All Mail', readonly=True)
    if debug: print(response)
    assert('OK' == status)
    d = datetime.datetime.strptime(before, '%Y-%m-%d')
    searchstring = '(before "{}")'.format(d.strftime('%d-%b-%Y'))
    if debug: print(searchstring)
    status, response = m.search(None, searchstring)
    if debug: print(response)
    assert('OK' == status)
    assert(1 == len(response))
    return(len(response[0].split()))

def countOn(m, on, debug=0):
    status, response = m.select('[Gmail]/All Mail', readonly=True)
    if debug: print(response)
    assert('OK' == status)
    d = datetime.datetime.strptime(on, '%Y-%m-%d')
    searchstring = '(on "{}")'.format(d.strftime('%d-%b-%Y'))
    if debug: print(searchstring)
    status, response = m.search(None, searchstring)
    if debug: print(response)
    assert('OK' == status)
    assert(1 == len(response))
    return(len(response[0].split()))

def countSince(m, since, debug=0):
    status, response = m.select('[Gmail]/All Mail', readonly=True)
    if debug: print(response)
    assert('OK' == status)
    d = datetime.datetime.strptime(since, '%Y-%m-%d')
    searchstring = '(since "{}")'.format(d.strftime('%d-%b-%Y'))
    if debug: print(searchstring)
    status, response = m.search(None, searchstring)
    if debug: print(response)
    assert('OK' == status)
    assert(1 == len(response))
    return(len(response[0].split()))

def countMessages(m, mailbox, debug=0):
    status, response = m.select(mailbox, readonly=True)
    if debug: print(response)
    assert('OK' == status)
    return(response[0])

def listMailboxes(m, debug=0):
    mailboxes = []
    status, response = m.list()
    assert('OK' == status)
    if debug: print(response)
    assert(list == type(response))
    for mailbox in response:
        assert(str == type(mailbox))
        if debug: print(mailbox)
        if '\Noselect' not in mailbox.split('"')[0]:
            mailboxes.append(mailbox.split('"')[-2])
    return(mailboxes)

def interactiveDelete(m, mailbox, debug=0):
    fd = sys.stdin.fileno()
    saveTCGetAttr = termios.tcgetattr(fd)
    status, response = m.select(mailbox, readonly=False)
    if debug: print(response)
    if 'OK' != status:
        return('mailbox not found')
    status, response = m.uid('search', None, 'ALL')
    assert('OK' == status)
    assert(type(response == list))
    assert(1 == len(response))
    message_count = 0
    delete_count = 0
    for msg_uid in response[0].split():
        message_count +=1
        status, response = m.uid('FETCH', msg_uid, '(RFC822)')
        assert('OK' == status)
        if debug: print('msgUID:{} len:{}'.format(msg_uid,len(response)))
        assert(type(response) == list)
        assert(2 <= len(response))
        assert(type(response[0]) == tuple)
        assert(2 <= len(response[0]))
        (imap_data, message_data) = response[0]
        headers = email.message_from_string(message_data)
        print(response)
        print(imap_data)
        print('To: {}'.format(headers['to']))
        print('From: {}'.format(headers['from']))
        print('Subject: {}'.format(headers['subject']))
        print 'Delete? (y/n/q): ',
        tty.setraw(fd)
        user_input = sys.stdin.read(1)
        termios.tcsetattr(fd, termios.TCSADRAIN, saveTCGetAttr)
        print(user_input)
        if 'y' == user_input:
            print m.uid('STORE', msg_uid, '+FLAGS', '(\\Deleted)')
            delete_count += 1
        if 'q' == user_input:
            break
        if 0 < delete_count and 0 == delete_count % 10:
            print m.expunge()
            print('\nexpunged!\n')
    if 0 < delete_count and 0 != delete_count % 10:
        print m.expunge()
        print('\nexpunged!\n')
    m.close()
    return([message_count, delete_count])

def envelopes(m, mailbox, debug=0):
    status, response = m.select(mailbox, readonly=True)
    if debug: print(response)
    if 'OK' != status:
        return('mailbox not found')
    status, response = m.uid('search', None, 'ALL')
    assert('OK' == status)
    assert(type(response == list))
    assert(1 == len(response))
    message_count = 0
    delete_count = 0
    for msg_uid in response[0].split():
        message_count +=1
        status, response = m.uid('FETCH', msg_uid, '(ENVELOPE)')
        assert('OK' == status)
        print(response)

def flags(m, mailbox, debug=0):
    status, response = m.select(mailbox, readonly=True)
    if debug: print(response)
    if 'OK' != status:
        return('mailbox not found')
    status, response = m.uid('search', None, 'ALL')
    assert('OK' == status)
    assert(type(response == list))
    assert(1 == len(response))
    message_count = 0
    delete_count = 0
    for msg_uid in response[0].split():
        message_count +=1
        status, response = m.uid('FETCH', msg_uid, '(FLAGS)')
        assert('OK' == status)
        print(response)

def append(m, filename, debug=0):
    with open(filename, 'rb') as f:
        msg = f.read()
    date_from_message = email.message_from_string(msg)['date']
    if None == date_from_message:
        date_time = imaplib.Time2Internaldate(time.time())
    else:
        date_time = imaplib.Time2Internaldate(
            (dateutil.parser.parse(date_from_message) - EPOCH).total_seconds())
    if debug: print(date_from_message, date_time)
    status, response = m.append('INBOX', '', date_time, msg)

def gmailLogout(m, debug=0):
    if debug: print('about to log out')
    m.logout()
    if debug: print('just logged out')

if '__main__' == __name__:
    args = parseArgs()
    m = gmailLogin(args.username, args.tokenFile, debug=args.debug)
    if args.before:
        print('{} messages before {}'.format(countBefore(m, args.before, debug=args.debug), args.before))
    if args.on:
        print('{} messages on {}'.format(countOn(m, args.on, debug=args.debug), args.on))
    if args.since:
        print('{} messages since {}'.format(countSince(m, args.since, debug=args.debug), args.since))
    if args.mailboxes:
        mailboxes = listMailboxes(m, debug=args.debug)
        for mailbox in mailboxes:
            message_count = countMessages(m, mailbox, debug=args.debug)
            print('{}:{}'.format(mailbox, message_count))
    if args.interactiveDelete:
        (message_count, delete_count) = interactiveDelete(m, args.interactiveDelete, debug=args.debug)
        print('messages processed:{} messages deleted:{}'.format(message_count, delete_count))
    if args.envelopes:
        envelopes(m, args.envelopes, debug=args.debug)
    if args.flags:
        flags(m, args.flags, debug=args.debug)
    if args.append:
        append(m, args.append, debug=args.debug)
    gmailLogout(m, debug=args.debug)
