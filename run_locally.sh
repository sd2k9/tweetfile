#/bin/sh

clear

# Run locally for debugging with some example data (not in git)
FAKECHROOT_EXCLUDE_PATH=/dev:/usr/lib/python3.5 PYTHONPATH=$PWD/pylib/lib/python3.5/site-packages fakechroot ./tweetfile.py < testmail_no_attach.eml

echo
echo
FAKECHROOT_EXCLUDE_PATH=/dev:/usr/lib/python3.5 PYTHONPATH=$PWD/pylib/lib/python3.5/site-packages fakechroot ./tweetfile.py < testmail_attach.eml

echo
echo
FAKECHROOT_EXCLUDE_PATH=/dev:/usr/lib/python3.5 PYTHONPATH=$PWD/pylib/lib/python3.5/site-packages fakechroot ./tweetfile.py < testmail_umlaute.eml

echo
echo
FAKECHROOT_EXCLUDE_PATH=/dev:/usr/lib/python3.5 PYTHONPATH=$PWD/pylib/lib/python3.5/site-packages fakechroot ./tweetfile.py < testmail_nihongo_umlaute.eml

echo
echo

FAKECHROOT_EXCLUDE_PATH=/dev:/usr/lib/python3.5:/usr/bin:/usr/share/perl:/usr/share/perl5:/usr/lib/perl PYTHONPATH=$PWD/pylib/lib/python3.5/site-packages fakechroot ./tweetfile.py < mail_pic.eml
