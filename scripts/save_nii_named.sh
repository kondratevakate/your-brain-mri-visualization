#!/bin/bash


for path in $1/*
# for each subdirectory in main dir
do

  # if it is a subdirectory

  if [ -d "${path}" ] ; then

      echo "Processing (basename $path) ..."
      # saving names for normalised and aseg files
      F_NORM="$(find $path/mri/ -name "*norm.mgz")";
      F_PARC="$(find $path/mri/ -name "*aparc+aseg.mgz")";
      # converting files to needed format
      mri_convert -it mgz -ot nii "$F_NORM" "$path/mri/$(basename $1)_$(basename $path)_norm.nii.gz"
      mri_convert -it mgz -ot nii "$F_PARC" "$path/mri/$(basename $1)_$(basename $path)_aparc+aseg.nii.gz"
  fi
done

