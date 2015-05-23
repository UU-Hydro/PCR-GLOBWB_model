#################################################################################################################
#														#
# R-script to convert daily tss files into monthly tss files
#														#
# -   created by E.H. Sutanudjaja 17 November 2011								#
# - finalized by E.H. Sutanudjaja 29  January 2012								#
#	for measurement noise, variance based on the standard deviation of measured heads within 30' pixels	#
#  														#
#################################################################################################################

rm(list=ls()); ls()

# reading the argument
YEAR = commandArgs()[length(commandArgs())]
print(YEAR)

# loading daily tss files:
daily_tss = read.table("results//gw_headd.tss",header=F,skip=(33450+2))
date      = seq(as.Date(paste(YEAR,"-01-01",sep=""),"%Y-%m-%d"),as.Date(paste(YEAR,"-12-31",sep=""),"%Y-%m-%d"),1)
daily_tss = data.frame(date,daily_tss)

monthly_used = seq(1,12,1)
for (im in 1:length(monthly_used))     		  {
dailycrop = daily_tss[which(as.numeric(substr(as.character(daily_tss$date),6,7)) == monthly_used[im]),]
month_add    = as.array(as.numeric(mean(dailycrop)))
month_add[1] = monthly_used[im]
month_add[2] = YEAR

print(im)
# if (im == 1) {monthmean = month_add} else {monthmean = rbind(monthmean,month_add)}
  if (im == 1) {cat(month_add,"\n",sep="\t",file="results//gw_headm.txt",append=F)} else {cat(month_add,"\n",sep="\t",file="results//gw_headm.txt",append=T)}

}

rm(list=ls()); ls()
