# Parses a manifest.json to get the nth layer tar path (n = $layer_num)
function get_layer_tar () {
  image_num=$1
  layer_num=$2
  start_num=$3

  cut -d '"' -f$(($(($layer_num*2))+$start_num)) < "image${image_num}/manifest.json"
}

# Parses the layer tar path to get the layer id
function get_layer_id () {
  layer_tar=$1

  echo $layer_tar | cut -d '/' -f1
}

set -ue #x

# Setting empty variables to not crash as unbound variables
tar1=""
tar2=""
diff_args=""


OPTIND=1

# Parse arguments (flags and parameters)
# -q: quiet - only print out which files differ, not how
# -e: exit upon first difference in layers
# -h: help screen

while [[ $# > 0 ]]
do
  if [[ $1 =~ ^-.* ]]
  then
    while getopts "qe" opt # ADD h
    do
      case $opt in
        q)
          diff_args=q
        ;;
        e)
          exit_on_first_diff=true
        ;;
        #h)
        #  echo h - NOT IMPLEMENTED YET
        #;;
        *)
          exit 1
        ;;
      esac
    done
    shift
  else
    if [[ ${#tar1} == 0 ]]
    then
      tar1=$1
      shift
    elif [[ ${#tar2} == 0 ]]
    then
      tar2=$1
      shift
    else
      echo 'Too many arguments (exactly 2 required)' >&2
      exit 1
    fi
  fi
done

if [[ ${#tar2} == 0 ]]
then
  echo 'Not enough arguments (exactly 2 required)' >&2
  exit 1
fi

base1=$(basename $tar1)
base2=$(basename $tar2)

mkdir -p temp
cd temp

# Creates directories for the images where relevant files will be stored
# Files include: manifest.json and the layer tars
for i in 1 2
do
  mkdir -p image$i
  cd image$i
  eval tar -xf ../../'$'tar$i "manifest.json"
  start=1
  while [ true ]
  do
    start=$(expr $start + 1)
    if [ $(cut -d '"' -f${start} < "manifest.json") = "Layers" ]
    then
      start=$(expr $start + 2)
      break
    fi
  done
  eval start$i=$start # Stores where the first layer tar path appears in each image
  cd ..
done

# Keeps track of which images have already had all layers looked at
image1_done=0
image2_done=0

i=0
while true
do
  image1_layer_tar=$(get_layer_tar 1 $i $start1)
  image2_layer_tar=$(get_layer_tar 2 $i $start2)

  # If the attempt to find the next layer tar failed, the image is out of layers
  if ((${#image1_layer_tar} < 71))
  then
    image1_done=1
  fi
  if ((${#image2_layer_tar} < 71))
  then
    image2_done=1
  fi

  # If an image is out of layers we break an move onto the case where one image has extra layers
  if [ $image1_done = 1 ] || [ $image2_done = 1 ]
  then
    break
  fi

  # If the layer tar paths (and thus the layer ids) don't match between the images,
  # we extract the layer tars and call diff to check how they differ
  if [ $image1_layer_tar != $image2_layer_tar ]
  then
    for j in 1 2
    do
      cd image$j
      eval image${j}_layer_id=$(eval get_layer_id '$'image${j}_layer_tar)
      eval tar -xf ../../'$'tar$j '$'image${j}_layer_tar
      cd ..
      eval mkdir -p '$'base$j/'$'image${j}_layer_tar

      eval tar -xf image$j/'$'image${j}_layer_tar --directory='$'base$j/'$'image${j}_layer_tar
    done
    diff -r$diff_args --no-dereference $base1/$image1_layer_id $base2/$image2_layer_id
  fi
  if [ exit_on_first_diff = true ]
  then
    exit 0
  fi
  # Increment which layers we are comparing
  i=$(expr $i + 1)
done

# Print out any remaning layers after the other image ran out
# NOTE: The loop is called on both, but only one will have extra layers,
# they cannot both have extra layers, as those will be paired up
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

      echo $(get_layer_id $image_layer_tar)
      k=$(expr $k + 1)

    done
  fi
done

# Cleanup
cd ..
# rm -rf temp
