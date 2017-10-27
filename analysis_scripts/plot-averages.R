library(plyr)
source('plot-utils.R')
source('generic-plot.R')

#graphs params
plot.width <- 308.43/72
plot.height <- 184.546607/72/1.25
plot.margin <- c(3.1, 3.3, 0.4, 0.4)
leg.inset <- c(0, 0, 0, 0)

transform.x <- function(x, killed) {
    p = length(killed[killed>=0])
    n = length(killed[killed<0])
    ifelse(x >= 0, x, n + x + 1 + max(killed))
}
legend.x <- function(x, killed) {
    n = length(killed[killed<0])
    ifelse(x <= max(killed), x+1, x - max(killed) - n - 1)
}

col <- function(topo, degree) {
    ifelse(topo == "caveman",
           ifelse(degree == 0, 1, 2),
           ifelse(degree == 0, 3, 4)
    )
}
lty <- function(topo, degree) {
    ifelse(topo == "caveman",
           ifelse(degree == 0, 1, 2),
           ifelse(degree == 0, 3, 4)
    )
}
pch <- function(topo, degree) {
    ifelse(topo == "caveman",
           ifelse(degree == 0, 1, 2),
           ifelse(degree == 0, 3, 4)
    )
}

plot.averages <- function(outputFile, d, leg.pos='topright', outputDir = './') {

    done <- myps(outputFile = outputFile, width=plot.width, height=plot.height, outputDir=outputDir)

    par(mar=plot.margin, xpd=F)

    d$x = transform.x(d$killed, unique(d$killed))
    d <- d[order(d$x),]
    div = 10000.0
    d$abs.gain = d$abs.gain / div

    plot.new()
    plot.window(xlim=c(-1, max(d$x)+1), ylim=c(min(d$abs.gain), max(d$abs.gain)) * 1.05, yaxs="i", xaxs="i")

    i <- 1
    ddply(d, c("topology", "degree"), function(x) {
        col = col(x[1,]$topology, x[1,]$degree)
        lty = lty(x[1,]$topology, x[1,]$degree)
        pch = pch(x[1,]$topology, x[1,]$degree)
        lines(x$x, x$abs.gain, col=col, lty=lty, lwd=2)
        points(x$x, x$abs.gain, col=col, pch=pch, cex=.8, lwd=2)
        i <<- i + 1
    })

    axis(1, padj=-.7, las=1, lwd=0, lwd.ticks=1, at=unique(d$x), labels=legend.x(unique(d$x), unique(d$killed)))
    axis(2, hadj=.7, las=1, lwd=0, lwd.ticks=1)
    title(xlab="dead node index", line=1.9)
    title(ylab="abs integral gain ($\\times 10^4)$", line=2.1)

    box()

    par(xpd=T)
    legend(
        leg.pos,
        legend=c("caveman", "caveman ($d_i = 1$)", "waxman", "waxman ($d_i = 1$)"),
        ncol=2,
        inset=c(0, 0),
        col    = col(c("caveman", "caveman", "waxman", "waxman"), c(0, 1, 0, 1)),
        lty    = lty(c("caveman", "caveman", "waxman", "waxman"), c(0, 1, 0, 1)),
        pch    = pch(c("caveman", "caveman", "waxman", "waxman"), c(0, 1, 0, 1)),
        pt.cex = .8,
        lwd    = 2,
        box.lwd=0,
        cex=.8,
        seg.len=2.5
    )
    done()
}

# csv file obtained with
# Rscript average-experiment-runs.R --folders t2[0-9][0-9]_summary --out absolute-gain.csv
d <- read.csv('absolute-gain.csv')
plot.averages('absolute-gain', d, leg.pos='topright', outputDir = './')
