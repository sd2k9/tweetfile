#!/bin/bash
#
# Shell script to call a program, and flag it's execution in case there
# is any output from the program.
#
# Copyright (C) 2010 Robert Lange (robert.lange@s1999.tu-chemnitz.de)
# Licensed under the GNU General Public License, version 2
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
#
# Crontab-Entry for simple log archiving
# # mail2web: Simple Logfile cleaner: Every 2 weeks make one backup
#   24           2       11,21    *     *      cd $HOME/mail2web; bzip2 -c watcher_report_output.log > watcher_report_output.log.bak.bz2 ; rm watcher_report_output.log
#
#
# The output is mailed to some location.
# Further calls are then prevented by a status file
# -> This is currently disabled because there is always some debug output
#

# *** Settings
PROG_CMD="./mail2web.py"
LOG_FILE="./weather_info_fetch.suspend"
MAIL_CMD="mail"
MAIL_TO_ME="MYMAILADDRESS"
# Send a mail to a tweetbymail-account - currently disabled
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
  $MAIL_CMD -s "$HOSTNAME: mail2web report" $MAIL_TO_ME < $LOG_FILE
  # Twitter failure - will not work yet
  #  $MAIL_CMD -s "EARTHQUAKE Failing" $MAIL_TO_TWITTER

  # TEMPORARY CLEAR LOGFILE AGAIN, DON'T WANNA FAIL
  rm $LOG_FILE

else
  # All OK
  echo "Execution OK"
  echo
fi

