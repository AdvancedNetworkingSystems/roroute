library(plyr)
source('plot-utils.R')
source('generic-plot.R')

#graphs params
plot.width <- 308.43/72
plot.height <- 184.546607/72/1.25
plot.margin <- c(3.1, 3.3, 2.0, 0.4)
leg.inset <- c(0, 0, 0, 0)

plot.exp.timers <- function(outputFile, d, idx, xlab, leg.pos='topright', outputDir = './') {

    done <- myps(outputFile = outputFile, width=plot.width, height=plot.height, outputDir=outputDir)

    par(mar=plot.margin, xpd=F)

    d <- d[order(d[[idx]], decreasing=T),]
    d$k = 1:nrow(d)

    plot.new()
    plot.window(xlim=c(0, nrow(d)+1), ylim=c(0, round(max(d$h, d$tc)) + 1.1), yaxs="i", xaxs="i")
    abline(h=2, lwd=t.lwd("th"), col=t.col("th"), lty=t.lty("th"))
    abline(h=5, lwd=t.lwd("ta"), col=t.col("ta"), lty=t.lty("ta"))
    plot.serie(d$k, d$h   , pt.col=d$ap, serie="h")
    plot.serie(d$k, d$tc  , pt.col=d$ap, serie="tc")
    kp = subset(d, killed==1)
    points(kp$k, kp$h)
    points(kp$k, kp$tc)
    text(d$k, d$tc+0.5, gsub("nuc0-", "", d$node), cex=.5)

    axis(1, padj=-.7, las=1, lwd=0, lwd.ticks=1)
    axis(2, hadj=.7, las=1, lwd=0, lwd.ticks=1)
    title(xlab=xlab, line=1.9)
    title(ylab="timer (s)", line=2.1)

    box()

    par(xpd=T)
    legend(
        leg.pos,
        legend=c('$t_H$', '$t_A$', '$t_H(i)$', '$t_A(i)$'),
        ncol=2,
        inset=c(0, -0.3),
        col    = t.col(c("th", "ta", "h", "tc")),
        lty    = t.lty(c("th", "ta", "h", "tc")),
        pch    = t.pch(c("th", "ta", "h", "tc")),
        pt.cex = t.cex(c("th", "ta", "h", "tc")),
        lwd    = t.lwd(c("th", "ta", "h", "tc")),
        box.lwd=0,
        cex=.8,
        seg.len=2.5
    )
    done()
}
args = commandArgs(trailingOnly=T)

if (interactive()) {
    args = c('./t100_summary',
             './t110_summary'
             )
} else {
    if (length(args) == 0) {
        stop("No arguments given. Expecting a list of .csv file names or a list of folders")
    }
}

for (f in args) {
    ext = substr(f, nchar(f)-3, nchar(f))
    expname = get.exp.name(f)
    if (ext == ".csv") {
        filename = f
    } else {
        filename = paste(f, "intervals.csv", sep="/")
    }
    if (!file.exists(filename)) {
        print(paste("No file found. Skipping", filename))
        next
    }
    d <- read.csv(filename)
    outdir = paste(dirname(filename), "/", sep="")
    ddply(d, c("strategy"), function(x) {
        plot.name = paste("timers", expname, x[1,]$strategy, "bybc", sep="-")
        plot.exp.timers(plot.name, x, "expbc", "nodes by decreasing $b_i$", leg.pos='topright', outputDir = outdir)
    })
}
