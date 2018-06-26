#!/bin/bash

set -u #x

idd=$1
out=$2
shift 2

echo "" > $out

while [[ $# > 0 ]]
do
  echo "" >> $out
  echo $(basename $1 | cut -d "_" -f2) >> $out
  echo $1 $2
  echo "$(sh $idd $1 $2 2>&1)" >> $out
  shift 2
done

cat $out
