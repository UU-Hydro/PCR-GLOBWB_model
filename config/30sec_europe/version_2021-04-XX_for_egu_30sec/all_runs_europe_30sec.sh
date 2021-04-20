#!/bin/bash

set -x

# for testing
#~ sbatch -t 59:00 -p short -J eu113235 --export PCRTHREADS="8",CLONE1="11",CLONE2="32",CLONE3="35" job_script_sbatch_pcrglobwb_europe_30sec_template.sh




sbatch -J 01030000 --export PCRTHREADS="24",CLONE1="3",CLONE2="0",CLONE3="0"   job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 02010000 --export PCRTHREADS="24",CLONE1="1",CLONE2="0",CLONE3="0"   job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 03130000 --export PCRTHREADS="24",CLONE1="13",CLONE2="0",CLONE3="0"  job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 04100000 --export PCRTHREADS="24",CLONE1="10",CLONE2="0",CLONE3="0"  job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 05302500 --export PCRTHREADS="12",CLONE1="30",CLONE2="25",CLONE3="0" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 06193600 --export PCRTHREADS="12",CLONE1="19",CLONE2="36",CLONE3="0" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 07062200 --export PCRTHREADS="12",CLONE1="6",CLONE2="22",CLONE3="0"  job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 08390200 --export PCRTHREADS="12",CLONE1="39",CLONE2="2",CLONE3="0"  job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 09441400 --export PCRTHREADS="12",CLONE1="44",CLONE2="14",CLONE3="0" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 10231600 --export PCRTHREADS="12",CLONE1="23",CLONE2="16",CLONE3="0" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 11340500 --export PCRTHREADS="12",CLONE1="34",CLONE2="5",CLONE3="0"  job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 12184038 --export PCRTHREADS="8",CLONE1="18",CLONE2="40",CLONE3="38" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 13330929 --export PCRTHREADS="8",CLONE1="33",CLONE2="9",CLONE3="29"  job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 14122043 --export PCRTHREADS="8",CLONE1="12",CLONE2="20",CLONE3="43" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 15262731 --export PCRTHREADS="8",CLONE1="26",CLONE2="27",CLONE3="31" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 16371724 --export PCRTHREADS="8",CLONE1="37",CLONE2="17",CLONE3="24" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 17074542 --export PCRTHREADS="8",CLONE1="7",CLONE2="45",CLONE3="42"  job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 18080441 --export PCRTHREADS="8",CLONE1="8",CLONE2="4",CLONE3="41"   job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 19152128 --export PCRTHREADS="8",CLONE1="15",CLONE2="21",CLONE3="28" job_script_sbatch_pcrglobwb_europe_30sec_template.sh
sbatch -J 20113235 --export PCRTHREADS="8",CLONE1="11",CLONE2="32",CLONE3="35" job_script_sbatch_pcrglobwb_europe_30sec_template.sh

#~ 24	01030000 ! 3		   !
#~ 24	02010000 ! 1		   !
#~ 24	03130000 ! 13		   !
#~ 24	04100000 ! 10		   !
#~ 12	05302500 ! 30	25	   !
#~ 12	06193600 ! 19	36	   !
#~ 12	07062200 ! 6	22	   !
#~ 12	08390200 ! 39	2	   !
#~ 12	09441400 ! 44	14	   !
#~ 12	10231600 ! 23	16	   !
#~ 12	11340500 ! 34	5	   !
#~ 8	12184038 ! 18	40	38 !
#~ 8	13330929 ! 33	9	29 !
#~ 8	14122043 ! 12	20	43 !
#~ 8	15262731 ! 26	27	31 !
#~ 8	16371724 ! 37	17	24 !
#~ 8	17074542 ! 7	45	42 !
#~ 8	18080441 ! 8	4	41 !
#~ 8	19152128 ! 15	21	28 !
#~ 8	20113235 ! 11	32	35 !

set +x
