#!/bin/bash

function verbose_eval {
    echo - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    echo $*
    echo
    eval $*
    echo ---------------------------------------------------------------------
    echo
}

export PYTHONPATH="src/django-weave/:${PYTHONPATH}"
export DJANGO_SETTINGS_MODULE=testproject.settings

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
    echo execute manage.py
    verbose_eval python src/django-weave/testproject/manage.py $*
fi
