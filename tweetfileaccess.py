# -*- coding: utf-8 -*-
# file name: ''mail2webuser.py''
#  project: eMail Web Interface
# function: List of users, passwords and return address who
#           are allowed to use this service.
#           Separated file to remove these settings from main file
#      created: 2010-10-22
#  last change: $LastChangedRevision$
#
# Copyright (C) 2010 Robert Lange (robert.lange@s1999.tu-chemnitz.de)
# Licensed under the GNU General Public License, version 2
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#

# *** Allowed users w/ return address
UserList = [
    {'from': 'from mail address',
     'code': 'passphrase in subject line',
     'replyto': 'send replies to this address, usually identical to from' },
#    Example:
#    {'from': 'sd2k9@github.com',
#     'code': '12345',
#     'replyto': 'secret_address@myhideout.com' },
    ]
