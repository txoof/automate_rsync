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
The .ini file is stored in `~/.config/com.txoof.automate_rsync`

The .ini file contains a basic configuration and one or more jobs. Most settings are optional. The example below is provided in `~/.config/com.txoof.automate_rsync` if it does not exist.

```
##### Base Configuration #####
## defines basic configuration ##

# `rsync_bin`: OPTIONAL -- path to rsync binary
# default: None -- automate_rsync searches $PATH for this 
#rsync_bin = /path/to/binary

# `global_rsync`: OPTIONAL -- add these options to all rsync jobs
#global_rsync = -a -z -v

##########################################################################
# create at least one job following the examples below
# white space and lines beginning with a `#` are ignored
# paths with spaces must be escaped: 
# `/my path/with spaces` becomes `/my\ path/with\ spaces`
# 
# To disable a job add a `#` to the job name. All example jobs below are
# disabled.
##########################################################################


[#Job]
##### Individual Job #####
## defines configuration for each job ##
# Remove the `#` in the job name to enable the job

# `direction`: OPTIONAL -- direction to run sync 'local-remote' or 'remote-local'
# local-remote -- SRC: localpath DEST: [USER@HOST]:remotepath (default if not specified)
# remote-local -- SRC: [USER@HOST]:remotepath DEST: localpath
#direction = local-remote

# `rsync_options`: OPTIONAL -- additional rsync options local to this job
# use this to specify any additional options that will apply to this job 
# these options are appended to the global options -- be careful not to double up or
# add conflicting options
#rsync --delete-excluded --port 8080

# `ssh_options`: OPTIONAL -- ssh options for this job in the ssh_config format 
# see the ssh and ssh_config(5) man pages for details
# ssh_options are added to the rsync options as: -e ssh "`ssh_options`"
#ssh_options = -p 22 -o IdentitiesOnly=yes

# `sshkey`: OPTIONAL -- specify a specific key for ssh
# this is particularly useful in combination with restricted rsync (rrsync)
# this option **MUST** be used with 'ssh_options = -o IdentitiesOnly=yes' otherwise
# ssh will use the first matching key it finds. 
#sshkey = /full/path/to/private/key-id_rsa

# `user`: OPTIONAL -- username at remote host
# this is specified as the 'USER@remotehost' portion of the rsync command
#user = my_remote_username

# `remotehost`: OPTIONAL -- ip address or hostname for remote host
# this will be added as the user@REMOTEHOST portion of the rsync command
#remotehost = 192.16.1.20
#remotehost = my_backup.host.foo

# `remotepath`: REQUIRED -- relative path to use as either SRC or DEST in rsync command
# in most cases, this will be relative to the root file system: /home/my_user/my_data/dir
# if using rrsync on the remote, this is relative to the root of the restricted fs: 
# /host_imac_data or /host_acer_data
#remotepath = /path/relative/to/root/of/remote/file/system
# BE SURE TO ESCAPE SPACES! 
#remotepath = /remote\ path/that\ has/spaces/

# `localpath`: REQUIRED -- local path relative to the local file system
#localpath = /path/to/my/datas
# BE SURE TO ESCAPE SPACES! 
#localpath = /path/with\ lots/of \spaces

# `exclude`: OPTIONAL -- comma separated list of exclude patterns
#exclude = .DS_Store, .git/*, core_dumps, /super/secret/data

# `log_file`: OPTIONAL -- path to log file for this job
# each job can have its own log file or the same file can be used for all jobs.
# logging only occurs if `-v` is included in the global_rsync or rsync_options. 
# Logging can also be triggered by specifying `-v` on the command line. 
# Increase verbosity by adding multiple `-v`
#log_file = /path/to/log/file.log

# `max_log`: OPTIONAL -- (int) maximum size of log file in bytes (default: no limit)
# (1048576 bytes == 1 megabyte)
# after the job is completed and the max size is larger than the specified size, 
# the log file will roll over to log_file.1 and a new log file will be generated
# log files will always exceed the max size by at least one byte. If space is an issue,
# set the max_log size small enough to accomodate potentially large logs.
#max_log = 52428800

# `timeout`: OPTIONAL -- (int) time in seconds before this job is optionally killed
# (default: false)
# if no timeout is set, all jobs will run concurrently
# when the timeout expires, the job can be optionally killed; if it is not killed
# any subsiquent jobs will be spawned and allowed to run concurently
# if bandwidth is an issue it may be good to choose extra long timeouts and use the 
# kill option.
#timeout = 1200

# `kill`: OPTIONAL -- (True/False) kill the job after the timeout has been reached (default)
# this option is only useful if a timeout is set
# if the timeout is exceeded and `kill` is false, the following job will be spawned and
# run concurrently
#kill = true
```


```python
! /Users/aaronciuffo/bin/develtools/mdconvert README.ipynb

```

    [NbConvertApp] Converting notebook README.ipynb to markdown



```python
s
```
