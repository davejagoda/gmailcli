#!/usr/bin/env python

# based on the gmail API sample python docs found here:
# https://developers.google.com/gmail/api/v1/reference/users/messages/send

import argparse
import httplib2
import oauth2client.client
import apiclient.discovery
import base64
import os
import mimetypes
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def create_message(sender, to, subject, message_text, attachment_paths, verbose=0):
# sender: email address of the sender
# to: list of receiver email addresses
# subject: The subject of the email message
# message_text: The text of the email message
# attachment_paths: The path[s] of the file[s] to be attached

    if attachment_paths:
        message = MIMEMultipart()
        message.attach(MIMEText(message_text))
    else:
        message = MIMEText(message_text)

    message['to'] = ','.join(to)
    message['from'] = sender
    message['subject'] = subject

    for attachment_path in attachment_paths:
        content_type, encoding = mimetypes.guess_type(attachment_path)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if verbose > 0:
            print('attachment type is: {}'.format(main_type))
        with open(attachment_path, 'rb') as f:
            if main_type == 'text':
                msg = MIMEText(f.read(), _subtype=sub_type)
                if verbose > 1:
                    print('Text')
            elif main_type == 'image':
                msg = MIMEImage(f.read(), _subtype=sub_type)
                if verbose > 1:
                    print('Image')
            elif main_type == 'audio':
                msg = MIMEAudio(f.read(), _subtype=sub_type)
                if verbose > 1:
                    print('Audio')
            elif main_type == 'application':
                msg = MIMEApplication(f.read(), _subtype=sub_type)
                if verbose > 1:
                    print('Application')
            else:
                msg = MIMEBase(main_type, sub_type)
                if verbose > 1:
                    print('Base')
                msg.set_payload(f.read())

        msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
        message.attach(msg)

    return {'raw': base64.b64encode(message.as_string())}

def get_gmail_service(tokenFile, verbose=0):
    with open(tokenFile, 'r') as f:
        credentials = oauth2client.client.Credentials.new_from_json(f.read())
        http = httplib2.Http()
        credentials.authorize(http)
        return(apiclient.discovery.build('gmail', 'v1', http=http))

if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tokenFile', required=True, help='file containing OAuth token in JSON format')
    parser.add_argument('-r', '--recipients', required=True, nargs='+', help='list of recipients')
    parser.add_argument('-s', '--subject', required=True, help='subject of email message')
    parser.add_argument('-b', '--body', required=True, help='body of email message')
    parser.add_argument('-a', '--attachments', nargs='*', default=[], help='list of attachment paths')
    parser.add_argument('-v', '--verbose', action='count', help='be verbose')
    args = parser.parse_args()

    gmail_service = get_gmail_service(args.tokenFile, args.verbose)

    msg = create_message('me', args.recipients, args.subject, args.body, args.attachments, args.verbose)
    if args.verbose > 1:
        print(msg)
    res = gmail_service.users().messages().send(userId='me', body=msg).execute()
    if args.verbose > 0:
        print(res)
