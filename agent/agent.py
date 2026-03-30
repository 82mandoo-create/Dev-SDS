#!/usr/bin/env python3
"""
AssetGuard PC Agent v1.0
기업 PC 모니터링 및 자산 관리 에이전트
Windows/Linux/macOS 지원
"""

import os
import sys
import json
import time
import platform
import subprocess
import threading
import logging
import socket
import uuid
import ctypes
import queue
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("requests 미설치: pip install requests")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ===== Configuration =====
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_config.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent.log")

DEFAULT_CONFIG = {
    "server_url": "http://localhost:8000",
    "agent_secret": "agent-communication-secret-key-2024",
    "agent_token": None,
    "pc_id": None,
    "heartbeat_interval": 60,  # seconds
    "activity_report_interval": 300,  # 5 minutes
    "app_scan_interval": 3600,  # 1 hour
    "log_level": "INFO"
}

# ===== Logging =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AssetGuardAgent")


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"설정 저장 실패: {e}")


# ===== System Information =====
class SystemInfo:
    @staticmethod
    def get_hostname() -> str:
        return socket.gethostname()

    @staticmethod
    def get_computer_name() -> str:
        if platform.system() == "Windows":
            return os.environ.get("COMPUTERNAME", socket.gethostname())
        return socket.gethostname()

    @staticmethod
    def get_os_info() -> Dict[str, str]:
        system = platform.system()
        return {
            "os_name": f"{system} {platform.release()}",
            "os_version": platform.version(),
            "os_build": platform.version().split(".")[-1] if "." in platform.version() else "",
            "os_architecture": platform.machine()
        }

    @staticmethod
    def get_cpu_info() -> str:
        if PSUTIL_AVAILABLE:
            try:
                import psutil
                cpu_count = psutil.cpu_count(logical=False)
                cpu_count_logical = psutil.cpu_count()
                freq = psutil.cpu_freq()
                freq_str = f" @ {freq.max:.0f}MHz" if freq else ""
                return f"{cpu_count} cores ({cpu_count_logical} logical){freq_str}"
            except:
                pass
        return platform.processor() or "Unknown"

    @staticmethod
    def get_ram_gb() -> Optional[float]:
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                return round(mem.total / (1024 ** 3), 1)
            except:
                pass
        return None

    @staticmethod
    def get_mac_address() -> str:
        try:
            mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
            return ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
        except:
            return ""

    @staticmethod
    def get_ip_address() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    @staticmethod
    def get_manufacturer_model() -> tuple:
        manufacturer = "Unknown"
        model = "Unknown"
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "computersystem", "get", "manufacturer,model"],
                    capture_output=True, text=True, timeout=5
                )
                lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip() and l.strip() != "Manufacturer  Model"]
                if lines:
                    parts = lines[0].split()
                    if len(parts) >= 2:
                        manufacturer = parts[0]
                        model = ' '.join(parts[1:])
            except:
                pass
        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/sys_vendor", 'r') as f:
                    manufacturer = f.read().strip()
                with open("/sys/class/dmi/id/product_name", 'r') as f:
                    model = f.read().strip()
            except:
                pass
        elif platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.split('\n'):
                    if "Model Name:" in line:
                        model = line.split(':')[1].strip()
                manufacturer = "Apple"
            except:
                pass
        return manufacturer, model

    @staticmethod
    def get_serial_number() -> str:
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "bios", "get", "serialnumber"],
                    capture_output=True, text=True, timeout=5
                )
                lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip() and l.strip() != "SerialNumber"]
                if lines:
                    return lines[0]
            except:
                pass
        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/product_serial", 'r') as f:
                    return f.read().strip()
            except:
                pass
        return str(uuid.uuid4())[:8].upper()

    @staticmethod
    def get_security_status() -> Dict[str, Any]:
        status = {
            "antivirus_installed": False,
            "antivirus_name": None,
            "firewall_enabled": False,
            "disk_encrypted": False,
            "windows_defender": False,
            "auto_update_enabled": False,
            "security_score": 0
        }

        if platform.system() == "Windows":
            # Check Windows Defender
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusEnabled"],
                    capture_output=True, text=True, timeout=10
                )
                if "True" in result.stdout:
                    status["windows_defender"] = True
                    status["antivirus_installed"] = True
                    status["antivirus_name"] = "Windows Defender"
            except:
                pass

            # Check Firewall
            try:
                result = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles", "state"],
                    capture_output=True, text=True, timeout=5
                )
                if "ON" in result.stdout:
                    status["firewall_enabled"] = True
            except:
                pass

            # Check BitLocker
            try:
                result = subprocess.run(
                    ["manage-bde", "-status", "C:"],
                    capture_output=True, text=True, timeout=10
                )
                if "Protection On" in result.stdout or "Fully Encrypted" in result.stdout:
                    status["disk_encrypted"] = True
            except:
                pass

        elif platform.system() == "Linux":
            # Check UFW firewall
            try:
                result = subprocess.run(
                    ["ufw", "status"],
                    capture_output=True, text=True, timeout=5
                )
                if "active" in result.stdout.lower():
                    status["firewall_enabled"] = True
            except:
                pass

            # Check for AV
            for av in ["clamav", "sophos", "symantec"]:
                try:
                    result = subprocess.run(["which", av], capture_output=True, text=True)
                    if result.returncode == 0:
                        status["antivirus_installed"] = True
                        status["antivirus_name"] = av.capitalize()
                        break
                except:
                    pass

        # Calculate security score
        score = 100
        if not status["antivirus_installed"]: score -= 25
        if not status["firewall_enabled"]: score -= 20
        if not status["disk_encrypted"]: score -= 15
        if not status["auto_update_enabled"]: score -= 10
        status["security_score"] = max(0, score)

        return status


