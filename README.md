# automate_rsync
Simplify running complex rsync jobs through an .ini file.

`automate_rsync` is writen entirely in Python 3 with standard modules and runs as a single executable file and should run in any \*nix like environment where rsync is available


## QUICK START
Copy & paste the lines below into the terminal to setup automated, unattended rsync jobs in macOS. If you are at all uneasy about running scripts downloaded and excuted without review, **GOOD FOR YOU!** You can review the scripts by cloning this repo, or downloading [this tar ball](https://github.com/txoof/automate_rsync/raw/master/automate_rsync.tgz).
1. Install automate_rsync system wide (only needs to be done once by an admin user
    * `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/txoof/automate_rsync/master/remote_install/system_install.sh)"`
    * `nano ~/.config/com.txoof.automate_rsync/automate_rsync.ini`
3. [Allow `bash` disk access](https://www.tech-otaku.com/mac/manually-granting-applications-full-disk-access-macos-catalina/)
2. Install a launchd plist to run automate_rysnc to run every 30 minutes (this must be done for every user)
    * `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/txoof/automate_rsync/master/remote_install/launchd_install.sh)"`


## Use
`$ automate_rsync.py`

```
automate_rsync -- run complex rsync jobs from an ini file

optional arguments:
  -h, --help  show this help message and exit
  -v          enable verbose output
  -d          set rsync --dry-run
```

## Use in macOS
automate_rsync can run from a LaunchDaemon in macOS. Begining in Mojave and later, Apple has implemented restrictions on how applications access certain folders within the user directory. This restriction also applies to shell utilities such as bash. 

When this script is run from the `terminal.app`, those privliges are likely already granted by the user when prompted by the OS on the first use. Launchd runs this script by envoking `bash -c "/usr/local/bin/automate_rsync.py"`. As such, `bash` needs to be granted full disk access large parts of the user's home directory. This must be done for every user.

* Provide full disk access to the `bash` binary
    * See these [instructions (12 March 2020)](https://www.tech-otaku.com/mac/manually-granting-applications-full-disk-access-macos-catalina/)

To install and enable `automate_rsync` use the included `install.sh` script and `daemon_install.sh` script, or do the following manually:
1. `$ cp automate_rsync.py /usr/local/bin/`
    * Provides system wide access to the binary
2. `$ cp com.txoof.automatersync.plist ~/Library/LaunchAgents` 
    * this must be done for each user
    * this is the launch agent file that launchdaemon will use to start the script
    * the default schedule to run is every 30 minutes (1800 seconds) see: `<key>StartInterval<key>`
4. `$ launchctl load ~/Library/LaunchAgets/com.txoof.automatersync.plist`
    * Make launchd aware of the plist file


### Diagnosing launchd issues
Launchd does not offer great debugging tools. Jobs that fail to run will do so very quietly. If you are having trouble with automate_rsync, it is likely due to some problem with the environment under which it runs from launchd. The bash shell that is run by the daemon is an extremely stripped down version without your regular LANG and PATH environment variables. This can cause all sorts of odd behavior.

Tips for debugging:
* Double check that automate_rsync runs on the command line. If it fails under normal circumstances, you've got bigger problems.
* Check in the `console.app` and search for 'com.txoof.automatersync' in the system.log section for some hints. 
    * `abnormal code:` indicates the script terminated with an error:
        * 1: general errors - could be just about anything
        * 127: command not found - likely means that your python environment is broken
    * Change the .plist file to match `<string>export LANG=en_US.UTF-8; /usr/local/bin/automate_rsync.py &gt;&gt; ~/plist.log</string>`
        * this will redirect any error output to `~/plist.log` for further review
    * Try adding the path to your rsync binary to your `automate_rsync.ini` file. 
        * use `$ which rsync` to determine the path to your rsync executable
        * add that path to your `automate_rsync.ini` file using `rsync_bin = /path/to/your/rsync` under the `[%base_config]` section




## Setup
The first time automate_rsync runs it will create an `.ini` file in `~/.config/com.txoof.automate_rsync` and remind you to edit the configuration file:
```
$ automate_rsync.py
automate_rsync
ERROR: no jobs are defined.
Edit /Users/jbuck/.config/com.txoof.automate_rsync/automate_rsync.ini
```

### .ini file
The default, suggested settings are shown below

The .ini file contains three main parts:

#### Basic configuration
```
[%base_config]
## options to use for all rsync jobs
rsync_options = -a -z
## deletion strategies to use (leave blank for none)
delete_options = --delete-excluded
```

#### SSH Options 
Options passed to the ssh module 
```
[%ssh_opts]
## extra options to pass to the ssh module
## -e "ssh <extrassh>"
## -o IdentitiesOnly=yes forces the use of one single key file
## this prevents ssh from searching all availble keys
extrassh = -o IdentitiesOnly=yes
```

#### Individual Jobs 
Each job must have a unique name
Add an `=` to the job name to disable it: `[=Home Dir -> Backup Server]`
```
[Job Title Goes Here]
## `direction`: optional -- not required (defaults to local-remote)
## this option controls the direction of the sync local-remote
## local-remote (default) rsyncs FROM the LOCAL computer to a REMOTE computer
## remote-local rsyncs FROM remote computer to LOCAL computer
direction: <direction of sync from: local-remote or from: remote-local>
# direction: local-remote

## `user`: optional -- not required for local syncs that do not use ssh
user = <remote username>
# user = jbuck

## `remotehost`: optional -- not required for local syncs that do not use ssh
remotehost = <remote ip or host name>
# remotehost = backupserver.local

## `sshkey`: optional -- not required for local syncs that do not use ssh
sshkey = <optional: path to private ssh key>

## `localpath`: required 
localpath = <local path to sync from -- mind the trailing `/`>
# localpath = /Users/jbuck/Documents <-- this will sync the dir
# localpath = /Users/jbuck/Documents/ <-- this will sync the contents only

## `remotepath`: required
remotepath = <remote path to sync into -- mind the trailing `/`>

## `exclude`: optional
exclude = <comma separated list of patterns to exclude from sync>
# exclude = .DS_Store, data_base, /Downloads, /Applications

## `log_file`: optional
log_file = <path to log file for this job - each job can have a different log file>
# log_file = ~/jobs.log

## `timeout`: optional
timeout = <seconds before rsync job times out (default: 'None' (no timeout))>
# timeout = 600
# timeout = None

## `kill`: optional
kill = <True/False - kill the job after the timeout expires (default: False)>
# kill = False

## `max_log`: optional
max_log = <max log size in bytes before rollover (1048576 bytes == 1 megabyte) (default: 0 no limit)>
# max_log = 5242880
    
```
    
### Example Configuration
```
[%base_config]
# -a: (bsd) archive mode; same as -rlptgoD (no -H)
# -z: (bsd) compress file data during the transfer
rsync_options = -a -z
# --delete-excluded: (bsd) also delete excluded files from dest dirs
delete_options = --delete-excluded

[%ssh_opts]
# -o IdentitiesOnly=yes: force the use of a single key
extrassh = -o IdentitiesOnly=yes

[iMac->MediaServer - Music]
# username at remote host
user = media
# ip or network name of remote host
remotehost = 192.168.1.9
# private ssh keyfile to use (this is only useful with the '-o IdentitiesOnly' option
sshkey = /Users/myuser/.ssh/id_rsa-media_server_restricted_key
# localpath to send
localpath = /Users/myuser/Music/
# remote path to use -- in this case a restricted rsync path
# this path actually sits in '/home/media/MUSIC/' but is truncated by 
# restricted rsync to show the last portion of the path
# this prevents malicious or accidental damage outside of the MUSIC directory
remotepath = /
# patterns to exclude separated by a ','
exclude = .AppleDouble, TV.*Shows, Music/Other, .DS_Store*
# log file
log_file = ~/Music_rsync.log
# max size before roll over (5mB)
max_log = 5242880
# timeout for job in seconds (20 minutes)
timeout = 1200
# kill the job after the timeout
kill = False
   
[local backup -> ColdBackup drive]
# this is a local rsync using a drive mounted locally
localpath = /Users/myuser/src
remotepath = /Volumes/ColdBackup
    
    
[image_store -> my iMac]
    # sync photos from an image store on a rrsync host
direction = remote-local
username = photo_user
    remotehost = image-store.local
    sshkey = /Users/myuser/.ssh/id_rsa-image_store_restricted_key
    localpath = /Users/myuser/Documents/Pictures/image-store
    remotepath = /stock_photos
    logfile = ~/image_store.log
    max_log = 2000000
    timeout = 12000
    kill = False
```


```python
! /Users/aaronciuffo/bin/develtools/mdconvert README.ipynb

```

    [NbConvertApp] Converting notebook README.ipynb to markdown

