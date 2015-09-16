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

version='automate rsync over ssh: version 0.1'

def setBaseConfig(baseConfig):
  config=ConfigParser.RawConfigParser(allow_no_value=True)
  #baseConfig={}
  #baseConfig['configFile']=configFile
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
    #FIXME - add a '#' option for disabling jobs.  Hack is to add % to job name
    if not '%' in i:
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
      #pull out exclude items (delimited ONLY by \'\ - single quotes)
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
        exit(2)
      

      jobCmd=rsyncCmd+"-i "+sshKey+"' "+excludeString+' '+localPath+' '+user+'@'+server+':'+remotePath

      rsyncJobs.append(jobCmd)  
      
  return(rsyncJobs)


def main():
  # add option to specify configuration file from command line
  
  baseConfig={}

  argv=sys.argv[1:]
  try:
    opts, args = getopt.getopt(argv, 'vqVc:')
  except getopt.GetOptError:
    if '-c' in argv:
      print 'Error: no alternative configuration file specified.'
      print 'Default configuration file is ~/.automate_rsyncrc'
      print 'usage: ', sys.argv[0], '-c <configuration file>'
    else:
      print 'usage:'
      print '-q       quiet (note: this only effects the verbosity of this script)'
      print '-v       verbose'
      print '-V       Version: ', version
      exit(2)

  for opt, arg in opts:
    if opt=='-c':
      baseConfig['configFile']=arg

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



  rsyncJobs=getRsyncJobs(baseConfig)

  for i in rsyncJobs:
    if baseConfig['talk'] > 0:
      print '\nrunning job:'
      if baseConfig['talk'] > 1:
        print i, '\n'
    # run the system call
    os.system(i)




main()

### RSYNC JOBS
#Documents
'''
def rsyncJob(user, server, localPath, remotePath, exclude='', sshKey='~/.ssh/id_rsa'): 
  sshOpts="-e 'ssh  -o IdentitiesOnly=yes -i "+sshKey+"'"
  remote=user+'@'+server+':'+remotePath
  excludeList=''

  for i in exclude:
    excludeList=excludeList+' --exclude '+i

  rsyncCmd=rsyncBin+' '+rsyncOpts+' '+sshOpts+' '+excludeList+' '+localPath+' '+remote

  os.system(rsyncCmd)

rsyncJob(
  user='txoof', 
  server='192.168.10.9',
  sshKey='/Users/aaronciuffo/.ssh/id_rsa-GC-Bkup',
  localPath='/Users/aaronciuffo/',
  remotePath='/',
  exclude=['Applications/', 'Movies/', 'Library/', 'Music/', '*nobackup*', 'Pictures/', 'Desktop/', 'Downloads/', '.DS_Store', '*Machines.localized*']
)

#Music
rsyncJob(
  user='txoof',
  server='192.168.10.9',
  sshKey='/Users/aaronciuffo/.ssh/id_rsa-GC-Media',
  localPath='/Users/aaronciuffo/Music/',
  remotePath='/',
  exclude=[".AppleDouble", "Podcast*", "TV.*Shows"]
)
'''
