#!/bin/bash
install_path=/usr/local/bin
executable=automate_rsync.py

echo "This script will install automate_rsync in $install_path"

if [ ! -d $install_path ]; then
  echo "This likely requires super user permissions"
  echo "allow this script to make $install_path? -- ctrl-c to cancel"
  sudo mkdir -p $install_path
fi

cp $executable $install_path/${executable:r}
