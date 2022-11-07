#!/usr/bin/python3


# --- configurations --- #

# Programs to do operations
rsync_prog = '/usr/bin/rsync'
move_prog = '/bin/mv'
remove_prog = '/bin/rm'
mkdir_prog = '/bin/mkdir'
timestamp_prog = '/bin/date \'+%Y-%m-%d %H:%M\' >'

# File to list exclude rules (configure this to your exclude file)
exclude_file = '/etc/rsync_exclude'

# Mountpoint of backup disk (configure this to your backup device mountpoint)
backup_mountpoint = '/backup'

# Name base is a path to the backup structure without mountpoint (ie. mountpoint/name_base.01/data_directories)
# (Configure this to base name on your backup device)
backup_name_base = 'backupdir/snapshot'

# Number of monthly, weekly and daily backups 
num_of_monthly_backups = 6
num_of_weekly_backups = 4
num_of_daily_backups = 4

# Locations to backup (configure these with full paths)
target_directories = ['list of','directories here', 'with full paths']

# Timestamp filename to write file with current date of backup to the backup directory
timestamp_filename = 'timestamp.txt'

# Target weekday to take weekly backups (Monday is 1 and Sunday is 7)
# Monthly backups are always taken at the first week of the month
target_weekday = 6

# Debug level 0...2
DEBUG = 0


# --- Code starts, function declarations --- #

import subprocess
from commands import getstatusoutput
from os import path
from sys import exit
from pipes import quote
import datetime

# Function to backup given directory to backup structure
def backup_directory(backup_source):
    if (DEBUG > 1): print('Backup \'%s\'' % backup_source)
    
    # Remove last '/' from soure directory if given
    if (backup_source[-1] == '/'):
	backup_source = backup_source[:-1]	    

    # Set backup targets and link target if exists
    backup_target = '%s/%s/' % (backup_mountpoint, backup_name_base)
    backup_links = '%s/%s.01/' % (backup_mountpoint, backup_name_base)
    
    links_string = ' --link-dest=%s ' % (backup_links)
    if (not path.isdir(backup_links)):
	links_string = ' '
    
    exclude_string = ' --exclude-from=%s --delete-excluded' % quote(exclude_file)
    if (not path.exists(exclude_file)):
	exclude_string = ''
    
    
    # Create new folder for the new backup if it doesn't exist (write timestamp file to directory)
    if (not path.isdir(backup_target)):
	mkdir_command = '%s %s' % (mkdir_prog, backup_target)
	if (DEBUG > 0):
	    print mkdir_command
	
	mkdir_exec = getstatusoutput(mkdir_command)
	if (mkdir_exec[0] != 0):
	    print mkdir_exec

	    
    # Build and execute Backup Command
    backup_command = '%s -a --delete%s%s%s %s' % (rsync_prog, exclude_string, links_string, backup_source, backup_target)
    if (DEBUG > 0):
	print backup_command
    
    backup_exec = getstatusoutput(backup_command)
    if (backup_exec[0] != 0):
	print backup_exec
    else:
	# On success, print timestamp to folder
    	timestamp_command = '%s %s' % (timestamp_prog, '%s%s' % (backup_target, timestamp_filename))
	if (DEBUG > 0):
	    print timestamp_command
	
	timestamp_exec = getstatusoutput(timestamp_command)
	if (timestamp_exec[0] != 0):
	    print timestamp_exec
	    
    return backup_exec
    
    
# Move old backup from source to target
def move_old_backup_to(source, target):
    if (DEBUG > 1): print('Move \'%s\' to \'%s\'' % (source, target))
    
    # Allow operations only in backup directory
    sd = '%s/%s' % (backup_mountpoint, source) 
    td = '%s/%s' % (backup_mountpoint, target)
    
    if (path.isdir(sd)):
        if (path.isdir(td)):
	    print('ERROR: target path \'%s\' already exists' % td)
	    return -1
	    
	else:
	    move_command = '%s %s %s' % (move_prog, sd, td)
	    if (DEBUG > 0):
		print move_command
	    
	    move_exec = getstatusoutput(move_command)
	    if (move_exec[0] != 0):
		print move_exec
		
	    return move_exec
	    
    else:
	print('ERROR: source path \'%s\' does not exist' % sd)
	return False

	
