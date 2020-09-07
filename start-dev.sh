#!/bin/bash

if [ ! -d "./bin" ]; then
	virtualenv -p /usr/bin/python3 .
	source bin/activate
	pip install -r ./requirements.txt
	./freeipa-delete-data.sh
	./freeipa-decompress-data.sh
	cd ./ui && npm install && cd ..
	
fi

bash --init-file <(echo "source bin/activate")
