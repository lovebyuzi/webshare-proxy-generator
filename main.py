import requests
import random
import string
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init
import sys
import os

# Initialize colorama
init(autoreset=True)

class WebShareProxyGenerator:
    def __init__(self, captcha_key: str, proxy=None, thread_id=0):
        self.captcha_key = captcha_key
        self.proxy = proxy
        self.thread_id = thread_id
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
        }
        
        # Set proxy if provided
        if proxy:
            proxy_url = f"http://{proxy}"
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            print(f"{Fore.BLUE}[Thread {self.thread_id}]{Style.RESET_ALL} Using proxy: {proxy}")
        
        self.base_url = "https://proxy.webshare.io/api/v2/"
        self.capmonster_url = "https://api.capmonster.cloud"
        
    def print_status(self, message, status="info"):
        """Print colored status messages"""
        colors = {
            "info": Fore.CYAN,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "debug": Fore.MAGENTA,
            "thread": Fore.BLUE
        }
        
        timestamp = time.strftime("%H:%M:%S")
        thread_prefix = f"{Fore.BLUE}[Thread {self.thread_id}]{Style.RESET_ALL}"
        print(f"{Fore.LIGHTBLACK_EX}[{timestamp}]{Style.RESET_ALL} {thread_prefix} {colors.get(status, Fore.WHITE)}{message}{Style.RESET_ALL}")
        
    def solve_captcha_direct(self):
        """Solve reCAPTCHA using direct CapMonster API requests"""
        self.print_status("Solving reCAPTCHA...", "info")
        
        try:
            task_data = {
                "clientKey": self.captcha_key,
                "task": {
                    "type": "RecaptchaV2TaskProxyless",
                    "websiteURL": "https://webshare.io",
                    "websiteKey": "6LeHZ6UUAAAAAKat_YS--O2tj_by3gv3r_l03j9d"
                }
            }
            
            temp_session = requests.Session()
            temp_session.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/json",
            }
            
            create_response = temp_session.post(
                f"{self.capmonster_url}/createTask",
                json=task_data,
                timeout=15
            )
            create_response.raise_for_status()
            
            task_id = create_response.json().get("taskId")
            if not task_id:
                self.print_status("No taskId in response", "error")
                return None
            
            self.print_status(f"Captcha task created: {task_id}", "debug")
            
            result_data = {
                "clientKey": self.captcha_key,
                "taskId": task_id
            }
            
            for attempt in range(20):
                result_response = temp_session.post(
                    f"{self.capmonster_url}/getTaskResult",
                    json=result_data,
                    timeout=15
                )
                result_response.raise_for_status()
                
                result = result_response.json()
                status = result.get("status")
                
                if status == "ready":
                    captcha_token = result.get("solution", {}).get("gRecaptchaResponse")
                    if captcha_token:
                        self.print_status("reCAPTCHA solved successfully!", "success")
                        return captcha_token
                    else:
                        self.print_status("No captcha token in solution", "error")
                        return None
                elif status == "processing":
                    if attempt % 3 == 0:
                        self.print_status(f"Captcha solving... ({attempt + 1}/20)", "debug")
                    time.sleep(1.5)
                else:
                    self.print_status(f"Unexpected status: {status}", "error")
                    return None
            
            self.print_status("Captcha solving timed out", "error")
            return None
            
        except Exception as e:
            self.print_status(f"Error solving captcha: {str(e)}", "error")
            return None
    
    def generate_valid_email(self):
        """Generate email that passes webshare's strict validation"""
        first_names = ["james", "michael", "david", "robert", "john", "thomas", 
                      "sarah", "emma", "olivia", "sophia", "ava", "mia", "charlotte",
                      "william", "chris", "daniel", "mark", "paul", "lisa", "jennifer"]
        
        last_names = ["smith", "johnson", "williams", "brown", "jones", "davis",
                     "miller", "wilson", "moore", "taylor", "anderson", "thomas",
                     "jackson", "white", "harris", "martin", "thompson", "garcia"]
        
        patterns = [
            f"{random.choice(first_names)}{random.choice(last_names)}{random.randint(10, 99)}",
            f"{random.choice(first_names)}{random.randint(1985, 2000)}",
            f"{random.choice(first_names)}.{random.choice(last_names)}{random.randint(1, 9)}",
            f"{random.choice(string.ascii_lowercase)}{random.choice(last_names)}{random.randint(10, 99)}",
            f"user{random.randint(100000, 999999)}",
            f"contact{random.randint(1000, 9999)}",
            f"mail{random.randint(10000, 99999)}",
            f"{random.choice(first_names)}{random.choice(last_names)[0]}{random.randint(85, 99)}",
        ]
        
        domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
        username = random.choice(patterns)
        return f"{username}@{random.choice(domains)}"
    
    def generate_random_password(self):
        """Generate a strong random password"""
        upper = random.choice(string.ascii_uppercase)
        lower = random.choice(string.ascii_lowercase)
        digits = random.choice(string.digits)
        special = random.choice("!@#$%^&*")
        rest = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return upper + lower + digits + special + rest
    
    def create_account(self):
        """Create a new account on webshare.io with captcha solving"""
        self.print_status("Creating account...", "info")
        
        captcha_token = self.solve_captcha_direct()
        if not captcha_token:
            self.print_status("Failed to solve captcha", "error")
            return None, None, None
        
        email = self.generate_valid_email()
        password = self.generate_random_password()
        
        payload = {
            "email": email,
            "password": password,
            "password_confirm": password,
            "tos_accepted": True,
            "recaptcha": captcha_token
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}register/",
                json=payload,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                auth_token = data.get('token')
                if auth_token:
                    self.print_status(f"Account created: {email}", "success")
                    return auth_token, email, password
                else:
                    self.print_status("No token in response", "error")
                    return None, None, None
            else:
                self.print_status(f"Registration failed: {response.status_code}", "error")
                return None, None, None
                
        except Exception as e:
            self.print_status(f"Registration error: {str(e)}", "error")
            return None, None, None
    
    def get_proxies(self, auth_token):
        """Get free proxies using the authentication token"""
        if not auth_token:
            return []
        
        self.print_status("Fetching proxies...", "info")
        
        headers = {
            "Authorization": f"Token {auth_token}",
            **self.session.headers
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}proxy/list/?mode=direct&page=1&page_size=100",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                proxies = []
                
                if 'results' in data:
                    for proxy in data['results']:
                        if all(key in proxy for key in ['proxy_address', 'port', 'username', 'password']):
                            proxy_str = f"{proxy['username']}:{proxy['password']}@{proxy['proxy_address']}:{proxy['port']}"
                            proxies.append(proxy_str)
                
                return proxies
            else:
                self.print_status(f"Proxy fetch failed: {response.status_code}", "error")
                return []
            
        except Exception as e:
            self.print_status(f"Proxy fetch error: {str(e)}", "error")
            return []
    
    def save_proxies(self, proxies, filename="output.txt"):
        """Save proxies to output.txt"""
        if not proxies:
            return False
        
        try:
            with open(filename, 'a') as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            return True
        except Exception:
            return False
    
    def save_account(self, email, password, filename="accounts.txt"):
        """Save account credentials to accounts.txt"""
        try:
            with open(filename, 'a') as f:
                f.write(f"{email}:{password}\n")
            return True
        except Exception:
            return False
    
    def run(self):
        """Main method to run the proxy generation"""
        for attempt in range(2):
            auth_token, email, password = self.create_account()
            
            if auth_token:
                self.save_account(email, password)
                proxies = self.get_proxies(auth_token)
                
                if proxies:
                    self.save_proxies(proxies)
                    self.print_status(f"SUCCESS: {email} - {len(proxies)} proxies saved!", "success")
                    return True
                else:
                    self.print_status(f"Account created but no proxies: {email}", "warning")
                    return True
            
            if attempt < 1:
                wait_time = random.randint(3, 8)
                self.print_status(f"Retrying in {wait_time}s...", "warning")
                time.sleep(wait_time)
        
        self.print_status("Failed after 2 attempts", "error")
        return False

