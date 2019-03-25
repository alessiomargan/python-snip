#! /bin/bash 
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv -a . -r requirements.txt -p `which python3` $1
