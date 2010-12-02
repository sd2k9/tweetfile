#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file name: ''mail2web.py''
#  project: eMail Web Interface
# function: Fetches web pages by a simple eMail interface
#           - Runs over the .forward file in the linux home directory
#
# Content of ~/.forward:
# |"cd /home/demonslave/mail2web; FAKECHROOT_EXCLUDE_PATH=/usr/lib/python2.5 fakechroot ./watcher_report_output.sh 2>&1 >> watcher_report_output.log"
#      created: 2010-10-04
#  last change: $Date$
#      Version: $Name:  $
#
# Copyright (C) 2010 Robert Lange (robert.lange@s1999.tu-chemnitz.de)
# Licensed under the GNU General Public License, version 2
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#



# *** Import modules
# To control output level easily
# from __future__ import print_function
import logging
# Argument parser
import optparse
# Read from stdin, Program path
import sys
# Prepare a Message as E-Mail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from email.encoders import encode_quopri
from email import Charset
# Send mail by SMTP
import smtplib
# To be able to catch also socket errors by their name
import socket
# URL Fetcher
import urllib
# Current date for Train fetcher
import datetime
# Chroot ability
import os

# Get the list of allowed users accessing this service
from mail2webuser import UserList


# *** Global settings as dictionary
Opts = {
    # Sender of the messages
    'sender': 'mail2web@localhost',
    # SMTP Server, Host
    'smtp_server_host': '127.0.0.1',
    'smtp_server_port': '25',         # For Direct Sending
    # Limit of data to fetch: 100k
    'data_limit': 100*1024
    }


# Provide logging shortcuts
pinfo  = logging.info
pwarn  = logging.warning
perror = logging.error


# ********************************************************************************
# *** Go into CHROOT - see help text in except block
chroot_dir = sys.path[0] + "/empty_chroot"
try:
    os.chroot(chroot_dir)
    pass
except OSError:
    # Something failed with CHROOTing - give help text
    print """
      Going into chroot failed; did you forgot to run
      me with fakechroot?
      To succeed the python libs must be excluded from CHROOT'ing
      with the shell variable setting
      FAKECHROOT_EXCLUDE_PATH=/usr/lib/python<version>"""
    print "       Chroot directory: " + chroot_dir
    print
    raise  # and now just propagate the error further



# ********************************************************************************
# *** Command execution objects

class WorkerBase:
    """Base class for command execution classes."""
    def execute(self,args):
       """Perform the command with the supplied arguments.

       Parameter args: The argument string for the respective command

       Return: Webpage to attach to the mail to send as result (as string)
               None when no Mail should be send

       """
       # Don't call the base class by itself
       NotImplementedError("Abstract base class must not be called!")


class WorkerTest(WorkerBase):
    """Just returns a Hello World message."""
    def execute(self,args):
        pinfo("Test: Returning Hello World Document")
        return "<html>Hello World</html>"

class WorkerWebFetch(WorkerBase):
    """Fetches the given address and returns it."""
    def execute(self,args):
        # When no URL scheme specified, just expect "http://"
        if args.find("://") is -1 :
            url = "http://" + args
        else:
            url = args
        pinfo("   Web: Fetching " + url + " (Limit: " + str(Opts['data_limit']) + ")" )
        try:
            url = urllib.urlopen(url)
            data = url.read(Opts['data_limit'])
        # urllib2: except  (urllib.URLError, ValueError) as detail:
        except  (IOError, ValueError),  detail:
            # Showing error message as return
            return "<html>Error fetching data from " + args + ":</br>" + \
                 str(detail) +  "</html>"
        else:   # No error, return the data fetched
            return data;


class MozillaUrlOpener(urllib.FancyURLopener):
    """For getting access to google, we need to change the user agent

    That is working the following way: http://wolfprojects.altervista.org/changeua.php
    """
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'


