#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


def check_file_exists(file_path):
    exists = os.path.exists(file_path)
    print(f"✓ {file_path}: {'Found' if exists else 'Not found'}")
    return exists


def check_function_in_file(file_path, function_name):
    if not os.path.exists(file_path):
        print(f"✗ Cannot check for {function_name} - {file_path} not found")
        return False

    with open(file_path, "r") as f:
        content = f.read()

    function_exists = f"def {function_name}" in content
    print(
        f"✓ Function {function_name}: {'Found' if function_exists else 'Not found'} in {file_path}"
    )
    return function_exists


def check_variable_in_file(file_path, variable_name):
    if not os.path.exists(file_path):
        print(f"✗ Cannot check for {variable_name} - {file_path} not found")
        return False

    with open(file_path, "r") as f:
        content = f.read()

    variable_exists = variable_name in content
    print(
        f"✓ Variable {variable_name}: {'Found' if variable_exists else 'Not found'} in {file_path}"
    )
    return variable_exists


def main():
    print("\n🔍 Verifying Bot Enhancements\n" + "-" * 30)

    main_py = check_file_exists("/Users/rezaflutt/Bot-web/__main__.py")
    check_file_exists("/Users/rezaflutt/Bot-web/proxy_rotator.py")

    if not main_py:
        print("❌ Main script not found. Verification failed.")
        return

    print("\n🔍 Checking Cross-Platform Compatibility\n" + "-" * 30)

    check_variable_in_file("/Users/rezaflutt/Bot-web/__main__.py", "DETECTED_OS")
    check_variable_in_file("/Users/rezaflutt/Bot-web/__main__.py", "get_user_data_dir")
    check_variable_in_file(
        "/Users/rezaflutt/Bot-web/__main__.py", "browser_launch_options"
    )
    check_function_in_file(
        "/Users/rezaflutt/Bot-web/__main__.py", "detect_installed_browsers"
    )

    print("\n🔍 Checking VPN/Proxy Verification\n" + "-" * 30)

    check_function_in_file(
        "/Users/rezaflutt/Bot-web/__main__.py", "check_vpn_proxy_connection"
    )
    check_function_in_file("/Users/rezaflutt/Bot-web/__main__.py", "verify_site_access")

    print("\n🔍 Checking Login Tracking\n" + "-" * 30)

    check_variable_in_file(
        "/Users/rezaflutt/Bot-web/__main__.py", "LOGIN_TRACKING_FILE"
    )
    check_variable_in_file(
        "/Users/rezaflutt/Bot-web/__main__.py", "AUTO_LOGIN_FREQUENCY"
    )
    check_function_in_file(
        "/Users/rezaflutt/Bot-web/__main__.py", "check_login_tracking"
    )

    print("\n🔍 Checking Scheduled Login\n" + "-" * 30)

    check_function_in_file("/Users/rezaflutt/Bot-web/__main__.py", "schedule_login")
    check_function_in_file("/Users/rezaflutt/Bot-web/__main__.py", "run_scheduler")

    print("\n🔍 Checking Frame Finding Enhancements\n" + "-" * 30)

    check_function_in_file(
        "/Users/rezaflutt/Bot-web/__main__.py", "find_frame_with_selector"
    )
    check_variable_in_file("/Users/rezaflutt/Bot-web/__main__.py", "max_retries")

    print("\n🔍 Checking Comment Removal\n" + "-" * 30)

    check_file_exists("/Users/rezaflutt/Bot-web/remove_comments.py")

    print("\n✅ Verification Complete!")


if __name__ == "__main__":
    main()
