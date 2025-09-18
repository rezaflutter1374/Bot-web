#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import asyncio
import random
import time
from datetime import datetime, timedelta
import re
import pandas as pd
import os
import json
import logging
import requests
import schedule
from typing import Tuple, List, Dict, Optional
from dotenv import load_dotenv
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Frame,
    Page,
)
import subprocess
import platform
import tempfile

load_dotenv()
USERNAME = os.getenv("BSH_USERNAME", "SERAZ_BSC")
PASSWORD = os.getenv("BSH_PASSWORD")
DETECTED_OS = platform.system().lower()
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


def get_platform_path(path):
    if DETECTED_OS == "windows":
        return path.replace("/", "\\")
    return path


def detect_installed_browsers():
    browsers = {}

    if DETECTED_OS == "windows":
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "Google\\Chrome\\Application\\chrome.exe",
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES", ""),
                "Google\\Chrome\\Application\\chrome.exe",
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", ""),
                "Google\\Chrome\\Application\\chrome.exe",
            ),
        ]
        firefox_paths = [
            "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
            os.path.join(
                os.environ.get("PROGRAMFILES", ""), "Mozilla Firefox\\firefox.exe"
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", ""), "Mozilla Firefox\\firefox.exe"
            ),
        ]
        edge_paths = [
            "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
            os.path.join(
                os.environ.get("PROGRAMFILES", ""),
                "Microsoft\\Edge\\Application\\msedge.exe",
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", ""),
                "Microsoft\\Edge\\Application\\msedge.exe",
            ),
        ]
        opera_paths = [
            "C:\\Program Files\\Opera\\launcher.exe",
            "C:\\Program Files (x86)\\Opera\\launcher.exe",
            "C:\\Program Files\\Opera\\opera.exe",
            "C:\\Program Files (x86)\\Opera\\opera.exe",
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Opera\\launcher.exe"),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", ""), "Opera\\launcher.exe"
            ),
        ]
        brave_paths = [
            "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            ),
        ]

    elif DETECTED_OS == "darwin":
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            os.path.expanduser(
                "~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ),
        ]
        firefox_paths = [
            "/Applications/Firefox.app/Contents/MacOS/firefox",
            os.path.expanduser("~/Applications/Firefox.app/Contents/MacOS/firefox"),
        ]
        edge_paths = [
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            os.path.expanduser(
                "~/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
            ),
        ]
        opera_paths = [
            "/Applications/Opera.app/Contents/MacOS/Opera",
            os.path.expanduser("~/Applications/Opera.app/Contents/MacOS/Opera"),
        ]
        brave_paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            os.path.expanduser(
                "~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            ),
        ]

    elif DETECTED_OS == "linux":
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
            "/snap/bin/google-chrome",
            os.path.expanduser("~/.local/bin/google-chrome"),
        ]
        firefox_paths = [
            "/usr/bin/firefox",
            "/snap/bin/firefox",
            os.path.expanduser("~/.local/bin/firefox"),
        ]
        edge_paths = [
            "/usr/bin/microsoft-edge",
            "/usr/bin/microsoft-edge-stable",
            "/snap/bin/microsoft-edge",
        ]
        opera_paths = [
            "/usr/bin/opera",
            "/usr/bin/opera-stable",
            "/snap/bin/opera",
        ]
        brave_paths = [
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/snap/bin/brave",
        ]
    else:
        return {}

    for path in chrome_paths:
        if os.path.exists(get_platform_path(path)):
            browsers["chrome"] = get_platform_path(path)
            break

    for path in firefox_paths:
        if os.path.exists(get_platform_path(path)):
            browsers["firefox"] = get_platform_path(path)
            break

    for path in edge_paths:
        if os.path.exists(get_platform_path(path)):
            browsers["edge"] = get_platform_path(path)
            break

    for path in opera_paths:
        if os.path.exists(get_platform_path(path)):
            browsers["opera"] = get_platform_path(path)
            break

    for path in brave_paths:
        if os.path.exists(get_platform_path(path)):
            browsers["brave"] = get_platform_path(path)
            break

    if DETECTED_OS in ["darwin", "linux"] and not browsers:
        try:
            for browser in [
                "google-chrome",
                "chromium",
                "firefox",
                "microsoft-edge",
                "opera",
                "brave-browser",
            ]:
                try:
                    path = (
                        subprocess.check_output(
                            ["which", browser], stderr=subprocess.DEVNULL
                        )
                        .decode()
                        .strip()
                    )
                    if path:
                        name = (
                            "chrome"
                            if browser in ["google-chrome", "chromium"]
                            else "edge"
                            if browser == "microsoft-edge"
                            else "brave"
                            if browser == "brave-browser"
                            else browser
                        )
                        browsers[name] = path
                except subprocess.CalledProcessError:
                    pass
        except Exception:
            pass

    return browsers


def get_temp_directory():
    return tempfile.gettempdir()


def get_user_data_dir():
    base_dir = os.getcwd()
    return os.path.join(base_dir, "userdata")


PROXY_ENABLED = os.getenv("PROXY_ENABLED", "false").lower() == "true"
PROXY_FILE = os.getenv("PROXY_FILE", "proxies.txt")
PROXY_ROTATION_INTERVAL = int(os.getenv("PROXY_ROTATION_INTERVAL", "30")) * 60
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
LOGIN_TRACKING_FILE = os.path.join(os.getcwd(), "login_tracking.json")
AUTO_LOGIN_FREQUENCY = 15
from botweb.infrastructure.proxy_rotator import ProxyRotator  # noqa: E402
from botweb.infrastructure.browser_detection import DeviceFingerprint  # noqa: E402

SAFETY_MODE = os.getenv("SAFETY_MODE", "true").lower() == "true"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(OUTPUT_DIR, "bot.log")
            if os.path.exists(OUTPUT_DIR)
            else "bot.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("bot-web")
FINGERPRINT_ENABLED = os.getenv("FINGERPRINT_ENABLED", "false").lower() == "true"
proxy_rotator = None


class HealthMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.success_count = 0
        self.errors = []
        self.last_error_time = None
        self.last_success_time = None

    def record_request(self):
        self.request_count += 1

    def record_success(self):
        self.success_count += 1
        self.last_success_time = datetime.now()

    def record_error(self, error):
        self.error_count += 1
        self.last_error_time = datetime.now()
        self.errors.append({"time": datetime.now(), "error": str(error)})

    def get_stats(self):
        runtime = datetime.now() - self.start_time
        success_rate = self.success_count / max(self.request_count, 1) * 100
        return {
            "runtime": str(runtime),
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": f"{success_rate:.2f}%",
            "last_error": str(self.errors[-1]["error"]) if self.errors else None,
            "last_error_time": self.last_error_time,
            "last_success_time": self.last_success_time,
        }


health_monitor = HealthMonitor()
if PROXY_ENABLED:
    try:
        proxy_rotator = ProxyRotator(PROXY_FILE, PROXY_ROTATION_INTERVAL)
        logger.info(
            f"Proxy rotation enabled with {proxy_rotator.get_stats()['total']} proxies"
        )
    except Exception as e:
        logger.error(f"Failed to initialize proxy rotator: {e}")
        proxy_rotator = None
        PROXY_ENABLED = False
