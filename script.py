import os

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
a_file.write("auto enp0s3\niface enp0s3 inet dhcp\nauto enp0s8\niface enp0s3 inet static\n\taddress 10.0.33.1\n\tnetmask 255.255.255.0\n\tnetwork 10.0.33.0\n\tbroadcast 10.0.33.255")

a_file = open("/etc/sysctl.conf" "a")
a_file.write("\nnet.ipv6.conf.all.disable_ipv6 = 1\nnet.ipv6.conf.default.disable_ipv6 = 1")
