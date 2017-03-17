#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file name: ''tweetfile.py''
#   project: Tweet a File
#  function: Receives a file via eMail, puts it into
#            the file system and twitter the shortended URL
#           - Runs over the .forward file in the linux home directory
#
# Content of ~/.forward:
# |"cd /home/<username>/tweetfile; TMP=/home/<username>/tweetfile/tmp FAKECHROOT_EXCLUDE_PATH=/dev:/usr/lib/python2.6:/usr/bin:/usr/share/perl:/usr/share/perl5:/usr/lib/perl:/home/<username>/tweetfile/tmp fakechroot ./watcher_report_output.sh 2>&1 >> watcher_report_output.log"
# /dev is required for SSL authentication, otherwise urllib2 fails with obscure error
# /usr/bin and *perl* is required for exiftool
# /home/<username>/tweetfile/tmp is required because twitter+tempfile creates temporary directories
# Run with local python lib for oauth2 and twitter:
#  PYTHONPATH=$PWD/pylib/lib/python2.6/site-packages ./tweetfile.py
#      created: 2011-03-16
#  last change: $LastChangedRevision$
#
#    Copyright (C) 2010,2017 Robert Lange <sd2k9@sethdepot.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#



# *** Import modules
# To control output level easily
# from __future__ import print_function
import logging
# Argument parser
import optparse
# Read from stdin
import sys
# Parse E-Mail Message
import email
# Parse International E-Mail Headers
import email.header
# Create E-Mail messages from scratch
import email.mime.text
# Send mail by SMTP
import smtplib
# To be able to catch also socket errors by their name
import socket
# Chroot ability, Path+Dir Manipulations, chmod
import os
# Regular Expressions
import re
# Temporary file name - abuse for random file name creation
import tempfile
# Error numbers
import errno
# Spawn sub-process
import subprocess
# Twitter interface
import twitter
# Required modules for bitly URL shortener
import urllib2
import urllib
import simplejson


# Get the list of allowed users accessing this service
# and global settings
from tweetfileaccess import UserList, Opts


# Provide logging shortcuts
pinfo  = logging.info
pwarn  = logging.warning
perror = logging.error


# ********************************************************************************
# *** Go into CHROOT - see help text in except block
try:
    # Some functions like tempfile don't care about chroot inside fakechroot
    # Therefore also change the OS directory before chroot'ing
    os.chdir(Opts['chroot_dir'])
    os.chroot(Opts['chroot_dir'])
    pass
except OSError:
    # Something failed with CHROOTing - give help text
    print """
      Going into chroot failed; did you forgot to run
      me with fakechroot?
      To succeed the python libs must be excluded from CHROOT'ing
      with the shell variable setting
      FAKECHROOT_EXCLUDE_PATH=/dev:/usr/lib/python2.6:/usr/bin:/usr/share/perl:/usr/share/perl5:/usr/lib/perl:/home/<username>/tweetfile/tmp
                             (Adapt Python and Perl version numbers when required)
      """
    print "       Chroot directory: " + Opts['chroot_dir']
    print
    raise  # and now just propagate the error further



# ******************************************************************************
# *** Objects

class ExtractMailError(BaseException):
   """Exception Class for function extract_mail_content

   These raised errors are not critical, they signal that the processing
   should be aborted here.
   """
   pass

class StoreFileError(BaseException):
   """Exception Class for function store_file

   These raised errors are not critical, they signal that the processing
   should be aborted here.
   """
   pass

class TwitterMsgError(BaseException):
   """Exception Class for class twittermsg

   These raised errors are not critical, they signal that the processing
   should be aborted here.
   """
   pass

class BitlyMsgError(BaseException):
   """Exception Class for Bit.Ly errors

   These raised errors are not critical, they signal that the processing
   should be aborted here.
   """
   pass