class WorkerGoogle(WorkerBase):
    """Queries Google with the supplied search term."""
    def execute(self,args):
        urlarg = urllib.quote_plus(args)   # Encode the data
        pinfo("   Google: Fetching Data " + urlarg + " (Limit: " + str(Opts['data_limit']) + ")" )
        # Template: http://www.google.co.jp/search?q=hallo&safe=off
        urldata = "http://www.google.com/search?q=%s&safe=off" % (urlarg)
        try:
            url = MozillaUrlOpener()
            url_open = url.open(urldata)
            data = url_open.read(Opts['data_limit'])
        # urllib2: except  (urllib.URLError, ValueError) as detail:
        except  (IOError, ValueError), detail:
            # Showing error message as return
            return "<html>Error fetching data from " + args + ":</br>" + \
                 str(detail) +  "</html>"
        else:   # No error, return the data fetched
            return data;

class WorkerGoogleFirst(WorkerBase):
    """Returns the first match from Google with the supplied search term.
       <br />
      This function is also known as "Feeling Lucky Search".
    """
    def execute(self,args):
        urlarg = urllib.quote_plus(args)   # Encode the data
        pinfo("   Google First: Fetching Data " + urlarg + " (Limit: " + str(Opts['data_limit']) + ")" )
        # Template: http://www.google.co.jp/search?q=hallo&safe=off&btnI
        urldata = "http://www.google.com/search?q=%s&safe=off&btnI" % (urlarg)
        try:
            url = MozillaUrlOpener()
            url_open = url.open(urldata)
            data = url_open.read(Opts['data_limit'])
        # urllib2: except  (urllib.URLError, ValueError) as detail:
        except  (IOError, ValueError), detail:
            # Showing error message as return
            return "<html>Error fetching data from " + args + ":</br>" + \
                 str(detail) +  "</html>"
        else:   # No error, return the data fetched
            return data;


class WorkerWadoku(WorkerBase):
    """Queries Wadoku German-Japanese dictionary."""
    def execute(self,args):
        urlarg = self.quote(args)   # Encode the data and Umlauts
        pinfo("   Wadoku: Asking for " + urlarg + " (Limit: " + str(Opts['data_limit']) + ")" )
        # Template: http://www.wadoku.de/wadoku/search/hallo
        urldata = "http://www.wadoku.de/wadoku/search/%s" % (urlarg)
        try:
            url = urllib.urlopen(urldata)
            data = url.read(Opts['data_limit'])
        # urllib2: except  (urllib.URLError, ValueError) as detail:
        except  (IOError, ValueError), detail:
            # Showing error message as return
            return "<html>Error fetching data from " + args + ":</br>" + \
                 str(detail) +  "</html>"
        else:   # No error, return the data fetched
            return data;
    def quote(self, args):
        """Quote the URL data and restore the Umlauts as required by Wadoku"""
        data = urllib.quote_plus(args)
        data = data.replace("Ae","Ä")
        data = data.replace("Oe","Ö")
        data = data.replace("Ue","Ü")
        data = data.replace("ae","ä")
        data = data.replace("oe","ö")
        data = data.replace("ue","ü")
        data = data.replace("sz","ß")
        return data


