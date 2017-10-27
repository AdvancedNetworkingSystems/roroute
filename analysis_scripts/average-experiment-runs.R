library(plyr)
library(argparser)

def.fields = c("degree", "topology", "hm", "tcm", "disablelq", "killed")

p <- arg_parser("Merges and computes the integral of multiple experiments")
p <- add_argument(p, "--fields", help="fields to group by", nargs=Inf, default=NA)
p <- add_argument(p, "--folders", help="list of folders", nargs=Inf)
p <- add_argument(p, "--out", help="output csv file", default="out.csv")

if (interactive()) {
    args = c('./t200_summary',
             './t201_summary',
             './t202_summary',
             './t203_summary',
             './t204_summary',
             './t205_summary',
             './t206_summary',
             './t207_summary',
             './t208_summary',
             './t209_summary'
             )
    arguments = parse_args(p, argv=c("--fields", def.fields, "--folders", args))
} else {
    arguments = parse_args(p)
    if (all(is.na(arguments$fields)))
        arguments$fields = def.fields
}

exp.dict = read.csv('./exp-dictionary.csv')
ds <- data.frame()
for (f in arguments$folders) {
    expfolder = regmatches(f ,regexpr("t[0-9]+_summary", f))
    filename = paste(f, "integral.csv", sep="/")
    if (!file.exists(filename)) {
        print(paste("No file found. Skipping", filename))
        next
    }
    d <- read.table(filename, sep=" ")
    names(d) = c("strategy", "prince", "folder", "integral")
    d$folder = expfolder
    d <- merge(d, exp.dict, by="folder")
    ds <- rbind(ds, d)
}

avg = ddply(ds, arguments$fields, function(x) {
    prince = subset(x, prince == 1)
    olsr = subset(x, prince == 0)
    olsr.int = sum(olsr$integral)/nrow(olsr)
    prince.int = sum(prince$integral)/nrow(prince)
    return(data.frame(abs.gain=olsr.int - prince.int, rel.gain=1-prince.int/olsr.int, olsr.int=olsr.int, prince.int=prince.int))
})

write.csv(avg, file=arguments$out, row.names=F)

print(avg)
