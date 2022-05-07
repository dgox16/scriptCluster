#!/bin/bash

apt install -y tftpd-hpa nfs-kernel-server isc-dhcp-server syslinux pxelinux debootstrap

head -n -3 /etc/network/interfaces > tempinterfaces && mv tempinterfaces /etc/network/interfaces
cat << EOF >> /etc/network/interfaces
auto enp0s3
iface enp0s3 inet dhcp

auto enp0s8
iface enp0s8 inet static
    address 10.0.33.1
    netmask 255.255.255.0
    network 10.0.33.0
    broadcast 10.0.33.255"
EOF

cat << EOF >> /etc/sysctl.conf

net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF

sed '1,$d' /etc/dhcp/dhcpd.conf > tempDHCPConf && mv tempDHCPConf /etc/dhcp/dhcpd.conf
cat << EOF >> /etc/dhcp/dhcpd.conf 
allow booting;
allow bootp;
subnet 10.0.2.0 netmask 255.255.255.0 {
}
subnet 10.0.33.0 netmask 255.255.255.0 {
    range 10.0.33.20 10.0.33.30;
    next-server 10.0.33.1;
    option routers 10.0.33.1;
    option broadcast-address 10.0.33.255;
host masternode {
    hardware ethernet '+ macMaestro +';
    fixed-address 10.0.33.1;
}

host node1 {
    hardware ethernet '+ mac1 +';
    fixed-address 10.0.33.11;
    filename "/pxelinux.0";
}
host node2 {
    hardware ethernet '+ mac2 +';
    fixed-address 10.0.33.12;
    filename "/pxelinux.0";
}
}
EOF

