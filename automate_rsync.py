#!/usr/bin/python
## automate rsync over ssh
# Version 1 - 24 July 2015

# run commands and interact with the OS
import os
# gracefully deal with configurationf iles
import ConfigParser

# regular expressions
import re

# handle commandline options
import sys, getopt

version='automate rsync over ssh: version 0.4'


# locate executables in the path
# Thanks to http://stackoverflow.com/users/20840/jay
# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python/377028#377028
def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

#make interactive prompts a little more standard looking
def query(info, prompt):
  div = '-'*30+'\n'
  if not info:
    info = '\n'+div
  else:
    info = '\n'+div+info

  if not prompt:
    prompt = ':'
  else:
    prompt = prompt+': '

  print info
  response = raw_input(prompt)

  return response

# create a config file if none is found
def checkConfig(baseConfig):
  # default configuration values:
  defRsyncOpts = '-avzh'

  if which('rsync') is None:
    defRsyncBin = '/usr/bin/rsync'
    print '**** rsync not found in path using:', defRsyncBin
  else: defRsyncBin = which('rsync')

  defSSHOpts = '-o IdentitiesOnly=yes'

  if not os.path.isfile(baseConfig['configFile']):
    info = 'No configuration file was found at: '+baseConfig['configFile']+'\nWould you like to create one?'
    prompt = 'y/N'
    response = query(info, prompt)
    if response=='y' or response=='Y':
      try:
        open(baseConfig['configFile'], 'w').write(str(''))
      except Exception, e:
        print 'Could not write config file:', e
        return(False)
    else:
      print 'Cannot continue without a configuration file. Exiting.'
      exit(0)
  
  config=ConfigParser.RawConfigParser()
  try:
    config.readfp(open(baseConfig['configFile']))
  except Exception, e:
    print 'Failed to load configuration file: ', baseConfig['configFile']
    print 'Error: ', e
    return(False)

  #check for required sections
  configChanges=False
  requiredSections=['%BaseConfig', '%sshOptions']

  for i in requiredSections:
    if not config.has_section(i):
      config.add_section(i)
      configChanges=True

  #Check required sections for options
  # BaseConfig
  if not config.has_option('%BaseConfig', 'rsyncBin'):
    info = 'Which rsync binary would you like to use?\nSystem rsync found at: '+defRsyncBin
    prompt = 'full path to rsync binary or press ENTER for default'
    response = query(info, prompt)

    if len(response) > 0:
      response=which('rsync')
    else:
      response=which('rsync')
    config.set('%BaseConfig', 'rsyncBin', response)
    configChanges=True

  if not config.has_option('%BaseConfig', 'rsyncOptions'):
    info = 'What global rsync options would you like to use for all jobs?\nTypical options are: ' + defRsyncOpts + '\nSee the rsync man page for more information.\nEnter your options below or press ENTER for the defaults (' + defRsyncOpts + ').'
    prompt = 'rsync options'
    response = query(info, prompt)
    if len(response) > 0:
      config.set('%BaseConfig', 'rsyncOptions', response)
      configChanges=True
    else:
      config.set('%BaseConfig', 'rsyncOptions', defRsyncOpts)



  if not config.has_option('%BaseConfig', 'deleteOptions'):
    info = '\nWhat delete options would you like to use?\nFor backups typical options are: --delete-excluded\nSee the rsync man page for more information.'
    prompt = 'delete options (press ENTER for none)'
    response = query(info, prompt)
    config.set('%BaseConfig', 'deleteOptions', response)
    configChanges=True

  if not config.has_option('%sshOptions', 'extraSSH'):
    info = 'What additional ssh options would you like to use with rsync?\nAll extra options need to be preceded with "-o"\nPlease see the rsync and ssh_config pages for more informaiton\nTo force rsync and ssh to use a specific SSH key use: '+defSSHOpts
    prompt = 'Press ENTER for default options or enter your own (space for none)'

    response = query(info, prompt)

    if response is None:
      response = defSSHOpts
    
    config.set('%sshOptions', 'extraSSH', response)
    configChanges=True

  if configChanges:
    try:
      with open(baseConfig['configFile'], 'wb') as configfile:
        config.write(configfile)
    except Exception, e:
      print 'Failed to write to', baseConfig['configFile']
      print 'Error:', e
      return(False)

  return(True)

def jobAdd(baseConfig):
  configChanges=False

  response = query('Would you like to interactively add a job?', 'Y/n: ')
