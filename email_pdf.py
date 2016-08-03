#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
from email import encoders
from email.utils import formatdate
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Crypto.PublicKey import RSA
from Crypto import Random
import os
import json

#### decrypt password with rsa
def dec_pass(id_rsa_file, pass_file):
    with open(id_rsa_file, 'r') as f:
        id_rsa = RSA.importKey(f.read())
    with open('pass.rsa', 'rb') as f:
        pass_text = id_rsa.decrypt(f.read()).decode('utf-8')
    return pass_text

#### load email settings #####
def load_email_settings(email_settings):
    with open(email_settings, 'r') as f:
        email_param = json.load(f)
    return email_param

def create_message(from_addr, to_addr, subject, body, mime, attach_file):
    """Build emal massage
    """
    msg = MIMEMultipart('alternative')
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = formatdate()
    cset = 'utf-8'

    if body != "":
        attachment_text = MIMEText(body, 'plain', cset)
        msg.attach(attachment_text)

    # set MIME type for attachmed file
    attachment = MIMEBase(mime['type'],mime['subtype'])
    # set attached file as a pay_load
    with open(attach_file['path'], 'rb') as f:
        attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    msg.attach(attachment)
    attachment.add_header("Content-Disposition","attachment", filename=attach_file['name'])
    return msg


def send_gmail(from_addr, id_rsa_file, passwd_rsa_file, msg):
    """Send email via gmail
    """
    try:
        s = smtplib.SMTP('smtp.gmail.com',587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        ### login to gmail with gmail account 'from_addr' and with decripted password file
        s.login(from_addr, dec_pass(id_rsa_file, passwd_rsa_file))
        s.send_message(msg)
        s.close()
    except:
        print('Email error occured. Email was not able to send.')

def push_email(settings, title, text, attach_pdf):
    email_settings = settings
    email_param =  load_email_settings(email_settings)
    id_rsa_file = os.path.expanduser(email_param['id_rsa_file'])
    passwd_rsa_file = email_param['passwd_rsa_file']

    from_addr = email_param['from_addr']
    to_addr = ",".join(email_param['to_addrs'])
    subject = title
    body_text = text
    mime={'type':'application', 'subtype':'pdf'}
    pdf_name = attach_pdf.rsplit('/')[-1]
    attach_file={'name':pdf_name, 'path':attach_pdf}
    msg = create_message(from_addr, to_addr, subject, body_text, mime, attach_file)
    if email_param['cc_addrs']:
        msg['Cc'] = ",".join(cc_addrs)
    if email_param['bcc_addrs']:
        msg['Bcc'] = ",".join(bcc_addrs)
    send_gmail(from_addr, id_rsa_file, passwd_rsa_file, msg)


if __name__ == '__main__':
    email_settings = 'email.json'
    email_param =  load_email_settings(email_settings)
    id_rsa_file = os.path.expanduser(email_param['id_rsa_file'])
    passwd_rsa_file = email_param['passwd_rsa_file']

    from_addr = email_param['from_addr']
    to_addr = ",".join(email_param['to_addrs'])
    # to_addr = 'testaddr@hoge.com'
    subject = "Email test with python"
    body_text = "hogehogehage ageage"
    ## for csv
    # mime={'type':'text', 'subtype':'comma-separated-values'}
    # attach_file={'name':'test.csv', 'path':'/tmp/test.csv'}
    ## for pdf
    mime={'type':'application', 'subtype':'pdf'}
    attach_file={'name':'160725-171642.pdf', 'path':'./160725-171642.pdf'}

    msg = create_message(from_addr, to_addr, subject, body_text, mime, attach_file)
    if email_param['cc_addrs']:
        msg['Cc'] = ",".join(cc_addrs)
    if email_param['bcc_addrs']:
        msg['Bcc'] = ",".join(bcc_addrs)

    send_gmail(from_addr, id_rsa_file, passwd_rsa_file, msg)
