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
VERSION = '3.0.10'
APP_NAME = 'automate_rsync'
DEVEL_NAME = 'com.txoof'
CONFIG_FILE = f'{APP_NAME}.ini'


EXPECTED_BASE_KEYS = {'rsync_bin': None,
                      'global_rsync': '',
#                       'rsync_options': '',
#                       'delete_options': '',
                      }

EXPECTED_JOB_KEYS = {'direction': 'local-remote',
                     'rsync_options': '',
                     'ssh_options': '',
                     'sshkey': None,
                     'user': None,
                     'remotehost': None,
                     'localpath': None,
                     'remotepath': None,
                     'exclude': [],
                     'log_file': '/dev/null',
                     'max_log': 0,
                     'timeout': None,
                     'kill': False,
                    }

# EXPECTED_SSH_KEYS = {
#                      'extrassh': ''
#                     }

CONFIG_PATH = Path(f'~/.config/{DEVEL_NAME}.{APP_NAME}').expanduser().absolute()





def sample_config():
    return '''[%base_config]
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

[#local-sync]
# sync files to a local exteral HDD
rsync_options = -a -z
direction = local-remote
localpath = /Users/myuser/Documents/project\ files
remotepath = /Volumes/Backup\ SSD/myuser/
# produces: /usr/bin/rsync /Users/myuser/Documents/project\ files /Volumes/Backup\ SSD/myuser/

[#acer_laptop documents -> backup host]
direction = local-remote
rsync_options = --delete-after --port 8022
ssh_options = -o IdentitiesOnly=yes
user = mpython
remotehost = backup.mydomain.com
sshkey = /home/eidle/.ssh/com_mydomain_backup-id_rsa
localpath = /home/edile/Documents
# with rrsync adjusted root
remotepath = /linux_laptop/
exclude = no_backup, My\ Picutres
log_file = ~/linux_laptop_rsync.log
max_log = 2000000
timeout = 1200
kill = True

[#remote photos -> linux_laptop]
direction = remote-local
ssh_options = -o IdentitiesOnly=yes
user = stockphotos
remotehost = image-host.local
sshkey = /home/edile/.ssh/local_image-host_id_rsa
remotepath = /home/stockphotos/latest/*
localpath = /home/edile/temp/stock_photos
exclude = *.RAW, meta_data/*
log_file = ~/remote_photos.log
max_log = 5000000
timeout = 2000
kill = True
'''





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
    try:  
        config.read(file)
    except Exception as e:
        do_exit(f'Error reading config file: {file}\n{e}')
    
    return config





def parse_job(job):
    expected_keys=EXPECTED_JOB_KEYS
    parsed_job = {}
    for key in expected_keys:
        try:
            parsed_job[key] = normalize_ini_key(job[key])
        except KeyError:
            parsed_job[key] = expected_keys[key]

    return parsed_job 





def normalize_ini_key(string):
    '''attempt to normalize values for by converting strings into boolean, or None for:
        'True', 'False', 'None'
        
    Args:
        value(`str`): value containing true, false, yes, no, none
    
    Raises:
        TypeError if value is not of type `str`
    
    Returns:
        bool or None'''
    
    if not isinstance(string, str):
        raise TypeError(f'{value} is not type `str`')
    
    true = ['true', 'yes', 'ok', '1']
    false = ['false', 'no', '0']
    none = ['none']
    
    values_dict = {True: true, False: false, None: none}
    ret_val = string
    
    for key, value in values_dict.items():
        if string.lower() in value:
            ret_val = key
            break
    
    return ret_val





def parse_config(config):
    '''build dictionary from configparser section using expected key/values'''
    
    expected_base_keys = EXPECTED_BASE_KEYS
#     expected_ssh_keys = EXPECTED_SSH_KEYS
    
    base_config = {}
#     ssh_opts = {}
        
    for key in expected_base_keys:
        try:
            base_config[key] = normalize_ini_key(config['%base_config'][key])
        except KeyError:
            base_config[key] = expected_base_keys[key]
    
#     for key in expected_ssh_keys:
#         try:
#             ssh_opts[key] = normalize_ini_key(config['%ssh_opts'][key])
#         except KeyError:
#             ssh_opts[key] = expected_ssh_keys[key]
#     return (base_config, ssh_opts)
    return (base_config)





