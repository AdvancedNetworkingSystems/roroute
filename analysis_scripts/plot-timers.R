library(plyr)
source('plot-utils.R')
source('generic-plot.R')

#graphs params
plot.width <- 308.43/72
plot.height <- 184.546607/72/1.25
plot.margin <- c(3.1, 3.3, 2.0, 0.4)
leg.inset <- c(0, 0, 0, 0)

add.alpha <- function(color) {
    col = col2rgb(3)
    return(rgb(col[1], col[2], col[3], 127, maxColorValue=255))
    # return(rgb(col[1], col[2], col[3], 60, maxColorValue=255))
}
add.alpha.v <- Vectorize(add.alpha)

plot.serie <- function(x, y, col, pt.col, lty, pch, cex=0.7, lwd=2) {
    lines(x, y, col=col, lty=lty, lwd=lwd)
    point.color = ifelse(pt.col == 1, add.alpha(col), col)
    points(x, y, col=point.color, pch=pch, cex=cex)
}

plot.timers <- function(outputFile, d, idx, xlab, leg.pos='topright', outputDir = './') {

    done <- myps(outputFile = outputFile, width=plot.width, height=plot.height, outputDir=outputDir)


    par(mar=plot.margin, xpd=F)

    d <- d[order(d[[idx]], decreasing=T),]
    d$k = 1:nrow(d)

    plot.new()
    plot.window(xlim=c(0, nrow(d)+1), ylim=c(0, round(max(d$h, d$tc, d$hnd, d$tcnd)) + 0.5), yaxs="i", xaxs="i")

    lwd=1
    abline(h=2, lwd=lwd, col=3, lty=1)
    abline(h=5, lwd=lwd, col=3, lty=2)
    plot.serie(d$k, d$h, col=1,    pt.col=d$ap, lty=1, pch=20, lwd=lwd)
    plot.serie(d$k, d$tc, col=1,   pt.col=d$ap, lty=2, pch=18, lwd=lwd)
    plot.serie(d$k, d$hnd, col=2,  pt.col=d$ap, lty=1, pch=4, lwd=lwd)
    plot.serie(d$k, d$tcnd, col=2, pt.col=d$ap, lty=2, pch=3, lwd=lwd)

    axis(1, padj=-.7, las=1, lwd=0, lwd.ticks=1)
    axis(2, hadj=.7, las=1, lwd=0, lwd.ticks=1)
    title(xlab=xlab, line=1.9)
    title(ylab="timer (s)", line=2.1)

    box()

    par(xpd=T)
    legend(
        leg.pos,
        legend=c('$t_H$', '$t_A$', '$t_H(i)$', '$t_A(i)$', '$t_H(i)$ ($d_i=1$)', '$t_A(i)$ ($d_i=1$)'),
        ncol=3,
        inset=c(0, -0.3),
        col=c(3, 3, 1, 1, 2, 2),
        lty=c(1, 2, 1, 2, 1, 2),
        pch=c(NA, NA, 20, 18, 4, 3),
        pt.cex=0.7,
        lwd=2,
        box.lwd=0,
        cex=.8,
        seg.len=2.5
    )
    done()
}
args = commandArgs(trailingOnly=T)

if (interactive()) {
    args = c('./backbone_theory.csv',
             './caveman.csv',
             './waxman.csv',
             './startgraph_waxman.csv',
             './startgraph_caveman.csv',
             './t100_summary/0/olsrd2_vanilla/start_graph.csv'
             )
} else {
    if (length(args) == 0) {
        stop("No arguments given. Expecting a list of .csv file names")
    }
}

for (f in args) {
    d <- read.csv(f)
    outdir = paste(dirname(f), "/", sep="")
    base = basename(f)
    name = unlist(strsplit(base, "[.]"))[1]
    plot.timers(name, d, "bc", "nodes by decreasing $b_i$", leg.pos='topright', outputDir = outdir)
}