# ===== Activity Monitor =====
class ActivityMonitor:
    def __init__(self):
        self.activities = []
        self.current_login_time = None
        self.current_user = None
        self._lock = threading.Lock()
        self._detect_current_user()

    def _detect_current_user(self):
        try:
            if platform.system() == "Windows":
                self.current_user = os.environ.get("USERNAME", "")
            else:
                self.current_user = os.environ.get("USER", "")
        except:
            self.current_user = ""

    def record_activity(self, activity_type: str, user_account: str = None, details: dict = None):
        with self._lock:
            activity = {
                "activity_type": activity_type,
                "user_account": user_account or self.current_user,
                "started_at": datetime.utcnow().isoformat(),
                "details": details or {}
            }
            self.activities.append(activity)
            logger.info(f"활동 기록: {activity_type} - {user_account or self.current_user}")

    def get_and_clear_activities(self) -> List[dict]:
        with self._lock:
            activities = self.activities.copy()
            self.activities.clear()
            return activities


# ===== Application Scanner =====
class AppScanner:
    @staticmethod
    def scan_installed_apps() -> List[Dict]:
        apps = []

        if platform.system() == "Windows":
            apps.extend(AppScanner._scan_windows_registry())
        elif platform.system() == "Linux":
            apps.extend(AppScanner._scan_linux_packages())
        elif platform.system() == "Darwin":
            apps.extend(AppScanner._scan_macos_apps())

        return apps

    @staticmethod
    def _scan_windows_registry() -> List[Dict]:
        apps = []
        try:
            import winreg
            keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            for hive, key_path in keys:
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                with winreg.OpenKey(key, winreg.EnumKey(key, i)) as subkey:
                                    try:
                                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        if name:
                                            version = ""
                                            publisher = ""
                                            install_date = None
                                            try: version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                            except: pass
                                            try: publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                                            except: pass
                                            try:
                                                date_str = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                                if date_str and len(date_str) == 8:
                                                    install_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T00:00:00"
                                            except: pass
                                            apps.append({
                                                "app_name": name,
                                                "app_version": version,
                                                "publisher": publisher,
                                                "install_date": install_date,
                                                "category": AppScanner._categorize_app(name)
                                            })
                                    except: pass
                            except: pass
                except: pass
        except ImportError:
            logger.warning("winreg를 사용할 수 없습니다 (Windows 전용)")
        return apps

    @staticmethod
    def _scan_linux_packages() -> List[Dict]:
        apps = []
        try:
            result = subprocess.run(["dpkg", "--list"], capture_output=True, text=True, timeout=30)
            for line in result.stdout.split('\n'):
                if line.startswith('ii'):
                    parts = line.split()
                    if len(parts) >= 3:
                        apps.append({
                            "app_name": parts[1],
                            "app_version": parts[2],
                            "publisher": "Linux Package",
                            "category": "system"
                        })
        except:
            pass
        return apps[:100]

    @staticmethod
    def _scan_macos_apps() -> List[Dict]:
        apps = []
        try:
            result = subprocess.run(
                ["ls", "/Applications"],
                capture_output=True, text=True, timeout=10
            )
            for app in result.stdout.split('\n'):
                if app.endswith('.app'):
                    name = app[:-4]
                    apps.append({
                        "app_name": name,
                        "publisher": "macOS App",
                        "category": AppScanner._categorize_app(name)
                    })
        except:
            pass
        return apps

    @staticmethod
    def _categorize_app(name: str) -> str:
        name_lower = name.lower()
        if any(kw in name_lower for kw in ['chrome', 'firefox', 'edge', 'safari', 'opera', 'browser']):
            return 'browser'
        elif any(kw in name_lower for kw in ['office', 'word', 'excel', 'powerpoint', 'outlook', 'teams', 'slack', 'zoom']):
            return 'productivity'
        elif any(kw in name_lower for kw in ['visual studio', 'vscode', 'intellij', 'eclipse', 'pycharm', 'git', 'python', 'node', 'java']):
            return 'development'
        elif any(kw in name_lower for kw in ['defender', 'antivirus', 'kaspersky', 'avast', 'norton', 'malware']):
            return 'security'
        elif any(kw in name_lower for kw in ['torrent', 'bittorrent', 'utorrent']):
            return 'unauthorized'
        return 'other'

    @staticmethod
    def get_running_processes() -> List[Dict]:
        if not PSUTIL_AVAILABLE:
            return []
        processes = []
        try:
            for proc in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        "app_name": proc.info['name'],
                        "is_running": True,
                    })
                except:
                    pass
        except:
            pass
        return processes[:50]