HEADLESS = os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes")
PORTAL_URL = "https://portal.bsh-partner.com"
INPUT_CANDIDATES = ['input[name="MatNr"]']
VERY_LONG_MS = 5_800_000
MAX_TOTAL_ENTRIES = 50000
MAX_RUN_SECONDS = 5 * 90 * 90
if not USERNAME or not PASSWORD:
    sys.exit("❌ Please set BSH_USERNAME and BSH_PASSWORD in your .env file.")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class RateLimitHandler:
    def __init__(self):
        self.request_times = []
        self.response_times = []
        self.consecutive_errors = 0
        self.last_error_time = None
        self.base_delay = 1.2
        self.max_delay = 450.0
        self.cool_down_period = 700.0
        self.throttling_threshold = 4.5
        self.burst_requests = 0
        self.last_burst_time = time.time()

    def record_request(self, response_time=None):
        current_time = time.time()
        self.request_times.append(current_time)
        if response_time:
            self.response_times.append(response_time)
            if len(self.response_times) > 25:
                self.response_times.pop(0)
        if len(self.request_times) > 15:
            self.request_times.pop(0)
        self.consecutive_errors = 0
        if current_time - self.last_burst_time < 60:
            self.burst_requests += 1
        else:
            self.burst_requests = 1
            self.last_burst_time = current_time

    def record_error(self):
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        self.burst_requests = 0

    def detect_throttling(self):
        if len(self.response_times) < 10:
            return False
        recent_times = self.response_times[-5:]
        historical_times = self.response_times[:-5]
        if not recent_times or not historical_times:
            return False
        avg_recent = sum(recent_times) / len(recent_times)
        avg_historical = sum(historical_times) / len(historical_times)
        if avg_recent > avg_historical * 2.5 and avg_recent > self.throttling_threshold:
            return True
        if avg_recent > self.throttling_threshold:
            slow_responses = sum(
                1 for t in recent_times if t > self.throttling_threshold
            )
            if slow_responses >= 3:
                return True
        return False

    def get_delay(self):
        now = time.time()
        if (
            self.consecutive_errors >= 3
            and self.last_error_time
            and now - self.last_error_time < self.cool_down_period
        ):
            return self.cool_down_period - (now - self.last_error_time)
        if self.detect_throttling():
            print("Server throttling detected, applying significant backoff...")
            return random.normalvariate(35, 5)
        if self.consecutive_errors > 0:
            delay = min(
                self.base_delay * (2.5**self.consecutive_errors), self.max_delay
            )
            return delay + random.normalvariate(delay * 0.4, delay * 0.1)
        if self.burst_requests > 15:
            print("Cooling down after a burst of requests...")
            self.burst_requests = 0
            return random.normalvariate(20, 4)
        return abs(random.normalvariate(4, 1.5))

    async def wait_if_needed(self):
        delay = self.get_delay()
        if delay > 0:
            if health_monitor:
                health_monitor.record_rate_limit()
            print(f"Rate limiting detected, waiting {delay:.1f} seconds...")
            await asyncio.sleep(delay)


rate_limiter = RateLimitHandler()


