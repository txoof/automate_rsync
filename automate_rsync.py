#!/usr/bin/env python3
# coding: utf-8








import configparser
from pathlib import Path
import os
import shutil
import sys
import logging
import tempfile
import uuid
import re
import shlex
import subprocess
import argparse
from datetime import datetime





# CONSTANTS
VERSION = '3.0.04-rc2'
APP_NAME = 'automate_rsync'
DEVEL_NAME = 'com.txoof'
CONFIG_FILE = f'{APP_NAME}.ini'


EXPECTED_BASE_KEYS = {'rsync_bin': None,
                      'rsync_options': '',
                      'delete_options': '',
                      }

EXPECTED_JOB_KEYS = {'user': None,
                     'remotehost': None,
                     'sshkey': None,
                     'localpath': None,
                     'remotepath': None,
                     'exclude': [],
                     'log_file': '/dev/null',
                     'max_log': 0,
                     'timeout': None,
                     'kill': False                     
                    }

EXPECTED_SSH_KEYS = {'extrassh': ''}

CONFIG_PATH = Path(f'~/.config/{DEVEL_NAME}.{APP_NAME}').expanduser().absolute()





def sample_config():
    return '''[%base_config]
## `rsync_bin`: optional -- path to rsync bin; useful if not in $PATH
rsync_bin = None
## `rsync_options`: optional -- options to use for all rsync jobs
rsync_options = -a -z
## `delete_options`: optional -- deletion strategies to use (leave blank for none)
delete_options = --delete-excluded

[%ssh_opts]
## extra options to pass to the ssh module
## -e "ssh <extrassh>"
## -o IdentitiesOnly=yes forces the use of one single key file
## this prevents ssh from searching all availble keys
extrassh = -o IdentitiesOnly=yes


## each 'job' must include at minimum the keys "localpath" and "remotepath"
## other keys are optional (see the example below)
## add an `=` to the beginning of a job to disable it
## copy this TEMPLATE and remove the `=` to label each job
[=TEMPLATE]
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


## Local sync example (disabled)
## sync the entire directory `foo` into `ColdStorage`
[=Foo -> Bar Local Sync]
localpath = /Users/jbuck/Documents/foo
remotepath = /Volumes/ColdStorage/


## Remote sync over ssh with specific ssh key (disabled)
## this is particularly useful when using restricted rsync at the remote end
[=iMac JBuck -> Backup Host]
user = jbuck
remotehost = backups.local
sshkey = /Users/jbuck/.ssh/id_rsa-backups
localpath = /Users/jbuck/Documents
## Note: this is the path **relative** to the remote filesystem
## Restricted rsync exposes only exposes a portion of the remote file system
## that portion is treated as the "root" of the file system
remotepath = /iMac.backups/
exclude = .AppleDouble, .DS_Store, .git, .local, /Library, /Application*, /Music
timeout = 600
kill = False
log_file = ~/documents_rsync.log
# 5 mB = 52428800 bytes
max_log = 52428800'''





def parse_args():
    parser = argparse.ArgumentParser(description=f'{APP_NAME} v{VERSION} -- run complex rsync jobs from an ini file')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='enable verbose output -- can be added multiple times')
    parser.add_argument('-d', '--dry_run', dest='dry_run', action='store_true', default=False, help='set rsync --dry-run')
    parser.add_argument('-V', '--version', dest='version', action='store_true', default=False, help='display version and exit')
    args, unknown_args = parser.parse_known_args()
    
    return args, unknown_args





def get_config(file):
    file = Path(file)
    
    if not file.exists():
        file.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        try:
            out_file = open(file, 'w')
            out_file.writelines(sample_config())
            out_file.close()
        except OSError as e:
            do_exit(e, 2)

    config = configparser.ConfigParser()
        
    config.read(file)
    
    return config





def parse_job(job):
    expected_keys=EXPECTED_JOB_KEYS
    parsed_job = {}
    for key in expected_keys:
        try:
            parsed_job[key] = job[key]
        except KeyError:
            parsed_job[key] = expected_keys[key]
    return parsed_job 





def parse_config(config):
    '''build dictionary from configparser section using expected key/values'''
    
    expected_base_keys = EXPECTED_BASE_KEYS
    expected_ssh_keys = EXPECTED_SSH_KEYS
    
    base_config = {}
    ssh_opts = {}
    
    for key in expected_base_keys:
        try:
            base_config[key] = config['%base_config'][key]
        except KeyError:
            base_config[key] = expected_base_keys[key]
    
    for key in expected_ssh_keys:
        try:
            ssh_opts[key] = config['%ssh_opts'][key]
        except KeyError:
            ssh_opts[key] = expected_ssh_keys[key]
    return (base_config, ssh_opts)





