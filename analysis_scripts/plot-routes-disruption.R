library(plyr)
source('plot-utils.R')
source('generic-plot.R')

args = commandArgs(trailingOnly=T)

folder = args[1]
if (length(args) == 2) {
    max.x = as.numeric(args[2])
} else {
    max.x = NA
}

experiments = read.table(paste(folder, "experiments.csv", sep="/"), sep=" ")
names(experiments) = c("total", "broken", "loop", "t", "time", "rep", "prince", "experiment")

ddply(experiments, c("rep", "experiment"), function(x) {
	experiment = x[1,]$experiment
	rep = x[1,]$rep
	xlim=c(0, ifelse(is.na(max.x), max(experiments$time) * 1.05, max.x))
	ylim=c(0, max(max(experiments$broken), max(experiments$loop)) *1.05)
	plot.routes(paste(experiment, rep, sep='-'), xlim, ylim, x, leg.pos='topright', outputDir = './')
})

# ddply(flow.data, .(size), function(x) {
# 	size = x[1,]$size
# 	print(paste("Size:", size))
# 	xlim=c(15, 85)
# 	ylim=c(80, 240)
# 	plot.data(paste('by-penetration', size, sep='-'), 'penetration', 'flow', 'controller', 'strc', xlim, ylim, 'penetration rate (\\%)', x, legend.for=c(), legend.prefix='', legend.suffix=c('', ''), leg.pos='topleft', outputDir = './', yat=NULL, ylab="flow (car/min)")
# })
