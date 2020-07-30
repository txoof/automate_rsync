#!/usr/bin/env python
# coding: utf-8


# In[17]:


#get_ipython().run_line_magic('load_ext', 'autoreload')
#get_ipython().run_line_magic('autoreload', '2')




# In[18]:


#get_ipython().run_line_magic('alias', 'nbc /Users/aaronciuffo/bin/develtools/nbconvert automate_rsync_v3.ipynb')
#get_ipython().run_line_magic('nbc', '')




# In[2]:


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




# In[3]:


# CONSTANTS
VERSION = '0.1.00'
APP_NAME = 'automate_rsync'
DEVEL_NAME = 'com.txoof'
CONFIG_FILE = f'{APP_NAME}.ini'


EXPECTED_BASE_KEYS = {'rsync_options': '',
                      'delete_options': ''}

EXPECTED_JOB_KEYS = {'user': None,
                     'remotehost': None,
                     'sshkey': None,
                     'localpath': None,
                     'remotepath': None,
                     'exclude': []}

EXPECTED_SSH_KEYS = {'extrassh': ''}

CONFIG_PATH = Path(f'~/.config/{DEVEL_NAME}.{APP_NAME}').expanduser().absolute()




# In[4]:


def sample_config():
    return '''[%base_config]
rsync_options = -a -z
delete_options = --delete-excluded

[%ssh_opts]
extrassh = -o IdentitiesOnly=yes


## each 'job' must include at minimum the keys "localpath" and "remotepath"
## other keys are optional (see the example below)
## add an `=` to the beginning of a job to disable it


## copy this TEMPLATE and remove the `=` to label each job
[=TEMPLATE]
## not required for local syncs that do not use ssh
user = <optional: remote username>

## not required for local syncs that do not use ssh
remotehost = <optional: ip or host name>

## not required for local syncs that do not use ssh
sshkey = <optional: path to private ssh key>

## required
localpath = <local path to sync from -- mind the trailing `/`>
# localpath = /Users/jbuck/Documents <-- this will sync the dir
# localpath = /Users/jbuck/Documents/ <-- this will sync the contents only

## required
remotepath = <remote path to sync into -- mind the trailing `/`>

## optional
exclude = <comma separated list of patterns to exclude from sync>
# exclude = .DS_Store, data_base, /Downloads, /Applications

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
exclude = .AppleDouble, .DS_Store, .git, .local, /Library, /Application*, /Music'''




# In[5]:


def parse_args():
    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('-v', dest='verbose', action='store_true', default=False, help='enable verbose output')
    parser.add_argument('-d', dest='dry_run', action='store_true', default=False, help='set rsync --dry-run')
    args, unknown = parser.parse_known_args()
    
    return args




# In[6]:


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




# In[7]:


def parse_job(job):
    expected_keys=EXPECTED_JOB_KEYS
    parsed_job = {}
    for key in expected_keys:
        try:
            parsed_job[key] = job[key]
        except KeyError:
            parsed_job[key] = expected_keys[key]
    return parsed_job 




# In[8]:


def parse_config(config):
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




# In[9]:


def build_rsync_command(name, job, base_config, ssh_opts, tempdir, dry_run=False, verbose=False):
    '''build an rsync from ini file
    
    Args:
        name(`str`): name of the job -- used for identifying exclude file
        job(`dict`): individual job from ini 
        base_config(`dict`): base_config from ini
        ssh_opts(`dict`): ssh_opts from ini
        tempdir(`Path`): path to temporary directory for exclude files
        dry_run(`bool`): add `--dry-run` to rsync command for testing
        verbose(`bool`): add `-v` to rsync command for debugging
    
    Returns:
        string -- rsync command'''
    
    name = re.sub(r'[\W_]+', '', name) + str(uuid.uuid4())
    
    rsync_command = []
    ssh_command = ''
    tempdir = Path(tempdir)
    
    # get the rsync binary path
    try:
        stream = os.popen('which rsync')
        rsync_bin = stream.read()
    except Exception as e:
        do_exit(e, 1)
    
    # add the binary
    rsync_command.append(rsync_bin)
    # add the options from the ini file
    rsync_command.append(base_config['rsync_options'])
    
    # add additional options from the args
    if dry_run:
        rsync_command.append('--dry-run')
        
    if verbose:
        rsync_command.append('-v')
    
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
        exclude_list = [x.strip() for x in job['exclude'].split(',')]
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
    
    if job['user']:
        remotepath = f"{job['user']}@{job['remotehost']}:{remotepath}"
    
    rsync_command.append(remotepath)
    
    
    return shlex.split(' '.join(rsync_command))
#     return rsync_command
    
    

    




# In[13]:


def main():
    args = parse_args()
    
    dry_run = args.dry_run
    verbose = args.verbose
    
    
    def do_exit(e, exit_status=99):
        '''try to handle exits and cleanup'''
        cleanup()
        print(f'{APP_NAME} v{VERSION}')
        print(e)
        sys.exit(exit_status)

    def cleanup():
        try:
            shutil.rmtree(tempdir)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(e)
            exit(2)
    
    tempdir = ''
    try:
        tempdir = tempfile.mkdtemp()
    except Exception as e:
        do_exit(e, 2)            
            
    config_file = Path(CONFIG_PATH)/CONFIG_FILE
    # config = get_config(Path(default_cfg_name).absolute())
    config = get_config(config_file)
    base_config, ssh_opts = parse_config(config)


    jobs = []
    for section in config.sections():
        if not (section.startswith('%') or section.startswith('=')):
            jobs.append(section)

    if len(jobs) < 1:
        do_exit('ERROR: no jobs are defined.\nEdit {config_file}', 1)

    if verbose:
        print(f'Found {len(jobs)} job(s):')
        for job in jobs:
            print(f'\t{job}')
    
    parsed_jobs = {}
    for job in jobs:
        parsed_jobs[job] = (parse_job(config[job]))

    rsync_commands = {}
    for job in parsed_jobs:
        rsync_commands[job] = build_rsync_command(name=job, job=parsed_jobs[job], base_config=base_config, ssh_opts=ssh_opts, 
                            tempdir=tempdir, dry_run=dry_run, verbose=verbose)


    for job in rsync_commands:
        print(f'Running job: [{job}]')
        if verbose:
            print(' '.join(rsync_commands[job]))
    #     stream = os.popen(command)
    #     print(f'this is the stream: {stream.read()}')

        process = subprocess.run(rsync_commands[job], 
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True
                                )
        output = process.stdout
        if verbose:
            print(output.strip())
            print('done')




# In[14]:


if __name__ == '__main__':
    main()