def build_rsync_command(name, job, base_config, ssh_opts, tempdir, dry_run=False, verbose=False):
    '''build an rsync from ini file
    
    Args:
        name(`str`): name of the job -- used for identifying exclude file
        job(`dict`): individual job from ini 
        base_config(`dict`): base_config from ini
        ssh_opts(`dict`): ssh_opts from ini
        tempdir(`Path`): path to temporary directory for exclude files
        dry_run(`bool`): add `--dry-run` to rsync command for testing
        verbose(`int`): add n `-v` to rsync command for increased debugging
    
    Returns:
        string -- rsync command'''
    
    name = re.sub(r'[\W_]+', '', name) + str(uuid.uuid4())
    
    rsync_command = []
    ssh_command = ''
    tempdir = Path(tempdir)
    
    # get the rsync binary path
    if base_config['rsync_bin']:
        rsync_bin = base_config['rsync_bin']
    else:
        try:
            stream = os.popen('which rsync')
            rsync_bin = stream.read()
        except Exception as e:
            do_exit(e, 1)
        
    if not rsync_bin:
        do_exit(f'could not locate rsync binary in `$PATH`\nconsider adding:\n"rsync_bin=/path/to/rsync"\n to [%base_config] section of {CONFIG_PATH}')
    
    # add the binary
    rsync_command.append(rsync_bin)
    # add the options from the ini file
    rsync_command.append(base_config['rsync_options'])
    
    # add additional options from the args
    if dry_run:
        rsync_command.append('--dry-run')
        
    if verbose:
        rsync_command.append('-'+'v'*verbose)
    
    rsync_command.append(base_config['delete_options'])
    
    if job['sshkey']:
            ssh_command = f'ssh -o IdentitiesOnly=yes -i {job["sshkey"]}'
        
    if len(ssh_command) > 0:
        rsync_command.append(f'-e "{ssh_command}"')
    
    
    try:
        exclude_file = open(tempdir/name, 'w')
    except Exception as e:
        do_exit(f'{e} while processing {name}', 2)
    

    if job['exclude']:
        # read the exclude string and split into list
        exclude_list = [x.strip() for x in job['exclude'].split(',')]
        # write list out to file
        for l in exclude_list:
            exclude_file.write(f'{l}\n')

        rsync_command.append(f'--exclude-from={tempdir/name}')
    
    if not job['localpath']:
        do_exit(f'no localpath specified for job: {name}')
    
    rsync_command.append(job['localpath'])
    
    if not job['remotepath']:
        do_exit(f'no remote path specified for job {name}')
    else:
        remotepath = job['remotepath']    
    
    # build a `user@remote.host:/path/` string if a user was specified
    if job['user']:
        remotepath = f"{job['user']}@{job['remotehost']}:{remotepath}"
    
    rsync_command.append(remotepath)
    
#     rsync_command.append(f">> {job['log_file']} 2>&1")
    
    return shlex.split(' '.join(rsync_command))
#     return rsync_command
    
    

    





class multi_line_string():
    '''multi-line string object 
    
    each time  multi_line_string.string is set equal to a string, it is added to 
    the existing string with a new line character
    
    Properties:
        string(`str`): string'''

    def __init__(self, s=''):
        self._string = ''
        self.append(s)
    
    def __str__(self):
        return str(self.string)
    
    def __repr__(self):
        return(str(self.string))
    
    @property
    def string(self):
        return self._string
    
    @string.setter
    def string(self, s):
        self._string = s
    
    def append(self, s):
        self._string = self._string + s + '\n'
    
    def clear(self):
        self._string = ''





def do_exit(e, exit_status=99):
    '''try to handle exits'''
    print(f'{APP_NAME} v{VERSION}')
    print(e)
    sys.exit(exit_status)





