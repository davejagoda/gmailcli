# gmailcli

GMail Command Line Interface

## server requirements

GMail account with IMAP enabled:
https://mail.google.com/mail/#settings/fwdandpop

If you want to use use *Application Specific Passwords* (instead of OAuth):

*enable "less secure apps":
 https://www.google.com/settings/security/lesssecureapps*

## client requirements

- python3.10
- packages from `Pipfile`

## installation

`cd ~/src/github`

`git clone git@github.com:davejagoda/gmailcli.git`

`cd gmailcli`

`pipenv install`

## potentially useful findings

`Labels` and `Folders` are basically the same thing. Adding a `Label`
to a message is like copying it to a `Folder`.

`Inbox` is a special `Label`. `All Mail` is the folder to which all
messages belong.

## invocations

*Prepend each command below with `pipenv run` **OR** run `pipenv
 shell` to active the virtualenv*

Generate refresh and access tokens:

`./writeGoogleBearerToken.py djcatchspam_client_secrets.json djcatchspam_gmail_token.json`

List all mailboxes and their respective message counts:

`./gmailimap.py -t djcatchspam_gmail_token.json -u djcatchspam@gmail.com -l`

Set debug level to 4 (just for this invocation):

`./gmailimap.py -t djcatchspam_gmail_token.json -u djcatchspam@gmail.com -dddd`

Send a mail message by providing recipient address, subject, and body
(be verbose):

`./gmailsend.py -t djcatchspam_gmail_token.json -r djcatchspam@gmail.com -s 'email subject' -b 'email body' -vv`

Send a mail message with 2 attachments:

`./gmailsend.py -t djcatchspam_gmail_token.json -r djcatchspam@gmail.com -s 'attachments' -b '2 attachments' -a file_in_cwd /tmp/file_with_path`
