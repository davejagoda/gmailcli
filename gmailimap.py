#!/usr/bin/env python
from __future__ import print_function
import argparse
import datetime
import dateutil.parser
import dateutil.tz
import email
import httplib2
import imaplib
import oauth2client.client
import os
import re
import sys
import termios
import time
import tty

EPOCHSTR = '1970-01-01 00:00:00 +0000'
EPOCH = dateutil.parser.parse(EPOCHSTR)
TZINFOS = {
    'EDT': dateutil.tz.gettz('America/New_York'),
    'EST': dateutil.tz.gettz('America/New_York')
}

def dt_is_naive(dt):
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return(True)
    return(False)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='count', default=0,
                        help='debug output')
    parser.add_argument('-m', '--mailbox', default='[Gmail]/All Mail',
                        help='name of mailbox to use')
    parser.add_argument('-t', '--tokenFile', default=None,
                        help='OAuth token file')
    parser.add_argument('-u', '--username', required=True, help='IMAP username')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--before', help='counts before CCYY-MM-DD')
    group.add_argument('-o', '--on', help='counts on CCYY-MM-DD')
    group.add_argument('-s', '--since', help='counts since CCYY-MM-DD')
    group.add_argument('-l', '--list', action='store_true',
                       help='list mailboxes')
    group.add_argument('-c', '--copy', action='store_true',
                       help='copy messages to Maildir compatible filenames')
    group.add_argument('-i', '--interactiveDelete', action='store_true',
                       help='ask to delete messages one by one')
    group.add_argument('-e', '--envelopes', action='store_true',
                       help='print all envelope data')
    group.add_argument('-f', '--flags', action='store_true',
                       help='print all flags')
    group.add_argument('-a', '--append', help='append this file')
    args = parser.parse_args()
    return(args)

def gmailLogin(username, tokenFile, debug):
    m = imaplib.IMAP4_SSL('imap.gmail.com')
    if debug > 0:
        print('about to log in')
        m.debug = debug # setting to 4 seems quite verbose
    if tokenFile:
        with open(tokenFile, 'r') as f:
            credentials = oauth2client.client.Credentials.new_from_json(
                f.read())
        if credentials.access_token_expired:
            if debug > 0: print('access token expired, refreshing')
            credentials.refresh(httplib2.Http())
        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username,
                                                       credentials.access_token)
        if debug > 1: print(auth_string)
        m.authenticate('XOAUTH2', lambda x: auth_string)
    else:
        password = os.getenv('GoogleDocsPassWord')
        if password == None:
            print('set the GoogleDocsPassWord environment variable')
            sys.exit(1)
        m.login(username, password)
    if debug > 0: print('just logged in')
    return(m)

def countBefore(m, mailbox, before, debug):
    status, response = m.select(mailbox, readonly=True)
    if debug > 1: print(response)
    assert('OK' == status)
    d = datetime.datetime.strptime(before, '%Y-%m-%d')
    searchstring = '(before "{}")'.format(d.strftime('%d-%b-%Y'))
    if debug > 1: print(searchstring)
    status, response = m.search(None, searchstring)
    if debug > 1: print(response)
    assert('OK' == status)
    assert(1 == len(response))
    return(len(response[0].split()))

def countOn(m, mailbox, on, debug):
    status, response = m.select(mailbox, readonly=True)
    if debug > 1: print(response)
    assert('OK' == status)
    d = datetime.datetime.strptime(on, '%Y-%m-%d')
    searchstring = '(on "{}")'.format(d.strftime('%d-%b-%Y'))
    if debug > 1: print(searchstring)
    status, response = m.search(None, searchstring)
    if debug > 1: print(response)
    assert('OK' == status)
    assert(1 == len(response))
    return(len(response[0].split()))

def countSince(m, mailbox, since, debug):
    status, response = m.select(mailbox, readonly=True)
    if debug > 1: print(response)
    assert('OK' == status)
    d = datetime.datetime.strptime(since, '%Y-%m-%d')
    searchstring = '(since "{}")'.format(d.strftime('%d-%b-%Y'))
    if debug > 1: print(searchstring)
    status, response = m.search(None, searchstring)
    if debug > 1: print(response)
    assert('OK' == status)
    assert(1 == len(response))
    return(len(response[0].split()))

def countMessages(m, mailbox, debug):
    status, response = m.select(mailbox, readonly=True)
    if debug > 1: print(response)
    assert('OK' == status)
    return(response[0])

def listMailboxes(m, debug):
    mailboxes = []
    status, response = m.list()
    if debug > 1: print(response)
    assert('OK' == status)
    assert(list == type(response))
    for mailbox in response:
        assert(str == type(mailbox))
        if debug > 0: print(mailbox)
        if '\Noselect' not in mailbox.split('"')[0]:
            mailboxes.append(mailbox.split('"')[-2])
    return(mailboxes)

def getMessage(m, msg_uid, debug):
    status, response = m.uid('FETCH', msg_uid,
#                             '(RFC822 X-GM-LABELS X-GM-THRID X-GM-MSGID)')
                             '(RFC822 X-GM-MSGID)')
    if debug > 1: print(response)
    if debug > 0: print('msgUID:{} len:{}'.format(msg_uid,len(response)))
    assert('OK' == status)
    assert(type(response) == list)
    assert(2 <= len(response))
    assert(type(response[0]) == tuple)
    assert(2 <= len(response[0]))
    (imap_data, message_data) = response[0]
    if debug > 1: print('imap_data:{}'.format(imap_data))
    pattern = re.compile('X-GM-MSGID\s+(\d+)')
    message_id = pattern.search(imap_data).group(1)
    return(message_data, message_id)

