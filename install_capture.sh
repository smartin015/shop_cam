#!/bin/bash
sudo cp capture/capture_hls /usr/bin/capture_hls
sudo cp shop_capture.service /etc/systemd/system/shop_capture.service
sudo systemctl enable shop_capture.service