def load_proxies(filename="proxies.txt"):
    """Load proxies from file"""
    try:
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except FileNotFoundError:
        return []

def create_account_task(args):
    """Task for thread pool"""
    captcha_key, proxy, thread_id = args
    generator = WebShareProxyGenerator(captcha_key, proxy, thread_id)
    return generator.run()

def print_banner():
    """Print awesome banner"""
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
{Fore.CYAN}║                                                              ║
{Fore.CYAN}║{Fore.MAGENTA}          🚀 WEB SHARE PROXY GENERATOR 🚀           {Fore.CYAN}║
{Fore.CYAN}║{Fore.YELLOW}         GITHUB.COM              {Fore.CYAN}║
{Fore.CYAN}║                                                              ║
{Fore.CYAN}╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
    print(banner)

def print_stats(successful, total, start_time):
    """Print statistics"""
    elapsed = time.time() - start_time
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    stats = f"""
{Fore.GREEN}╔══════════════════════════════════════════════════════════════╗
{Fore.GREEN}║{Fore.WHITE}                     📊 STATISTICS 📊                   {Fore.GREEN}║
{Fore.GREEN}╠══════════════════════════════════════════════════════════════╣
{Fore.GREEN}║{Fore.CYAN}   Successful Accounts: {Fore.GREEN}{successful:2d}/{total:2d} {Fore.WHITE}({success_rate:.1f}%)                 {Fore.GREEN}║
{Fore.GREEN}║{Fore.CYAN}   Elapsed Time: {Fore.YELLOW}{elapsed:.1f} seconds{Fore.WHITE}                          {Fore.GREEN}║
{Fore.GREEN}║{Fore.CYAN}   Accounts/Min: {Fore.YELLOW}{(successful/elapsed*60) if elapsed > 0 else 0:.1f}{Fore.WHITE}                          {Fore.GREEN}║
{Fore.GREEN}╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
    print(stats)

def main():
    """Main function"""
    print_banner()
    
    # Load config or ask for API key
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            captcha_key = config.get('captcha_apikey', '')
    except:
        captcha_key = input(f"{Fore.YELLOW}Enter your CapMonster API key: {Fore.CYAN}").strip()
    
    if not captcha_key:
        print(f"{Fore.RED}CapMonster API key is required!{Style.RESET_ALL}")
        return
    
    # Ask if user wants to use proxies
    use_proxies = input(f"{Fore.YELLOW}Use proxies? (y/n): {Fore.CYAN}").strip().lower() == 'y'
    proxies_list = []
    
    if use_proxies:
        proxies_list = load_proxies("proxies.txt")
        if not proxies_list:
            print(f"{Fore.YELLOW}No proxies found, continuing without proxies{Style.RESET_ALL}")
            use_proxies = False
        else:
            print(f"{Fore.GREEN}Loaded {len(proxies_list)} proxies{Style.RESET_ALL}")
    
    # Ask user for number of accounts to create
    try:
        num_accounts = int(input(f"{Fore.YELLOW}How many accounts to create? (1-20): {Fore.CYAN}").strip())
        num_accounts = max(1, min(20, num_accounts))
    except ValueError:
        num_accounts = 1
    
    # Ask for thread count
    try:
        max_workers = int(input(f"{Fore.YELLOW}How many threads? (1-8): {Fore.CYAN}").strip())
        max_workers = max(1, min(8, max_workers))
    except ValueError:
        max_workers = 3
    
    print(f"\n{Fore.GREEN}Starting {num_accounts} accounts with {max_workers} threads...{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}Press Ctrl+C to stop{Style.RESET_ALL}\n")
    
    start_time = time.time()
    successful_accounts = 0
    tasks = []
    
    # Create tasks
    for i in range(num_accounts):
        proxy = random.choice(proxies_list) if use_proxies and proxies_list else None
        tasks.append((captcha_key, proxy, i + 1))
    
    # Execute tasks with thread pool
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(create_account_task, task): task for task in tasks}
            
            for future in as_completed(futures):
                if future.result():
                    successful_accounts += 1
                
                # Print progress
                progress = (successful_accounts / num_accounts) * 100
                print(f"{Fore.LIGHTBLACK_EX}Progress: {progress:.1f}% ({successful_accounts}/{num_accounts}){Style.RESET_ALL}", end='\r')
    
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Stopped by user!{Style.RESET_ALL}")
    
    # Print final statistics
    print_stats(successful_accounts, num_accounts, start_time)
    
    # Show file locations
    print(f"{Fore.CYAN}📁 Files created:")
    print(f"{Fore.GREEN}   → Accounts: {Fore.WHITE}accounts.txt")
    print(f"{Fore.GREEN}   → Proxies:  {Fore.WHITE}output.txt")
    print(f"{Fore.GREEN}   → Config:   {Fore.WHITE}config.json{Style.RESET_ALL}")

if __name__ == "__main__":
    main()