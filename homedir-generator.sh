#!/bin/bash

# In production, we need to create zfs datasets for each user home directory on the nfs server
# This is done by a bash script similar to this one that creates home directories whenever an IPA user does not have one
# it's limited to users with home directories in /home/users
# A script creates the home directories/zfs datasets because 
#     a) it limits the need for the account microservice to have an ssh key that gives it access to the nfs server
#     b) mkhomedir / oddjob-mkhomedir are terrible
#
# See NaC for the production implementation

# If you create a user while in development, you'll need to run this script to have 
# their /etc/skel setup before you can use any of the services that require fs access
# i.e. most of them
# It'l also fix any permissions needed for web hosting

if [ "$EUID" -ne 0 ]
  then echo "Homedir generator requires sudo to use chown"
  exit
fi

if [ "$PWD" == "/" ]
  then echo "Do not run this in your root directory as it will break your system permissions"
  exit
fi


printf "[$(date -u)] Starting user home directory generator / permissions fixer\n"

# www-data uid and gid is 33 on ubuntu/debian
www_data_id="33"

# Ensure home and skel
mkdir -p ./home/users
mkdir -p ./etc/skel

while true
do
  printf "\n[$(date -u)] Scanning IPA users (with home dirs in /home/users/*) to find users missing home directories / bad permissions\n"

  # Get list of every IPA user
  all_users=$(docker-compose exec -T ipa.netsoc.local bash -c "echo netsoc_freeipa | kinit admin &>/dev/null && ipa user-find --all" | awk '/User login/{ print $3 }')
  
  for user in $all_users
  do 
    printf "[$(date -u)] Checking $user...\n"

    # Get IPA user info
    uid=`docker-compose exec -T ipa.netsoc.local bash -c "getent passwd $user | cut -d ':' -f 3"`
    gid=`docker-compose exec -T ipa.netsoc.local bash -c "getent passwd $user | cut -d ':' -f 4"`
    home=`docker-compose exec -T ipa.netsoc.local bash -c "getent passwd $user | cut -d ':' -f 6"`

    # If their homedir is in /home/users
    if [[ $home == "/home/users/$user" ]]; then

      # Create it if it doesn't exist
      if [ ! -d "./home/users/$user" ]; then
        printf "[$(date -u)] $user ($uid:$gid) does not have a home directory, setting them up now\n"
        
        # Make home dir
        mkdir ./home/users/$user

        # Copy in skel
        cp -a ./etc/skel/. ./home/users/$user/.

        # Chown every file we copied from skel to them
        find ./home/users/$user/ -name "*"  -not -path "./home/users/$user/" -exec chown $uid:$uid {} \;      
      else
        printf "[$(date -u)] $user already has home directory setup\n"
      fi

      printf "[$(date -u)] $user ensuring correct permissions on homedir and www dir\n"
      
      # Give www-data group ownership so we can serve websites in the future
      chown $uid:$www_data_id ./home/users/$user

      # drwxr-x--- their home dir for www-data group perms
      chmod 750 ./home/users/$user

      # Ensure www dir setup
      mkdir -p ./home/users/$user/www
      chown $uid:$www_data_id ./home/users/$user/www
      chmod 750 ./home/users/$user/www
      chmod g+s ./home/users/$user/www  



    else
      printf "[$(date -u)] $user does not have a home directory pointed inside /home/users/, ignoring user\n"
    fi
  done

  printf "[$(date -u)] Scanning complete, sleeping for 15 secs\n"
  sleep 15
done
