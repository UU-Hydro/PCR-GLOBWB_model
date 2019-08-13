#!/bin/bash
#SBATCH -N 1
#SBATCH -t 119:59:00
#SBATCH -p normal
#SBATCH --constraint=haswell
#~ #SBATCH -J haswell-normal-edwinvua

#SBATCH -J %3

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com

pcrcalc

echo %1
echo %2

while countfiles=20
do 
countfiles=20
done
