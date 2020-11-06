Vagrant.configure(2) do |config|
  config.vagrant.plugins = "vagrant-reload"

  config.vm.box = "ubuntu/xenial64"

  config.vm.provider "virtualbox" do |vb|
    vb.name = "Masterarbeit" + Time.now.strftime(" %Y-%m-%d")
    vb.gui = false
    vb.memory = 4048
    vb.cpus = 2
    vb.customize ["modifyvm", :id, "--vram", "32"]
  end

  config.vm.synced_folder '.', '/vagrant'
  config.ssh.forward_x11 = true
  config.vm.hostname = "p4"
  config.vm.provision "shell", path: "dependencies/root-bootstrap.sh"
  config.vm.provision :reload
  config.vm.provision "shell", path: "dependencies/libyang-sysrepo.sh"
  config.vm.provision "shell", privileged: false, path: "dependencies/user-bootstrap.sh"
end