def build_rsync_command(name, job, base_config, tempdir, dry_run=False, verbose=False):
    '''build an rsync from ini file
    
    Args:
        name(`str`): name of the job -- used for identifying exclude file
        job(`dict`): individual job from ini 
        base_config(`dict`): base_config from ini
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
    
    rsync_bin = base_config['rsync_bin']
    
#     if base_config['rsync_bin'] == 'None' or not base_config['rsync_bin']:
#         rsync_bin = None
#     else:
#         rsync_bin = Path(base_config['rsync_bin'])
            
    if not rsync_bin:
        try:
            stream = os.popen('which rsync')
            rsync_bin = Path(stream.read().rstrip('\n'))
        except Exception as e:
            do_exit(e, 1)
    
    if not rsync_bin:
        do_exit(f'could not locate rsync binary in `$PATH`\nconsider adding:\n"rsync_bin=/path/to/rsync"\n to [%base_config] section of {CONFIG_PATH}')
        
    if not rsync_bin.is_file():
        do_exit(f'{rsync_bin} does not appear to exist.\nconsider udating:\n"rsync_bin = /path/to/rsync"\n to [%base_config] section of {CONFIG_PATH}')
    
    # add the binary
    rsync_command.append(rsync_bin.as_posix())
    # add the global options from the ini file
#     rsync_command.append(base_config['rsync_options'])
    rsync_command.append(base_config['global_rsync'])
    
    # and any job specific rsync options
    rsync_command.append(job['rsync_options'])
    
    # add additional options from the args
    if dry_run:
        rsync_command.append('--dry-run')
        
    if verbose:
        rsync_command.append('-'+'v'*verbose)
    
#     rsync_command.append(base_config['delete_options'])
    
    ssh_command = ''
    if job['sshkey']:
#             ssh_command = f'ssh -o IdentitiesOnly=yes -i {job["sshkey"]}'
#         ssh_command = f'ssh {ssh_opts["extrassh"]} -i {job["sshkey"]}'
        ssh_command = f"ssh {job['ssh_options']} -i {job['sshkey']}"
    elif not job['sshkey'] and job['ssh_options']:
        ssh_command = f"ssh {job['ssh_options']}"
        
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
    
#     rsync_command.append(job['localpath'])
    localpath = job['localpath']
    # add dobule quotes to protect spaces in filenames
    localpath = f'\"{localpath}\"'
    
    if not job['remotepath']:
        do_exit(f'no remote path specified for job {name}')
    else:
        remotepath = job['remotepath']    
        # add double quotes to protect spaces in filenames
        remotepath = f'\"{remotepath}\"'
    
    # build a `user@remote.host:/path/` string if a user was specified
    if job['user']:
        remotepath = f"{job['user']}@{job['remotehost']}:{remotepath}"
    
    if job['direction'] == 'remote-local':
        rsync_command.append(remotepath)
        rsync_command.append(localpath)
    else:
        rsync_command.append(localpath)
        rsync_command.append(remotepath)
    

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
#     base_config, ssh_opts = parse_config(config)
    base_config = parse_config(config)

    # get the list of jobs
    jobs = []
    for section in config.sections():
        # split out the configuration from the jobs
        #  ignore any job that begins with a literal '='
        if not (section.startswith('%') or section.startswith('#')):
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

#         rsync_commands[job] = build_rsync_command(name=job, job=parsed_jobs[job], base_config=base_config, ssh_opts=ssh_opts, 
#                             tempdir=tempdir, dry_run=args.dry_run, verbose=verbose)
        rsync_commands[job] = build_rsync_command(name=job, job=parsed_jobs[job], base_config=base_config, 
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
        if timeout:
            try:
                timeout = int(timeout)
            except TypeError:
                do_exit(f'TypeError in {job}: timeout = {timeout} -- expected `integer` or `None`', 2)
        
#         if timeout == 'None':
#             timeout = None
#         else:
#             try:
#                  timeout = int(timeout)            
#             except TypeError:
#                 do_exit(f'TypeError in {job}: timeout = {timeout} -- expected `integer` or `None`', 2)
        
        kill = parsed_jobs[job]['kill']
        if kill not in (True, False):
            do_exit(f'TypeError in {job}: kill = {kill} -- expected `boolean`', 2)
        
#         if kill == 'False':
#             kill = False
#         elif kill == 'True':
#             kill = True
#         else:
#             do_exit(f'TypeError in {job}: kill = {kill} -- expected `True/False`', 2)
            
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
                collected_output.append(f'timeout for job {job} expired, process was not killed\njob continues, but monitoring has stopped')
        
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








# sys_args_initial = sys.argv
# sys.argv.clear()
# sys.argv.extend(['-v', '-d'])





# sys.argv





# from IPython.core.debugger import set_trace





# from IPython.core.debugger import set_trace


