#!/bin/bash

export PYTHONPATH=`pwd`:/home/jonny/ctf-gameserver/src
backend=`mktemp -d`

for i in {0..100}
do
  /home/jonny/ctf-gameserver/scripts/checker/ctf-testrunner --first 1437258032 --backend $backend --tick $i --ip vulnbox-test.faust.ninja --team 1 --service 1 responsivesecurity:Checker
done

