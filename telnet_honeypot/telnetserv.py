#!/usr/bin/env python3

import argparse
import socket
import sys
import threading
import os
from datetime import datetime
from typing import Optional, Dict, Tuple


IAC = b"\xff"  
WONT = b"\xfc"
ECHO = b"\x01"
SUPPRESS_GO_AHEAD = b"\x03"
LINEMODE = b"\x22"
TERMINAL_TYPE = b"\x18"
NAWS = b"\x1f"


class TelnetHoneypot:
    
    def __init__(self, host: str = "0.0.0.0", port: int = 23, 
                 log_file: str = "telnet_honeypot.log", verbose: bool = True):
        self.host = host
        self.port = port
        self.log_file = log_file
        self.verbose = verbose
        self.running = True
        self.connection_count = 0
        
        
    def _print_status(self, message: str, status_type: str = "info"):

        colors = {
            "info": "\033[94m",      
            "success": "\033[92m",   
            "warning": "\033[93m",    
            "error": "\033[91m",     
            "connection": "\033[95m", 
            "reset": "\033[0m"        
        }
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = colors.get(status_type, colors["info"])
        
        if self.verbose:
            print(f"{color}[{timestamp}] {message}{colors['reset']}")
            sys.stdout.flush()
    
    def _log(self, message: dict):
      
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            if self.verbose:
                self._print_status(f"Не удалось записать в лог-файл: {e}", "error")
        
        if self.verbose:
            action = message.get("action", "unknown")
            
            if action == "connection":
                self._print_status(
                    f"🔌 НОВОЕ ПОДКЛЮЧЕНИЕ | IP: {message.get('client_ip')} | "
                    f"Порт: {message.get('client_port')}",
                    "connection"
                )
            elif action == "login_attempt":
                self._print_status(
                    f"🔑 ПОПЫТКА ВХОДА | IP: {message.get('client_ip')} | "
                    f"Логин: {message.get('username')} | Пароль: {message.get('password')}",
                    "warning"
                )
            elif action == "error":
                self._print_status(
                    f"❌ ОШИБКА | IP: {message.get('client_ip')} | "
                    f"Ошибка: {message.get('error')}",
                    "error"
                )
            else:
                print(log_entry.strip())
    
    def _strip_telnet_iac(self, data: bytes) -> bytes:
    
        result = b""
        i = 0
        while i < len(data):
            if data[i] == 0xFF:
                i += 2
                if i < len(data) and data[i-1] in [0xFA, 0xF9, 0xFB, 0xFC, 0xFD, 0xFE]:
                    i += 1
            else:
                result += bytes([data[i]])
                i += 1
        return result
    
    def _send_telnet_negotiation(self, client_socket: socket.socket):
        
        try:
            telnet_responses = bytes([
                0xFF, 0xFC, 0x01,  # IAC WONT ECHO
                0xFF, 0xFC, 0x03,  # IAC WONT SUPPRESS GO AHEAD
                0xFF, 0xFC, 0x22,  # IAC WONT LINEMODE
                0xFF, 0xFC, 0x18,  # IAC WONT TERMINAL TYPE
                0xFF, 0xFC, 0x1F,  # IAC WONT NAWS
            ])
            client_socket.send(telnet_responses)
        except:
            pass
    
    def _print_connection_details(self, client_ip: str, client_port: int, 
                                   username: str = None, password: str = None):
        
        print("\n" + "=" * 70)
        self._print_status("НОВОЕ ПОДКЛЮЧЕНИЕ ОБНАРУЖЕНО!", "connection")
        print(f"{'=' * 70}")
        print(f"  📍 IP Адрес: {client_ip}")
        print(f"  🔌 Порт: {client_port}")
        print(f"  🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if username:
            print(f"  👤 Логин: {username}")
        if password:
            print(f"  🔐 Пароль: {password}")
        print(f"{'=' * 70}\n")
    
    def _handle_client(self, client_socket: socket.socket):
       
        try:
            client_ip, client_port = client_socket.getpeername()
        except OSError as error:
            self._print_status(f"Ошибка получения адреса клиента: {error}", "error")
            return
        
        self.connection_count += 1
        
        self._log({
            "action": "connection",
            "client_ip": client_ip,
            "client_port": client_port,
            "connection_number": self.connection_count
        })
        
        try:
            
            self._send_telnet_negotiation(client_socket)
            
            state = "USERNAME"
            username = None
            buffer = b""
            
            client_socket.send(b"login: ")
            
            while self.running:
                try:
                    client_socket.settimeout(None)  # Без таймаута
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    clean_data = self._strip_telnet_iac(data)
                    
                    if clean_data:
                        buffer += clean_data
                    
                    while b'\n' in buffer or b'\r' in buffer:
                        if b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                        elif b'\r' in buffer:
                            line, buffer = buffer.split(b'\r', 1)
                        else:
                            break
                        
                        line = line.strip()
                        if line:
                            if state == "USERNAME":
                                username = line.decode('utf-8', errors='replace')
                                state = "PASSWORD"
                                client_socket.send(b"Password: ")
                                
                            elif state == "PASSWORD":
                                password = line.decode('utf-8', errors='replace')
                                
                                self._print_connection_details(
                                    client_ip, 
                                    client_port,
                                    username=username,
                                    password=password
                                )
                                
                                self._log({
                                    "action": "login_attempt",
                                    "client_ip": client_ip,
                                    "client_port": client_port,
                                    "username": username,
                                    "password": password,
                                    "connection_number": self.connection_count
                                })
                                
                                client_socket.send(b"\r\nLogin incorrect\r\n")
                                client_socket.send(b"Connection closed by foreign host.\r\n")
                                return
                                
                except (ConnectionResetError, BrokenPipeError):
                    break
                except Exception as e:
                    self._log({
                        "action": "error",
                        "client_ip": client_ip,
                        "client_port": client_port,
                        "error": str(e),
                        "connection_number": self.connection_count
                    })
                    break
                    
        except Exception as e:
            self._print_status(f"Ошибка обработки клиента {client_ip}: {e}", "error")
        finally:
            client_socket.close()
            self._print_status(
                f"🔌 СОЕДИНЕНИЕ ЗАКРЫТО | IP: {client_ip} | Всего подключений: {self.connection_count}",
                "info"
            )
    
    def start(self):

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
        except PermissionError:
            self._print_status(f"Для использования порта {self.port} требуются права администратора!", "error")
            self._print_status(f"Попробуйте: sudo python telnet_honeypot.py", "info")
            return
        except OSError as error:
            self._print_status(f"Не удалось запустить сервер: {error}", "error")
            return
        
        server_socket.listen(5)
        
        self._print_status("Сервер запущен и ожидает подключений...", "success")
        self._print_status(f"Логирование подключений в файл: {self.log_file}", "info")
        print("\n" + "=" * 70 + "\n")
        
        try:
            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    self._print_status(
                        f"📡 Входящее соединение от {client_address[0]}:{client_address[1]}",
                        "info"
                    )
                    
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    active_threads = threading.active_count() - 1
                    self._print_status(
                        f"📊 Статистика: Активных соединений: {active_threads} | "
                        f"Всего подключений: {self.connection_count}",
                        "info"
                    )
                    
                except Exception as error:
                    if self.running:
                        self._print_status(f"Ошибка при принятии соединения: {error}", "error")
        except KeyboardInterrupt:
            self._print_status("\nПолучен сигнал остановки...", "warning")
        finally:
            self.stop()
            server_socket.close()
    
    def stop(self):

        self.running = False
        self._print_status(
            f"\nСервер остановлен. Всего обработано подключений: {self.connection_count}",
            "success"
        )
        self._print_status(f"Логи сохранены в файл: {self.log_file}", "info")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="IP адрес для прослушивания (по умолчанию: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=23, help="Порт для прослушивания (по умолчанию: 23)")
    parser.add_argument("--log", default="telnet_honeypot.log", help="Файл логов (по умолчанию: telnet_honeypot.log)")
    parser.add_argument("--quiet", action="store_true", help="Тихий режим (минимальный вывод)")
    
    args = parser.parse_args()
    
    honeypot = TelnetHoneypot(
        host=args.host,
        port=args.port,
        log_file=args.log,
        verbose=not args.quiet
    )
    
    try:
        honeypot.start()
    except KeyboardInterrupt:
        honeypot.stop()
        print("\n👋 До свидания!")


if __name__ == "__main__":
    main()