# Fahrplan-Abfrage mit http://world.jorudan.co.jp/norikae/cgi-bin/engkeyin.cgi
class WorkerNorikae(WorkerBase):
    """Queries Norikae train time table. <br />

    We expect the format [TO.]FROM.TO[.HH.MM[.DD[.Month[.YYYY]]]]] <br />
    Everything missing will be taken as now. <br />
    String literal "TO." at beginning will select arrival-time instead of departure time.
    <br />
    Examples:<br />
    DO train TO.Tokyo.Miyaji - Timetable now from Tokyo to Miyaji<br />
    DO train TO.Tokyo.Miyaji.17.45.20.11 - Timetable from Tokyo to  Miyaji on 5.45pm 20.Nov
    <br />
    Attention: When you misspell the stations you will get an meaningless error message!
    """
    def execute(self,args):
        url = "http://world.jorudan.co.jp/norikae/cgi-bin/engkeyin.cgi"
        raw_data = self.parse_args(args)   # parse arguments
        data = urllib.urlencode(raw_data)  # Encode for POST
        if data is None:
            pinfo("   Norikae: Failing to parse argument string " + args)
            # Showing error message as return
            return "<html>Train: Failing to parse argument string " + args + \
                    "</html>"
        # print url # Debug
        # print data # Debug
        pinfo("   Norikae: Asking for " + data + " (Limit: " + str(Opts['data_limit']) + ")" )
        # import sys # Debug
        # sys.exit(1) # Debug

        try:
            url = urllib.urlopen(url, data)  # Do a post request
            data = url.read(Opts['data_limit'])
        # urllib2: except  (urllib.URLError, ValueError) as detail:
        except  (IOError, ValueError), detail:
            # Showing error message as return
            return "<html>Error fetching data from " + args + ":</br>" + \
                 str(detail) +  "</html>"
        else:   # No error, return the data fetched
            return data;

    def parse_args(self, args_in):
       """Parse the arguments into dict usable with Norikae POST

       Returns None for Fail
       """


       # First we parse the arguments into abstract values
       dc = self.parse_abstract_args(args_in)
       if dc is None:
           return None # Some failure occured

       # Process to actual field names
       # from_in: text
       # to_in: text
       # Dyyyymm - YYYYMM
       # Ddd - DD
       # Dhh - h am/pm
       # Dmn - m
       # Sfromto - from/to
       dcp = {}
       dcp['from_in'] = dc['from']
       dcp['to_in']   = dc['to']
       dcp['Dyyyymm'] = "%04d%02d" % (int(dc['year']), int(dc['month']))
       dcp['Ddd']     = "%02d" % (int(dc['day']))
       dcp['Dhh']     = "%02d" % (int(dc['hour']))
       dcp['Dmn']     = "%02d" % (int(dc['min']))
       dcp['Sfromto'] = dc['fromto']
       # Preset values from my side
       dcp['Sseat'] = "1"     # Unreserved
       # dcp['Bchange']     = ""  # Button not clicked
       dcp['Bsearch']     = " Search "        # Search button clicked
       # Other hidden values
       dcp["Knorikae"]    =  "Knorikae"
       dcp["proc_mode"]   =  "K"
       dcp["proc_sw"]     =  "11"   # 2nd screen
       dcp["proc_sw_sub"] =  "0"
       dcp["from_nm"]     =  ""
       dcp["to_nm"]       =  ""
       dcp["Sfrom_sw"]    =  "1"
       return dcp


    def parse_abstract_args(self, args):
       """Parse the arguments into abstract dict.

       Returns None for Fail
       """
       # Dummy Debug function
       # dc = {}
       # dc['from'] = "Tatsutaguchi"
       # dc['to'] = "Miyaji"
       # dc['year'] = 2010
       # dc['month'] = 11
       # dc['day'] = 20
       # dc['hour'] = 15
       # dc['min'] = 40
       # dc['fromto'] = 'from'


       # Fill with today's defaults  - adjust to Japan Time
       now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
       dc = {}
       dc['year'] = now.year
       dc['month'] = now.month
       dc['day'] = now.day
       dc['hour'] = now.hour
       dc['min'] = now.minute
       # We expect the format [TO.]FROM.TO.[.MM[.HH[.DD[.Month[.YYYY]]]]]
       sa = args.split(".")  # Just split on "."
       # print sa # Debug
       # Just parse it the way we're going
       if not sa:
           return None
       data = sa.pop(0)
       if data == "TO":
           dc['fromto'] = 'to'  # To-Mode
           # Fetch also real from
           if not sa:
               return None
           data = sa.pop(0)
       else:
           dc['fromto'] = 'from'  # From-Mode
       dc['from'] = data
       if not sa:
           return None
       data = sa.pop(0)
       dc['to'] = data
       # Now all defaults are filled and we will exit when it's fine
       if not sa:
           return dc
       data = sa.pop(0)
       dc['hour'] = data
       if not sa:
           return dc
       data = sa.pop(0)
       dc['min'] = data
       if not sa:
           return dc
       data = sa.pop(0)
       dc['day'] = data
       if not sa:
           return dc
       data = sa.pop(0)
       dc['month'] = data
       if not sa:
           return dc
       data = sa.pop(0)
       dc['year'] = data
       # All parsed and done
       return dc



