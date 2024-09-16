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

It was developed and tested with Python versions 3.10.6 and 3.12.3, but generally requires Python version 3.10 or higher. Also, required to install python libraries listed in requirement.txt file. 

## ffmpeg tool

Required to install the ffmpge tool. The ffmpeg tool used for conversion of input (mp4 or wav) file into wav audio file with mono mode and sampling frequency of 16000Hz. These parameters of audio file required for pyaanote.audio library. Also, ffmpeg used for criation of final audio cuts.

# Docker

I prepared Dockerfile for criation of Docker image with catisfied requirements. In Linux environment next command can be used for creation of the docker image:
```console
cd <application_directory>
sudo docker build --network=host -t <image_name> .
```

# Usage

## Unzip and prepare the model

Unzip the "pytorch_model_emb.zip" file with embedding model and locate it in the same direcory with the rest files.

## JSON config

Before running the application required to setup the config_params.json file. In the file you will find 3 parameters to set:
path_ffmpeg - path to ffmpeg tool
path_yaml - path to configuration faml file with parameters of the model (recommended to use default if you dont want to change the speaker diarization model)
min_duration - minimal duration in seconds used for segmentation model to seperate between speaking segments for the same speaker (0.5 default value)

## Running

To run the application in Linux environment use next command:
```console
python3 diarization.py -f <input_file>
```
Under <input_file> set inout mp4 or wav file for which you want to perform speaker dizarization.

## Running Log

 After running the application script you will find running log file "running.log" in the directory where you running from the script.
