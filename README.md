# Description

In this repository, you will find a speaker diarization application implemented using the [pyannote.audio](https://huggingface.co/pyannote) library and the [ffmpeg](https://ffmpeg.org/) tool. t is designed to work in offline mode and uses two pretrained models required for speaker diarization. The segmentation model is [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) , and the embedding model is [pyannote/wespeaker-voxceleb-resnet34-LM](https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM).

The application is oriented toward two speakers only but can be generalized with some code modifications. It accepts mp4 and wav files as input.

As a result, the application creates a CSV file with speaker diarization timestamps and generates audio file segments based on them. The audio cuts are split into three categories: the first speaker, the second speaker, and both speakers speak at the same time.

> [!NOTE]
> To access the model descriptions, you need to be registered on [huggingface.co](https://huggingface.co) and accept the conditions for each model.

# Requirements

## OS

The application was tested in a Linux (Ubuntu 24.04 LTS) environment but is potentially not restricted to Linux OS only. 

## Python version

It was developed and tested with Python versions 3.10.6 and 3.12.3, but generally requires Python version 3.10 or higher. Additionally, it is necessary to install the Python libraries listed in the requirements.txt file.

## ffmpeg tool

You are also required to install the ffmpeg tool. The ffmpeg tool is used for converting the input mp4 or wav files into a wav audio file with mono mode and a sampling frequency of 16,000 Hz. These audio file parameters are required by the pyannote.audio library. Furthermore, ffmpeg is used for creating the final audio cuts.

# Docker

I prepared a Dockerfile for the creation of a Docker image with the required dependencies. In a Linux environment, the following commands can be used to create the Docker image:
```console
cd <application_directory>
sudo docker build --network=host -t <image_name> .
```

In a Linux environment, the following commands can be used to run the application from the Docker image:
```console
cd <application_directory>
cp <input_file> <application_directory>
sudo docker run --rm -v $(pwd):/app <image_name> python3 /app/diarization.py -f /app/<input_file_name>
```
> [!NOTE]
> It is necessary to copy the input file (the desired mp4 or wav file) to the application directory. Only this directory will be mounted to the Docker image environment, allowing access to the input file from within the image.

# Usage

## Unzip and prepare the model

Unzip the "pytorch_model_emb.zip" file containing the embedding model and place it in the same directory as the other files.

## JSON config

Before running the application, you need to set up the config_params.json file. In this file, you will find three parameters to configure:
- path_ffmpeg: The path to the ffmpeg tool.
- path_yaml: The path to the configuration yaml file with the model parameters (it is recommended to use the default yalm file if you don't want to change the speaker diarization models).
- min_duration: The minimum duration (in seconds) used by the segmentation model to separate speaking segments for the same speaker (0.5 is the default value).
## Running

To run the application in a Linux environment, use the following command:
```console
python3 diarization.py -f <input_file>
```
Under <input_file> set input mp4 or wav file for which you want to perform speaker dizarization.

After running the application script, you will find the "result_dir" directory in the directory from which you ran the script. The "result_dir" directory will include the csv report and directories with audio file cuts by speaker.

## Running Log

After running the application script, you will find the log file "running.log" in the directory from which you ran the script.