# *** Build dict of worker classes, with the command name as key
WorkerClasses = {'test': WorkerTest,
                 'web': WorkerWebFetch,
                 'google': WorkerGoogle,
                 'gfirst': WorkerGoogleFirst,
                 'wadoku': WorkerWadoku,
                 'train': WorkerNorikae,
                 }



# ********************************************************************************
# *** Functions

def extract_mail_content(readin):
    """Extract required information from mail streamed into stdin.


    Also character encoding for command is transformed when required

    Argument: file object to read from
    Return: Sender E-Mail, Passcode, Command-String

    """

    # Read the first 16k - to avoid any buffer overflow or so
    data = readin.read(16*1024)
    # Debug
    # print data

    # Variables
    addr = ''
    code = ''
    command = ''
    charset = ''

    # Extract the data
    for it in data.split("\n"):
        if it.startswith("From: ") and addr is '' :  # We found from, for 1st time
            addr = it[6:]
        if it.startswith("Subject: ") and code is '' :  # We found code, for 1st time
            code = it[9:]
        if it.startswith("DO ") and command is '' :  # We found cmd, for 1st time
            command = it[3:]
        if it.startswith("Content-Type:") and charset is '' :  # We found character encoding?
            charsetfind = it.rfind("charset=")
            if charsetfind is not -1:  # Yes, we have some
                charset = it[charsetfind+8:]


    # Okay, change character encoding for the command when specified
    # But no need to recode UTF-8
    if (charset is not '') and not (charset.lower() == "utf-8") :
        pinfo("Recode command from charset " + charset)
        try:
            command_re = command.decode("ISO-2022-JP")
            command_re = command_re.encode("utf-8")
            command = command_re
        except UnicodeError, details:
            pwarning("Failed to recode command! Error is " +\
                     str(detail) +\
                     "\nContinuing with orginal string.")

    # Return
    return addr, code, command


def  check_user(sender, passcode):
    """ Check for valid user and password.

    Returns 2 Parameters
       1.P (valid): true when a valid user/password pair was found
       2.P (receiver): Return mail address for this user

    """

    # Return Vars
    valid = False
    rec = None

    # Search for sender address
    for it in UserList:
        if sender.find(it['from']) is not -1:   # We have a match
            pinfo("Matched user " + it['from'] + " in " + sender)
            if it['code'] == passcode:   # And also the password is OK
                pinfo("   Password matched")
                rec = it['replyto']
                if rec:
                    valid = True  # Everything fine
                else:    # There is no replyto defined?!
                    perror("   Empty replyto fetched from user definition! You are wrong! Pleas fix")
                break   # Out of our loop
            else:
                pwarn("   Password verification failed, continuing with next user")
    else:   # Just give a status, this is an invalid mail
        pinfo("No user matched; silenty ignoring mail")

    # Just return our results
    return valid, rec


def send_mail(command_id, command_raw, payload, rec):
    """Sent the fetched information as Mail to the receiver.

    Parameter
       command_id:  Name of the executed command
       command_raw: Complete command with arguments
       payload: The HTML page to return
       rec: The Mail receiver

    Return: True for OK, False for Failure
    """

    # Override python's weird assumption that utf-8 text should be encoded with base64
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')

    # First format as a message
    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['Subject'] = 'Mail2Web Fetched: ' + command_id
    # me == the sender's email address
    msg['From'] =  Opts['sender']
    msg['To'] = rec
    # Plain text as explanation
    msg_explanation = MIMEText( "This is the demon slave\n" + \
                   "I executed for you:\n" + command_raw + \
                   "\n\nHave fun!\n" + \
                   "To reach some admin, please mailto: admin@thishost\n" + \
                   "This mail address only takes commands for fetching web sites\n" +\
                   "\nPlease be also remindad that this is an beta service. " +\
                   "This means particularly that I am currently logging and " +\
                   "inspecting all accesses.",
                    "text", "utf-8" ) # And the explanation as text
    msg_explanation.add_header('Content-Disposition', 'inline')  # Show message inline
    msg.attach(msg_explanation)
    # And our HTML we want to send, and it's an attachment
    msg_payload = MIMEText(payload, "html", "utf-8")
    msg_payload.add_header('Content-Disposition', 'attachment; filename="result.html"')
    msg.attach(msg_payload)

    # Send the email via our own SMTP server.
    # Debug
    # print msg.as_string()
    # return False
    pinfo("Will send the result now to " + rec + " ...")
    try:   # Open Connection; Catch exceptions
        smtp = smtplib.SMTP(Opts['smtp_server_host'], Opts['smtp_server_port'])
    except (smtplib.SMTPException, socket.error), detail:
        perror("Establishing SMTP connection to " + \
                   Opts['smtp_server_host'] + ":"  + Opts['smtp_server_port'] + \
                   " failed: " + str(detail))
        return False
    try:   # Send data; Catch exceptions
        smtp.sendmail(Opts['sender'], rec, msg.as_string())
        smtp.quit()
    except smtplib.SMTPException, detail:
        perror("SMTP Mail sending failed: " + str(detail))
        return False
    pinfo("  Successfully send " + str(len(msg.as_string()))  + " bytes; Finished now\n")

    # Everything fine - let's return
    return True

