from pathlib import Path
# application version number
version = '0.0.1'

# developer name
devel_name = 'com.txoof'

# application name
app_name = 'automate_rsync'


app_long_name = '.'.join([devel_name, app_name])

# logging configuration
logging_cfg = './logging.cfg'

# config file name
default_cfg_name = 'automate_rsync.ini'

# user config file
user_cfg = Path(f'~/.config/{app_long_name}/{default_cfg_name}').expanduser()

# absolute path for calculating relative paths 
absPath = Path(__file__).absolute().parent
