# Transformer OpenDroneMap

Uses OpenDroneMap to process drone captured RGB data.

### Sample Docker Command line
Below is a sample command line that shows how the OpenDroneMap Docker image could be run.
An explanation of the command line options used follows.
Be sure to read up on the [docker run](https://docs.docker.com/engine/reference/run/) command line for more information.

```docker run --rm --mount "src=/home/test,target=/mnt,type=bind" agpipeline/opendronemap:2.0 --working_space "/mnt" --metadata "/mnt/test/experiment.json" "/mnt/2018-10-21"```

This example command line assumes the source files are located in the `/home/test` folder of the local machine.
The name of the image to run is `agpipeline/opendronemap:2.0`.

We are using the same folder for the source files and the output files.
By using multiple `--mount` options, the source and output files can be located in separate folders.

**Docker commands** \
Everything between 'docker' and the name of the image are docker commands.

- `run` indicates we want to run an image
- `--rm` automatically delete the image instance after it's run
- `--mount "src=/home/test,target=/mnt,type=bind"` mounts the `/home/test` folder to the `/mnt` folder of the running image

We mount the `/home/test` folder to the running image to make files available to the software in the image.

**Image's commands** \
The command line parameters after the image name are passed to the software inside the image.
Note that the paths provided are relative to the running image (see the --mount option specified above).

- `--working_space "/mnt"` specifies the folder to use as a workspace
- `--metadata "/mnt//mnt/test/experiment.json"` contains the experiment metadata
- `"/mnt/2018-10-21"` is the name of the folder containing images to process
