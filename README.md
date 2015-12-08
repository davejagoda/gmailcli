# gmailcli

GMail Command Line Interface

## server requirements

GMail account with IMAP enabled: https://mail.google.com/mail/#settings/fwdandpop

~~ enable "less secure apps": https://www.google.com/settings/security/lesssecureapps~~

## client requirements

- Python
- IMAP
- google-api-python-client

## installation

`cd ~/src/github`

`git clone git@github.com:davejagoda/gmailcli.git`

`cd gmailcli`

`virtualenv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`

## potentially useful findings

`Labels` and `Folders` are basically the same thing. Adding a `Label` to a message is like copying it to a `Folder`.

`Inbox` is a special `Label`. `All Mail` is the folder to which all messages belong.
