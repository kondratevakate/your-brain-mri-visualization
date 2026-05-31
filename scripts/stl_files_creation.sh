#!/bin/bash
for f in $1/*

do
  echo "Processing $f file..."
  # Create a surface model of the binarized volume with mri_tessellate
  # echo "${f%.nii.gz}.stl"
  mri_tessellate $f 1 $1/subcortical

  # Convert binary surface output into stl format
  mris_convert $1/subcortical "${f%.nii.gz}.stl"

 
done

