# Bot-web Enhancement Project

## Overview
This project enhances the Bot-web application with improved cross-platform compatibility, anti-detection mechanisms, login tracking, VPN/proxy verification, multi-browser support, and scheduled login functionality.

## Enhancements Implemented

### 1. Multi-Browser Support
- Added `detect_installed_browsers()` function to identify available browsers on the system
- Implemented automatic browser selection based on availability (Chrome, Firefox, Edge, Opera, Brave)
- Added fallback mechanisms to use alternative browsers if primary choice fails
- Enhanced browser launch options for each browser type

#### Testing Multi-Browser Support

To test the multi-browser detection and selection logic, run:

```bash
python3 test_multi_browser_support.py
```

This test script will:
- Detect all available browsers on your system (Chrome, Firefox, Edge, Opera, Brave)
- Verify browser executable paths exist and are accessible
- Show the browser preference order (Chrome > Firefox > Edge > Opera > Brave)
- Indicate which browser would be selected for automation based on availability
- Test the 'which' command detection method on Unix-like systems
- Provide a comprehensive test summary with pass/fail status

The test performs two main validations:
1. **Browser Detection Test**: Verifies the system can detect installed browsers and their paths
2. **Browser Launch Logic Test**: Confirms the browser selection preference order works correctly

### 2. Cross-Platform Compatibility
- Added OS detection for Windows, macOS, and Linux
- Implemented platform-specific browser executable path detection
- Created `get_user_data_dir()` function for consistent user data storage across platforms
- Enhanced browser launch options with structured configuration
- Added multiple fallback mechanisms for browser launch failures

### 2. VPN/Proxy Verification
- Added `check_vpn_proxy_connection()` to verify proxy connectivity before starting
- Implemented `verify_site_access()` to ensure target site is accessible
- Added user prompts for connection issues with retry options

### 3. Login Tracking & Scheduled Login
- Added automatic login tracking with `LOGIN_TRACKING_FILE` and `AUTO_LOGIN_FREQUENCY`
- Implemented `check_login_tracking()` to determine when login is needed
- Modified `safe_login()` to use tracking data for login decisions
- Added `schedule_login()` function to run the bot automatically every 15 days
- Implemented `run_scheduler()` to manage scheduled logins
- Added command-line argument `--schedule` to run the bot in scheduler mode

### 4. Enhanced Frame Finding
- Improved `find_frame_with_selector()` with retry mechanisms
- Added main frame priority checking
- Implemented systematic frame checks with reduced timeouts
- Added mouse movement interactions between retries to refresh frames

### 5. Code Cleanup
- Created `remove_comments.py` utility to clean up code comments
- Removed all comments from Python files while preserving functionality
- Maintained shebang and encoding lines for proper execution

## Usage

### Running the Bot
The bot can be run with the standard command:
```
python3 __main__.py
```

### Running with Scheduled Login (every 15 days)
```
python3 __main__.py --schedule
```

### Verification
To verify all enhancements are properly implemented:
```
python3 verify_enhancements.py
```

### Comment Removal
To remove comments from Python files:
```
python3 remove_comments.py <file_or_directory>
```

## Requirements
All dependencies are listed in `requirements.txt`.