#!/bin/bash
sudo cp run.sh /usr/bin/run_network_av && sudo chmod a+x /usr/bin/run_network_av
sudo cp network_av /usr/bin/network_av
sudo cp shop_cam.service /etc/systemd/system/shop_cam.service
sudo systemctl enable shop_cam.service

