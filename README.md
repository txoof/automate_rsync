# automate_rsync
Configure rsync once, add multiple jobs with simple headings

Released under GPL V3.0

Created by Aaron Ciuffo (aaron.ciuffo gmail)

This script aims to create a simple method for configuring complex rsync jobs and
adding additional jobs easily.

Quick start (tl;dr):

  If no configuration file is found (~/.automate_rsyncrc) the script will walk you
  through the intial configuration.

    $ ./automate_rsync 

No configuration file was found at:  /Users/aaronciuffo/.automate_rsyncrc
Would you like to create one?
y/N: y

Which rsync binary would you like to use for backups?
Default:  /usr/bin/rsync
full path to rsync binary or press ENTER for default:

What global rsync options would you like to use?
Typical options are: -avzh
See the rsync man page for more information.
rsync options: -avzh

What delete options would you like to use?
For backups typical options are: --delete-excluded
See the rsync man page for more information.
delete options: --delete-excluded

What additional ssh options would you like to use with rsync?
All extra options need to be preceded with "-o"
Please see the rsync and ssh_config pages for more informaiton.
To force rsync and ssh to use ONLY a specified SSH key use: -o IdentitiesOnly=yes
extraSSH options: -o IdentitiesOnly=yes
gathering jobs...
No rsync jobs found.  Please add a job to /Users/aaronciuffo/.automate_rsyncrc
Would you like to interactively add a job?
Y/n: y

Please give this job a descriptive name such as "Remote Host - LocalDirectory"
jobName: ponies.horse - backup race stats

What is the *remote* username to use?
user: jockey

What is the hostname or IP address of the remote rsync host?
server: ponies.horse

What is the full path to the ssh key should be used with this server?
If no key is to be used or only one key per server is used this can be blank
If a specific key is used please set extraSSH=-o IdentitiesOnly=yes
sshKey: /home/jockey/.ssh/id_rsa-ponies

What is the full local path to be backedup?
localPath: /home/jockey/race_stats/

What is the full remote path?
If you you are using restricted rsync this path should be relative to the restricted path
For more information about securing passwordless rsync jobs with rrsync please see
https://ftp.samba.org/pub/unpacked/rsync/support/rrsync
remotePath: /home/jockey/backup_stats

What should be excluded?
Please see the rsync man page for more information on regular expressions and exclusions
Format: "/path/to/Dir1", "*Virtual.Machines", "*dump", "\.swp"
exclude: "*junk*", "/home/jockey/race_stats/depricated/"
Done adding your job: ponies.horse - backup race stats

For more information on configuring SSH, rsync and this script please see instructions.txt
