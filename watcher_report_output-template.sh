#!/bin/bash
#
# Shell script to call a program, and flag it's execution in case there
# is any output from the program.
#
# Copyright (C) 2010 Robert Lange <sd2k9@sethdepot.org>
# Licensed under the GNU General Public License, version 2
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
# CURRENTLY FLAGGING IS DISABLED! JUST MAILING
#
# Crontab Entry for simple backup:
# # tweetfile: Simple Logfile cleaner: Every 2 weeks make one backup
#   24           2       11,21    *     *      cd $HOME/tweetfile; bzip2 -c watcher_report_output.log > watcher_report_output.log.bak.bz2 ; rm watcher_report_output.log
#
#
# The output is mailed to some location.
# Further calls are then prevented by a status file
# -> This is currently disabled because there is always some debug output
#

# *** Settings
# PROG_CMD="./tweetfile.py"
PROG_CMD="./tweetfile.py --quiet"
LOG_FILE="./tweetfile.suspend"
MAIL_CMD="mail"
MAIL_TO_ME="MYMAILADDRESS"
# Send a mail to a tweetbymail-account
MAIL_TO_TWITTER="MYtweetbymailADDRESS"
# Hostname used in the  mail subject
HOSTNAME="MYHOSTNAME"

# Print current time
echo
date


# *** Execute and check for return
if [ -s "$LOG_FILE" ]; then
  # Banned execution
  echo "Further execution prevented, because lockfile $LOG_FILE is non-zero"
  exit
else
  echo "Executing $PROG_CMD with STDIN..."
  cat | $PROG_CMD &> $LOG_FILE
fi


# *** Error in execution?
if [ -s "$LOG_FILE" ]; then
  echo "Error encountered!"
  echo "Content of $LOG_FILE:"
  cat $LOG_FILE

  # TODO: Mail the message me
  $MAIL_CMD -s "$HOSTNAME: tweetfile report" $MAIL_TO_ME < $LOG_FILE
  # Twitter failure
  $MAIL_CMD -s "TWEETFILE Failing" $MAIL_TO_TWITTER

  # TEMPORARY CLEAR LOGFILE AGAIN, DON'T WANNA FAIL
  # rm $LOG_FILE

else
  # All OK
  echo "Execution OK"
  echo
fi

