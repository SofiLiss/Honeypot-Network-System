import logging
import threading
import re
import socket
import random
import sys
from datetime import datetime
from io import StringIO
from typing import Optional

import paramiko
from paramiko import RSAKey, ServerInterface, Transport
from paramiko.common import OPEN_SUCCEEDED, OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
from paramiko.ssh_exception import SSHException

# Отключаем логирование paramiko
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

CTRL_C = b"\x03"
CTRL_D = b"\x04"
ANSI_SEQUENCE = b"\x1b"
DEL = b"\x7f"

FAKE_COMMANDS = {
	"ls": "bin boot cdrom dev etc home lib lib32 libx64 lib64 lost+found media mnt opt proc root run sbin snap srv sys tmp usr var",
	"pwd": "/",
	"whoami": "root",
	"": "",
	"cd": "",
	"cd /": "",
	"uname": "Linux",
	"uname -s": "Linux",
	"uname -n": "fake-server",
	"uname -r": "5.4.0-26-generic",
	"uname -v": "#26-Ubuntu SMP",
	"uname -m": "x86_64",
	"uname -p": "x86_64",
	"uname -i": "x86_64",
	"uname -o": "GNU/Linux",
	"uname -a": "Linux fake-server 5.4.0-26-generic #26-Ubuntu SMP x86_64 x86_64 x86_64 GNU/Linux",
}