# ===== Notification Manager =====
class NotificationManager:
    @staticmethod
    def show_popup(title: str, message: str):
        """Show popup notification"""
        system = platform.system()
        if system == "Windows":
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=10, threaded=True)
                return
            except ImportError:
                pass
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
            except:
                pass
        elif system == "Linux":
            try:
                subprocess.run(
                    ["notify-send", "-a", "AssetGuard", "-t", "10000", title, message],
                    timeout=5
                )
            except:
                pass
        elif system == "Darwin":
            try:
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}" subtitle "AssetGuard"'
                ], timeout=5)
            except:
                pass
        logger.info(f"알림 표시: {title} - {message}")


# ===== Main Agent =====
class AssetGuardAgent:
    def __init__(self):
        self.config = load_config()
        self.activity_monitor = ActivityMonitor()
        self.app_scanner = AppScanner()
        self.notif_manager = NotificationManager()
        self.running = False
        self._threads = []
        self._last_app_scan = datetime.min
        self._last_heartbeat = datetime.min

    def _make_request(self, method: str, endpoint: str, data: dict = None, timeout: int = 30) -> Optional[dict]:
        if not REQUESTS_AVAILABLE:
            logger.error("requests 라이브러리가 필요합니다")
            return None
        url = f"{self.config['server_url']}/api/v1{endpoint}"
        try:
            if method.upper() == "POST":
                resp = requests.post(url, json=data, timeout=timeout)
            elif method.upper() == "GET":
                resp = requests.get(url, params=data, timeout=timeout)
            else:
                return None

            if resp.status_code in [200, 201]:
                return resp.json()
            else:
                logger.warning(f"API 오류 {resp.status_code}: {endpoint} - {resp.text[:200]}")
                return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"서버 연결 실패: {self.config['server_url']}")
            return None
        except Exception as e:
            logger.error(f"요청 실패: {e}")
            return None

    def register(self) -> bool:
        """에이전트 등록"""
        logger.info("에이전트 등록 시도...")
        sys_info = SystemInfo()
        os_info = sys_info.get_os_info()
        manufacturer, model = sys_info.get_manufacturer_model()

        data = {
            "agent_secret": self.config["agent_secret"],
            "hostname": sys_info.get_hostname(),
            "computer_name": sys_info.get_computer_name(),
            "serial_number": sys_info.get_serial_number(),
            "mac_address": sys_info.get_mac_address(),
            "manufacturer": manufacturer,
            "model": model,
            "cpu_info": sys_info.get_cpu_info(),
            "ram_gb": sys_info.get_ram_gb(),
            **os_info
        }

        result = self._make_request("POST", "/pcs/agent/register", data)
        if result:
            self.config["agent_token"] = result["agent_token"]
            self.config["pc_id"] = result["pc_id"]
            save_config(self.config)
            logger.info(f"✅ 등록 성공! PC ID: {result['pc_id']}, 자산태그: {result['asset_tag']}")
            return True
        logger.error("❌ 등록 실패")
        return False

    def heartbeat(self):
        """하트비트 전송"""
        if not self.config.get("agent_token"):
            return

        sys_info = SystemInfo()
        security = sys_info.get_security_status()

        data = {
            "agent_token": self.config["agent_token"],
            "ip_address": sys_info.get_ip_address(),
            "is_online": True,
            **security
        }

        result = self._make_request("POST", "/pcs/agent/heartbeat", data)
        if result:
            # Process notifications from server
            notifs = result.get("notifications", [])
            for notif in notifs:
                self.notif_manager.show_popup(
                    notif.get("title", "AssetGuard"),
                    notif.get("message", "")
                )
        self._last_heartbeat = datetime.utcnow()

    def report_activities(self):
        """활동 보고"""
        activities = self.activity_monitor.get_and_clear_activities()
        if not activities:
            # Add a login activity if it's been a while
            activities.append({
                "activity_type": "heartbeat",
                "user_account": self.activity_monitor.current_user,
                "started_at": datetime.utcnow().isoformat(),
                "details": {}
            })

        data = {
            "agent_token": self.config["agent_token"],
            "activities": activities
        }
        self._make_request("POST", "/pcs/agent/activities", data)

    def scan_and_report_apps(self):
        """앱 스캔 및 보고"""
        logger.info("앱 스캔 시작...")
        installed_apps = self.app_scanner.scan_installed_apps()
        running_procs = self.app_scanner.get_running_processes()

        all_apps = installed_apps + [p for p in running_procs if not any(a["app_name"] == p["app_name"] for a in installed_apps)]

        if all_apps:
            data = {
                "agent_token": self.config["agent_token"],
                "applications": all_apps[:200]
            }
            self._make_request("POST", "/pcs/agent/applications", data)
            logger.info(f"✅ {len(all_apps)}개 앱 보고 완료")

        self._last_app_scan = datetime.utcnow()

    def _heartbeat_loop(self):
        while self.running:
            try:
                self.heartbeat()
            except Exception as e:
                logger.error(f"하트비트 오류: {e}")
            time.sleep(self.config.get("heartbeat_interval", 60))

    def _activity_loop(self):
        # Report initial login
        self.activity_monitor.record_activity("login", details={"type": "agent_start"})
        
        while self.running:
            try:
                self.report_activities()
            except Exception as e:
                logger.error(f"활동 보고 오류: {e}")
            time.sleep(self.config.get("activity_report_interval", 300))

    def _app_scan_loop(self):
        while self.running:
            try:
                self.scan_and_report_apps()
            except Exception as e:
                logger.error(f"앱 스캔 오류: {e}")
            time.sleep(self.config.get("app_scan_interval", 3600))

    def start(self):
        """에이전트 시작"""
        logger.info("=" * 50)
        logger.info("🛡️  AssetGuard Agent v1.0 시작")
        logger.info(f"🖥️  서버: {self.config['server_url']}")
        logger.info(f"💻  호스트: {SystemInfo.get_hostname()}")
        logger.info("=" * 50)

        # Register if no token
        if not self.config.get("agent_token"):
            if not self.register():
                logger.error("등록 실패. 5초 후 재시도...")
                time.sleep(5)
                if not self.register():
                    logger.error("등록 재시도 실패. 종료합니다.")
                    return False

        self.running = True

        # Start threads
        threads_config = [
            ("heartbeat", self._heartbeat_loop),
            ("activity", self._activity_loop),
            ("app_scan", self._app_scan_loop),
        ]

        for name, target in threads_config:
            t = threading.Thread(target=target, name=name, daemon=True)
            t.start()
            self._threads.append(t)

        logger.info("✅ 에이전트 실행 중...")
        return True

    def stop(self):
        logger.info("에이전트 종료 중...")
        self.running = False
        # Report logout
        self.activity_monitor.record_activity("logout", details={"type": "agent_stop"})
        self.report_activities()

    def run(self):
        """Main run loop"""
        if not self.start():
            return

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n중단 신호 받음...")
        finally:
            self.stop()
            logger.info("👋 에이전트 종료")


