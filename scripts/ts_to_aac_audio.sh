#!/bin/bash
gst-launch-1.0 filesrc location=$1 ! tsdemux name=demux  demux. ! aacparse ! filesink location=$2
