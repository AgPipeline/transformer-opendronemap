#!/bin/bash
id=$(docker create opendronemap/odm:0.9.1) && docker cp $id:/code/ ./ && docker rm $id
mv ./code/SuperBuild/ ./
mv ./code/docker/ ./
mv ./code/modules/ ./
mv ./code/opendm/ ./
mv ./code/stages/ ./