class HealthMonitor:
    def __init__(self, userdata_dir):
        self.userdata_dir = userdata_dir
        self.log_file = os.path.join(userdata_dir, "bot_health.log")
        self.metrics_file = os.path.join(userdata_dir, "metrics.json")
        self.critical_events_file = os.path.join(userdata_dir, "critical_events.json")
        self.setup_logging()
        self.metrics = self.load_metrics()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(self.log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def load_metrics(self):
        default_metrics = {
            "session_start": None,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": 0,
            "login_failures": 0,
            "challenges_detected": 0,
            "average_response_time": 0,
            "last_error": None,
            "consecutive_errors": 0,
            "uptime_seconds": 0,
            "request_times": [],
            "errors": [],
        }
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, "r") as f:
                    return {**default_metrics, **json.loads(f.read())}
        except Exception:
            pass
        return default_metrics

    def save_metrics(self):
        try:
            with open(self.metrics_file, "w") as f:
                f.write(json.dumps(self.metrics, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    def start_session(self):
        self.metrics["session_start"] = time.time()
        self.logger.info("🚀 Bot session started with enhanced safety monitoring")

    def record_request(self, success=True, response_time=None, error=None):
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
            self.metrics["consecutive_errors"] = 0
            if response_time:
                self.metrics["request_times"].append(response_time)
                if len(self.metrics["request_times"]) > 100:
                    self.metrics["request_times"] = self.metrics["request_times"][-50:]
                current_avg = self.metrics["average_response_time"]
                total_successful = self.metrics["successful_requests"]
                self.metrics["average_response_time"] = (
                    current_avg * (total_successful - 1) + response_time
                ) / total_successful
        else:
            self.metrics["failed_requests"] += 1
            self.metrics["consecutive_errors"] += 1
            self.metrics["last_error"] = {
                "timestamp": time.time(),
                "error": str(error) if error else "Unknown error",
            }
            if error:
                self.metrics["errors"].append(str(error))
            self.logger.error(f"Request failed: {error}")

    def record_rate_limit(self):
        self.metrics["rate_limit_hits"] += 1
        self.logger.warning("Rate limit detected")

    def record_login_failure(self):
        self.metrics["login_failures"] += 1
        self.logger.error("Login failure recorded")

    def record_challenge_detected(self, challenge_type: str):
        self.metrics["challenges_detected"] += 1
        self.log_critical_event("challenge_detected", challenge_type)

    def log_critical_event(self, event_type: str, details: str):
        timestamp = datetime.now().isoformat()
        self.logger.critical(f"CRITICAL_EVENT: {event_type} - {details} - {timestamp}")
        event_data = {"timestamp": timestamp, "type": event_type, "details": details}
        try:
            with open(self.critical_events_file, "a") as f:
                f.write(json.dumps(event_data) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log critical event: {e}")

    def get_health_status(self):
        if self.metrics["session_start"]:
            self.metrics["uptime_seconds"] = time.time() - self.metrics["session_start"]
        success_rate = 0
        if self.metrics["total_requests"] > 0:
            success_rate = (
                self.metrics["successful_requests"] / self.metrics["total_requests"]
            )
        status = "healthy"
        if self.metrics["consecutive_errors"] >= 5:
            status = "critical"
        elif success_rate < 0.8 and self.metrics["total_requests"] > 10:
            status = "degraded"
        elif self.metrics["rate_limit_hits"] > 10:
            status = "throttled"
        elif self.metrics["login_failures"] >= 3:
            status = "account_locked"
        return {
            "status": status,
            "success_rate": success_rate,
            "uptime_minutes": self.metrics["uptime_seconds"] / 60,
            "avg_response_time": self.metrics["average_response_time"],
            "consecutive_errors": self.metrics["consecutive_errors"],
            "login_failures": self.metrics["login_failures"],
            "challenges_detected": self.metrics["challenges_detected"],
        }

    def log_health_summary(self):
        health = self.get_health_status()
        self.logger.info(
            f"Health Status: {health['status']} | Success Rate: {health['success_rate']:.2%} | Uptime: {health['uptime_minutes']:.1f}m"
        )
        self.save_metrics()

    def get_session_summary(self) -> dict:
        if not self.metrics["session_start"]:
            return {}
        duration = datetime.now() - datetime.fromtimestamp(
            self.metrics["session_start"]
        )
        avg_request_time = (
            sum(self.metrics["request_times"]) / len(self.metrics["request_times"])
            if self.metrics["request_times"]
            else 0
        )
        return {
            "session_duration": str(duration),
            "total_requests": self.metrics["total_requests"],
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "login_failures": self.metrics["login_failures"],
            "challenges_detected": self.metrics["challenges_detected"],
            "average_request_time": round(avg_request_time, 2),
            "success_rate": round(
                (
                    self.metrics["successful_requests"]
                    / max(self.metrics["total_requests"], 1)
                )
                * 100,
                1,
            ),
            "unique_errors": len(set(self.metrics["errors"])),
        }


health_monitor = None
proxy_rotator = None
if PROXY_ENABLED:
    proxy_rotator = ProxyRotator()
    print(
        f"Proxy rotation {'enabled' if proxy_rotator.proxies else 'failed - no proxies found'}"
    )


async def human_sleep(a: float = 0.25, b: float = 0.8):
    await asyncio.sleep(random.uniform(a, b))


async def human_type(
    locator,
    text: str,
    min_delay_ms: int = 40,
    max_delay_ms: int = 110,
    typing_mode: str = "normal",
):
    if typing_mode == "fast":
        min_delay_ms = int(min_delay_ms * 0.6)
        max_delay_ms = int(max_delay_ms * 0.7)
        mistake_probability = 0.03
        burst_probability = 0.4
        pause_probability = 0.05
    elif typing_mode == "careful":
        min_delay_ms = int(min_delay_ms * 1.2)
        max_delay_ms = int(max_delay_ms * 1.3)
        mistake_probability = 0.01
        burst_probability = 0.1
        pause_probability = 0.15
    elif typing_mode == "hesitant":
        min_delay_ms = int(min_delay_ms * 1.5)
        max_delay_ms = int(max_delay_ms * 1.8)
        mistake_probability = 0.05
        burst_probability = 0.05
        pause_probability = 0.25
    else:
        mistake_probability = 0.02
        burst_probability = 0.2
        pause_probability = 0.1
    common_keys = "etaoinshrdlu "
    rare_keys = "qjxzwkvbpygfmc"
    consecutive_fast = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if random.random() < mistake_probability:
            mistake_type = random.choice(["typo", "double"])
            if mistake_type == "typo":
                typo_char = random.choice("qwertyuiopasdfghjklzxcvbnm")
                await locator.type(typo_char, delay=int(random.normalvariate(60, 10)))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await locator.press("Backspace")
                await asyncio.sleep(random.uniform(0.05, 0.15))
            elif mistake_type == "double":
                await locator.type(ch, delay=int(random.normalvariate(60, 10)))
                await locator.type(ch, delay=int(random.normalvariate(40, 5)))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await locator.press("Backspace")
                await asyncio.sleep(random.uniform(0.05, 0.15))
                i += 1
                continue
        if ch.lower() in common_keys:
            delay_factor = 0.8
        elif ch.lower() in rare_keys:
            delay_factor = 1.3
        else:
            delay_factor = 1.0
        if i > 0 and text[i - 1] == ch:
            delay_factor *= 0.7
        elif ch == " ":
            delay_factor *= 1.2
        if random.random() < burst_probability:
            consecutive_fast += 1
            burst_factor = max(0.5, 0.9 - (consecutive_fast * 0.05))
            delay_factor *= burst_factor
        else:
            consecutive_fast = 0
        adjusted_min = int(min_delay_ms * delay_factor)
        adjusted_max = int(max_delay_ms * delay_factor)
        delay = max(
            10,
            min(
                200,
                random.normalvariate(
                    (adjusted_min + adjusted_max) / 2, (adjusted_max - adjusted_min) / 4
                ),
            ),
        )
        await locator.type(ch, delay=int(delay))
        if random.random() < pause_probability:
            pause_duration = random.uniform(0.06, 0.18)
            if ch in ".,:;!?" or ch == " ":
                pause_duration *= 1.5
            await asyncio.sleep(pause_duration)
        i += 1


def load_part_codes_from_excel(file_path="input_codes.xlsx"):
    try:
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found, using default codes")
            return ["12345", "67890", "ABCDE"]
        df = pd.read_excel(file_path)
        possible_columns = [
            "part_code",
            "code",
            "part_number",
            "part",
            "codes",
            "numbers",
        ]
        part_column = None
        for col in df.columns:
            if col.lower().strip() in possible_columns:
                part_column = col
                break
        if part_column is None:
            part_column = df.columns[0]
            print(f"Using first column '{part_column}' as part codes")
        codes = df[part_column].dropna().astype(str).str.strip().tolist()
        codes = [
            code for code in codes if code and code.lower() not in ["nan", "none", ""]
        ]
        print(f"Loaded {len(codes)} part codes from {file_path}")
        return codes[:MAX_TOTAL_ENTRIES]
    except Exception as e:
        print(f"Error loading Excel file {file_path}: {e}")
        print("Using default part codes")
        return ["12345", "67890", "ABCDE"]


async def human_scroll(page: Page):
    try:
        scroll_count = random.randint(2, 4)
        for i in range(scroll_count):
            direction = random.choices([1, -1], weights=[0.8, 0.2])[0]
            delta = random.randint(100, 350) * direction
            if i == 0:
                delta = int(delta * 0.7)
            elif i == scroll_count - 1:
                delta = int(delta * 0.6)
            await page.mouse.wheel(0, delta)
            if random.random() < 0.3:
                await asyncio.sleep(random.uniform(0.4, 0.8))
            else:
                await asyncio.sleep(random.uniform(0.15, 0.35))
            if random.random() < 0.4:
                await page.mouse.move(
                    random.randint(100, 800), random.randint(100, 600)
                )
    except Exception:
        pass


async def human_warmup(page: Page):
    await asyncio.sleep(random.uniform(0.6, 1.3))
    await human_scroll(page)


def build_user_agent() -> str:
    major = random.choice([123, 124, 125, 126])
    return (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
    )


async def prompt_vpn_check():
    print("\n⚠️ VPN/Proxy connection check failed!")
    print("The target site may be blocked in your region.")
    print("Please ensure your VPN or proxy is active and properly configured.")
    print("\nTroubleshooting tips:")
    print("1. Check if your VPN/proxy service is running")
    print("2. Try connecting to a different VPN server")
    print("3. Verify your proxy settings in the configuration file")
    print("4. Check your internet connection")

    retry = input(
        "\nDo you want to retry after checking your connection? (y/n): "
    ).lower()
    return retry == "y" or retry == "yes"


async def create_stealth_context(p):
    slow_mo = random.randint(30, 90)
    userdata_dir = get_user_data_dir()
    os.makedirs(userdata_dir, exist_ok=True)
    fingerprint = DeviceFingerprint(userdata_dir)
    fingerprint.rotate_if_needed()

    connection_ok = check_vpn_proxy_connection()
    site_accessible = verify_site_access(PORTAL_URL)

    if not connection_ok or not site_accessible:
        retry = await prompt_vpn_check()
        if not retry:
            print(
                "❌ Operation aborted. Please check your VPN/proxy connection and try again."
            )
            sys.exit(1)

    proxy_settings = None
    if PROXY_ENABLED and proxy_rotator and proxy_rotator.proxies:
        try:
            current_proxy = proxy_rotator.get_current_proxy()
            if current_proxy:
                proxy_settings = proxy_rotator.get_proxy_for_playwright(current_proxy)
                masked_proxy = f"{current_proxy['host']}:{current_proxy['port']}"
                print(f"Using proxy: {masked_proxy}")
                if health_monitor:
                    health_monitor.logger.info(f"Using proxy: {masked_proxy}")
        except Exception as e:
            print(f"Failed to configure proxy: {e}")
            if health_monitor:
                health_monitor.logger.error(f"Proxy configuration error: {e}")

    # Common browser arguments for all browser types
    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-site-isolation-trials",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-infobars",
        "--window-position=0,0",
        "--ignore-certifcate-errors",
        "--ignore-certifcate-errors-spki-list",
        "--disable-accelerated-2d-canvas",
        "--hide-scrollbars",
        "--disable-notifications",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-component-extensions-with-background-pages",
        "--disable-extensions",
        "--disable-features=TranslateUI,BlinkGenPropertyTrees",
        "--disable-ipc-flooding-protection",
        "--disable-renderer-backgrounding",
        "--mute-audio",
        "--force-color-profile=srgb",
        "--enable-features=NetworkService,NetworkServiceInProcess",
        "--disable-features=AudioServiceOutOfProcess",
        "--disable-popup-blocking",
        "--disable-speech-api",
        "--disable-sync",
        "--disable-remote-fonts",
        "--metrics-recording-only",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    if DETECTED_OS == "windows":
        browser_args.extend(["--disable-gpu", "--disable-3d-apis"])
    elif DETECTED_OS == "linux":
        browser_args.extend(["--disable-gpu", "--no-zygote"])

    available_browsers = detect_installed_browsers()
    if not available_browsers:
        print("❌ No supported browsers found on your system.")
        print("Please install Chrome, Firefox, Edge, or Opera and try again.")
        sys.exit(1)

    print(f"📊 Detected browsers: {', '.join(available_browsers.keys())}")

    browser = None
    _browser_type = None
    _browser_name = None

    browser_launch_options = {
        "headless": HEADLESS,
        "slow_mo": slow_mo,
        "args": browser_args,
    }

    launch_attempts = []

    if "chrome" in available_browsers:
        launch_attempts.append((p.chromium, "chrome", available_browsers["chrome"]))
    if "firefox" in available_browsers:
        launch_attempts.append((p.firefox, "firefox", available_browsers["firefox"]))
    if "edge" in available_browsers:
        launch_attempts.append((p.chromium, "edge", available_browsers["edge"]))
    if "opera" in available_browsers:
        launch_attempts.append((p.chromium, "opera", available_browsers["opera"]))
    if "brave" in available_browsers:
        launch_attempts.append((p.chromium, "chrome", available_browsers["brave"]))

    if not launch_attempts:
        launch_attempts = [(p.chromium, "chromium", None), (p.firefox, "firefox", None)]

    for browser_engine, name, executable_path in launch_attempts:
        try:
            options = browser_launch_options.copy()
            if executable_path:
                options["executable_path"] = executable_path

            if name in ["chrome", "edge", "opera"]:
                try:
                    browser = await browser_engine.launch(channel=name, **options)
                    _ = browser_engine
                    _ = name
                    print(f"✅ Successfully launched {name.capitalize()}")
                    break
                except Exception as e:
                    print(f"Could not launch with channel specification: {e}")

                    try:
                        browser = await browser_engine.launch(**options)
                        _ = browser_engine
                        _ = name
                        print(
                            f"✅ Successfully launched {name.capitalize()} (fallback mode)"
                        )
                        break
                    except Exception as e:
                        print(f"Failed fallback launch attempt: {e}")
                        continue
            elif name == "brave":
                try:
                    browser = await browser_engine.launch(**options)
                    _ = browser_engine
                    _ = "brave"
                    print("✅ Successfully launched Brave Browser")
                    break
                except Exception as e:
                    print(f"Failed to launch Brave: {e}")
                    continue
            else:
                try:
                    browser = await browser_engine.launch(**options)
                    _ = browser_engine
                    _ = name
                    print(f"✅ Successfully launched {name.capitalize()}")
                    break
                except Exception as e:
                    print(f"Failed to launch {name}: {e}")
                    continue
        except Exception as e:
            print(f"Failed to launch {name}: {e}")
            continue

    if not browser:
        try:
            print("⚠️ Attempting generic browser launch as fallback...")
            browser = await p.chromium.launch(headless=HEADLESS)

            _ = p.chromium
            _ = "chromium"
            print("✅ Successfully launched browser with generic options")
        except Exception as e:
            logging.error(f"Failed to launch any browser: {e}")
            print("❌ Could not launch any browser. Please check your installation.")
            sys.exit(1)
    ctx_kwargs = {
        "user_agent": fingerprint.get_user_agent(),
        "locale": "tr-TR",
        "timezone_id": "Europe/Istanbul",
        "viewport": fingerprint.get_viewport(),
        "color_scheme": "light",
        "device_scale_factor": 2,
        "java_script_enabled": True,
        "accept_downloads": True,
        "ignore_https_errors": True,
    }
    if proxy_settings:
        ctx_kwargs["proxy"] = proxy_settings
    state_path = os.path.join(userdata_dir, "state.json")
    if os.path.exists(state_path):
        context = await browser.new_context(storage_state=state_path, **ctx_kwargs)
    else:
        context = await browser.new_context(**ctx_kwargs)
    await context.set_extra_http_headers(
        {
            "Accept-Language": fingerprint.get_accept_language(),
            "DNT": "1",
            **fingerprint.get_headers(),
        }
    )

    plugin_js = ""
    for i, plugin in enumerate(fingerprint.get_plugins()):
        plugin_js += f"""
                plugins[{i}] = {{
                    name: "{plugin["name"]}",
                    filename: "{plugin["filename"]}",
                    description: "{plugin["description"]}",
                    length: 1
                }};"""

    await context.add_init_script(
        f"""
        // Advanced anti-detection script with comprehensive browser fingerprint protection
        // Overwrite the 'webdriver' property to prevent detection
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
            enumerable: true,
            configurable: true
        }});
        // Override hardware concurrency and device memory
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fingerprint.get_hardware_concurrency()},
            enumerable: true,
            configurable: true
        }});
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {fingerprint.get_device_memory()},
            enumerable: true,
            configurable: true
        }});
        // Override plugins to match fingerprint
        Object.defineProperty(navigator, 'plugins', {{
            get: () => {{
                const plugins = {{
                    length: {len(fingerprint.get_plugins())}
                }};
                let i = 0;
                {plugin_js}
                return plugins;
            }},
            enumerable: true,
            configurable: true
        }});
        // Override permissions API
        if (navigator.permissions) {{
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = function(parameters) {{
                if (parameters.name === 'notifications') {{
                    return Promise.resolve({{
                        state: "prompt",
                        onchange: null
                    }});
                }}
                return originalQuery.call(this, parameters);
            }};
        }}
        // Add subtle canvas noise to prevent fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
            const canvas = this;
            setTimeout(() => {{
                const ctx = canvas.getContext('2d');
                if (ctx) {{
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const data = imageData.data;
                    for (let i = 0; i < data.length; i += 4) {{
                        // Add very subtle noise that won't be visible but will change the hash
                        data[i] = Math.min(255, Math.max(0, data[i] + (Math.random() - 0.5) * {fingerprint.get_canvas_noise() * 10}));
                        data[i+1] = Math.min(255, Math.max(0, data[i+1] + (Math.random() - 0.5) * {fingerprint.get_canvas_noise() * 10}));
                        data[i+2] = Math.min(255, Math.max(0, data[i+2] + (Math.random() - 0.5) * {fingerprint.get_canvas_noise() * 10}));
                    }}
                    ctx.putImageData(imageData, 0, 0);
                }}
            }}, 0);
            return originalToDataURL.call(this, type, quality);
        }};
        // Override WebGL fingerprinting
        const getParameterProxyHandler = {{
            apply: function(target, ctx, args) {{
                const param = args[0];
                const result = target.apply(ctx, args);
                // Return modified values for parameters commonly used in fingerprinting
                if (param === 37445) {{ // UNMASKED_VENDOR_WEBGL
                    return 'Intel Inc.';
                }}
                if (param === 37446) {{ // UNMASKED_RENDERER_WEBGL
                    return 'Intel Iris OpenGL Engine';
                }}
                return result;
            }}
        }};
        // Apply proxy to WebGL getParameter
        if (WebGLRenderingContext.prototype.getParameter) {{
            WebGLRenderingContext.prototype.getParameter = new Proxy(
                WebGLRenderingContext.prototype.getParameter,
                getParameterProxyHandler
            );
        }}
        // Apply proxy to WebGL2 getParameter if available
        if (window.WebGL2RenderingContext && WebGL2RenderingContext.prototype.getParameter) {{
            WebGL2RenderingContext.prototype.getParameter = new Proxy(
                WebGL2RenderingContext.prototype.getParameter,
                getParameterProxyHandler
            );
        }}
        // Modify performance timing to prevent timing attacks
        if (window.performance && window.performance.now) {{
            const originalNow = window.performance.now;
            const timeOffset = {fingerprint.get_timing_offset()};
            window.performance.now = function() {{
                return originalNow.call(this) + timeOffset;
            }};
        }}
        // Override language properties
        Object.defineProperty(navigator, 'language', {{
            get: () => 'tr-TR',
            enumerable: true,
            configurable: true
        }});
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['tr-TR', 'tr', 'en-US', 'en'],
            enumerable: true,
            configurable: true
        }});
        """
    )
    try:
        await context.grant_permissions(["geolocation", "notifications"])
    except Exception:
        pass
    return browser, context


async def find_frame_with_selector(
    page: Page, selector: str, timeout_ms: int = VERY_LONG_MS
) -> Frame:
    poll = 0.5
    waited = 0.0
    max_retries = 3
    retry_count = 0

    async def has_selector(target):
        try:
            return (await target.query_selector(selector)) is not None
        except Exception:
            return False

    while retry_count < max_retries:
        waited = 0.0
        while waited < timeout_ms / 1000.0:
            if await has_selector(page.main_frame):
                return page.main_frame
            for fr in page.frames:
                if fr != page.main_frame and await has_selector(fr):
                    return fr
            await asyncio.sleep(poll)
            waited += poll
        retry_count += 1
        if retry_count < max_retries:
            print(
                f"Retrying frame search for selector: {selector} (attempt {retry_count}/{max_retries})"
            )
            await asyncio.sleep(1 * retry_count)
            try:
                await page.mouse.move(50, 50)
                await asyncio.sleep(0.5)
                await page.mouse.move(100, 100)
            except Exception:
                pass
    raise PlaywrightTimeoutError(
        f"Timeout finding selector {selector} in any frame after {max_retries} attempts."
    )


async def find_first_available_input(
    page: Page, timeout_ms: int = VERY_LONG_MS
) -> Tuple[Frame, str]:
    for sel in INPUT_CANDIDATES:
        try:
            frame = await find_frame_with_selector(page, sel, timeout_ms=timeout_ms)
            locator = frame.locator(sel).first
            if await locator.count() > 0:
                await locator.scroll_into_view_if_needed()
                await locator.click(timeout=60_000)
                return frame, sel
        except Exception:
            continue
    raise PlaywrightTimeoutError("❌ No available MatNr input found in any frame.")


async def fill_and_submit_input_repeat(
    frame: Frame, selector: str, code: str, total_counter: List[int], start_time: float
):
    elapsed = time.time() - start_time
    if elapsed >= MAX_RUN_SECONDS or total_counter[0] >= MAX_TOTAL_ENTRIES:
        return
    await rate_limiter.wait_if_needed()
    if total_counter[0] > 0 and total_counter[0] % 10 == 0:
        print("🛡️ Taking extended break after 10 requests...")
        await asyncio.sleep(random.uniform(5, 10))
    request_start = time.time()
    try:
        challenge = await detect_challenges(frame.page)
        if challenge:
            print(f"🚨 Challenge detected during processing: {challenge}")
            return
        locator = frame.locator(selector).first
        await locator.wait_for(state="visible", timeout=120_000)
        await locator.scroll_into_view_if_needed()
        await locator.fill("")
        await human_sleep(0.15, 0.35)
        await human_type(locator, code)
        try:
            await locator.press("Enter")
        except Exception:
            try:
                await locator.click()
            except Exception:
                pass
        total_counter[0] += 1
        print(
            f"   🔁 Input {total_counter[0]} / {MAX_TOTAL_ENTRIES} done for code {code}"
        )
        response_time = time.time() - request_start
        rate_limiter.record_request(response_time=response_time)
        if health_monitor:
            health_monitor.record_request(success=True, response_time=response_time)
        await asyncio.sleep(random.uniform(0.8, 1.5))
    except Exception as e:
        response_time = time.time() - request_start
        print(f"Error processing code {code}: {e}")
        rate_limiter.record_error()
        if health_monitor:
            health_monitor.record_request(
                success=False, error=e, response_time=response_time
            )
        raise


def _normalize_price_to_float(price_text: str) -> Optional[float]:
    if not price_text:
        return None
    t = price_text.replace("\u00a0", " ").strip()
    t = re.sub(r"(TRY|TL|₺)", "", t, flags=re.IGNORECASE).strip()
    if "," in t and "." in t:
        t = t.replace(",", "")
    elif "," in t and "." not in t:
        t = t.replace(".", "")
        t = t.replace(",", ".")
    t = re.sub(r"[^0-9.]", "", t)
    try:
        return float(t) if t else None
    except Exception:
        return None


async def extract_price_for_code(frame: Frame, code: str) -> Dict[str, Optional[str]]:
    price_text: Optional[str] = None
    part_no: Optional[str] = None
    desc: Optional[str] = None
    try:
        row = frame.locator(f"table.tbl-striped tr:has(td:has-text('{code}'))").first
        if await row.count() > 0:
            try:
                part_no = (await row.locator("td").nth(0).inner_text()).strip()
            except Exception:
                pass
            try:
                desc = (await row.locator("td").nth(1).inner_text()).strip()
            except Exception:
                pass
            try:
                cell = row.locator("td").nth(6)
                if await cell.count() > 0:
                    price_text = (await cell.inner_text()).strip()
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ Error extracting price for {code}: {e}")
    price_num = _normalize_price_to_float(price_text or "")
    return {
        "Requested Code": code,
        "Found Part No": part_no or "",
        "Description": desc or "",
        "Price Text": price_text or "",
        "Price Numeric": price_num,
    }


async def select_turkey(page: Page):
    turkey_link = page.locator("a:has(span.flag-icon-tr)")
    if await turkey_link.count() > 0:
        await turkey_link.first.click()
        print("✅ Turkey selected")
        return
    raise PlaywrightTimeoutError("❌ Could not find/select Turkey flag.")


async def click_servis_and_quickfinder(page: Page):
    frame = await find_frame_with_selector(
        page, 'div.pfPrimaryMenu > a.pfPrimaryMenuA:has-text("Servis")'
    )
    servis = frame.locator(
        'div.pfPrimaryMenu > a.pfPrimaryMenuA:has-text("Servis")'
    ).first
    await servis.hover()
    try:
        await servis.click()
    except Exception:
        await servis.click(force=True)
    await asyncio.sleep(0.6)
    quickfinder = frame.locator(
        'div.pfSecondaryMenu > a.pfSecondaryMenuA:has-text("Quickfinder")'
    ).first
    await quickfinder.click()
    print("✅ Quickfinder clicked")
    await asyncio.sleep(0.5)


async def detect_challenges(page: Page) -> Optional[str]:
    challenge_selectors = [
        ("iframe[src*='recaptcha']", "reCAPTCHA detected"),
        ("iframe[src*='captcha']", "CAPTCHA challenge"),
        (".g-recaptcha", "reCAPTCHA detected"),
        ("#recaptcha", "reCAPTCHA detected"),
        ("div[data-sitekey]", "CAPTCHA challenge"),
        ("div[class*='captcha']", "CAPTCHA challenge"),
        ("img[alt*='captcha' i]", "Image CAPTCHA detected"),
        ("img[src*='captcha' i]", "Image CAPTCHA detected"),
        ("[data-testid='challenge']", "Site challenge"),
        ("div.error-page", "Access denied"),
        ("div.rate-limit", "Rate limit exceeded"),
        ("div.login-error", "Login error detected"),
        ("#cf-challenge-running", "Cloudflare protection"),
        ("#cf-please-wait", "Cloudflare protection"),
        (".cf-browser-verification", "Cloudflare verification"),
        ("div[class*='challenge']", "Challenge detected"),
        ("div[class*='security-check']", "Security check detected"),
        ("div[class*='bot-check']", "Bot check detected"),
        ("div[class*='verify']", "Verification required"),
    ]
    for selector, message in challenge_selectors:
        if await page.locator(selector).count() > 0:
            if health_monitor:
                health_monitor.record_challenge_detected(message)
            return message
    try:
        page_text = await page.inner_text("body") or ""
        page_text = page_text.lower()
        blocked_phrases = [
            "access denied",
            "blocked",
            "security check",
            "unusual activity",
            "automated access",
            "bot detected",
            "human verification",
            "suspicious activity",
            "too many requests",
            "rate limited",
        ]
        for phrase in blocked_phrases:
            if phrase in page_text:
                message = f"Blocked text detected: {phrase}"
                if health_monitor:
                    health_monitor.record_challenge_detected(message)
                return message
    except Exception:
        pass
    return None


async def is_logged_in(page: Page) -> bool:
    try:
        login_indicators = [
            "#PORTAL_LOGINNAME",
            "#PORTAL_PASSWORD",
            "#loginsubmitbtn",
            "form:has([type=password])",
            ".login-form",
            "#loginForm",
            "input[name=password]",
            "input[name=username]",
            "button:has-text('Log in')",
            "button:has-text('Sign in')",
            "a:has-text('Log in')",
            "a:has-text('Sign in')",
        ]
        for selector in login_indicators:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return False
            except Exception:
                continue
        logged_in_indicators = [
            ".user-avatar",
            ".profile-link",
            ".logout-button",
            ".signout",
            "#user-menu",
            ".account-info",
            ".user-profile",
            ".user-name",
            "a:has-text('Log out')",
            "a:has-text('Sign out')",
            "a:has-text('Logout')",
            "button:has-text('Log out')",
            "button:has-text('Sign out')",
            "[aria-label*='account' i]",
            "[aria-label*='profile' i]",
            ".avatar",
            ".user-icon",
            ".profile-icon",
        ]
        for selector in logged_in_indicators:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except Exception:
                continue
        current_url = page.url
        logged_in_url_patterns = [
            "account",
            "dashboard",
            "profile",
            "home",
            "member",
            "user",
            "portal",
            "secure",
            "my-",
            "overview",
        ]
        for pattern in logged_in_url_patterns:
            if pattern in current_url.lower():
                return True
        try:
            page_content = await page.content()
            logged_in_content_patterns = [
                "Welcome back",
                "My Account",
                "Your Account",
                "Sign Out",
                "Log Out",
                "Logout",
                "My Profile",
                "Account Settings",
                "Your Profile",
                "Dashboard",
            ]
            for pattern in logged_in_content_patterns:
                if pattern.lower() in page_content.lower():
                    return True
        except Exception:
            pass
        try:
            cookies = await page.context.cookies()
            auth_cookie_names = ["auth", "session", "token", "user", "logged_in", "sid"]
            for cookie in cookies:
                cookie_name = cookie.get("name", "").lower()
                for auth_name in auth_cookie_names:
                    if auth_name in cookie_name:
                        return True
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"Error checking login status: {e}")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"login_check_error_{timestamp}.png")
        except Exception as screenshot_error:
            print(f"Failed to take error screenshot: {screenshot_error}")
        return False


def check_login_tracking():
    try:
        current_month = datetime.now().strftime("%Y-%m")
        tracking_data = {}
        if os.path.exists(LOGIN_TRACKING_FILE):
            with open(LOGIN_TRACKING_FILE, "r") as f:
                tracking_data = json.load(f)
        if current_month not in tracking_data:
            tracking_data[current_month] = {"login_count": 0, "last_login": None}
        login_count = tracking_data[current_month]["login_count"]
        need_login = login_count % AUTO_LOGIN_FREQUENCY == 0
        tracking_data[current_month]["login_count"] += 1
        tracking_data[current_month]["last_login"] = datetime.now().isoformat()
        with open(LOGIN_TRACKING_FILE, "w") as f:
            json.dump(tracking_data, f, indent=2)
        return need_login
    except Exception as e:
        print(f"Warning: Login tracking error: {e}")
        return True


async def safe_login(page: Page, max_retries: int = 3) -> bool:
    login_attempts = 0
    base_delay = 15
    jitter_factor = 0.2
    need_login = check_login_tracking()
    if not need_login:
        print("Skipping login based on tracking frequency")
        return True
    while login_attempts < max_retries:
        try:
            print(f"[3] Logging in... (attempt {login_attempts + 1}/{max_retries})")
            await human_warmup(page)
            challenge = await detect_challenges(page)
            if challenge:
                print(f"🚨 Challenge detected: {challenge}")
                if "CAPTCHA" in challenge or "reCAPTCHA" in challenge:
                    print("⏸️  Bot paused - manual intervention required for CAPTCHA")
                    return False
                else:
                    print(f"Attempting to handle challenge: {challenge}")
                    await human_scroll(page)
                    await asyncio.sleep(random.uniform(3, 5))
            user_l = page.locator("#PORTAL_LOGINNAME")
            pass_l = page.locator("#PORTAL_PASSWORD")
            await user_l.wait_for(state="visible", timeout=120_000)
            await user_l.click()
            await human_type(user_l, USERNAME, typing_mode="careful")
            await human_sleep(0.4, 0.9)
            await pass_l.click()
            await human_type(pass_l, PASSWORD, typing_mode="careful")
            await human_sleep(0.5, 1.0)
            await page.mouse.move(
                random.randint(1, 5), random.randint(1, 5), steps=random.randint(1, 5)
            )
            await page.click("#loginsubmitbtn", delay=random.randint(30, 70))
            await asyncio.sleep(random.uniform(1.5, 2.5))
            challenge = await detect_challenges(page)
            if challenge:
                print(f"🚨 Post-login challenge: {challenge}")
                if health_monitor:
                    health_monitor.record_challenge_detected(challenge)
                return False
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=15_000)
                await page.wait_for_load_state("networkidle", timeout=30_000)
                if await is_logged_in(page):
                    print("✅ Login successful")
                    if health_monitor:
                        health_monitor.record_request(success=True)
                    return True
                else:
                    print("❌ Login failed - verification failed")
                    error_selectors = [
                        ".error",
                        ".alert",
                        ".message-error",
                        "[role=alert]",
                        "#error",
                        "#errorMessage",
                        ".form-error",
                        ".login-error",
                    ]
                    for selector in error_selectors:
                        error_elem = await page.locator(selector).count()
                        if error_elem > 0:
                            error_text = await page.locator(selector).first.inner_text()
                            print(f"Login error message: {error_text}")
                            break
                    login_attempts += 1
                    if login_attempts < max_retries:
                        delay = (
                            base_delay
                            * (1.5**login_attempts)
                            * (1 + random.uniform(-jitter_factor, jitter_factor))
                        )
                        print(f"Waiting {delay:.1f} seconds before next attempt...")
                        await asyncio.sleep(delay)
                    continue
            except Exception as e:
                print(f"❌ Login verification failed: {e}")
                if health_monitor:
                    health_monitor.record_request(success=False, error=e)
                login_attempts += 1
                if login_attempts < max_retries:
                    delay = (
                        base_delay
                        * (1.5**login_attempts)
                        * (1 + random.uniform(-jitter_factor, jitter_factor))
                    )
                    print(f"Waiting {delay:.1f} seconds before next attempt...")
                    await asyncio.sleep(delay)
        except Exception as e:
            print(f"❌ Login error: {e}")
            if health_monitor:
                health_monitor.record_request(success=False, error=e)
            login_attempts += 1
            if login_attempts < max_retries:
                delay = (
                    base_delay
                    * (1.5**login_attempts)
                    * (1 + random.uniform(-jitter_factor, jitter_factor))
                )
                print(f"Waiting {delay:.1f} seconds before next attempt...")
                await asyncio.sleep(delay)
    print("🚨 Max login attempts reached - bot stopped for safety")
    if health_monitor:
        health_monitor.record_login_failure()
    return False


