#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo 'Must provide path to dev-env'
    exit 0
fi

if [ ! -d "./bin" ]; then
	virtualenv -p /usr/bin/python3 .
	source bin/activate
	pip3 install -r ./requirements.txt
	cd $1/backing-services/freeipa
	./freeipa-delete-data.sh
	./freeipa-decompress-data.sh
	cd - && cd ./ui && npm install && cd ..
fi

cd $1
bash --init-file <(echo "source bin/activate") -c "./dev-env up admin api"
