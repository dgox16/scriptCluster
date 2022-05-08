#!/bin/bash
mac1="08:00:27:44:c6:e4"
mac2="08:00:27:78:61:49"
macMaestro="08:00:27:91:2c:6c"
mac1Dir="01-${mac1//:/-}"
mac2Dir="01-${mac2//:/-}"

head -n -3 /etc/network/interfaces > temp && mv temp /etc/network/interfaces
cat << EOF >> /etc/network/interfaces
auto enp0s3
iface enp0s3 inet dhcp

auto enp0s8
iface enp0s8 inet static
    address 10.0.33.14
    netmask 255.255.255.240
    network 10.0.33.0
    broadcast 10.0.33.15
EOF

apt install -y tftpd-hpa nfs-kernel-server openssh-server isc-dhcp-server syslinux pxelinux debootstrap

# cat << EOF >> /etc/sysctl.conf

# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1
# EOF

sed '1,$d' /etc/dhcp/dhcpd.conf > temp && mv temp /etc/dhcp/dhcpd.conf
cat << EOF >> /etc/dhcp/dhcpd.conf
allow booting;
allow bootp;
subnet 10.0.2.0 netmask 255.255.255.0 {
}

subnet 10.0.33.0 netmask 255.255.255.240 {
    range 10.0.33.6 10.0.33.10;
    option routers 10.0.33.14;
    option broadcast-address 10.0.33.15;
    group {                                    
        filename "pxelinux.0";                 
        next-server 10.0.33.14;                 
        host node1 {                           
            hardware ethernet $mac1;
            fixed-address 10.0.33.1;
        }
        host node2 {                            
            hardware ethernet $mac2;
            fixed-address 10.0.33.2;
        }
    }
}
EOF

sed '1,$d' /etc/default/isc-dhcp-server > temp && mv temp /etc/default/isc-dhcp-server
cat << EOF >> /etc/default/isc-dhcp-server
DHCPDv4_CONF=/etc/dhcp/dhcpd.conf
DHCPDv4_PID=/var/run/dhcpd.pid
INTERFACESv4="enp0s8"
EOF

systemctl restart isc-dhcp-server
mkdir -p /srv/tftp /srv/nfs

sed '1,$d' /etc/default/tftpd-hpa > temp && mv temp /etc/default/tftpd-hpa
cat << EOF >> /etc/default/tftpd-hpa
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/srv/tftp"
TFTP_ADDRESS="10.0.33.14:69"
TFTP_OPTIONS="--secure --create"
EOF
systemctl restart tftpd-hpa

sed '1,$d' /etc/exports > temp && mv temp /etc/exports
cat << EOF >> /etc/exports
/srv/nfs/node1/ 10.0.33.1(rw,async,no_root_squash,no_subtree_check)
/srv/nfs/node2/ 10.0.33.2(rw,async,no_root_squash,no_subtree_check)
EOF

mkdir /srv/nfs/nodeX
debootstrap --arch amd64 bullseye /srv/nfs/nodeX https://deb.debian.org/debian


sed '1,$d' /srv/nfs/nodeX/etc/fstab > temp && mv temp /srv/nfs/nodeX/etc/fstab
cat << EOF >> /srv/nfs/nodeX/etc/fstab
/dev/nfs / nfs tcp,nolock 0 0
proc /proc proc defaults 0 0
none /tmp tmpfs defaults 0 0
none /var/tmp tmpfs defaults 0 0
none /media tmpfs defaults 0 0
none /var/log tmpfs defaults 0 0
EOF

# ANTES de chroot
mount -o bind /dev /srv/nfs/nodeX/dev
mount -o bind /run /srv/nfs/nodeX/run
mount -o bind /sys /srv/nfs/nodeX/sys
cp -a /home/scriptCluster/ /srv/nfs/nodeX/home/
chroot /srv/nfs/nodeX/

cp -vax /srv/nfs/nodeX/boot/*.pxe /srv/tftp
cp -vax /usr/lib/PXELINUX/pxelinux.0 /srv/tftp
cp -vax /usr/lib/syslinux/modules/bios/ldlinux.c32 /srv/tftp
tar czvf /srv/nfs/nodeX.tgz -C /srv/nfs/ nodeX --remove-files

cd /srv/nfs
tar xzvf nodeX.tgz
mv nodeX node1
tar xzvf nodeX.tgz
mv nodeX node2

sed '1,$d' /srv/nfs/node1/etc/hostname > temp && mv temp /srv/nfs/node1/etc/hostname
cat << EOF >> /srv/nfs/node1/etc/hostname
node1
EOF
sed '1,$d' /srv/nfs/node2/etc/hostname > temp && mv temp /srv/nfs/node2/etc/hostname
cat << EOF >> /srv/nfs/node2/etc/hostname
node2
EOF

mkdir /srv/tftp/pxelinux.cfg
touch /srv/tftp/pxelinux.cfg/0A002101
touch /srv/tftp/pxelinux.cfg/0A002102

cat << EOF >> /srv/tftp/pxelinux.cfg/0A002101
default node1
prompt 1
timeout 3
    label node1
    kernel vmlinuz.pxe
    append rw initrd=initrd.pxe root=/dev/nfs ip=dhcp nfsroot=10.0.33.14:/srv/nfs/node1/
EOF

cat << EOF >> /srv/tftp/pxelinux.cfg/0A002102
default node2
prompt 1
timeout 3
    label node2
    kernel vmlinuz.pxe
    append rw initrd=initrd.pxe root=/dev/nfs ip=dhcp nfsroot=10.0.33.14:/srv/nfs/node2/
EOF


