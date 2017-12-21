#!/usr/bin/env sh

if [ -d wishful-poprow ]; then
	cd wishful-poprow
	git pull --rebase origin master
else
	git clone https://ans.disi.unitn.it/redmine/wishful-poprow.git
fi
