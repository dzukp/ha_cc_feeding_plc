#!/bin/bash

mkdir -p ../../custom_components/ && cp -r ../ha_config/custom_components/ ../../custom_components/
mkdir -p ../../www/ && cp -r ../ha_config/www/ ../../www/
mkdir -p ../../lovelace/ && cp -r ../ha_config_dk/lovelace/ ../../lovelace/
cp ../ha_config_dk/*.yaml ../../
