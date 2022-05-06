import os
# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument("macMaestro")
# parser.add_argument("mac1")
# parser.add_argument("mac2")
# args = parser.parse_args()
mac1 = "08:00:27:44:c6:e4"
mac2 = "08:00:27:78:61:49"
macMaestro = "08:00:27:91:2c:6c"
mac1Dir = "01-" + mac1.replace(":","-")
mac2Dir = "01-" + mac2.replace(":","-")

os.system("apt install -y tftpd-hpa nfs-kernel-server isc-dhcp-server syslinux pxelinux debootstrap")

fileInterfaces = open("/etc/network/interfaces", "r")
list_of_lines = fileInterfaces.readlines()
list_of_lines[-1] = ""
list_of_lines[-2] = ""
list_of_lines[-3] = ""
fileInterfaces = open("/etc/network/interfaces", "w")
fileInterfaces.writelines(list_of_lines)
fileInterfaces.close()
fileInterfaces= open("/etc/network/interfaces", "a")
fileInterfaces.write("auto enp0s3\niface enp0s3 inet dhcp\n\nauto enp0s8\niface enp0s8 inet static\n\taddress 10.0.33.1\n\tnetmask 255.255.255.0\n\tnetwork 10.0.33.0\n\tbroadcast 10.0.33.255")

fileSysctl = open("/etc/sysctl.conf", "a")
fileSysctl.write("\nnet.ipv6.conf.all.disable_ipv6 = 1\nnet.ipv6.conf.default.disable_ipv6 = 1")

fileDhcpd = open("/etc/dhcp/dhcpd.conf", "w") 
fileDhcpd.truncate(0)
fileDhcpd.write('allow booting;\nallow bootp;\nsubnet 10.0.2.0 netmask 255.255.255.0 {\n}\n\nsubnet 10.0.33.0 netmask 255.255.255.0 {\n\trange 10.0.33.20 10.0.33.30;\n\tnext-server 10.0.33.1;\n\toption routers 10.0.33.1;\n\toption broadcast-address 10.0.33.255;\nhost masternode {\n\thardware ethernet '+ macMaestro +';\n\tfixed-address 10.0.33.1;\n}\n\nhost node1 {\n\thardware ethernet '+ mac1 +';\n\tfixed-address 10.0.33.11;\n\tfilename "/pxelinux.0";\n}\nhost node2 {\n\thardware ethernet '+ mac2 +';\n\tfixed-address 10.0.33.12;\n\tfilename "/pxelinux.0";\n}\n}')
fileDhcpd.close()

fileISCDHCP = open("/etc/default/isc-dhcp-server", "w")
fileISCDHCP.truncate(0)
fileISCDHCP.write('DHCPDv4_CONF=/etc/dhcp/dhcpd.conf\nDHCPDv4_PID=/var/run/dhcpd.pid\nINTERFACESv4="enp0s8"')
fileISCDHCP.close()

os.system("systemctl restart isc-dhcp-server")
os.system("mkdir -p /srv/tftp /srv/nfs")

fileExports = open("/etc/exports", "w")
fileExports.truncate(0)
fileExports.write("/srv/nfs/node1/ 10.0.33.11(rw,async,no_root_squash,no_subtree_check)\n/srv/nfs/node2/ 10.0.33.12(rw,async,no_root_squash,no_subtree_check)")
fileExports.close()

fileTftpd = open("/etc/default/tftpd-hpa", "w")
fileTftpd.truncate(0)
fileTftpd.write('TFTP_USERNAME="tftp"\nTFTP_DIRECTORY="/srv/tftp"\nTFTP_ADDRESS="10.0.33.1:69"\nTFTP_OPTIONS="--secure --create"')
fileTftpd.close()

os.system("cp -vax /usr/lib/PXELINUX/pxelinux.0 /srv/tftp")
os.system("cp -vax /usr/lib/syslinux/modules/bios/ldlinux.c32 /srv/tftp")
os.system("mkdir /srv/tftp/pxelinux.cfg")
os.system("touch /srv/tftp/pxelinux.cfg/"+ mac1Dir)
os.system("touch /srv/tftp/pxelinux.cfg/"+ mac2Dir)

filePxelinux = open("/srv/tftp/pxelinux.cfg/"+mac1Dir, "w")
filePxelinux.write("default node1\nprompt 1\ntimeout 3\n\tlabel node1\n\tkernel vmlinuz.pxe\n\tappend rw initrd=initrd.pxe root=/dev/nfs ip=dhcp nfsroot=10.0.33.1:/srv/nfs/node1/")
filePxelinux.close()
filePxelinux = open("/srv/tftp/pxelinux.cfg/"+mac2Dir, "w")
filePxelinux.write("default node2\nprompt 1\ntimeout 3\n\tlabel node2\n\tkernel vmlinuz.pxe\n\tappend rw initrd=initrd.pxe root=/dev/nfs ip=dhcp nfsroot=10.0.33.1:/srv/nfs/node2/")
filePxelinux.close()

os.system("systemctl restart tftpd-hpa")
os.system("systemctl restart nfs-kernel-server")

os.system("mkdir /srv/nfs/node1")
os.system("debootstrap --arch amd64 bullseye /srv/nfs/node1 https://deb.debian.org/debian")

fileFstab = open("/srv/nfs/node1/etc/fstab", "w")
fileFstab.truncate(0)
fileFstab.write("/dev/nfs / nfs tcp,nolock 0 0\nproc /proc proc defaults 0 0\nnone /tmp tmpfs defaults 0 0\nnone /var/tmp tmpfs defaults 0 0\nnone /media tmpfs defaults 0 0\nnone /var/log tmpfs defaults 0 0")
fileFstab.close()

fileInterfacesNodo = open("/srv/nfs/node1/etc/network/interfaces", "w")
fileInterfacesNodo.truncate(0)
fileInterfacesNodo.write("source /etc/network/interfaces.d/*\niface enp0s3 inet dhcp")
fileInterfacesNodo.close()

os.system("cp -a /home/scriptCluster/ /srv/nfs/node1/home/")
os.system("chroot /srv/nfs/node1")

os.system("cp -vax /srv/nfs/node1/boot/*.pxe /srv/tftp")
os.system("cp -a /srv/nfs/node1/ /srv/nfs/node2")

fileHostname = open("/srv/nfs/node1/etc/hostname", "w")
fileHostname.truncate(0)
fileHostname.write("node1")
fileHostname.close()
fileHostname = open("/srv/nfs/node2/etc/hostname", "w")
fileHostname.truncate(0)
fileHostname.write("node2")
fileHostname.close()

os.system("systemctl restart tftpd-hpa")
os.system("systemctl restart nfs-kernel-server")
os.system("systemctl restart isc-dhcp-server")
os.system("reboot")

