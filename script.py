import os
# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument("macMaestro")
# parser.add_argument("mac1")
# parser.add_argument("mac2")
# args = parser.parse_args()
mac1 = "08:00:27:44:c6:34"
mac2 = "08:00:27:78:61:49"
macMaestro = "08:00:27:91:2c:6c"
mac1Dir = "01-" + mac1.replace(":","-")
mac2Dir = "01-" + mac2.replace(":","-")
os.system("apt install -y tftpd-hpa nfs-kernel-server isc-dhcp-server syslinux pxelinux debootstrap")

a_file = open("/etc/network/interfaces", "r")
list_of_lines = a_file.readlines()
list_of_lines[-1] = ""
list_of_lines[-2] = ""
list_of_lines[-3] = ""
a_file = open("/etc/network/interfaces", "w")
a_file.writelines(list_of_lines)
a_file.close()
a_file = open("/etc/network/interfaces", "a")
a_file.write("auto enp0s3\niface enp0s3 inet dhcp\n\nauto enp0s8\niface enp0s8 inet static\n\taddress 10.0.33.1\n\tnetmask 255.255.255.0\n\tnetwork 10.0.33.0\n\tbroadcast 10.0.33.255")

a_file = open("/etc/sysctl.conf", "a")
a_file.write("\nnet.ipv6.conf.all.disable_ipv6 = 1\nnet.ipv6.conf.default.disable_ipv6 = 1")

a_file = open("/etc/dhcp/dhcpd.conf", "w") 
a_file.truncate(0)
a_file.write('allow booting;\nallow bootp;\nsubnet 10.0.2.0 netmask 255.255.255.0 {\n}\n\nsubnet 10.0.33.0 netmask 255.255.255.0 {\n\trange 10.0.33.20 10.0.33.30;\n\tnext-server 10.0.33.1;\n\toption routers 10.0.33.1;\n\toption broadcast-address 10.0.33.255;\nhost masternode {\n\thardware ethernet '+ macMaestro +';\n\tfixed-address 10.0.33.1;\n}\n\nhost node1 {\n\thardware ethernet '+ mac1 +';\n\tfixed-address 10.0.33.11;\n\tfilename "/pxelinux.0";\n}\nhost node2 {\n\thardware ethernet '+ mac2 +';\n\tfixed-address 10.0.33.12;\n\tfilename "/pxelinux.0";\n}\n}')
a_file.close()

a_file = open("/etc/default/isc-dhcp-server", "w")
a_file.truncate(0)
a_file.write('DHCPDv4_CONF=/etc/dhcp/dhcpd.conf\nDHCPDv4_PID=/var/run/dhcpd.pid\nINTERFACESv4="enp0s8"')
a_file.close()

os.system("systemctl restart isc-dhcp-server")
os.system("mkdir -p /srv/tftp /srv/nfs")

a_file = open("/etc/exports", "w")
a_file.truncate(0)
a_file.write("/srv/nfs/node1/ 10.0.33.11(rw,async,no_root_squash,no_subtree_check)\n/srv/nfs/node2/ 10.0.33.12(rw,async,no_root_squash,no_subtree_check)")
a_file.close()

a_file = open("/etc/default/tftpd-hpa", "w")
a_file.truncate(0)
a_file.write('TFTP_USERNAME="tftp"\nTFTP_DIRECTORY="/srv/tftp"\nTFTP_ADDRESS="10.0.33.1:69"\nTFTP_OPTIONS="--secure --create"')
a_file.close()

os.system("cp -vax /usr/lib/PXELINUX/pxelinux.0 /srv/tftp")
os.system("cp -vax /usr/lib/syslinux/modules/bios/ldlinux.c32 /srv/tftp")
os.system("mkdir /srv/tftp/pxelinux.cfg")
os.system("touch /srv/tftp/pxelinux.cfg/"+ mac1Dir)
os.system("touch /srv/tftp/pxelinux.cfg/"+ mac2Dir)

a_file = open("/srv/tftp/pxelinux.cfg/"+mac1Dir, "w")
a_file.write("default node1\nprompt 1\ntimeout 3\n\tlabel node1\n\tkernel vmlinuz.pxe\n\tappend rw initrd=initrd.pxe root=/dev/nfs ip=dhcp nfsroot=10.0.33.1:/srv/nfs/node1/")
a_file.close()
a_file = open("/srv/tftp/pxelinux.cfg/"+mac2Dir, "w")
a_file.write("default node2\nprompt 1\ntimeout 3\n\tlabel node2\n\tkernel vmlinuz.pxe\n\tappend rw initrd=initrd.pxe root=/dev/nfs ip=dhcp nfsroot=10.0.33.1:/srv/nfs/node2/")
a_file.close()

os.system("systemctl restart tftpd-hpa")
os.system("systemctl restart nfs-kernel-server")

os.system("mkdir /srv/nfs/node1")
os.system("debootstrap --arch amd64 bullseye /srv/nfs/node1 https://deb.debian.org/debian")

a_file = open("/srv/nfs/node1/etc/fstab", "w")
a_file.truncate(0)
a_file.write("/dev/nfs / nfs tcp,nolock 0 0\nproc /proc proc defaults 0 0\nnone /tmp tmpfs defaults 0 0\nnone /var/tmp tmpfs defaults 0 0\nnone /media tmpfs defaults 0 0\nnone /var/log tmpfs defaults 0 0")
a_file.close()

a_file = open("/srv/nfs/node1/etc/network/interfaces", "w")
a_file.truncate(0)
a_file.write("source /etc/network/interfaces.d/*\niface enp0s3 inet dhcp")
a_file.close()

# Cosas por sabe

os.system("chroot /srv/nfs/node1")
os.system("mount -t proc proc proc")
os.system("apt update -y && apt install -y initramfs-tools linux-image-amd64 ")
os.system("echo BOOT=nfs >> /etc/initramfs-tools/initramfs.conf")
os.system("mkinitramfs -d /etc/initramfs-tools/initramfs.conf -o /boot/initrd.pxe")
os.system("update-initramfs -u")
# os.system("cp -vax /boot/initrd.img* /boot/initrd.pxe")
# os.system("cp -vax /boot/vmlinuz* /boot/vmlinuz.pxe")