# ********************************************************************************

# *** Main Program
def main():

    # *** Command line parsing
    cmd_usage="usage: %prog [options] args"
    cmd_desc ="""Mail2Web - don't call yourself, add it into your .forward file"""
    cmd_version="%prog " + __version__
    cmd_parser = optparse.OptionParser(usage=cmd_usage,
                                   description=cmd_desc, version=cmd_version)
    cmd_parser.add_option('-V', action='version', help=optparse.SUPPRESS_HELP)
    cmd_parser.add_option('--quiet', '-q', dest='quiet', action='store_true',
                        default=False, help='Quiet Output')
    # more options to add
    (cmd_opts, cmd_args) = cmd_parser.parse_args()

    # Setup logging: Show only from warnings when being QUIET
    logging.basicConfig(level=logging.WARNING if cmd_opts.quiet else logging.INFO,
                    format="%(message)s")

    # Chroot logging only here, because otherwise it will confuse the logger
    pinfo("Went into chroot with directory " + chroot_dir)

    # Abort when different than no argument
    if len(cmd_args) != 0:
        perror("No command line arguments are expected!")
        cmd_parser.print_usage()
        return 1


    # *** First read stdin to extract the information for parsing
    sender, passcode, command_raw = extract_mail_content(sys.stdin)
    # Error check: All must be filled
    if not sender:
        perror("Failed to identify sender name - something's wrong")
        return 1
    if not passcode:
        perror("Failed to identify passcode - empty subject?")
        return 1
    if not command_raw:
        perror("Failed to identify command - you forgot the command?")
        return 1

    # Break down the command string: "cmd aguments"
    command_id, dummy, command_arg = command_raw.partition(" ")

    # Debug
    # print "from", sender
    # print "code", passcode
    # print "cmd", command_raw
    # print "cmd_id", command_id
    # print "cmd_arg", command_arg

    # Check for User, and Password
    valid, receiver = check_user(sender, passcode)
    if not valid:   # Check failed, so we go out here
        # "No valid authentication, exiting" -> Should be reported in check_user
        return 0
    # DBG
    # print receiver

    # Check for command existence and call it
    if command_id in WorkerClasses:   # Found it
        pinfo("Command: " + command_raw)
        ret = (WorkerClasses[command_id])().execute(args=command_arg)
    else:  # Fake an return with help message
        ret = "<html><p>Your command " + command_id + " is not supported.</p>"
        ret += "<p>Supported commands are:<ul>"
        for it,obj in WorkerClasses.iteritems():
            ret += "<li>" + it + ":<br />" +  obj.__doc__ + "</li>"
        ret += "</ul></p></html>"
        pinfo("Unknown command, send short help message instead")

    # If it's None, then we're done here
    if ret is None:
        pinfo("Worker returned None; exiting w/o further actions")
        return 0

    # Something returned? Submit it
    # Debug
    # print ret
    # return 0

    # Send the result by email
    if not send_mail(command_id=command_id, command_raw=command_raw,
                     payload=ret, rec=receiver):
        return 1    # There was some kind of error


    # All done, over and out
    return 0



# *** Call Main program
__version__ = filter(str.isdigit, "$LastChangedRevision: 000$")
if __name__ == "__main__":
    main()