def check_vpn_proxy_connection(test_url="https://api.ipify.org"):
    try:
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            print(
                f"VPN/Proxy check successful. Your current IP: {response.text.strip()}"
            )
            return True
    except requests.RequestException as e:
        print(f"VPN/Proxy connection check failed: {e}")
        return False


def verify_site_access(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code < 400
    except requests.RequestException:
        return False


async def run_bot(scheduled=False):
    global health_monitor, proxy_rotator
    print("\n" + "=" * 50)
    print("IMPORTANT: This site may be restricted in some regions.")
    print("A VPN or proxy connection is required to access it.")
    print("=" * 50)
    vpn_active = check_vpn_proxy_connection()
    site_accessible = verify_site_access(PORTAL_URL)
    if not vpn_active or not site_accessible:
        user_input = input(
            "VPN/Proxy connection check failed or site is not accessible.\nDo you want to continue anyway? (y/n): "
        )
        if user_input.lower() != "y":
            print("Exiting. Please activate a VPN/proxy and try again.")
            return
    userdata_dir = get_user_data_dir()
    os.makedirs(userdata_dir, exist_ok=True)
    health_monitor = HealthMonitor(userdata_dir)
    health_monitor.start_session()
    if PROXY_ENABLED and not proxy_rotator:
        try:
            proxy_rotator = ProxyRotator(PROXY_FILE, PROXY_ROTATION_INTERVAL)
            print(
                f"Proxy rotation {'enabled' if proxy_rotator.proxies else 'failed - no proxies found'}"
            )
            if proxy_rotator.proxies:
                health_monitor.logger.info(
                    f"Proxy rotation enabled with {len(proxy_rotator.proxies)} proxies"
                )
                health_monitor.logger.info(
                    f"Proxy rotation interval: {PROXY_ROTATION_INTERVAL} seconds"
                )
        except Exception as e:
            print(f"Failed to initialize proxy rotator: {e}")
            health_monitor.logger.error(f"Proxy rotator initialization error: {e}")
    print("🚀 Starting BSH Quick Finder Bot (Safety-Enhanced)...")
    start_time = time.time()
    login_failures = 0
    max_login_failures = 3
    async with async_playwright() as p:
        browser, context = await create_stealth_context(p)
        page = await context.new_page()
        page.set_default_timeout(VERY_LONG_MS)
        results: List[Dict[str, str]] = []
        total_counter = [0]
        codes_list = load_part_codes_from_excel("input_codes.xlsx")
        if not codes_list:
            print("⚠️ No codes found in input file")
            return
        try:
            print("[1] Opening portal...")
            try:
                await page.goto(PORTAL_URL, wait_until="domcontentloaded")
            except Exception as e:
                if PROXY_ENABLED and proxy_rotator and "proxy" in str(e).lower():
                    print(f"Proxy error: {e}")
                    print("Rotating to next proxy and retrying...")
                    await browser.close()
                    current_proxy = proxy_rotator.get_current_proxy()
                    if current_proxy:
                        proxy_rotator.mark_proxy_failure(current_proxy)
                    browser, context = await create_stealth_context(p)
                    page = await context.new_page()
                    page.set_default_timeout(VERY_LONG_MS)
                    await page.goto(PORTAL_URL, wait_until="domcontentloaded")
                else:
                    raise
            await human_warmup(page)
            challenge = await detect_challenges(page)
            if challenge:
                print(f"🚨 Pre-login challenge detected: {challenge}")
                if health_monitor:
                    health_monitor.record_challenge_detected(challenge)
                if PROXY_ENABLED and proxy_rotator and proxy_rotator.proxies:
                    print("Rotating proxy and retrying due to challenge detection...")
                    current_proxy = proxy_rotator.get_current_proxy()
                    if current_proxy:
                        proxy_rotator.mark_proxy_failure(current_proxy)
                    return await run_bot()
                return
            print("[2] Selecting Turkey...")
            await select_turkey(page)
            await human_sleep(0.3, 0.8)
            if not await safe_login(page):
                login_failures += 1
                print(f"Login attempt {login_failures}/{max_login_failures} failed")
                if (
                    PROXY_ENABLED
                    and proxy_rotator
                    and proxy_rotator.proxies
                    and login_failures < max_login_failures
                ):
                    print("Rotating proxy and retrying login...")
                    current_proxy = proxy_rotator.get_current_proxy()
                    if current_proxy:
                        proxy_rotator.mark_proxy_failure(current_proxy)
                    await browser.close()
                    browser, context = await create_stealth_context(p)
                    page = await context.new_page()
                    page.set_default_timeout(VERY_LONG_MS)
                    return
                return
            await human_warmup(page)
            await click_servis_and_quickfinder(page)
            last_proxy_rotation = time.time()
            for idx, code in enumerate(codes_list, 1):
                elapsed = time.time() - start_time
                if elapsed >= MAX_RUN_SECONDS:
                    print("⏰ 2 hours passed, stopping bot...")
                    break
                if PROXY_ENABLED and proxy_rotator and proxy_rotator.proxies:
                    proxy_elapsed = time.time() - last_proxy_rotation
                    if proxy_elapsed >= PROXY_ROTATION_INTERVAL:
                        print(
                            f"Rotating proxy after {PROXY_ROTATION_INTERVAL / 60:.1f} minutes..."
                        )
                        current_proxy = proxy_rotator.get_current_proxy()
                        if current_proxy:
                            proxy_rotator.mark_proxy_success(current_proxy)
                        await browser.close()
                        browser, context = await create_stealth_context(p)
                        page = await context.new_page()
                        page.set_default_timeout(VERY_LONG_MS)
                        await page.goto(PORTAL_URL, wait_until="domcontentloaded")
                        await human_warmup(page)
                        if not await safe_login(page):
                            print("Failed to re-login after proxy rotation")
                            return
                        await human_warmup(page)
                        await click_servis_and_quickfinder(page)
                        last_proxy_rotation = time.time()
                print(f"[*] ({idx}/{len(codes_list)}) Processing code: {code}")
                try:
                    frame, input_sel = await find_first_available_input(page)
                    await fill_and_submit_input_repeat(
                        frame, input_sel, code, total_counter, start_time
                    )
                    result = await extract_price_for_code(frame, code)
                    results.append(result)
                    if PROXY_ENABLED and proxy_rotator:
                        current_proxy = proxy_rotator.get_current_proxy()
                        if current_proxy:
                            proxy_rotator.mark_proxy_success(current_proxy)
                except Exception as e:
                    print(f"❌ Error on code {code}: {e}")
                    if health_monitor:
                        health_monitor.record_error(str(e))
                    network_error = any(
                        err in str(e).lower()
                        for err in [
                            "network",
                            "timeout",
                            "connection",
                            "refused",
                            "reset",
                            "closed",
                            "blocked",
                            "denied",
                            "forbidden",
                            "403",
                            "429",
                            "503",
                        ]
                    )
                    if (
                        PROXY_ENABLED
                        and proxy_rotator
                        and proxy_rotator.proxies
                        and network_error
                    ):
                        print("Network error detected. Rotating proxy and retrying...")
                        current_proxy = proxy_rotator.get_current_proxy()
                        if current_proxy:
                            proxy_rotator.mark_proxy_failure(current_proxy)
                        await browser.close()
                        browser, context = await create_stealth_context(p)
                        page = await context.new_page()
                        page.set_default_timeout(VERY_LONG_MS)
                        await page.goto(PORTAL_URL, wait_until="domcontentloaded")
                        await human_warmup(page)
                        if not await safe_login(page):
                            print(
                                "Failed to re-login after proxy rotation due to error"
                            )
                            return
                        await human_warmup(page)
                        await click_servis_and_quickfinder(page)
                        last_proxy_rotation = time.time()
                        idx -= 1
                        continue
                    results.append(
                        {
                            "Requested Code": code,
                            "Found Part No": "",
                            "Description": "Error",
                            "Price Text": "",
                            "Price Numeric": None,
                        }
                    )
                await asyncio.sleep(random.uniform(1.2, 2.5))
            if results:
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                out_path = os.path.join(OUTPUT_DIR, f"BshOutput_{ts}.xlsx")
                df = pd.DataFrame(
                    results,
                    columns=[
                        "Requested Code",
                        "Found Part No",
                        "Description",
                        "Price Text",
                        "Price Numeric",
                    ],
                )
                df.to_excel(out_path, index=False, engine="openpyxl")
                print(f"✅ All results saved to Excel: {out_path}")
                system_name = platform.system()
                try:
                    if system_name == "Windows":
                        os.startfile(out_path)
                    elif system_name == "Darwin":
                        subprocess.run(["open", out_path])
                    else:
                        subprocess.run(["xdg-open", out_path])
                    print("📂 Excel file opened automatically.")
                except Exception as e:
                    print(f"⚠️ Could not auto-open Excel file: {e}")
            else:
                print("⚠️ No results to save.")
            if PROXY_ENABLED and proxy_rotator and proxy_rotator.proxies:
                stats = proxy_rotator.get_stats()
                print("\n📊 Proxy Statistics:")
                print(f"  Total proxies: {stats['total']}")
                print(f"  Successful: {stats['successful']}")
                print(f"  Failed: {stats['failed']}")
                print(f"  Unused: {stats['unused']}")
                print(f"  Success rate: {stats['success_rate']:.1f}%")
                if health_monitor:
                    health_monitor.logger.info(f"Proxy statistics: {stats}")
                try:
                    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    stats_dir = os.path.join(OUTPUT_DIR, "proxy_stats")
                    os.makedirs(stats_dir, exist_ok=True)
                    stats_file = os.path.join(stats_dir, f"proxy_stats_{ts}.json")
                    detailed_stats = {
                        "summary": stats,
                        "proxies": proxy_rotator.get_detailed_stats(),
                    }
                    with open(stats_file, "w") as f:
                        json.dump(detailed_stats, f, indent=2)
                    print(f"📄 Detailed proxy statistics saved to: {stats_file}")
                except Exception as e:
                    print(f"⚠️ Could not save proxy statistics: {e}")
        except Exception as e:
            print(f"Fatal error: {e}")
            if health_monitor:
                health_monitor.record_error(f"Fatal error: {e}")
        finally:
            try:
                userdata_dir = os.path.join(os.getcwd(), "userdata")
                os.makedirs(userdata_dir, exist_ok=True)
                state_path = os.path.join(userdata_dir, "state.json")
                await context.storage_state(path=state_path)
            except Exception:
                pass
            try:
                await browser.close()
                if health_monitor:
                    summary = health_monitor.get_session_summary()
                    health_monitor.logger.info(
                        f"Session Summary: {json.dumps(summary, indent=2)}"
                    )
                    health_monitor.log_health_summary()
                total_time = time.time() - start_time
                print(f"\n✅ Bot completed safely in {total_time:.1f}s")
                print(f"📈 Processed {len(results)} part codes")
                print("🛡️ Safety mode: Active (challenge detection + rate limiting)")
                if health_monitor and summary:
                    print("\n📋 Session Summary:")
                    print(f"   • Success Rate: {summary.get('success_rate', 0)}%")
                    print(f"   • Total Requests: {summary.get('total_requests', 0)}")
                    print(f"   • Failed Requests: {summary.get('failed_requests', 0)}")
                    print(f"   • Login Failures: {summary.get('login_failures', 0)}")
                    print(
                        f"   • Challenges Detected: {summary.get('challenges_detected', 0)}"
                    )
                    print(
                        f"   • Average Request Time: {summary.get('average_request_time', 0)}s"
                    )
            except Exception as cleanup_error:
                print(f"❌ Cleanup error: {cleanup_error}")
                if health_monitor:
                    health_monitor.logger.error(f"Cleanup error: {cleanup_error}")


def create_sample_proxies_file():
    if not os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, "w") as f:
            f.write("# BSH Bot Proxy Configuration\n")
            f.write("# Format: ip:port or ip:port:username:password\n")
            f.write("# One proxy per line\n\n")
            f.write("# Examples:\n")
            f.write("# 192.168.1.1:8080\n")
            f.write("# proxy.example.com:3128\n")
            f.write("# 10.0.0.1:8888:user:pass\n")
            f.write("\n# Add your proxies below:\n")
        print(f"📄 Created sample {PROXY_FILE} file. Please add your proxies there.")


