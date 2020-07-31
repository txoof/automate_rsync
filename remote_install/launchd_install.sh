#!/bin/bash
launch_agent_path=~/Library/LaunchAgents
plist_file=com.txoof.automatersync.plist
url=https://raw.githubusercontent.com/txoof/automate_rsync/master/com.txoof.automatersync.plist


pushd () {
  command pushd "$@" > /dev/null
}

popd () {
  command popd "$@" > /dev/null
}


if [ ! -d $launch_agent_path ]; then
  mkdir -p $launch_agent_path
fi

echo "downloading plist file"
pushd $launch_agent_path
curl -s -O $url
popd
launchctl load $launch_agent_path/$plist_file
printf "\nautomate_rsync will now run every 1800 seconds (30 min).\n"
printf "edit $launch_agent_path/$plist_file to change the interval\n"
printf "############################################################\n"
printf "it is critical that you have provided bash full disk access!\n"
printf "############################################################\n"
printf "if you have not done this yet see: https://www.tech-otaku.com/mac/manually-granting-applications-full-disk-access-macos-catalina/ \n"

