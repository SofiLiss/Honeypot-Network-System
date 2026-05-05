# Система имитации сетевой инфраструктуры для раннего обнаружения кибератак
Это набор скриптов для быстрого развертывания сети виртуальных машин, с ssh, telnet и mysql honepot-ловушками, работающих на Docker контейнерах, так же в сети организована система логирования событий для сбора данных о сканировании сети (вы можете получить ip, username, время сканирования и некоторые другие данные).

![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=flat&logo=ruby&logoColor=white) 



## Необходимое програмное обеспечение
Для Windows:
  - WSL2 (для скачивания и настройки откройте https://learn.microsoft.com/ru-ru/windows/wsl/setup/environment)
  - Vagrant (Version 2.4.9; для скачивания откройте https://developer.hashicorp.com/vagrant)
  - Oracle VirtualBox (Version 7.2; для скачивания откройте https://www.virtualbox.org/)
  - Dokcer Desktop (для скачивания откройте https://docs.docker.com/desktop/) 
    
## Развертка инфраструктуры
1. Подготовка необходимых файлов
Скачайте все файлы или клонируйте репозиторий с помощью GIT Bash 

```bash
git clone https://github.com/SofiLiss/Honeypot-Network-System
```
Отредактируйте файл playbook: замените строки /path/to/ssh_honeypot_folder, /path/to/mysql_honeypot_folder, /path/to/telnet_honeypot_folder на пути к соответвующим папкам каждого honepot из репозитория

2. Установка ПО на подсистему Linux
Открываем WSL2
Устанавливаем vagrant

```bash
wget https://releases.hashicorp.com/vagrant/2.4.9/vagrant_2.4.9-1_amd64.deb
sudo apt install ./vagrant_2.4.9-1_amd64.deb
```
Открываем файл .bashrc для редактирования

```bash
nano ~/.bashrc
```
В конец файла добавляем строки

```bash
export VAGRANT_WSL_ENABLE_WINDOWS_ACCESS="1"
export VAGRANT_WSL_WINDOWS_ACCESS_USER_HOME_PATH="/mnt/c/Users/YOUR_WINDOWS_USERNAME"
export PATH="$PATH:/mnt/c/Program Files/Oracle/VirtualBox"
export PATH="$PATH:/mnt/c/Windows/System32/WindowsPowerShell/v1.0/"
```
(1)Разрешаем Vagrant доступ к приложениям Windows
(2)Вместо YOUR_WINDOWS_USERNAME впишите свое имя пользователя Windows
(3,4)Добавляем в PATH пути к VirtualBox и PowerShell, установленным на Windows

Устанавливаем ansible

```bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible -y
```

3. Сборка и запуск системы
Создаем среду vagrant

```bash
mkdir my-vagrant-project
cd my-vagrant-project
mv mnt/путь/к/скачанному/ранее/Vagrantfile .
mv mnt/путь/к/скачанной/ранее/папке/provisioning .
```
В этой же директории поднимаем систему

```bash
vagrant up
```
Наслаждайтесь 