def validate_proxy_config():
    if not PROXY_ENABLED:
        return True, []
    warnings = []
    if not os.path.exists(PROXY_FILE):
        return False, [f"Proxy file {PROXY_FILE} not found. Creating sample file."]
    try:
        with open(PROXY_FILE, "r") as f:
            lines = f.readlines()
        valid_proxies = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) not in [2, 4]:
                warnings.append(f"Line {i + 1}: Invalid proxy format: {line}")
                continue
            if len(parts) >= 2:
                try:
                    port = int(parts[1])
                    if port < 1 or port > 65535:
                        warnings.append(
                            f"Line {i + 1}: Invalid port number: {parts[1]}"
                        )
                        continue
                except ValueError:
                    warnings.append(f"Line {i + 1}: Port must be a number: {parts[1]}")
                    continue
            valid_proxies.append(line)
        if not valid_proxies:
            warnings.append("No valid proxies found in the proxy file.")
            return False, warnings
        if len(valid_proxies) < 3 and len(valid_proxies) > 0:
            warnings.append(
                f"Only {len(valid_proxies)} valid proxies found. For better performance, consider adding more proxies."
            )
        return len(valid_proxies) > 0, warnings
    except Exception as e:
        return False, [f"Error reading proxy file: {str(e)}"]


def ensure_directories():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    userdata_dir = get_user_data_dir()
    os.makedirs(userdata_dir, exist_ok=True)
    if PROXY_ENABLED:
        proxy_dir = os.path.dirname(PROXY_FILE)
        if proxy_dir and proxy_dir != ".":
            os.makedirs(proxy_dir, exist_ok=True)