#  print 'Would you like to interactively add a job?'
#  response=raw_input('Y/n: ')
  if not (response=='y' or response=='Y' or response==''):
    #print 'Exiting. Please manually add at least one job to', baseConfig['configFile']
    return(True)
    #exit(0)
    
  if not os.path.isfile(baseConfig['configFile']):
    print 'No configuration file was found at: ', baseConfig['configFile']
    exit(1)
  
  config=ConfigParser.RawConfigParser()
  try:
    config.readfp(open(baseConfig['configFile']))
  except Exception, e:
    print 'Failed to load configuration file: ', baseConfig['configFile']
    print 'Error: ', e
    return(False)
  
  info = 'Please give this job a descriptive name such as "Remote Host - LocalDirectory"'
  prompt = 'job name'
  jobName= query(info, prompt)
  configChanges=True
  config.add_section(jobName)

  info = 'What is the *remote* username to use?'
  prompt = 'remote username'
  userName = query(info, prompt)
  config.set(jobName, 'user', userName)


  info = 'Would you like to fetch (download) files FROM the REMOTE server?'
  prompt = 'y/N'
  response = query(info, prompt)
  if response == 'y' or response == 'Y':
    config.set(jobName, 'fetchonly', 'true')

  info = 'What is the hostname or IP address of the remote rsync host?'
  prompt = 'server ip or fqdn'
  server=query(info, prompt)
  config.set(jobName, 'server', server)

  info = 'What is the full path to the ssh key should be used with this server?\nIf no key is to be used, or there is only one key per remote host, this can be blank.\nNOTE: If a specific key is used please set extraSSH=-o IdentitiesOnly=yes in the following step.'
  prompt = 'path to sshKey'
  sshKey = query(info, prompt)
  config.set(jobName, 'sshKey', sshKey)

  info = 'What is the full local path to be used?'
  prompt = 'local path'
  localPath = query(info, prompt)
  config.set(jobName, 'localPath', localPath)

  info = 'What is the full remote path to be used?\nIf you you are using restricted rsync this path should be relative to the root of the restricted path.\nFor more information about securing passwordless rsync jobs with rrsync please see:\nhttps://ftp.samba.org/pub/unpacked/rsync/support/rrsync'
  prompt = 'remote path:'
  remotePath = query(info, prompt)
  config.set(jobName, 'remotePath', remotePath)

  info = 'What should be excluded from the transfer?\nPlease see the rsync man page for more information on regular expressions and exclusions\nFormat: "/path/to/Dir1", "*Virtual.Machines", "*dump", "\.swp"'
  prompt = 'exclude'
  exclude=query(info, prompt)
  config.set(jobName, 'exclude', exclude)

  
  if configChanges:
    try:
      with open(baseConfig['configFile'], 'wb') as configfile:
        config.write(configfile)
    except Exception, e:
      print 'Failed to write to', baseConfig['configFile']
      print 'Error:', e
      return(False)
    print 'Done adding your job:', jobName,'\n'
  #add another job
  jobAdd(baseConfig)
  

def setBaseConfig(baseConfig):
  #read base configuration from config file
  config=ConfigParser.RawConfigParser(allow_no_value=True)
  #baseConfig={}
  #baseConfig['configFile']=configFile

  # check for config file or create one with the user
  if not checkConfig(baseConfig):
    print 'Error in configuraiton file:', baseConfig['configFile']
    exit(1)

  configFile=baseConfig['configFile']
  try:
    config.readfp(open(configFile))
  except Exception, e:
    print 'Failed to load configuration file at: ', configFile
    print 'Please create a configuration file at: ', configFile
    print 'Error: ', e
    exit(2)

  sectionKey='%BaseConfig'
  # read in basic configuration settings
  try:
    baseConfig['rsyncBin']=config.get(sectionKey, 'rsyncBin')
  except Exception, e:
    print 'Using /usr/bin/rsync for rsync binary'
    baseConfig['rsyncBin']='/usr/bin/python'

  try:
    baseConfig['rsyncOptions']=config.get(sectionKey, 'rsyncOptions')
  except Exception, e:
    print 'Using rsync options: --archive --verbose --compress --human-readable'
    baseConfig['rsyncOptions']='-avzh'

  try:
    baseConfig['deleteOptions']=config.get(sectionKey, 'deleteOptions')
  except Exception, e:
    print 'No files on remote host will be deleted.'
    baseConfig['deleteOptions']=''


  # read in SSH configuration settings
  sectionKey='%sshOptions'
  try:
    baseConfig['extraSSH']=config.get(sectionKey, 'extraSSH')
  except Exception, e:
    baseConfig['extraSSH']=''

  if baseConfig['talk'] > 1:
    print '***baseConfig Values***'
    for key, value in baseConfig.iteritems():
      print key+':', value
    print 2*'\n'

  return(baseConfig)


