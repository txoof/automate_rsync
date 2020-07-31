#!/bin/bash
install_path=/usr/local/bin
executable=automate_rsync.py
script="https://raw.githubusercontent.com/txoof/automate_rsync/master/automate_rsync.py"


pushd () {
  command pushd "$@" > /dev/null
}

popd () {
  command popd "$@" > /dev/null
}

echo "This script will install automate_rsync in $install_path and create directories as needed"

if [ ! -d $install_path ]; then
  echo "This likely requires super user permissions"
  echo "allow this script to make $install_path? -- ctrl-c to cancel"
  sudo mkdir -p $install_path
fi

pushd $install_path
echo "downloading script"
curl -s -O $script
chmod +x $install_path/$executable
popd
printf "\n"
/usr/local/bin/automate_rsync.py
printf "\nDon't forget to add jobs before continuing!"