def copyMessages(m, mailbox, debug):
    status, response = m.select(mailbox, readonly=True)
    if debug > 1: print(response)
    if 'OK' != status:
        return('mailbox not found')
    status, response = m.uid('search', None, 'ALL')
    if debug > 1: print(response)
    assert('OK' == status)
    assert(type(response == list))
    assert(1 == len(response))
    message_count = 0
    for msg_uid in response[0].split():
        message_count +=1
        (message_data, message_id) = getMessage(m, msg_uid, debug)
        parsed_msg = email.message_from_string(message_data)
        date_from_message = parsed_msg['date']
        if debug > 0:
            print('Date: {}'.format(date_from_message))
            print('Subject: {}'.format(parsed_msg['subject']))
        if date_from_message is None:
            date_from_message = EPOCHSTR
        try:
            dt = dateutil.parser.parse(date_from_message)
        except ValueError:
            print('Got a ValueError, try fuzzy')
            dt = dateutil.parser.parse(date_from_message, fuzzy=True)
        if dt_is_naive(dt):
            print('Performing TZ name lookup')
            try:
                dt = dateutil.parser.parse(date_from_message, tzinfos=TZINFOS)
            except ValueError:
                print('Got a ValueError, strip last word, force UTC')
                dt = dateutil.parser.parse(' '.join(
                    date_from_message.split()[:-1])).replace(
                        tzinfo=dateutil.tz.tzutc()
                    )
        if dt_is_naive(dt):
            print('TZ name lookup failed, forcing UTC')
            dt = dateutil.parser.parse(date_from_message).replace(
                tzinfo=dateutil.tz.tzutc()
            )
        filename = '{}.{}.gmail'.format(int((dt - EPOCH).total_seconds()),
                                        message_id)
        with open(filename, 'w') as f:
            f.write(message_data)

def interactiveDelete(m, mailbox, debug):
    fd = sys.stdin.fileno()
    saveTCGetAttr = termios.tcgetattr(fd)
    status, response = m.select(mailbox, readonly=False)
    if debug > 1: print(response)
    if 'OK' != status:
        return('mailbox not found')
    status, response = m.uid('search', None, 'ALL')
    if debug > 1: print(response)
    assert('OK' == status)
    assert(type(response == list))
    assert(1 == len(response))
    message_count = 0
    delete_count = 0
    for msg_uid in response[0].split():
        message_count +=1
        (message_data, message_id) = getMessage(m, msg_uid, debug)
        parsed_msg = email.message_from_string(message_data)
        print('Date: {}'.format(parsed_msg['date']))
        print('To: {}'.format(parsed_msg['to']))
        print('From: {}'.format(parsed_msg['from']))
        print('Subject: {}'.format(parsed_msg['subject']))
        print('---')
        if debug > 1: print(parsed_msg)
        print('Delete? (y/n/q): ', end='')
        tty.setraw(fd)
        user_input = sys.stdin.read(1)
        termios.tcsetattr(fd, termios.TCSADRAIN, saveTCGetAttr)
        print(user_input)
        if 'y' == user_input:
            print(m.uid('STORE', msg_uid, '+FLAGS', '(\\Deleted)'))
            delete_count += 1
        if 'q' == user_input:
            break
        if 0 < delete_count and 0 == delete_count % 10:
            print(m.expunge())
            print('\nexpunged!\n')
    if 0 < delete_count and 0 != delete_count % 10:
        print(m.expunge())
        print('\nexpunged!\n')
    m.close()
    return([message_count, delete_count])

def envelopes(m, mailbox, debug):
    status, response = m.select(mailbox, readonly=True)
    if debug > 1: print(response)
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

def flags(m, mailbox, debug):
    status, response = m.select(mailbox, readonly=True)
    if debug > 1: print(response)
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

def append(m, mailbox, filename, debug):
    with open(filename, 'rb') as f:
        message_data = f.read()
    date_from_message = email.message_from_string(message_data)['date']
    if None == date_from_message:
        date_time = imaplib.Time2Internaldate(time.time())
    else:
        date_time = imaplib.Time2Internaldate(
            (dateutil.parser.parse(date_from_message) - EPOCH).total_seconds())
    if debug > 1: print(date_from_message, date_time)
    status, response = m.append(mailbox, '', date_time, message_data)

def gmailLogout(m, debug):
    if debug > 0: print('about to log out')
    m.logout()
    if debug > 0: print('just logged out')

if '__main__' == __name__:
    args = parseArgs()
    m = gmailLogin(args.username, args.tokenFile, debug=args.debug)
    if args.before:
        print('{} messages before {}'.format(countBefore(
            m, args.mailbox, args.before, debug=args.debug), args.before))
    if args.on:
        print('{} messages on {}'.format(countOn(
            m, args.mailbox, args.on, debug=args.debug), args.on))
    if args.since:
        print('{} messages since {}'.format(countSince(
            m, args.mailbox, args.since, debug=args.debug), args.since))
    if args.list:
        mailboxes = listMailboxes(m, debug=args.debug)
        for mailbox in mailboxes:
            message_count = countMessages(m, mailbox, debug=args.debug)
            print('{}:{}'.format(mailbox, message_count))
    if args.copy:
        copyMessages(m, args.mailbox, debug=args.debug)
    if args.interactiveDelete:
        (message_count, delete_count) = interactiveDelete(
            m, args.mailbox, debug=args.debug)
        print('messages processed:{} messages deleted:{}'.format(
            message_count, delete_count))
    if args.envelopes:
        envelopes(m, args.mailbox, debug=args.debug)
    if args.flags:
        flags(m, args.mailbox, debug=args.debug)
    if args.append:
        append(m, args.mailbox, args.append, debug=args.debug)
    gmailLogout(m, debug=args.debug)