# Remove target directory
def remove_directory(target):
    if (DEBUG > 1): print('Remove \'%s\'' % target)
    
    # Allow operations only in backup directory
    td = '%s/%s' % (backup_mountpoint, target)
    
    if (path.isdir(td)):
	remove_command = '%s -r %s' % (remove_prog, td)
	if (DEBUG > 0):
	    print remove_command
	
	remove_exec = getstatusoutput(remove_command)
	if (remove_exec[0] != 0):
	    print remove_exec
	    
	return remove_exec

    else:
	print('ERROR: target path \'%s\' does not exist' % td)
	return False

	
# Remove backup with index
def remove_backup(idx):
    target = '%s.%02d' % (backup_name_base,idx)
    if (path.isdir('%s/%s' % (backup_mountpoint, target))):
	return remove_directory(target)
    return False

    
# Remove all too old backups (if number of backups is decreased smaller, this removes all older backups)
def remove_all_old_backups():
    #Remove backup with id N_max and all larger
    idx = N_max
    while (remove_backup(idx)):
	idx += 1
    
	
# Algorithm to move and remove backups in daily, weekly and monthly fashion
# it takes current_date as an argument for testing purposes, usually it should be used using default argument
def store_old_backups(current_date = datetime.datetime.today()):
    if (current_date.isoweekday() == target_weekday):
	if (current_date.day <= 7):
	    # Monthly backups (only at first week of a month)
	    for i in range(N_max, N_w, -1):
		source = '%s.%02d' % (backup_name_base,i-1)
		target = '%s.%02d' % (backup_name_base,i)
		if (path.isdir('%s/%s' % (backup_mountpoint, source))):
		    move_old_backup_to(source, target)
	else:
	    #remove last weekly backup as it was not moved to monthly backups
	    remove_backup(N_w)
	    
	# Weekly backups
	for i in range(N_w, N_d, -1):
	    source = '%s.%02d' % (backup_name_base,i-1)
	    target = '%s.%02d' % (backup_name_base,i)
	    if (path.isdir('%s/%s' % (backup_mountpoint, source))):
		move_old_backup_to(source, target)
    else:
	#remove last daily backup as it was not moved to weekly backups
	remove_backup(N_d)
	    
    # Daily backups
    for i in range(N_d, 1, -1):
	source = '%s.%02d' % (backup_name_base,i-1)
	target = '%s.%02d' % (backup_name_base,i)
	if (path.isdir('%s/%s' % (backup_mountpoint, source))):
	    move_old_backup_to(source, target)
    
    # Move last backup to first daily archive
    source = '%s' % backup_name_base
    target = '%s.%02d' % (backup_name_base,1)
    if (path.isdir('%s/%s' % (backup_mountpoint, source))):
	move_old_backup_to(source, target)

	    
# A function to check if backup disk is mounted
def is_backup_disk_mounted(mountpoint):
    df = subprocess.Popen(["df"], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    lines = output.split("\n")
    for i in range(1, len(lines)):
	lineparts = lines[i].split()
	if (len(lineparts) > 5):
	    if (lineparts[5] == mountpoint):
		return True 

    return False
	    
    
# --- Backup script starts --- #

# Compute number of backup history
if num_of_monthly_backups < 0:
    num_of_monthly_backups = 0
if num_of_weekly_backups < 0:
    num_of_weekly_backups = 0
if num_of_daily_backups < 1:
    num_of_daily_backups = 1
    
N_max = num_of_monthly_backups + num_of_weekly_backups + num_of_daily_backups
N_w = num_of_weekly_backups + num_of_daily_backups
N_d = num_of_daily_backups


# Check that backup mountpoint doesn't have '/' at the end (this restricts backing up to '/' and other mountpoints don't end to it)
if (backup_mountpoint[-1] == '/'):
    backup_mountpoint = backup_mountpoint[:-1]

# Check that base name doesn't have '/' at the end
if (backup_name_base[-1] == '/'):
    backup_name_base = backup_name_base[:-1]
    
# Check that backup directory structure and mountpoint exist
backup_path = '%s/%s' % (backup_mountpoint, backup_name_base)
backup_root = backup_path[:(backup_path.rindex('/'))]

if (not is_backup_disk_mounted(backup_mountpoint)):
    print('ERROR: backup mountpoint \'%s\' does not exist, backup not completed!' % backup_mountpoint)
    exit(-1)

if (not path.isdir(backup_root)):
    print('ERROR: backup root path \'%s\' does not exist, backup not completed!' % backup_root)
    exit(-1)

    
# Algorithm starts
remove_all_old_backups()
store_old_backups()

for i in range(len(target_directories)):
    backup_directory(quote(target_directories[i]))
    
    
