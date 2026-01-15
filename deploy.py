
import os
import sys
import subprocess
import time
import socket
import json
import shutil
from datetime import datetime

# Cores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(msg):
    print(f"\n{Colors.HEADER}=== {msg} ==={Colors.ENDC}")

def print_ok(msg):
    print(f"{Colors.OKGREEN}[OK] {msg}{Colors.ENDC}")

def print_fail(msg):
    print(f"{Colors.FAIL}[FAIL] {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}[INFO] {msg}{Colors.ENDC}")

def check_command(command):
    return shutil.which(command) is not None

def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0

def get_system_info():
    print_step("Coletando Informações do Sistema")
    
    info = {
        "os": sys.platform,
        "python": sys.version.split()[0],
        "cwd": os.getcwd(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Check Docker
    try:
        docker_version = subprocess.check_output(["docker", "--version"]).decode().strip()
        info["docker"] = docker_version
        print_ok(f"Docker encontrado: {docker_version}")
    except:
        info["docker"] = "Not found"
        print_fail("Docker não encontrado")

    # Check Docker Compose
    try:
        compose_version = subprocess.check_output(["docker-compose", "--version"]).decode().strip()
        info["docker_compose"] = compose_version
        print_ok(f"Docker Compose encontrado: {compose_version}")
    except:
        info["docker_compose"] = "Not found"
        print_fail("Docker Compose não encontrado")

    print_info(f"Sistema Operacional: {info['os']}")
    print_info(f"Diretório Atual: {info['cwd']}")
    
    return info

def start_docker_desktop():
    print_info("Tentando iniciar o Docker Desktop automaticamente...")
    possible_paths = [
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe"
    ]
    
    started = False
    for path in possible_paths:
        if os.path.exists(path):
            try:
                # Usar Popen para não bloquear o script
                subprocess.Popen([path], close_fds=True)
                print_ok(f"Docker Desktop iniciado: {path}")
                started = True
                break
            except Exception as e:
                print_fail(f"Erro ao iniciar Docker Desktop: {e}")
    
    if not started:
        print_fail("Não foi possível encontrar o executável do Docker Desktop.")
        print_info("Por favor, inicie-o manualmente.")
        return False
        
    print_info("Aguardando Docker Engine inicializar (pode levar alguns minutos)...")
    
    # Aguardar até 2 minutos
    for i in range(60):
        try:
            subprocess.check_call(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print()
            print_ok("Docker Engine detectado e operante!")
            return True
        except subprocess.CalledProcessError:
            time.sleep(2)
            sys.stdout.write(".")
            sys.stdout.flush()
    
    print()
    print_fail("Timeout aguardando Docker Engine. Verifique se o Docker Desktop está rodando.")
    return False

def check_docker_daemon():
    print_step("Verificando Docker Daemon")
    try:
        subprocess.check_call(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_ok("Docker Daemon está rodando")
        return True
    except subprocess.CalledProcessError:
        print_fail("Docker Daemon NÃO está rodando!")
        return start_docker_desktop()

def setup_environment():
    print_step("Configurando Ambiente")
    
    # 1. Verificar .env
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print_ok("Arquivo .env criado a partir de .env.example")
        else:
            print_fail("Arquivo .env.example não encontrado!")
            return False
    else:
        print_ok("Arquivo .env já existe")

    # 2. Verificar diretórios necessários
    dirs = ["pgdata", "radius/sql"]
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d, exist_ok=True)
                print_ok(f"Diretório criado: {d}")
            except Exception as e:
                print_fail(f"Falha ao criar diretório {d}: {e}")

    return True

def deploy_containers():
    print_step("Iniciando Deploy (Docker Compose)")
    
    cmd = ["docker-compose", "up", "-d", "--build"]
    
    try:
        print_info("Executando build e start dos containers... (Isso pode demorar)")
        subprocess.check_call(cmd)
        print_ok("Comando docker-compose executado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print_fail(f"Falha no deploy: {e}")
        return False

def verify_services():
    print_step("Verificando Serviços")
    
    services = [
        {"name": "API Backend", "port": 8000},
        {"name": "Admin Panel", "port": 5000},
        {"name": "PostgreSQL", "port": 5432},
        {"name": "Redis", "port": 6379},
        {"name": "Radius Auth", "port": 1812}, # UDP, hard to check with simple TCP connect
        {"name": "Zabbix Web", "port": 8081}
    ]
    
    print_info("Aguardando 10 segundos para inicialização dos serviços...")
    time.sleep(10)
    
    all_ok = True
    for svc in services:
        # Pular check TCP para Radius (UDP)
        if svc["name"] == "Radius Auth":
            continue
            
        if check_port("localhost", svc["port"]):
            print_ok(f"{svc['name']} está acessível na porta {svc['port']}")
        else:
            print_fail(f"{svc['name']} NÃO está respondendo na porta {svc['port']}")
            all_ok = False
            
    return all_ok

def main():
    print(f"{Colors.BOLD}=== Open-SGP Installer & Deployer ==={Colors.ENDC}\n")
    
    # 1. System Info
    sys_info = get_system_info()
    
    # 2. Docker Daemon Check
    if not check_docker_daemon():
        sys.exit(1)
        
    # 3. Setup Env
    if not setup_environment():
        sys.exit(1)
        
    # 4. Deploy
    if not deploy_containers():
        sys.exit(1)
        
    # 5. Verify
    if verify_services():
        print_step("Deploy Concluído com Sucesso!")
        print_info("Acesse o sistema em:")
        print(f"   Admin Panel: http://localhost:5000")
        print(f"   API Docs:    http://localhost:8000/docs")
        print(f"   Zabbix:      http://localhost:8081")
    else:
        print_step("Deploy Finalizado com Avisos")
        print_info("Alguns serviços podem não ter iniciado corretamente.")
        print_info("Verifique os logs com: docker-compose logs -f")

if __name__ == "__main__":
    main()
