#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo 'Must provide path to dev-env. For example: ./start-dev.sh ../dev-env'
    exit 1
fi

WD=`pwd`
DEV_ENV=$(readlink -f $1)

if [ ! -d "./bin" ]; then
	virtualenv -p /usr/bin/python3 .
	source bin/activate
	pip3 install -r ./requirements.txt
	cd $PWD/ui
	npm install
	cd $PWD
fi

cd $DEV_ENV
bash --init-file <(echo "source bin/activate") -c "./dev-env stop ipa"
$DEV_ENV/backing-services/freeipa/freeipa-delete-data.sh
$DEV_ENV/backing-services/freeipa/freeipa-decompress-data.sh
bash --init-file <(echo "source bin/activate") -c "./dev-env start ipa"

echo "version: \"3.7\"
services:
  cloud:
    volumes:
      - ${WD}/ui:/app
  api:
    volumes:
      - ${WD}/api:/app
      - ${WD}/api/requirements.txt:/requirements.txt
      - ${WD}/config.sample.yml:/config.yml
" > ./cloud/docker-compose.override.yml

bash --init-file <(echo "source bin/activate") -c "./dev-env up cloud api"
