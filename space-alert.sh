#!/bin/sh
## run this script in crontab at the desired timeframe to check for hard drive space
### in this case, will send you an alert when it reaches a used space of 95 %

df -H | grep '/dev/sd' | awk '{ print $5 " " $1 }' | while read output;
do
  echo $output
  usep=$(echo $output | awk '{ print $1}' | cut -d'%' -f1  )
  partition=$(echo $output | awk '{ print $2 }' )
  if [ $usep -ge 95 ]; then
    echo "Running out of space \"$partition ($usep%)\" on $(hostname) as on $(date)" |
     mail -s "Alert: Almost out of disk space $usep%" -a "From: <alerts@paulnetwork.org>" alerts@paulnetwork.org
  fi
done
