library(plyr)
library(ggplot2)
require('tikzDevice')
require(RColorBrewer)
source('plot-utils.R')
source('ccs.palettes.R')

#palette(brewer.pal(3, "Paired"))

palette(brewer.pal(4, "RdYlBu"))
a <- palette()
np <- c('black', a[4], a[1], a[2])
a[3] <- a[1]
a[2] <- a[4]
a[1] <- 'black'
palette(np)

#graphs params
plot.width <- 308.43/72
plot.height <- 184.546607/72/1.25
plot.margin <- c(3.1, 3.3, 0.4, 0.4)
leg.inset <- c(0, 0, 0, 0)

colorize <- function(color) {
    col = col2rgb(3)
    return(rgb(col[1], col[2], col[3], 127, maxColorValue=255))
    # return(rgb(col[1], col[2], col[3], 60, maxColorValue=255))
}
color.ap <- Vectorize(colorize)

plot.serie <- function(x, y, pt.col, serie) {
    lines(x, y, col=t.col(serie), lty=t.lty(serie), lwd=t.lwd(serie))
    point.color = ifelse(pt.col == 1, color.ap(t.col(serie)), t.col(serie))
    points(x, y, col=point.color, pch=t.pch(serie), cex=t.cex(serie))
}

t.col <- function(timer) {
    ifelse(timer == "th", 3,
    ifelse(timer == "ta", 3,
    ifelse(timer == "h", 1,
    ifelse(timer == "tc", 1,
    ifelse(timer == "hnd", 2, 2)))))
}
t.pch <- function(timer) {
    ifelse(timer == "th", NA,
    ifelse(timer == "ta", NA,
    ifelse(timer == "h", 20,
    ifelse(timer == "tc", 18,
    ifelse(timer == "hnd", 4, 3)))))
}
t.lty <- function(timer) {
    ifelse(timer == "th", 1,
    ifelse(timer == "ta", 2,
    ifelse(timer == "h", 1,
    ifelse(timer == "tc", 2,
    ifelse(timer == "hnd", 1, 2)))))
}
t.lwd <- function(timer) {
    2
}
t.cex <- function(timer) {
    0.7
}

get.exp.name <- function(path) {
    parts <- unlist(strsplit(path, "/"))
    for (p in parts) {
        if (substr(p, 1, 1) == "t" &
            (substr(p, nchar(p)-7, nchar(p)) == "_summary" |
             substr(p, nchar(p)-7, nchar(p)) == "_results"
             )
            ) {
            n = substr(p, 2, nchar(p)-8)
            if (suppressWarnings(!is.na(as.numeric(n)))) {
                return(substr(p, 1, nchar(p)-8))
            }
        }
    }
    return("")
}

plot.routes <- function(outputFile, xlim, ylim, data, leg.pos='topright', outputDir = './') {

    done <- myps(outputFile = outputFile, width=plot.width, height=plot.height, outputDir=outputDir)

    par(mar=plot.margin, xpd=F)

    plot.new()
    plot.window(xlim=xlim, ylim=ylim, yaxs="i", xaxs="i")

    #n.colors <- 2
    #palette(gray.colors(n=n.colors, start=0, end=0.8))
    #palette(get.ccs.fireprint.palette(n=n.colors, max=0.7))

    ddply(data, c("prince"), function(x) {
        x <- x[order(x$time),]
        prince = x[1,]$prince
        lines(x$time, x$broken, col=prince+1, lwd=2, lty=1)
        lines(x$time, x$loop, col=prince+1, lwd=2, lty=2)
        0
    })

    axis(1, padj=-.7, las=1, lwd=0, lwd.ticks=1)
    axis(2, hadj=.7, las=1, lwd=0, lwd.ticks=1)
    title(xlab="time (s)", line=1.9)
    title(ylab="paths", line=2.1)

    legend(
        leg.pos,
        legend=c('OLSR (broken)', 'OLSR (loop)', 'Poprouting (broken)', 'Poprouting (loop)'),
        ncol=1,
        inset=c(0, 0),
        col=c(1, 1, 2, 2),
        lty=c(1, 2, 1, 2),
        lwd=3,
        box.lwd=0,
        cex=.8,
        seg.len=3
    )

    box()
    done()
}

plot.boxplot <- function(outputFile, cf, xlim, ylim, xlab, data, outputDir = './results/', yat=NULL, xat=NULL, ylab='speed (km/h)', xlabels=c()) {

    bpdata <- data.frame()
    ddply(data, c(cf), function(x) {
        r <- x[1,]
        d <- data.frame(c(r$min, r$q25, r$q50, r$q75, r$max) * 3.6)
        names(d) <- c(r[cf])
        if (length(bpdata) == 0) {
            bpdata <<- d
        } else {
            bpdata <<- cbind(bpdata, d)
        }
        0
    })
    print(bpdata)
    bxpdata <- list(stats=data.matrix(bpdata), names=names(bpdata), n=rep(1, ncol(bpdata)))

    done <- myps(outputFile = outputFile, width=plot.width, height=plot.height, outputDir=outputDir)

    par(mar=plot.margin, xpd=F)

    plot.new()
    plot.window(xlim=xlim, ylim=ylim, yaxs="i", xaxs="i")

    bxp(bxpdata, axes=F, ylim=ylim, xaxs="i", yaxs="i")
    points(data[[cf]]+1, data$mean*3.6, pch=4)

    axis(1, padj=-.7, las=1, lwd=0, lwd.ticks=1, labels=xlabels, at=1:length(xlabels))
    axis(2, hadj=.7, las=1, lwd=0, lwd.ticks=1, at=yat)
    title(xlab=xlab, line=1.9)
    title(ylab=ylab, line=2.1)

    box()
    done()
}
