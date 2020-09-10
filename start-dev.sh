#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo 'Must provide path to dev-env. For example: ./start-dev.sh ../dev-env'
    exit 1
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

WD=`pwd`
cd $1

if [ ! -f "./admin/docker-compose.override.yml" ]; then
	echo "version: \"3.7\" 
services:
  admin:
    volumes:
      - ${WD}/ui:/app
  api:
    volumes:
      - ${WD}/api:/app
      - ${WD}/api/requirements.txt:/requirements.txt
      - ${WD}/config.sample.yml:/config.yml
" > ./admin/docker-compose.override.yml
fi

bash --init-file <(echo "source bin/activate") -c "./dev-env up admin api"
