# MASTER_NODE=nuc10
# CONFIG_FILE=$HOME/.ssh/twist-ssh.cfg
MASTER_NODE=nuc0-44.wilab1.ilabt.iminds.be
CONFIG_FILE=$HOME/.ssh/wilab1-ssh.cfg
HOME_FOLDER=`ssh -F ${CONFIG_FILE} ${MASTER_NODE} "pwd"`
