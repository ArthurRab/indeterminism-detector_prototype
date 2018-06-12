set -eu

tar1=$1
tar2=$2

mkdir temp
cd temp

for i in 1 2
do
  mkdir image$i
  cd image$i
  eval tar -xf ../../'$'tar$i "manifest.json"
  start=1
  while [ true ]
  do
    start=`expr $start + 1`
    if [ `cut -d '"' -f${start} < "manifest.json"` = "Layers" ]
    then
      start=`expr $start + 2`
      break
    fi
  done
  eval start$i=$start
  cd ..
done

echo $start1 $start2


cd ..
rm -rf temp
