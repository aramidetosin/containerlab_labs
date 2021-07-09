#!/bin/sh
ssh aramideo@192.168.1.16 "sudo -S ip netns exec clab-isistopology-vr-vmx tcpdump -U -nni eth3 -w -" | wireshark -k -i -
