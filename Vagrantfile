Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"
  config.vm.box_version = "12.20250126.1"
  config.vm.synced_folder "./", "/vagrant", owner: "vagrant"
  config.ssh.guest_port = 2222
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 1
  end


  # ===== МАШИНА 1: sqlserv =====
  config.vm.define "MYSQLSERVER" do |m|
    m.vm.network "private_network", ip: "192.168.56.5"
  end

  # ===== МАШИНА 2: workstation1 =====
  config.vm.define "workstation1" do |w|
    w.vm.network "private_network", ip: "192.168.56.21"
  end

  # ===== МАШИНА 3: workstation2 =====
  config.vm.define "workstation2" do |ww|
    ww.vm.network "private_network", ip: "192.168.56.22"
  end

  # ===== МАШИНА 4: admin =====
  config.vm.define "administration_host" do |a|
    a.vm.network "private_network", ip: "192.168.56.30"
    a.vm.provider "parallels" do |prl|
      prl.update_guest_tools = true
    end
  end


  config.vm.provision "ansible" do |ansible|
    ansible.compatibility_mode = "2.0"
    ansible.playbook = "provisioning/playbook.yaml"
    ansible.inventory_path = "provisioning/inventory.ini"
    # Позволяет Ansible использовать vagrant ssh user и ключи
    # ansible.extra_vars = {
    #   ansible_user: 'vagrant',
    #   ansible_ssh_private_key_file: '.vagrant/machines/MYSQLSERVER/virtualbox/private_key'
    # }
    ansible.groups = {
      "mysqlserv" => ["MYSQLSERVER"],
      "workstations" => ["workstation1", "workstation2"],
      "adminhost" => ["administration_host"]
    }
  end
end