def main():    
    def do_exit(e, exit_status=99):
        # redefine locally to also handle cleanup of temp dirs
        '''try to handle exits and cleanup'''
        cleanup()
        print(f'{APP_NAME} v{VERSION}')
        print(e)
        sys.exit(exit_status)

    def cleanup():
        if tempdir:
            try:
                shutil.rmtree(tempdir)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
                exit(2)

        if log_output:
            try:
                log_output.close()
            except Exception as e:
                print(e)
                exit(2)
            
    
    # declare these so cleanup() can function everywhere
    tempdir = None
    log_output = None     

    # get the command line arguments
    args, unknown_args = parse_args()

    if len(unknown_args) > 0:
        do_exit(f'Unknown arguments: {unknown_args}', 1)
    
    # print version, exit
    if args.version:
        do_exit('', 0)
    
    if args.verbose > 0:
        verbose = args.verbose
    else:
        verbose = False   
   
    # create tempdir for exclude files
    try:
        tempdir = tempfile.mkdtemp()
    except Exception as e:
        do_exit(e, 2)            
    
    # build configuration
    config_file = Path(CONFIG_PATH)/CONFIG_FILE
    config = get_config(config_file)
    base_config, ssh_opts = parse_config(config)

    # get the list of jobs
    jobs = []
    for section in config.sections():
        # split out the configuration from the jobs
        #  ignore any job that begins with a literal '='
        if not (section.startswith('%') or section.startswith('=')):
            jobs.append(section)
    
    if len(jobs) < 1:
        do_exit(f'ERROR: no jobs are defined.\nEdit {config_file} to create jobs', 1)

    parsed_jobs = {}
    # sanitize the jobs, build job dictionary with the appropriate keys
    for job in jobs:
        parsed_jobs[job] = (parse_job(config[job]))

    # build rsync commands as lists using job configuration
    rsync_commands = {}
    for job in parsed_jobs:
        rsync_commands[job] = build_rsync_command(name=job, job=parsed_jobs[job], base_config=base_config, ssh_opts=ssh_opts, 
                            tempdir=tempdir, dry_run=args.dry_run, verbose=verbose)
    
    
    # run the jobs
    for job, command in rsync_commands.items():
        collected_output = multi_line_string('\n')
        collected_output.append('-='*30)
        collected_output.append(f'{APP_NAME} v{VERSION}')
        collected_output.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))        
        collected_output.append(f'running job: [{job}]')
        collected_output.append(f"\ncommand: {' '.join(command)}\n")

        
        # set the output file for the log
        log_file = Path('/dev/null').absolute()
        
        try:
            log_file = Path(parsed_jobs[job]['log_file']).expanduser().absolute()
        except KeyError:
            pass
        
        try:
            # open with buffering = 1 to ensure lines are written in the correct order
            # Without this option the header may be written after the rsync information 
            log_output = open(log_file, 'a', buffering=1)
        except OSError as e:
            do_exit(f'error opening log file ({log_file}): {e}')
            
        # log progress thus far
        log_output.write(str(collected_output))
        if verbose:
            print(collected_output)
            
        # clear the collected output
        collected_output.clear()
        
        # get the timeout and kill values
        timeout = parsed_jobs[job]['timeout']
        if timeout == 'None':
            timeout = None
        else:
            try:
                 timeout = int(timeout)            
            except TypeError:
                do_exit(f'TypeError in {job}: timeout = {timeout} -- expected `integer` or `None`', 2)
        
        kill = parsed_jobs[job]['kill']
        
        if kill == 'False':
            kill = False
        elif kill == 'True':
            kill = True
        else:
            do_exit(f'TypeError in {job}: kill = {kill} -- expected `True/False`', 2)
            
        # run the command
        process = subprocess.Popen(command, 
                                 stderr=subprocess.STDOUT, 
                                 stdout=log_output, 
                                 universal_newlines=True)
        
        # check on the status
        try:
            out = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if kill:
                process.kill()
                collected_output.append(f'timeout for job {job} expired, process was killed')
            else:
                collected_output.append(f'timeout for job {job} expired, process was not killed; continuing')
        
        max_log = parsed_jobs[job]['max_log']
        
        try:
            max_log = int(max_log)
        except TypeError:
            do_exit(f'TypeError in {job}: max_log = {max_log} -- expected `integer`', 2)
        
        if log_file.stat().st_size > max_log:
            log_archive = Path(str(log_file)+'.1')
            try:
                shutil.move(log_file, log_archive)
            except (FileNotFoundError, OSError):
                print(f'could not move {log_file} -> {log_archive}')
            
            
        
        
        
        collected_output.append(f"completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        collected_output.append(f'[{job}] done')
        
        if verbose:
            print(collected_output)
        log_output.write(str(collected_output)) 
        
        log_output.close()


    cleanup()





if __name__ == '__main__':
    job = main()





parse_args()





saved_argv = sys.argv





sys.argv.pop()
sys.argv.pop()





sys.argv.append('-v')








