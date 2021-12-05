# Networked intelligent workshop audio/video system

This is a collection of scripts and programs that provide a "research" platform for doing interesting things with
audio and video of a home workshop / makerspace.

There are three domains of interest:

* Recording for later presentation/reference
* Live streaming for remote interactions (via web or VR)
* Computer vision and audio for automation

See https://docs.google.com/document/d/1VW54ekxYT4wwJILSfTJFvfji0oQn1ebv5zD55KB5Wdo/ for additional engineering log.

## Installation

### Install dependencies for run.sh

** gstreamer libraries **

See also (here)[https://docs.nvidia.com/jetson/l4t/index.html#page/Tegra%20Linux%20Driver%20Package%20Development%20Guide/accelerated_gstreamer.html#wwpID0E0R40HA]

Note that for the Jetson Nano, scripts **MUST** be set up within an installation of the NVIDIA jetson nano official image - jetson nanos running Ubuntu
or other distro fail to install the proper gstreamer plugins to allow for hardware-based video encoding.

```
sudo apt-get install gstreamer1.0-tools gstreamer1.0-alsa \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav
sudo apt-get install libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  libgstreamer-plugins-good1.0-dev \
  libgstreamer-plugins-bad1.0-dev
```

** Aivero realsense toolkit  **

Follow this section if you want to use a realsense camera. Original installation instructions at https://gitlab.com/aivero/legacy/public/aivero-rgbd-toolkit.

Download the latest armv8 release - currently [this one](https://drive.google.com/u/0/uc?id=1VoBx2SES10AWMiHBqR-gwFW8vX-beZvc&export=download) as of 2021Q4.

Transfer it to the jetson nano (e.g. via SCP) and then extract it - the archive must be extracted relative to root for the right folder locations:

```
sudo mkdir -p  /opt/aivero && sudo chown $USER:USER /opt/aivero
tar -C / -xvf aivero_rgbd_toolkit_master.tar.gz
```

To enable use of both the NVIDIA and the aivero GST plugins, we need to edit the environment so both paths are included.
Open `/opt/aivero/rgbd_toolkit_armv8/aivero_environment.sh and replace the GST_PLUGIN_PATH` line with:

```
export GST_PLUGIN_PATH=/usr/lib/aarch64-linux-gnu/gstreamer-1.0:$PREFIX/lib/gstreamer-1.0
```


** Python 3.7 or above is required for http.server specific serving directory in run.sh **

```
sudo apt -y install python3.8
```

** rpicamsrc gstreamer element **
```
git clone https://github.com/thaytan/gst-rpicamsrc.git
cd gst-rpicamsrc/
./autogen.sh 
make
sudo make install
```

** Install paho-mqtt C++ libraries **
```
sudo apt-get install build-essential gcc make cmake cmake-gui cmake-curses-gui git doxygen graphviz libssl-dev
git clone https://github.com/eclipse/paho.mqtt.c.git
cd paho.mqtt.c
cmake -Bbuild -H. -DPAHO_WITH_SSL=ON
sudo cmake --build build/ --target install
sudo ldconfig
cd ..
git clone https://github.com/eclipse/paho.mqtt.cpp
cd paho.mqtt.cpp
cmake -Bbuild -H. -DPAHO_BUILD_DOCUMENTATION=TRUE -DPAHO_BUILD_SAMPLES=TRUE
sudo cmake --build build/ --target install
sudo ldconfig
```

### Building the binary

Build the C++ file (can also run build.sh, but including initial command here for posterity):
```
cd .../l2_makerspace/infra/timelapse
gcc network_av.cc -o network_av -lstdc++ -lpaho-mqtt3c -lpaho-mqtt3cs -lpaho-mqtt3a -lpaho-mqtt3as `pkg-config --cflags --libs gstreamer-1.0`
```

### Manual running
```
# Create a ramdisk to reduce chatter on the bus (assuming we're using a USB SSD)
# Following tutorial at https://www.linuxbabe.com/command-line/create-ramdisk-linux
# Experimentally, video streaming seems to use about 15M of space.
mkdir -p /tmp/ramdisk && chmod 777 /tmp/ramdisk
sudo mount -t tmpfs -o size=128m myramdisk /tmp/ramdisk

# For realsense, source the aivero environment (modified, as above)
source /opt/aivero/rgbd_toolkit_armv8/aivero_environment.h

# Run the binary from the ramdisk directory so the files are output there
cd /tmp/ramdisk && $PATH_TO_REPO/infra/timelapse/network_av

# In a separate tab, run simple webserver
cd /tmp/ramdisk && python3 -m http.server 8080

# Browse to <IP>:8080 for video!
```

Can also use VLC to receive the stream. To record headless:

```
cvlc -vvv http://192.168.1.8:8080/playlist.m3u8 --sout file/ts:stream.mpg

# Playback
vlc stream.mpg
```

# Manual testing

See ./scripts folder 

# Custom gst plugin to convert depth camera image to RVL

Extending from framework checked in at https://github.com/jackersson/gst-python-plugins

`gstplugin_py` is the default example plugin

```
export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$PWD/venv/lib/gstreamer-1.0/:$PWD/gst/
gst-inspect-1.0 gstplugin_py
gst-launch-1.0 videotestsrc ! gstplugin_py int-prop=100 float-prop=0.2 bool-prop=True str-prop="set" ! fakesink

```

`rvlencode` converts a depth image to run-variable-length encoding

