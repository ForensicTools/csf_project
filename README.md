# Linux Persistence Detection

## Install and Run

`pip3 install -r requirements.txt`
`python3 persistence.py`

## Output

Two files will be created after successful execution of the script
  - report.txt 
  - user_bash.zip
### Report

Hidden executable - any files on the system that are both hidden (start with '.') and are marked as executable by a user (https://attack.mitre.org/techniques/T1158/)

Setuid files - any files with a setuid bit on.  This will allow any user to run the executable as the owner (https://attack.mitre.org/techniques/T1166/)

Setgid directories - any directories with setgid bit on.  File is run with permissions of the group (https://attack.mitre.org/techniques/T1166/)

  #### Users
  
  https://attack.mitre.org/techniques/T1098/
  
  Scheduled tasks - list of crontab info. Can find any persistence mechanism with scheduled tasks (https://attack.mitre.org/techniques/T1168/)
  
  Chrome extensions - if applicable, will list ID or name (if possible) of chrome extension (https://attack.mitre.org/techniques/T1176/)
  
  Group membership (https://attack.mitre.org/techniques/T1098/)
  
  Active sessions - validate all current logged in users
  
### User Bash

All users' bashrc and bash_profile files will be added to a zip file to be manually inspected for any malicious modification (https://attack.mitre.org/techniques/T1156/)


## Resources

For a comprehensive list of persistence techniques, see https://attack.mitre.org/
