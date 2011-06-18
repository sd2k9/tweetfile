# -*- coding: utf-8 -*-
# file name: ''tweetfileaccess.py''
#   project: Tweet a File
#  function: List of users and twitter credentials who
#            are allowed to use this service.
#            Separated file to remove these settings from main file
#      created: 2011-03-16
#  last change: $LastChangedRevision$
#
# Copyright (C) 2010 Robert Lange (robert.lange@s1999.tu-chemnitz.de)
# Licensed under the GNU General Public License, version 2
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#

# Read Program path for chroot base dir - disable when not needed
import sys

# *** Global settings as dictionary
Opts = {
    # Root directory to chroot to
    # This directory will serve as chroot for the program; the files will be placed below
    'chroot_dir': sys.path[0] + "/tweetfile_data",
    # 'chroot_dir': "/srv/www/default/tweetfile",
    # When set to another value that None this file permission is applied to all newly created files
    # 'chmod': None,
    'chmod': 0644,  # -rw-r--r--
    # set to true to automatically strip all EXIF information from
    # JPEG images
    # This needs a lot of additional FAKECHROOT_EXCLUDE_PATH settings;
    # See README for this
    'strip_exif': True,
    # 'strip_exif': False,

    #  bit.ly URL shortener user name and API key - None when not used
    # You can get it from here: https://bit.ly/a/your_api_key
   'bitly_api_user' : "username",
   'bitly_api_key'  : "apikey",
   # 'bitly_api_user' : None,
   # 'bitly_api_key' : None,
}


# *** Allowed users w/ return address
UserList = {
    0:{  # userid: arbitrary unique numerical user id
     'rcpt': 'recipient address',
     'allowedfrom': ['accept from sender address 1',
                     'accept from sender address 2',
                     '...',
      ],
     'putfileto':'directory relative to chroot without slash, put the received files here',
     'fileurlbase':'url under which the file in putfileto shows up, no trailing slash',
      # You need to register this application to your twitter account
      # to allow it's access
      # - Log into your account
      # - Go to Settings/Developer Applications (https://twitter.com/apps)
      # - Register a new applicaton
      # - Fill the data; Suggestions
      #   Application Name: tweetfile-<username>
      #   Description: Tweet a file
      #   Applicaton Website: https://github.com/sd2k9/tweetfile
      #   Application Type: Client
      #   Default Access type: Read & Write
      #   Use Twitter for login: Yes (checked)
      # - Then fill consumer_key and consumer_secret with the supplied data
      # - Execute program ./get_access_token.py userid to retrieve the
      #   access_token_* data and fill it here also
      'twitter': {
                  'consumer_key': '',
                  'consumer_secret': '',
                  'access_token_key': '',
                  'access_token_secret': ''
      }
    },
    #    Example:
    1:{  # userid
     'rcpt': 'tweetfile.5000@tweetfiler-domail.org',
     'allowedfrom': ['tweeter@gmail.com',
                     'mobile@softbunk.ne.jp',
      ],
     'putfileto':'greatuser',
     'fileurlbase':'http://sethdepot.org/share/tweetfile/greatuser',
      'twitter': {
                  'consumer_key': 'fdkjsfhjsdkfhkjasdkg',
                  'consumer_secret': 'jksdfhkjlsdafklsdjgskldjgklsdfjklasdjfkl',
                  'access_token_key': 'hklsafhkldsghksldhgkldkljdkljsdaklfjsdklfjsdlk',
                  'access_token_secret': 'klsdfdklsfjklsdjfkljdsklfjklsdjflkdsjlk'
      }
    },
}