# ********************************************************************************
# *** Twitter object
class twittermsg:
    """ Twitter the given string"""

    # Variables
    _api = ""

    def __init__(self, tcreds):     # C'tor
        """Constructor with twitter credentials

           The required credentials are stored as dict in tcred with the content
           consumer_key
           consumer_secret
           access_token_key
           access_token_secret
        """
        # Changes: Username/password: Consumer Data, not account
        # access_*: Fetch from tool python-twitter/get_access_token.py
        self._api = twitter.Api(consumer_key=tcreds['consumer_key'],
                               consumer_secret=tcreds['consumer_secret'],
                               access_token_key=tcreds['access_token_key'],
                               access_token_secret=tcreds['access_token_secret']
                                )
        # print self._api.VerifyCredentials()

    def _urlshorten(self, link):
        """Shortens the provided link"""
        bitly_api_user = Opts['bitly_api_user']
        bitly_api_key = Opts['bitly_api_key']
        if bitly_api_user is None or bitly_api_key is None :
            # If no bitly API key defined, do nothing
            return link

        try:
           return bitly_shorten(bitly_api_user, bitly_api_key, link)
        except BitlyMsgError as detail:  # we failed
            raise TwitterMsgError("URL shortening failed with failure " + str(detail))
        except:
            raise # Other errors are forwarded


    def doit(self, msg, flink):
        """Twitter the message with file link.

        The file link will be URL-shortened

        msg: The message
        flink: File link
        """

        # Shorten URL, when existing
        if flink is None:
            postfix = ""   # Nothing to attach
        else:
            postfix = " " + self._urlshorten(flink)

        pinfo('Tweet: "' + msg + '"' + postfix)

        # For Debug: Manually disable
        if Opts.has_key('testmode') and Opts['testmode']:
            pwarn("   Tweet not posted in testmode")
        else:
            self._api.PostUpdate(msg + postfix)


    def finish(self):
        """Cleanup and clear credentials"""
        self._api.ClearCredentials()

# ******************************************************************************
# *** Functions

def extract_mail_content(readin):
    """Extract required information from mail streamed into stdin.


    Also character encoding for command is transformed when required

    Argument: file object to read from
    Return: User ID
            Tweet Text
            Message Object itself
            Attachment as message object
               None when no Attachment found

    Raises exception ExtractMailError when an error occurs;
    Error message to print is stored as 'args'
    """


    # Create Mail parser object and parse the mail
    msg = email.message_from_file(readin)

    # Debug
    # print "Sender " + msg['from']
    # print "Tweet Text " + msg['subject']
    # print "Multipart? "
    # if msg.is_multipart():
    #     print "True"
    # else:
    #     print "False"
    # raise ExtractMailError("Debug abort")


    # Now decide whether it is an valid request or not
    # Decided on the base of sender and recipient
    send = msg['From']
    rec  = msg['To']
    uid = None        # Set to user ID in case a match is found
    # Security check: How to handle something like "From/To: good@org <evil@org>"?
    if rec.count("@") != 1:
        raise ExtractMailError("Double or None @ in recipient address found - bailing out because of confusion: " + rec)
    if send.count("@") != 1:
        raise ExtractMailError("Double or None @ in sender address found - bailing out because of confusion: " + send)
    for key,it in UserList.iteritems():
        # Go through user list and check
        if rec.rfind(it['rcpt']) != -1:   # We have a match
            # Now check that also the sender is allowed
            for listitem in it['allowedfrom']:
                if send.rfind(listitem) != -1:   # We have a match
                    uid = key
                    break
        if uid is not None:
            break # loop aboarder when match was found
    if uid is None:   # We had no match, so we're going back
        raise ExtractMailError("No match for From/To Address, Exiting: " + send + "/" + rec)
    # Else: Found a match which is valid

    # Now get the attachment when there is one
    attachment = None   # First there is none
    if msg.is_multipart():
        attachment = msg.get_payload()[-1]   # Get last Attachment when existing

    # Don't forget to decode header, otherwise you can end up with something
    # like "Mit =?UTF-8?B?c8O2bGRlbg==?= umlauten"
    # Help comes from: http://stackoverflow.com/questions/5343191/how-does-encoding-in-email-subjects-work-django-python
    text_decoded = email.header.decode_header(msg['Subject'])
    text = ""
    for text_parts in text_decoded:
        # When merging multiple parts, a space must be inserted
        if text != "":
            text = text + " "
        if text_parts[1] is None:    # No special encoding
            text = text + text_parts[0]
        else:                        # Decoding necessary
            text = text + text_parts[0].decode(text_parts[1])
    # Last required conversion step
    # Help from: http://www.saltycrane.com/blog/2008/11/python-unicodeencodeerror-ascii-codec-cant-encode-character/
    text = unicode(text).encode("utf-8")

    # Return
    return uid, text, msg, attachment


