# automate_rsync
Configure rsync once, add multiple jobs with simple headings

This script aims to create a simple method for configuring complex rsync jobs and
adding additional jobs easily.

Quick start (tl;dr):

  If no configuration file is found (~/.automate_rsync.rc) the script will walk you
  through the intial configuration.

  $ ./automate_rsync

This document assumes a basic understanding of SSH and the ability to connect to 
a remote host using SSH.

Getting Started:
  * Configuring rsync and ssh
    - Generate and install keys for passwordless authentication
    - Secure SSH with restricted rsync (rrsync) - Optional
    - Determine rsync options
    - testing

  * Configuring automate-rsync
    - rsync configuration
    - Creating jobs


Configuring rsync and ssh

  This section aims to help setup the userland elements of rsync over ssh. Setting up
  an SSH server is beyond the scope of this document.

  - Generate Keys:
    SSH keys are a method for authenticating on a remote host. To automate rsync over 
    ssh it is important to generate keys that do not require passwords. This creates
    a significant security risk if the keys are compromised. Please see the section
    below on securing SSH with restricted rsync.

    A public key is installed on a remote host and works with its private key pair
    to authenticate a user.  It is vital that the private key remains secure and is
    NEVER shared. The private key should remain on the local computer.


    1) Generate a public/private key set.  If you have an existing key pair make sure 
       to provide an alternative file name (-f <keyname>) to preserve your existing keys.
       Leave the passphrase blank; if a passphrase is specified it will be required 
       every time the key is accessed. Keys are typically kept in ~/.ssh, but can be
       kept any where.

      [LocalHost]$ ssh-keygen -f ~/.ssh/MyKey

      Generating public/private rsa key pair.
      Enter passphrase (empty for no passphrase):
      Enter same passphrase again:
      Your identification has been saved in MyKey.
      Your public key has been saved in MyKey.pub.
      The key fingerprint is:
      e9:70:3b:4b:27:62:cb:54:88:2c:c9:b9:d8:30:28:e3 yourUserName@MyCurrentHost.local
      The key's randomart image is:
      +--[ RSA 2048]----+
      |                 |
      |                 |
      |                 |
      |.. + . . .       |
      |* = o o S        |
      |o* o   = .       |
      |.Eo   + * .      |
      |     + + =       |
      |      o .        |
      +-----------------+

     2) Install the public key on the DestinationServer
        * Transmit the public key to the DestiationServer:
      
          [LocalHost]$ sftp user@DestiationHost

          user@DestnationHosts's password:
          sftp> put myKey.pub
          sftp> quit

        * Connect to the DestinationSever:

          [LocalHost]$ ssh user@DestinationHost
          
          user@DestinationHost's password:
    
        * Backup authroized keys (DO NOT SKIP THIS!)
          [DestinationHost]$ cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys-`date +%Y-%m-%d`

        * Install the public key

          [DestinationHost]$ echo '#Public key from SourceHost - MM/YYYY' >> ~/.ssh/authorized_keys
          [DestinationHost]$ cat ~/MyKey.pub >> ~/.ssh/authorized_keys

        * Disconnect
          [DestinationHost]$ exit

    3) Test your keypair
      * Connect to the DestinationServer with ssh using a specific key

        [LocalHost]$ ssh -o IdentitiesOnly=yes -i ~/.ssh/MyKey user@DestinationHost

        Last login: Thu Sep 27 21:37:20 1999 from 192.1.10.99
        [DestinationHost]$

      * If all goes well you should connect to the DestinationHost without 
        entering a password.  
        Continue on to the next section.
        If a password is requested, try the steps below.

    4) Trouble Shooting
      * Double check your command. Are you specifying the full and proper path to 
        your PRIVATE key?

      * Run ssh in verbose mode:

        [Localhost]$ ssh -o IdentitiesOnly=yes -i ~/.ssh/MyKey user@DestinationHost

      * Look for potential problems. A common issue is specifying the wrong key file:
        
        debug1: Authentications that can continue: publickey,password,keyboard-interactive
        debug1: Next authentication method: publickey
        debug1: Offering RSA public key: /home/user/.ssh/MyKey
        debug1: Authentications that can continue: publickey,password,keyboard-interactive

        ********* This typically indicates that the key was refused.
        debug1: Next authentication method: keyboard-interactive
        debug1: Authentications that can continue: publickey,password,keyboard-interactive
        debug1: Next authentication method: password


  - Determine rsync options:
    Once a passwordless connection has been established an appropriate rsync 
    command needs to be crafted. Rsync is very powerful and its features far 
    exceed the scope of this document. The next section suggests some appropriate 
    settings, but is by no means exhaustive.

    1) Try a simple rsync to the remote:
      * Create a sample directory with a few small files

      [LocalHost]$ mkdir ~/foobar
      [LocalHost]$ date > a.txt
      [LocalHost]$ date > b.txt
      [LocalHost]$ date > c.txt

     * Run a simple rsync to the remote host 
      [LocalHost]$ rsync -avzh ./foo user@DestinationHost:/home/user

      uilding file list ... done
      foo/
      foo/a.txt
      foo/b.txt
      foo/c.txt

      sent 358 bytes  received 92 bytes  128.57 bytes/sec
      total size is 90  speedup is 0.20

    * Rsync should copy the files without prompting for a password

    * If the job does not complete as expected, try the command again but with
      -avvvh for greater verbosity

    2) 