def main():
    agent = AssetGuardAgent()

    if len(sys.argv) > 1:
        if sys.argv[1] == "register":
            agent.register()
        elif sys.argv[1] == "status":
            config = load_config()
            print(f"서버: {config.get('server_url')}")
            print(f"토큰: {'설정됨' if config.get('agent_token') else '미설정'}")
            print(f"PC ID: {config.get('pc_id', '없음')}")
        elif sys.argv[1] == "reset":
            config = load_config()
            config["agent_token"] = None
            config["pc_id"] = None
            save_config(config)
            print("에이전트 재설정 완료")
        elif sys.argv[1] == "test":
            print("시스템 정보 수집 테스트:")
            sys_info = SystemInfo()
            print(f"  호스트명: {sys_info.get_hostname()}")
            print(f"  컴퓨터명: {sys_info.get_computer_name()}")
            print(f"  OS: {sys_info.get_os_info()}")
            print(f"  CPU: {sys_info.get_cpu_info()}")
            print(f"  RAM: {sys_info.get_ram_gb()} GB")
            print(f"  IP: {sys_info.get_ip_address()}")
            print(f"  MAC: {sys_info.get_mac_address()}")
            security = sys_info.get_security_status()
            print(f"  보안 상태: {security}")
    else:
        agent.run()


if __name__ == "__main__":
    main()
