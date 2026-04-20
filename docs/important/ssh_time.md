srodrigo@srv746951:~$ sudo su
[sudo] password for srodrigo:
root@srv746951:/home/srodrigo# echo "ClientAliveInterval 60" >> /etc/ssh/sshd_config
root@srv746951:/home/srodrigo# echo "ClientAliveInterval 600" >> /etc/ssh/sshd_config
root@srv746951:/home/srodrigo# echo "ClientAliveCountMax 1200" >> /etc/ssh/sshd_config
root@srv746951:/home/srodrigo# service ssh restart
root@srv746951:/home/srodrigo#
