#!/bin/bash

FILENAME=$1

if  [ ! -f  "sample.zip"  ]; then
    echo  "new sample.zip will be created."
else
    echo  "old sample.zip will be removed."
    rm  sample.zip
fi

if  [ ! -f  "index.py"  ]; then
    echo  "new index.py will be created."
else
    echo  "old index.py will be removed."
    rm  fc_function_for_remediation_kms_tag.py
fi
cp $FILENAME fc_function_for_remediation_kms_tag.py
zip -r -j sample.zip fc_function_for_remediation_kms_tag.py
