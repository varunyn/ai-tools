#!/usr/bin/env python3
"""
Test script to verify OCI configuration is working correctly.
This script checks both local and system OCI configurations.
"""

import os
import yaml
import sys

def get_oci_config(config_profile):
    """
    Get OCI configuration from local file first, then fall back to system config.
    Same function as used in the main application.
    """
    try:
        import oci
    except ImportError:
        print("❌ OCI SDK not installed. Run: pip install oci")
        return None
    
    # Try local OCI config first (for Docker setup)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    local_config_path = os.path.join(project_root, 'config', 'oci-config')
    
    if os.path.exists(local_config_path):
        try:
            print(f"✅ Found local OCI config at: {local_config_path}")
            config = oci.config.from_file(local_config_path, config_profile)
            print(f"✅ Successfully loaded profile '{config_profile}' from local config")
            return config
        except Exception as e:
            print(f"❌ Could not load local OCI config: {e}")
    else:
        print(f"ℹ️  No local OCI config found at: {local_config_path}")
    
    # Fall back to system OCI config
    system_config_path = '~/.oci/config'
    expanded_path = os.path.expanduser(system_config_path)
    if os.path.exists(expanded_path):
        try:
            print(f"✅ Found system OCI config at: {expanded_path}")
            config = oci.config.from_file(system_config_path, config_profile)
            print(f"✅ Successfully loaded profile '{config_profile}' from system config")
            return config
        except Exception as e:
            print(f"❌ Could not load system OCI config: {e}")
            return None
    else:
        print(f"❌ No system OCI config found at: {expanded_path}")
        return None

def test_config_yaml():
    """Test loading the application config.yaml file"""
    print("\n🔍 Testing config.yaml...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    if not os.path.exists(config_path):
        print(f"❌ config.yaml not found at {config_path}. Please create it from config.yaml.example")
        return None, None
    
    try:
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        compartment_id = config_data.get('compartment_id')
        config_profile = config_data.get('config_profile', 'DEFAULT')
        
        print(f"✅ config.yaml loaded successfully")
        print(f"   📦 Compartment ID: {compartment_id[:20]}..." if compartment_id else "❌ No compartment_id found")
        print(f"   👤 Config Profile: {config_profile}")
        
        return compartment_id, config_profile
    
    except Exception as e:
        print(f"❌ Error loading config.yaml: {e}")
        return None, None

def test_oci_connection(config, compartment_id):
    """Test actual OCI connection"""
    print("\n🌐 Testing OCI connection...")
    
    if not config or not compartment_id:
        print("❌ Cannot test connection without valid config and compartment ID")
        return False
    
    try:
        import oci
        
        # Test with Identity service (simple and available in all regions)
        identity_client = oci.identity.IdentityClient(config)
        
        # Try to list availability domains (lightweight operation)
        response = identity_client.list_availability_domains(compartment_id)
        
        print(f"✅ OCI connection successful!")
        print(f"   🏢 Tenancy: {config.get('tenancy', 'Unknown')[:20]}...")
        print(f"   👤 User: {config.get('user', 'Unknown')[:20]}...")
        print(f"   🌍 Region: {config.get('region', 'Unknown')}")
        print(f"   📍 Found {len(response.data)} availability domains")
        
        return True
        
    except Exception as e:
        print(f"❌ OCI connection failed: {e}")
        return False

def main():
    print("🧪 OCI Configuration Test")
    print("=" * 50)
    
    # Test config.yaml
    compartment_id, config_profile = test_config_yaml()
    
    # Test OCI configuration loading
    print(f"\n🔍 Testing OCI configuration for profile '{config_profile}'...")
    config = get_oci_config(config_profile or 'DEFAULT')
    
    # Test actual connection
    connection_success = test_oci_connection(config, compartment_id)
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 30)
    if compartment_id and config and connection_success:
        print("✅ All tests passed! Your OCI configuration is working correctly.")
        print("🚀 You can now run the Streamlit application.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Troubleshooting tips:")
        print("   1. Ensure config.yaml has valid compartment_id and config_profile")
        print("   2. Verify your OCI credentials are correct")
        print("   3. Check that your private key file exists and is readable")
        print("   4. Ensure you have permissions for the specified compartment")
        
        sys.exit(1)

if __name__ == "__main__":
    main() 