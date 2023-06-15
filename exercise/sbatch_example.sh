#!/bin/bash

# type of nodes/partitions, thin is the default one, for other types, please check https://servicedesk.surf.nl/wiki/display/WIKI/Snellius+usage+and+accounting (including their prices)
#SBATCH -p thin

# number of node (note pcrglobwb still does not support parallelization between nodes, hence this is most likely always one)
#SBATCH -N 1

# number of cores, for a thin node, this should be a multiply of 32 (with the maximum 128 cores per a thin node)
#SBATCH -n 32

# maximum wall clock time (hr:mm:ss), the longest is 120 hours
#SBATCH -t 0:59:00 

# job name
#SBATCH -J example

#~ # email notification/alert (please use your email address, if you want to use this feature)
#~ # - alert at start, end and abortion of execution
#~ #SBATCH --mail-type=ALL
#~ # send notificationl to this address
#~ #SBATCH --mail-user=johndoe@yahoo.com


############ start of your job #########################

# go to your home and list its content
cd $HOME
pwd
ls -lah *

# an infinite loop
while countfiles=20
do 
countfiles=20
done

# print your account information
accinfo

############ end of your job ###########################


