# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "custom_debian"
  config.vm.box_url = "E:/my_custom_debian.box"
  config.vm.box_check_update = false

   ################################# adminhost

  config.vm.define "adminhost" do |node|
  node.vm.network "private_network", ip: "192.168.56.10", auto_config: false
  node.vm.provision "shell", inline: <<-SHELL
    nmcli connection up enp0s8-static
    cat > /etc/NetworkManager/system-connections/enp0s8-static.nmconnection << 'EOF'
[connection]
id=enp0s8-static
type=ethernet
interface-name=enp0s8
autoconnect=true

[ipv4]
method=manual
addresses=192.168.56.10/24
gateway=192.168.56.1

[ipv6]
method=disabled
EOF
    chmod 600 /etc/NetworkManager/system-connections/enp0s8-static.nmconnection
  nmcli connection reload
  hostnamectl set-hostname adminhost
    echo "127.0.1.1 adminhost" >> /etc/hosts
  SHELL

  node.vm.provider "virtualbox" do |vb|
    vb.name   = "adminhost"
    vb.memory = 1024
    vb.cpus   = 1
    vb.customize ["modifyvm", :id, "--nic3", "none"]
    vb.customize ["modifyvm", :id, "--nic4", "none"]
    vb.customize ["modifyvm", :id, "--groups", "/manage"]
  end
end

 ################################# sqlserver

  config.vm.define "sqlserver" do |node|

  node.vm.network "private_network", ip: "192.168.56.20", auto_config: false

  node.vm.provision "shell", inline: <<-SHELL
    nmcli connection up enp0s8-static
    cat > /etc/NetworkManager/system-connections/enp0s8-static.nmconnection << 'EOF'
[connection]
id=enp0s8-static
type=ethernet
interface-name=enp0s8
autoconnect=true

[ipv4]
method=manual
addresses=192.168.56.20/24
gateway=192.168.56.1

[ipv6]
method=disabled
EOF
    chmod 600 /etc/NetworkManager/system-connections/enp0s8-static.nmconnection
  nmcli connection reload
  hostnamectl set-hostname sqlserver
    echo "127.0.1.1 sqlserver" >> /etc/hosts
  SHELL

  node.vm.provider "virtualbox" do |vb|
    vb.name   = "sqlserver"
    vb.memory = 1024
    vb.cpus   = 1
    vb.customize ["modifyvm", :id, "--nic3", "none"]
    vb.customize ["modifyvm", :id, "--nic4", "none"]
    vb.customize ["modifyvm", :id, "--groups", "/manage"]
  end
end


  ################################ workstation1 — группа: workstations

  config.vm.define "workstation1" do |node|
    
  node.vm.network "private_network", ip: "192.168.56.31", auto_config: false

  node.vm.provision "shell", inline: <<-SHELL
    nmcli connection up enp0s8-static
    cat > /etc/NetworkManager/system-connections/enp0s8-static.nmconnection << 'EOF'
[connection]
id=enp0s8-static
type=ethernet
interface-name=enp0s8
autoconnect=true

[ipv4]
method=manual
addresses=192.168.56.31/24
gateway=192.168.56.1

[ipv6]
method=disabled
EOF
    chmod 600 /etc/NetworkManager/system-connections/enp0s8-static.nmconnection
  nmcli connection reload
  hostnamectl set-hostname workstation1
    echo "127.0.1.1 workstation1" >> /etc/hosts
  SHELL

  node.vm.provider "virtualbox" do |vb|
    vb.name   = "workstation1"
    vb.memory = 1024
    vb.cpus   = 1
    vb.customize ["modifyvm", :id, "--nic3", "none"]
    vb.customize ["modifyvm", :id, "--nic4", "none"]
    vb.customize ["modifyvm", :id, "--groups", "/manage"]
  end
end


  #################################### workstation2 — группа: workstations

  config.vm.define "workstation2" do |node|

  node.vm.network "private_network", ip: "192.168.56.32", auto_config: false

  node.vm.provision "shell", inline: <<-SHELL
    nmcli connection up enp0s8-static
    cat > /etc/NetworkManager/system-connections/enp0s8-static.nmconnection << 'EOF'
[connection]
id=enp0s8-static
type=ethernet
interface-name=enp0s8
autoconnect=true

[ipv4]
method=manual
addresses=192.168.56.32/24
gateway=192.168.56.1

[ipv6]
method=disabled
EOF
    chmod 600 /etc/NetworkManager/system-connections/enp0s8-static.nmconnection
  nmcli connection reload
  hostnamectl set-hostname workstation2
    echo "127.0.1.1 workstation1" >> /etc/hosts
  SHELL

  node.vm.provider "virtualbox" do |vb|
    vb.name   = "workstation2"
    vb.memory = 1024
    vb.cpus   = 1
    vb.customize ["modifyvm", :id, "--nic3", "none"]
    vb.customize ["modifyvm", :id, "--nic4", "none"]
    vb.customize ["modifyvm", :id, "--groups", "/manage"]
  end
end
end