def getRsyncJobs(baseConfig):
  config=ConfigParser.RawConfigParser(allow_no_value=True)

  #if baseConfig['dryRun']:
  if baseConfig.get('dryRun'):     
    baseConfig['rsyncOptions'] = baseConfig['rsyncOptions']+'n'

  rsyncCmd=baseConfig['rsyncBin']+' '+baseConfig['rsyncOptions']+' '+baseConfig['deleteOptions']+' '+"-e 'ssh "+baseConfig['extraSSH']+' '
  
  try:
    config.readfp(open(baseConfig['configFile']))
  except Exception, e:
    print 'Failed to load configuration file at: ', baseConfig['configFile']
    print 'Please create a configuration file at: ', baseconfig['configFile']
    print 'Error: ', e
    exit(2)
  
  if baseConfig['talk'] > 0:
    print 'gathering jobs...'

  rsyncJobs=[]
  for i in config.sections():

    #Configuration sections begin with a '%'; job sections can be any string
    # Literal '#' are treated as comments and jobs that contain a '#' are skipped
    if not ('%' in i or '#' in i):
      if baseConfig['talk'] > 0:
        print 'found job: ', i
      excludeList=[]
      excludeString=''
      user=''
      server=''
      sshKey=''
      localPath=''
      remotePath=''
      for j in config.options(i):
      #pull out exclude items 
        try:
          rawExclude=config.get(i, 'exclude')
        except Exception, e:
          rawExclude=''

      #FIXME - find a better way to clean up and split the exclude strings
      # I'm SURE there's a bettery way to do this
      cleanExclude=re.sub("'", "", rawExclude)
      cleanExclude=re.sub(",", "", cleanExclude)
      cleanExclude=re.sub('"', '', cleanExclude)
      excludeList=cleanExclude.split()
      for k in excludeList:
        excludeString=' --exclude '+k+excludeString

      # fail gracefully if any of these things are missing
      try:
        user=config.get(i, 'user')
        server=config.get(i, 'server')
        sshKey=config.get(i, 'sshKey')
        localPath=config.get(i, 'localPath')
        remotePath=config.get(i, 'remotePath')
      except Exception, e:
        print 'Fatal Error: ', e
        exit(1)
      
      # ignore if these options are not present

      try:
        config.getboolean(i, 'fetchonly')
        fetchOnly = True
      except Exception, e:
        fetchOnly = False

#      if config.getboolean(i, 'fetchonly'):
#        fetchOnly = True
#      else:
#        fetchOnly = False


      # build final command here:
     
      # rsync from server to local
      if fetchOnly:
        jobCmd = rsyncCmd+"-i"+sshKey+"' "+excludeString+' '+user+'@'+server+':'+remotePath+' '+localPath

      #rsync from local to server
      else:
        jobCmd=rsyncCmd+"-i "+sshKey+"' "+excludeString+' '+localPath+' '+user+'@'+server+':'+remotePath

      rsyncJobs.append(jobCmd)  
     
  if len(rsyncJobs) < 1:
    print 'No rsync jobs found.  Please add a job to', baseConfig['configFile']
    jobAdd(baseConfig)
  return(rsyncJobs)


def main():
  # add option to specify configuration file from command line
  
  baseConfig={}
  interactiveAdd=False

  argv=sys.argv[1:]
  try:
    opts, args = getopt.getopt(argv, 'dvqVIc:')
  except getopt.GetoptError:
    if '-c' in argv:
      print 'Error: no alternative configuration file specified.'
      print 'Default configuration file is ~/.automate_rsyncrc'
      print 'usage: ', sys.argv[0], '-c <configuration file>'
      exit(0)
    else:
      print 'usage:'
      print '-c <path to configuration file>'
      print '-d       dry run - no changes made'
      print '-I       interactively add an rsync job'
      print '-q       quiet (note: this only effects the verbosity of this script)'
      print '-v       verbose'
      print '-V       Version:', version
      exit(0)

  for opt, arg in opts:
    if opt=='-c':
      baseConfig['configFile']=arg


    if opt=='-d':
      baseConfig['dryRun'] = True
    else:
      baseConfig['dryRun'] = False

    if opt=='-I':
      interactiveAdd=True

    if opt=='-q':
      baseConfig['talk']=0

    if opt=='-v':
      baseConfig['talk']=2

    if opt=='-V':
      print 'Version: ', version
      exit()

  if not 'talk' in baseConfig:
    baseConfig['talk']=1

  if not 'configFile' in baseConfig:
    baseConfig['configFile']=os.path.expanduser('~/.automate_rsyncrc')


  #setup basic configuration for how rsync should act
  baseConfig=setBaseConfig(baseConfig)

  if interactiveAdd:
    jobAdd(baseConfig)

  rsyncJobs=getRsyncJobs(baseConfig)

  for i in rsyncJobs:
    if baseConfig.get('dryRun'):
      print '#'*20
      print 'Dry Run - no files will be transferred'
    if baseConfig['talk'] > 0:
      print '\nrunning job:'
      if baseConfig['talk'] > 1:
        print i, '\n'
    # run the rsync job in the shell
    os.system(i)

main()