def store_file(uid, msg):
    """Store the attachment with random name in file system

    Argument: User ID
              Attachment as message object

    Returns the file name without path of the created file

    Raises exception StoreFileError when an error occurs;
    Error message to print is stored as 'args'
    """


    # Get file suffix
    filename = msg.get_filename()   # File name as stored in attachment
    mo = re.search("(\.[^\.]*)$", os.path.basename(filename)) # Search for suffix
    if mo is None:  # Guess suffix if file suffix is not existing
        fsuff = mimetypes.guess_extension(msg.get_content_type())
        if not fsuff:
            fsuff = ""   # Empty suffix
    else:   # We found a match for the suffix
        fsuff = mo.group(1)


    # Check and create directory if required
    dpath = UserList[uid]['putfileto']   # Base directory
    try:
        os.mkdir(dpath)
    except OSError, e:
        # Ignore directory exists error
        if e.errno != errno.EEXIST:
            raise

    # Get a random file name
    fp = tempfile.NamedTemporaryFile(suffix=fsuff, prefix ='', dir = dpath, delete=False)
    filename = fp.name

    # Debug
    # print "Created DIR: " + dpath
    pinfo("Attachment saved to file (in chroot) " + filename)
    # Now finally write the file
    fp.write(msg.get_payload(decode=True))
    # Close file
    fp.close()

    # For JPEG image files try to trip all EXIF information from it
    if Opts['strip_exif']:    # when enabled
        if (re.search("jpe?g$", fsuff, re.IGNORECASE)):
            try:
                pinfo("Found jpeg image, strip EXIF tags with exiftool")
                # Call the exiftool it
                phandler = subprocess.Popen(["exiftool", "-all=", "-overwrite_original", filename], \
                                              shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Catch program output, only print it in case of error
                cmd_stdout, cmd_stderr = phandler.communicate()
                retcode = phandler.returncode
                if retcode < 0:
                    raise StoreFileError(cmd_stdout + cmd_stderr + "Tried to remove EXIF tags from image but exiftool was terminated by signal " + str(-retcode))
                elif retcode > 0:
                    raise StoreFileError(cmd_stdout + cmd_stderr + "Tried to remove EXIF tags from image but exiftool returned error code " + str(retcode))
            except OSError, e:
                raise StoreFileError(cmd_stdout + cmd_stderr + "Tried to remove EXIF tags from image but exiftool execution failed: " + str(e))
            except:
                perror(cmd_stdout + cmd_stderr)
                raise   # Other errors are passed further
            # Print program output as info message
            pinfo(cmd_stdout)
            pinfo(cmd_stderr)

    # When enabled, change access rights
    if Opts['chmod'] is not None:
        os.chmod(filename, Opts['chmod'])

    # Over and out, returning the pure file name
    return os.path.basename(filename)


def bitly_shorten(user, apikey, url):
  """
  Shorten URLs with the bit.ly service

  Parameters:
  user: bit.ly user name
  apikey: bit.ly API key
  url: URL to shorten

  return: Shortened URL

  Inspired from
  http://segfault.in/2010/10/shorten-urls-using-python-and-bit-ly/
  """

  params = urllib.urlencode({'longUrl': url, 'login': user, 'apiKey': apikey, 'format': 'json'})
  req = urllib2.Request("http://api.bit.ly/v3/shorten?%s" % params)
  response = urllib2.urlopen(req)
  j = simplejson.loads(response.read())
  if j['status_code'] == 200:
      return j['data']['url']
  raise BitlyMsgError('%s'%j['status_txt'])



# ********************************************************************************

# *** Main Program
def main():

    # *** Command line parsing
    cmd_usage="usage: %prog [options] args"
    cmd_desc ="""tweetfile - Don't call yourself, add it into your .forward file"""
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
    pinfo("Went into chroot with directory " + Opts['chroot_dir'])

    # Abort when different than no argument
    if len(cmd_args) != 0:
        perror("No command line arguments are expected!")
        cmd_parser.print_usage()
        return 1


    # *** First read stdin to extract the information for parsing
    try:
        uid, text, msg, getfile = extract_mail_content(sys.stdin)
    except ExtractMailError, detail:
        # Error encountered, most likely not allowed user
        pwarn(detail)
        return 1   # Parsing of .forward file should continue
    except:
        raise      # Other errors are just raised further

    # Debug
    pinfo("uid " + str(uid) + " --> " + UserList[uid]['rcpt'])
    pinfo("text " + text)
    if getfile is None:
        pinfo("No attachment found")
    else:
        pinfo("Attachment found with name " +  getfile.get_filename())


    # Store the attachment in file system
    if getfile is not None:
        try:
            # Add the urlbase to the filename
            file_link =  UserList[uid]['fileurlbase'] + "/" + store_file(uid, getfile)
        except StoreFileError, detail:
            # Error encountered, we just raise it
            perror(detail)
            raise
        except:
            raise      # Other errors are just raised further
    else:  # We had no file link
        file_link = None


    # Then tweet the stuff
    try:
       twit = twittermsg(UserList[uid]['twitter'])       # Create new object
       twit.doit(text, file_link)
       pinfo("Twitter update done")
       twit.finish()    # Cleanup
    except TwitterMsgError, detail:
        # Error encountered
        perr(detail)
        return 1   # failure
    except: # All other errors - propagate
       raise

    # Create new message with the tweet content
    mailbody = "Forwarded by tweetfile"
    if file_link:
        mailbody = "Link: " + file_link + "\n\n" + mailbody
    fmsg = email.mime.text.MIMEText(mailbody, "plain", "utf-8")
    fmsg["From"]    = msg["From"]
    fmsg["To"]      = "placeholder@sethdepot.org"
    fmsg["Subject"] = email.header.Header(text, "utf-8")
    # Finally forward the mail, when it is requested
    if Opts.has_key('testmode') and Opts['testmode']:
        pwarn("   No mail forwarding in testmode")
    elif UserList[uid]['forwardto'] is not None:
        try:   # Open SMTPConnection; Catch exceptions
            smtp = smtplib.SMTP(Opts['smtp_server_host'], Opts['smtp_server_port'])
        except (smtplib.SMTPException, socket.error), detail:
            perror("Establishing SMTP connection to " + \
                       Opts['smtp_server_host'] + ":"  + Opts['smtp_server_port'] + \
                   " failed: " + str(detail))
        except:
            raise      # Rais all other errors
        else:  # No error opening, continue
            for rcpts in UserList[uid]['forwardto']:  # Iterate over all reciptiens
                try:   # Send data; Catch exceptions
                    # Update fmsg rcpt
                    fmsg.replace_header('To', rcpts)
                    smtp.sendmail(fmsg['From'], rcpts, fmsg.as_string())
                except smtplib.SMTPException, detail:
                    perror("SMTP Mail sending failed: " + str(detail))
                    break
                else:
                    pinfo("  Successfully forwarded message to " + rcpts + "\n")
        # Over and out
        smtp.quit()


    # All done, over and out
    return 0



# *** Call Main program
__version__ = ''.join(filter(str.isdigit, "$LastChangedRevision$"))
if __version__ == "":
   __version__ = "(development version)"
if __name__ == "__main__":
    sys.exit(main())
