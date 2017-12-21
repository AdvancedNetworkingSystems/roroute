#!/usr/bin/env sh

if [ -d wishful-poprow ]; then
	cd wishful-poprow
	git pull --rebase origin master
else
	git clone ssh://git@ans.disi.unitn.it:6022/wishful-poprow.git
fi
