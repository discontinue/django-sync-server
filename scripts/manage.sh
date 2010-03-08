#!/bin/bash

function verbose_eval {
    echo - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    echo $*
    echo
    eval $*
    echo ---------------------------------------------------------------------
    echo
}

activate_file="./bin/activate"

echo _____________________________________________________________________
echo activate the virtual environment:

if [ ! -f $activate_file ]
then
    echo
    echo " **** Error: File '$activate_file' not exists!"
    echo
else
    verbose_eval source $activate_file
    
    echo _____________________________________________________________________
    echo Go into source folder:
    verbose_eval cd src/django-weave/weave_project/
    
    echo _____________________________________________________________________
    echo execute manage.py
    verbose_eval python manage.py $*
fi
