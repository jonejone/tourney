#!/bin/bash
if [ ! -z $1 ]; then
    ATTRIB='-a$1'
fi

while find . -name "*.py" | 
    xargs inotifywait -e delete_self 2> /dev/null; do 
        python manage.py test -s $ATTRIB
    done