ANSI_REGEX = re.compile(rb"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


class FakeSSHServer:
	
	def __init__(self, host: str = "0.0.0.0", port: int = 2222, 
				 log_file: str = "ssh_honeypot.log", verbose: bool = True):
		self.host = host
		self.port = port
		self.log_file = log_file
		self.verbose = verbose
		self.server_banner = random.choice([
			"OpenSSH 7.5", "OpenSSH 7.3", 
			"Serv-U SSH Server 15.1.1.108", "OpenSSH 6.4"
		])
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
	

		# self._print_status("Сервер запущен и ожидает подключений...", "success")
		# self._print_status(f"Логирование подключений в файл: {self.log_file}", "info")
		# print("\n" + "=" * 70 + "\n")
	
	def _log(self, message: dict):
	
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		log_entry = f"[{timestamp}] {message}\n"
		
		
		with open(self.log_file, "a") as f:
			f.write(log_entry)
		
		
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
			elif action == "command":
				self._print_status(
					f"💻 ВВЕДЕНА КОМАНДА | IP: {message.get('client_ip')} | "
					f"Команда: {message.get('command')}",
					"info"
				)
			elif action == "publickey_auth":
				self._print_status(
					f"🔑 АУТЕНТИФИКАЦИЯ ПО КЛЮЧУ | IP: {message.get('client_ip')} | "
					f"Пользователь: {message.get('username')}",
					"info"
				)
			else:
				print(log_entry.strip())
	
	@staticmethod
	def _generate_ssh_keys() -> str:
		
		key = RSAKey.generate(2048)
		string_io = StringIO()
		key.write_private_key(string_io)
		return string_io.getvalue()
	
	def _handle_interactive_session(self, channel: paramiko.Channel, 
									client_ip: str, client_port: int):

		channel.send(b"Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-26-generic x86_64)\r\n\r\n")
		timeout_start = datetime.now().timestamp() + 300
		
		while datetime.now().timestamp() < timeout_start:
			try:
				channel.send(b"$ ")
				command_line = self._receive_line(channel)
			except (TimeoutError, EOFError):
				break
			
			self._log({
				"action": "command",
				"client_ip": client_ip,
				"client_port": client_port,
				"command": command_line
			})
			
			if command_line == "exit":
				break
			
			self._send_response(channel, command_line)
	
	def _receive_line(self, channel: paramiko.Channel) -> str:
		
		line = b""
		
		while not any(line.endswith(char) for char in [b"\r", b"\n", CTRL_C]):
			channel.settimeout(10)
			received = channel.recv(1024)
			
			if not received or received == CTRL_D:
				channel.send(b"^D\r\n")
				raise EOFError
			
			if received == CTRL_C:
				channel.send(b"^C\r\n")
			elif received == b"\r":
				channel.send(b"\n")
			elif ANSI_SEQUENCE in received:
				received = ANSI_REGEX.sub(b"", received)
			
			if DEL in received:
				received = received.replace(DEL, b"")
			
			if received:
				line += received
				channel.send(received)
		
		return line.strip().decode(errors="replace")
	
	def _send_response(self, channel: paramiko.Channel, command: str):
		
		if not command or command.endswith(CTRL_C.decode()):
			return
		
		if command in FAKE_COMMANDS:
			response = FAKE_COMMANDS[command]
			channel.send(f"{response}\r\n".encode())
		elif command.startswith("cd "):
			target = self._parse_arguments(command)
			if not target:
				channel.send(b"\r\n")
			else:
				if target.startswith("~"):
					target = target.replace("~", "/root")
				channel.send(f"sh: 1: cd: can't cd to {target}\r\n".encode())
		elif command.startswith("ls "):
			target = self._parse_arguments(command)
			if not target:
				channel.send(f"{FAKE_COMMANDS['ls']}\r\n".encode())
			else:
				channel.send(f"ls: cannot open directory '{target}': Permission denied\r\n".encode())
		else:
			channel.send(f"{command}: command not found\r\n".encode())
	
	@staticmethod
	def _parse_arguments(command: str) -> Optional[str]:
		
		args = [arg for arg in command.split(" ")[1:] if arg and not arg.startswith("-")]
		return args[0] if args else None
	
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
	
	def _handle_client(self, client_socket: socket.socket, private_key: str):
		
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
		
		class SSHHandler(ServerInterface):
			def __init__(self, ip, port, parent):
				self.client_ip = ip
				self.client_port = port
				self.parent = parent
				self.event = threading.Event()
				self.auth_data = {}
			
			def check_channel_request(self, kind, *args, **kwargs):
				return OPEN_SUCCEEDED if kind == "session" else OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
			
			def check_auth_password(self, username, password):
				username = username if isinstance(username, str) else username.decode()
				password = password if isinstance(password, str) else password.decode()
				
				self.auth_data['username'] = username
				self.auth_data['password'] = password
				
				
				self.parent._print_connection_details(
					self.client_ip, 
					self.client_port,
					username=username,
					password=password
				)
				
				self.parent._log({
					"action": "login_attempt",
					"client_ip": self.client_ip,
					"client_port": self.client_port,
					"username": username,
					"password": password,
					"connection_number": self.parent.connection_count
				})
				
				# Всегда разрешаем вход
				return paramiko.common.AUTH_SUCCESSFUL
			
			def check_auth_publickey(self, username, key):
				fingerprint = key.get_fingerprint().hex()
				
				self.parent._print_connection_details(
					self.client_ip,
					self.client_port,
					username=username,
					password="(публичный ключ)"
				)
				
				self.parent._log({
					"action": "publickey_auth",
					"client_ip": self.client_ip,
					"client_port": self.client_port,
					"username": username,
					"fingerprint": fingerprint,
					"connection_number": self.parent.connection_count
				})
				return paramiko.common.AUTH_SUCCESSFUL
			
			def check_channel_exec_request(self, channel, command):
				command = command if isinstance(command, str) else command.decode()
				
				self.parent._print_status(
					f"💻 ВЫПОЛНЕНА КОМАНДА | IP: {self.client_ip} | Команда: {command[:100]}",
					"warning"
				)
				
				self.parent._log({
					"action": "command_exec",
					"client_ip": self.client_ip,
					"client_port": self.client_port,
					"command": command,
					"connection_number": self.parent.connection_count
				})
				self.event.set()
				return True
			
			def check_channel_shell_request(self, *args, **kwargs):
				self.parent._print_status(
					f"🐚 ЗАПРОШЕНА ИНТЕРАКТИВНАЯ ОБОЛОЧКА | IP: {self.client_ip}",
					"info"
				)
				return True
			
			def check_channel_direct_tcpip_request(self, *args, **kwargs):
				return OPEN_SUCCEEDED
			
			def check_channel_pty_request(self, *args, **kwargs):
				return True
		
		transport = Transport(client_socket)
		transport.local_version = f"SSH-2.0-{self.server_banner}"
		transport.add_server_key(RSAKey(file_obj=StringIO(private_key)))
		
		handler = SSHHandler(client_ip, client_port, self)
		
		try:
			transport.start_server(server=handler)
		except (SSHException, EOFError, ConnectionResetError) as error:
			self._print_status(f"Ошибка SSH сервера для {client_ip}: {error}", "error")
			return
		
		channel = transport.accept(30)
		
		if channel is not None:
			self._handle_interactive_session(channel, client_ip, client_port)
		
		transport.close()
		
		self._print_status(
			f"🔌 СОЕДИНЕНИЕ ЗАКРЫТО | IP: {client_ip} | Всего подключений: {self.connection_count}",
			"info"
		)
	
	def start(self):
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		try:
			server_socket.bind((self.host, self.port))
		except OSError as error:
			self._print_status(f"Не удалось запустить сервер: {error}", "error")
			return
		
		server_socket.listen(5)
		private_key = self._generate_ssh_keys()
		
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
						args=(client_socket, private_key)
					)
					client_thread.daemon = True
					client_thread.start()
					
					# Вывод статистики
					active_threads = threading.active_count() - 1  # минус основной поток
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

	import argparse
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--host", default="0.0.0.0", help="IP адрес для прослушивания (по умолчанию: 0.0.0.0)")
	parser.add_argument("--port", type=int, default=2222, help="Порт для прослушивания (по умолчанию: 2222)")
	parser.add_argument("--log", default="ssh_honeypot.log", help="Файл логов (по умолчанию: ssh_honeypot.log)")
	parser.add_argument("--quiet", action="store_true", help="Тихий режим (минимальный вывод)")
	
	args = parser.parse_args()
	
	honeypot = FakeSSHServer(
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
