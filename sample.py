async def setup_browser(self):
    """Set up browser with download permissions and enhanced settings"""
    try:
        print("🌐 Setting up browser with enhanced download permissions...")
        
        # Create custom profile directory for our session
        custom_profile = self.downloads_dir / "browser_profile"
        custom_profile.mkdir(exist_ok=True)
        
        # Set Chrome preferences for downloads
        prefs = {
            "download.default_directory": str(self.downloads_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "profile.default_content_settings.popups": 0,
        }
        
        # Write preferences to the profile
        prefs_file = custom_profile / "Default"
        prefs_file.mkdir(exist_ok=True)
        
        import json
        with open(prefs_file / "Preferences", "w") as f:
            json.dump({"download": prefs}, f)
        
        browser_args = [
            f"--user-data-dir={custom_profile}",
            "--allow-running-insecure-content",
            "--disable-web-security",
            "--disable-blink-features=AutomationControlled",
            "--exclude-switches=enable-automation",
        ]
