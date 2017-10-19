library(plyr)
library(ggplot2)

experiments = read.table("./t130_summary/experiments.csv")
names(experiments) = c("total", "broken", "loop", "t", "time", "rep", "prince", "experiment")

idx = ddply(experiments, .(rep, prince), function(x) {
    x = x[order(x$t),]
    idx = min(which(x$broken != 0))
    ci = min(which(x$broken + x$loop == 0 & x$t > idx))
    return(data.frame(ci=ci))
})
cut.index = max(idx$ci) + 6
experiments = subset(experiments, t < cut.index)

to.plot <- experiments
to.plot <- subset(experiments, rep %in% c(0:9))
p = ggplot(to.plot, aes(x=time, y=broken, col=factor(prince))) + xlim(c(0,40)) +
    geom_line(size=1.1) +
    scale_color_hue(name="Strategy", labels=c("OLSRd", "Prince")) +
    geom_line(aes(x=time, y=loop), size=1.1, linetype = "dashed") +
    facet_grid(rep~.) +
    theme(legend.text=element_text(size=20)) +
    guides(colour = guide_legend(override.aes = list(size=3)))
print(p)
