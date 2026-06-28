#!/usr/bin/env python3

import socket
import struct
import random
import sys
import threading
from datetime import datetime
from typing import Optional, Dict, Tuple

CTRL_C = b"\x03"
CTRL_D = b"\x04"

class MySQLHoneypot:
	
	def __init__(self, host: str = "0.0.0.0", port: int = 3306, 
				 log_file: str = "mysql_honeypot.log", verbose: bool = True):
		self.host = host
		self.port = port
		self.log_file = log_file
		self.verbose = verbose
		self.running = True
		self.connection_count = 0
		self.server_version = random.choice(["8.0.19", "8.0.23", "5.7.32", "5.6.51"])
		
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
		
		timestamp = datetime.now().strftime("%Y-%Y-%m-%d %H:%M:%S")
		log_entry = f"[{timestamp}] {message}\n"
		
		with open(self.log_file, "a") as f:
			f.write(log_entry)
		
		# Вывод в консоль с форматированием
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
					f"Логин: {message.get('username')} | Пароль: {message.get('password_used')}",
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
	
	def _store2(self, value: int) -> bytes:
		"""Упаковка 2-байтового числа в little-endian"""
		return struct.pack('<H', value)
	
	def _store4(self, value: int) -> bytes:
		"""Упаковка 4-байтового числа в little-endian"""
		return struct.pack('<I', value)
	
	def _create_server_greeting(self, thread_id: int) -> bytes:

		protocol_version = b'\x0a'
		server_version = self.server_version.encode() + b'\x00'
		salt_1 = bytes([random.randint(0, 255) for _ in range(8)]) + b'\x00'
		
		capabilities = b'\xff\xf7\x21\x02\x00\xff\x81\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
					   b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff' + \
					   b'mysql_native_password\x00'
		
		greeting = (protocol_version + server_version + self._store4(thread_id) + salt_1 + capabilities)
		packet_length = struct.pack('<I', len(greeting))[:3]
		packet = packet_length + b'\x00' + greeting
		
		return packet
	
	def _create_auth_failed(self, seq: int, user: str, host: str, use_pwd: bool = True) -> bytes:

		error_template = b'\xff\x15\x04' + b'#28000'
		password_status = "YES" if use_pwd else "NO"
		error_msg = f"Access denied for user '{user}'@'{host}' (using password: {password_status})".encode()
		
		payload = error_template + error_msg
		packet_length = struct.pack('<I', len(payload))[:3]
		packet = packet_length + bytes([seq]) + payload
		
		return packet
	
	def _parse_auth_packet(self, data: bytes) -> Dict:

		result = {
			'user': 'unknown',
			'has_password': True,  
			'auth_plugin': 'mysql_native_password'
		}
		
		try:
		
			import re
			ascii_strings = re.findall(b'[a-zA-Z0-9_@.-]{3,32}', data)
			
			
			if ascii_strings:
				skip_words = [b'localhost', b'client', b'plugin', b'auth', b'password', 
							b'sha2', b'caching', b'native', b'mysql', b'linux', b'x86']
				
				for s in ascii_strings:
					decoded = s.decode('utf-8', errors='ignore')
					
					if not any(skip in s.lower() for skip in skip_words):
						if len(decoded) > 2 and decoded.isprintable():
							result['user'] = decoded
							break
			
	
			if b'caching_sha2_password' in data:
				result['auth_plugin'] = 'caching_sha2_password'
			elif b'mysql_native_password' in data:
				result['auth_plugin'] = 'mysql_native_password'
			
			
			result['has_password'] = True
			
			print(f"[DEBUG] Found user: {result['user']}")
			print(f"[DEBUG] Auth: {result['auth_plugin']}")
			
		except Exception as e:
			print(f"[DEBUG] Error: {e}")
		
		return result
	
	def _print_connection_details(self, client_ip: str, client_port: int, 
								   username: str = None, password_used: bool = False):

		print("\n" + "=" * 70)
		self._print_status("НОВОЕ ПОДКЛЮЧЕНИЕ ОБНАРУЖЕНО!", "connection")
		print(f"{'=' * 70}")
		print(f"  📍 IP Адрес: {client_ip}")
		print(f"  🔌 Порт: {client_port}")
		print(f"  🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		print(f"  🗄️  Версия MySQL: {self.server_version}")
		if username:
			print(f"  👤 Логин: {username}")
			print(f"  🔐 Пароль использован: {'ДА' if password_used else 'НЕТ'}")
		print(f"{'=' * 70}\n")
	
	def _handle_client(self, client_socket: socket.socket):

		try:
			client_ip, client_port = client_socket.getpeername()
		except OSError as error:
			self._print_status(f"Ошибка получения адреса клиента: {error}", "error")
			return
		
		self.connection_count += 1
		thread_id = random.randint(1, 1000000)
		
		self._log({
			"action": "connection",
			"client_ip": client_ip,
			"client_port": client_port,
			"connection_number": self.connection_count
		})
		
		try:
			
			greeting = self._create_server_greeting(thread_id)
			client_socket.send(greeting)
			
			
			client_socket.settimeout(30)
			data = client_socket.recv(1024)
			
			if not data:
				self._print_status(f"⚠️ Нет данных от {client_ip}:{client_port}", "warning")
				return
			
			
			login_info = self._parse_auth_packet(data)
			username = login_info['user']
			has_password = login_info['has_password']
			
			
			self._print_connection_details(
				client_ip, 
				client_port,
				username=username,
				password_used=has_password
			)
			
			
			self._log({
				"action": "login_attempt",
				"client_ip": client_ip,
				"client_port": client_port,
				"username": username,
				"password_used": "YES" if has_password else "NO",
				"connection_number": self.connection_count
			})
			
			
			error_packet = self._create_auth_failed(2, username, client_ip, has_password)
			client_socket.send(error_packet)
			
			self._print_status(
				f"📤 ОТКАЗАНО В ДОСТУПЕ | IP: {client_ip} | Пользователь: {username}",
				"warning"
			)
			
		except socket.timeout:
			self._print_status(f"⏰ Таймаут соединения от {client_ip}:{client_port}", "warning")
			self._log({
				"action": "error",
				"client_ip": client_ip,
				"client_port": client_port,
				"error": "Connection timeout",
				"connection_number": self.connection_count
			})
		except Exception as e:
			self._print_status(f"❌ Ошибка обработки клиента {client_ip}: {e}", "error")
			self._log({
				"action": "error",
				"client_ip": client_ip,
				"client_port": client_port,
				"error": str(e),
				"connection_number": self.connection_count
			})
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
		except OSError as error:
			self._print_status(f"Не удалось запустить сервер: {error}", "error")
			return
		
		server_socket.listen(5)
		
		self._print_status("Сервер запущен и ожидает подключений...", "success")
		self._print_status(f"Логирование подключений в файл: {self.log_file}", "info")
		self._print_status(f"Версия MySQL: {self.server_version}", "info")
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
		"""Остановка сервера"""
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
	parser.add_argument("--port", type=int, default=3306, help="Порт для прослушивания (по умолчанию: 3306)")
	parser.add_argument("--log", default="mysql_honeypot.log", help="Файл логов (по умолчанию: mysql_honeypot.log)")
	parser.add_argument("--quiet", action="store_true", help="Тихий режим (минимальный вывод)")
	
	args = parser.parse_args()
	
	honeypot = MySQLHoneypot(
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