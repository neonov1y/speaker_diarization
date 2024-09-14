# Description

In this repository you will find speaker diarization application implemented using [pyannote.audio](https://huggingface.co/pyannote) library and [ffmpeg](https://ffmpeg.org/) tool. It designed to work in offline mode and use two pretrained models required for speaker diarization. The segmentation model is [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) and the embedded model is [pyannote/wespeaker-voxceleb-resnet34-LM](https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM).

The application oriented for two speakers only but can be generallyzed with some code modifications. As input it accepts mp4 and wav files.

As the result application creates CSV file with speaker diarization time stamps and creates audio file cuts according to it. The audio cuts splited to 3 categories: first speaker speak, second speaker speak and both speakers speak at the same time. 

[!NOTE]
Note that to get access to the models description you need to be registred in [huggingface.co](https://huggingface.co) and to accept the conditions.

# Requirements

The application tested in Linux (Ubuntu 24.04 LTS) environment but potentially not restricted to it. It developed and tested with python versions Python-3.10.6 and Python 3.12.3 but generally require Python version greater or equal to 3.10.

The ffmpeg tool used for conversion of input (mp4 or wav) file into wav audio file with mono mode and sampling frequency of 16000Hz. This parameters of auiod file required for pyaanote.audio library. Also, ffmpeg used for criation of final audio cuts.

# Docker

I prepared Dockerfile for preparation Docker image with catisfied requirements. In Linux environment next command can be used for creation of the docker image:
sudo docker build --network=host -t diarization .

# Usage
