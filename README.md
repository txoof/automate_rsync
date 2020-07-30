# automate_rsync
Simplify running complex rsync jobs through an .ini file.

automate_rsync is writen entirely in Python 3 with standard modules and runs as a single file.

## Use
`$ automate_rsync.py`

```
automate_rsync -- run complex rsync jobs from an ini file

optional arguments:
  -h, --help  show this help message and exit
  -v          enable verbose output
  -d          set rsync --dry-run
```

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
[jobs]
## `user`: not required for local syncs that do not use ssh
user = <optional: remote username>

## `remotehost`: not required for local syncs that do not use ssh
remotehost = <optional: ip or host name>

## `sshkey`:not required for local syncs that do not use ssh
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
    
[local backup -> ColdBackup drive]
# this is a local rsync using a drive mounted locally
localpath = /Users/myuser/src
remotepath = /Volumes/ColdBackup
```


```python
%alias mdc /Users/aaronciuffo/bin/develtools/mdconvert README.ipynb
%mdc
```

    [NbConvertApp] Converting notebook README.ipynb to markdown

