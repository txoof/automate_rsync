#!/bin/bash
tar_list=./tar_list.txt
tar_ball=automate_rsync.tgz
app_name=automate_rsync.py
version_number=`grep VERSION $app_name | sed -nE  's/^VERSION[ ]+=[ ]+(.*)/\1/p' | tr -d \'\"`

tar cvzf automate_rsync.tgz -T $tar_list
git commit -m "update tarball" $tar_ball

echo consider tagging and pushing this package:
printf "\tgit tag v$version_number\n"
printf "\tgit push origin v$version_number\n"
