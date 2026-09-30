# Система имитации сетевой инфраструктуры для раннего обнаружения кибератак
Это набор скриптов для быстрого развертывания сети виртуальных машин, с ssh, telnet и mysql honepot-ловушками, работающих на Docker контейнерах, так же в сети организована система логирования событий для сбора данных о сканировании сети (вы можете получить ip, username, время сканирования и некоторые другие данные).

![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white) ![Python](https://img.shields.io/badge/Python-489620?style=flat&logo=python&logoColor=white) ![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=flat&logo=ruby&logoColor=white) 



## Необходимое програмное обеспечение
Для Windows:
  - WSL2
  - Vagrant (Version 2.4.9)
  - Oracle VirtualBox (Version 7.2)
  - Dokcer Desktop
    
## Развертка инфраструктуры
### 1. Подготовка необходимых файлов
Скопируйте репозиторий

Скачайте или создайте собственный vagrant box и отредактируйте Vagrantfile
### 2. Установка ПО на подсистему Linux
Устанавливаем всё вышеуказанное ПО на машину  Windows

Открываем WSL2:
  Устанавливаем vagrant
  
  В конец .bashrc добавляем строки (name_of_your_user замените на ваше имя пользователя)
  
  ```bash
  export VAGRANT_WSL_ENABLE_WINDOWS_ACCESS="1"
  export VAGRANT_WSL_WINDOWS_ACCESS_USER_HOME_PATH="/mnt/c/Users/name_of_your_user"
  export PATH="$PATH:/mnt/c/Program Files/Oracle/VirtualBox"
  export PATH="$PATH:/mnt/c/Windows/System32/WindowsPowerShell/v1.0/"
  ```

### 3. Сборка и запуск системы
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
