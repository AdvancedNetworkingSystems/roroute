library(plyr)

args = commandArgs(trailingOnly=T)

get.experiment = function(folder, r, n, prince) {
    routes = read.table(paste(r,
                              ifelse(prince, "prince", "olsrd2_vanilla"),
                              "routes_summary",
                              sep="/"),
                        sep=" ")
    names(routes) = c("total", "broken", "loop")
    if (!all(routes$broken == 0))
        routes = routes[min(which(routes$broken != 0)):nrow(routes),]
    routes$t = 1:nrow(routes)
    routes$time = routes$t * 0.3
    routes$rep = n
    routes$prince = ifelse(prince, 1, 0)
    routes$experiment = folder
    return(routes)
}

if (length(args) != 1) {
    print("Usage: Rscript average-experiments.R <experiments folder>")
    stop()
}

folder = args[1]

reps = list.dirs(path=folder, recursive=F)

experiments <- data.frame()
for (r in reps) {
    n = suppressWarnings(as.numeric(basename(r)))
    if (!is.na(n)) {
        print(paste("Processing repetition", n))
        experiments <- rbind(experiments, get.experiment(folder, r, n, prince=F))
        experiments <- rbind(experiments, get.experiment(folder, r, n, prince=T))
    }
}
cis = ddply(experiments, c("rep", "prince"), function(x) {
    return(data.frame(ci=min(which(x$broken + x$loop == 0))))
})
cut.index = max(cis$ci) + 6
experiments = subset(experiments, t < cut.index)

integral = ddply(experiments, c("rep", "prince", "experiment"), function(x) {
    return(data.frame(i=sum(x$broken) + sum(x$loop)))
})

average = ddply(integral, c("prince", "experiment"), function(x) {
    avg = mean(x$i)
    if (nrow(x) > 1) {
        ci = t.test(x$i)
        lc = ci$conf.int[1]
        uc = ci$conf.int[2]
    } else {
        lc = avg
        uc = avg
    }
    return(data.frame(average=avg, lc=lc, uc=uc, total=sum(x$i)))
})

lr = data.frame(experiment=folder, lr=1-average[average$prince==1,]$total/average[average$prince==0,]$total)

write.table(experiments, file=paste(folder, "experiments.csv", sep="/"), row.names=F, col.names=F)
write.table(integral, file=paste(folder, "integral.csv", sep="/"), row.names=F, col.names=F)
write.table(average, file=paste(folder, "average.csv", sep="/"),   row.names=F, col.names=F)
write.table(lr, file=paste(folder, "lr.csv", sep="/"),             row.names=F, col.names=F)
