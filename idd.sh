function get_layer_tar () {
  image_num=$1
  layer_num=$2
  start_num=$3

  echo `cut -d '"' -f$(($(($layer_num*2))+$start_num)) < "image${image_num}/manifest.json"`
}

function get_layer_id () {
  layer_tar=$1

  echo `echo $layer_tar | cut -d '/' -f1`
}

##CURRENTLY DOES NOT DETECT IF THERE ARE LAYERS WHICH ARE THE SAME BUT IN A DIFFERENT ORDER

set -u #ex

tar1=$1
tar2=$2

base1=$(basename $tar1)
base2=$(basename $tar2)

echo REMOVE -p
mkdir -p temp
cd temp

for i in 1 2
do
  echo REMOVE -p
  mkdir -p image$i
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

image1_done=0
image2_done=0

i=0
while true
do
  image1_layer_tar=`get_layer_tar 1 $i $start1`
  image2_layer_tar=`get_layer_tar 2 $i $start2`

  if ((${#image1_layer_tar} < 74))
  then
    image1_done=1
  fi
  if ((${#image2_layer_tar} < 74))
  then
    image2_done=1
  fi

  if [ $image1_done = 1 ] || [ $image2_done = 1 ]
  then
    break
  fi

  if [ $image1_layer_tar != $image2_layer_tar ]
  then
    for j in 1 2
    do
      cd image$j
      eval image${j}_layer_id=`eval get_layer_id '$'image${j}_layer_tar`
      eval tar -xf ../../'$'tar$j '$'image${j}_layer_tar
      cd ..
      eval mkdir -p '$'base$j/'$'image${j}_layer_tar

      eval tar -xf image$j/'$'image${j}_layer_tar --directory='$'base$j/'$'image${j}_layer_tar
    done
    diff -r $base1/$image1_layer_id $base2/$image2_layer_id
  fi

  i=`expr $i + 1`
done

for j in 1 2
do
  k=$i
  if eval [ '$'image${j}_done != 1 ]
  then
    eval start='$'start${j}
    eval echo Layers only in '$'tar${j}:
    while true
    do
      image_layer_tar=`get_layer_tar $j $k $start`
      if (( ${#image_layer_tar} < 74))
      then
        break
      fi

      echo `get_layer_id $image_layer_tar`
      k=`expr $k + 1`

    done
  fi
done

cd ..
rm -rf temp
