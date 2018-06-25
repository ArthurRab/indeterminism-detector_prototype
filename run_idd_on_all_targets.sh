#!/bin/bash

set -ux

idd=$1
out = $2
shift 2

echo "" > $out

for i in $#
do
  eval sh $idd '$'$i '$'$(expr $i + 1) >> $out
done
