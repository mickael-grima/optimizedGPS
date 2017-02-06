#!/usr/bin/env bash
sudo apt-get update

# dependencies
sudo apt-get install curl \
     linux-image-extra-$(uname -r) \
     linux-image-extra-virtual

# add docker's official GPG key
curl -fsSL https://yum.dockerproject.org/gpg | sudo apt-key add -

sudo add-apt-repository \
     "deb https://apt.dockerproject.org/repo/ \
     ubuntu-$(lsb_release -cs) \
     main"

# Install docker
sudo apt-get update
sudo apt-get -y install docker-engine

# Install docker machine
curl -L https://github.com/docker/machine/releases/download/v0.9.0/docker-machine-`uname -s`-`uname -m` >/tmp/docker-machine &&
chmod +x /tmp/docker-machine &&
sudo cp /tmp/docker-machine /usr/local/bin/docker-machine
