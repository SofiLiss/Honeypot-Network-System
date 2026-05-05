# Система имитации сетевой инфраструктуры для раннего обнаружения кибератак
Это набор скриптов для быстрого развертывания сети виртуальных машин, с ssh, telnet и mysql honepot-ловушками, работающих на Docker контейнерах, так же в сети организована система логирования событий для сбора данных о сканировании сети (вы можете получить ip, username, время сканирования и некоторые другие данные).
![Python](https://img.shields.io/badge/python-3.10+-green)

## Необходимое програмное обеспечение
Для Windows:
  - WSL2 (для скачиания и настройки откройте https://learn.microsoft.com/ru-ru/windows/wsl/setup/environment)
  - Vagrant (Version 2.4.9; для скачивания откройте https://developer.hashicorp.com/vagrant)
  - Oracle VirtualBox (Version 7.2; для скачивания откройте https://www.virtualbox.org/)
    
## Развертка инфраструктуры
1. Заупскаем WSL2
Устанавливаем vagrant

```bash
wget https://releases.hashicorp.com/vagrant/2.4.9/vagrant_2.4.9-1_amd64.deb
sudo apt install ./vagrant_2.4.9-1_amd64.deb
```

Устанавливаем ansible

```bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible -y
```
2. Подготовка необходимых файлов
Чтобы склонировать репозиотрий введите

```bash
wget https://releases.hashicorp.com/vagrant/2.4.9/vagrant_2.4.9-1_amd64.deb
sudo apt install ./vagrant_2.4.9-1_amd64.deb
```
## Стек технологий
* Python 3.10
