# Pynq DPU with VART for Face recognition and tracking
Python based, face detection and tracking example application using VART API

## Prepare the Ultra96v2
### Install Pynq on the Ultra96v2
1. Get the pre-built SD image : [ultra96v2-pynq-image-v2.5](http://avnet.me/ultra96v2-pynq-image-v2.5)
2. Flash a SD Card with the collect image. (tested with [BalenaEtcher](https://www.balena.io/etcher/))

### Install Pynq Dpu
> The following come from https://github.com/Xilinx/DPU-PYNQ

#### Upgrade Board
This upgrade step is to make sure users have a DPU-ready image.
This step is only required for one time.

On your board, run `su` to use super user. Then run the following commands:

```shell
git clone --recursive --shallow-submodules https://github.com/Xilinx/DPU-PYNQ.git
cd DPU-PYNQ/upgrade
make
```

The upgrade process may take up to 1 hour, since a few packages will
need to be installed. Please be patient. For more information, users can check
the [PYNQ v2.5 upgrade instructions](./upgrade/README.md)

#### Install

Run the following on board:

```shell
pip3 install pynq-dpu
```

### Install additional required packages:

```shell
pip3 install centroid-tracker
pip3 install screeninfo
```

## Use
TBD
## References
https://github.com/Avnet/Ultra96-PYNQ
https://github.com/Xilinx/DPU-PYNQ