def display_startup_banner():
    print("\n" + "=" * 60)
    print("🤖 BSH Bot - Starting Up")
    print("=" * 60)
    if PROXY_ENABLED:
        print("🔄 Proxy Rotation: ENABLED")
        if os.path.exists(PROXY_FILE):
            try:
                with open(PROXY_FILE, "r") as f:
                    lines = [
                        line.strip()
                        for line in f.readlines()
                        if line.strip() and not line.strip().startswith("#")
                    ]
                    proxy_count = len(lines)
                print(f"📊 Proxies loaded: {proxy_count}")
                print(f"⏱️ Rotation interval: {PROXY_ROTATION_INTERVAL} seconds")
            except Exception:
                print("⚠️ Could not read proxy file")
    else:
        print("🔄 Proxy Rotation: DISABLED")
    print("🛡️ Safety mode: Active (challenge detection + rate limiting)")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print("=" * 60 + "\n")


def schedule_login():
    print("\n" + "=" * 60)
    print("🤖 BSH Bot - Scheduled Login")
    print("=" * 60)
    print(
        f"Running scheduled login task at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    vpn_active = check_vpn_proxy_connection()
    site_accessible = verify_site_access(PORTAL_URL)

    if not vpn_active or not site_accessible:
        print("❌ VPN/Proxy connection check failed or site is not accessible.")
        print("Scheduled login skipped. Will retry at next scheduled time.")
        if health_monitor:
            health_monitor.log_critical_event(
                "scheduled_login_vpn_failure", "VPN/Proxy connection check failed"
            )
        return

    try:
        asyncio.run(run_bot(scheduled=True))
        print("✅ Scheduled login completed successfully")
        print(
            f"Next scheduled login: {(datetime.now() + timedelta(days=AUTO_LOGIN_FREQUENCY)).strftime('%Y-%m-%d')}"
        )
        return schedule.CancelJob
    except Exception as e:
        print(f"❌ Scheduled login failed: {e}")
        if health_monitor:
            health_monitor.log_critical_event("scheduled_login_failure", str(e))


def run_scheduler():
    schedule_login()

    schedule.every(AUTO_LOGIN_FREQUENCY).days.do(schedule_login)
    print(f"🔄 Scheduled login every {AUTO_LOGIN_FREQUENCY} days")
    print(
        f"Next scheduled login: {(datetime.now() + timedelta(days=AUTO_LOGIN_FREQUENCY)).strftime('%Y-%m-%d')}"
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n⏹️  Scheduler interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    ensure_directories()
    if PROXY_ENABLED:
        create_sample_proxies_file()
    if PROXY_ENABLED:
        is_valid, warnings = validate_proxy_config()
        if warnings:
            print("⚠️ Proxy configuration warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        if not is_valid:
            print(
                "❌ Invalid proxy configuration. Please fix the issues and try again."
            )
            sys.exit(1)
    display_startup_banner()

    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        print("Starting scheduler mode...")
        run_scheduler()
    else:
        try:
            asyncio.run(run_bot(scheduled=False))
        except KeyboardInterrupt:
            print("\n⏹️  Bot interrupted by user")
        except Exception as e:
            print(f"\n❌ Bot failed: {e}")
            if health_monitor:
                health_monitor.log_critical_event("bot_crash", str(e))
