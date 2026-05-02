# -*- coding: utf-8 -*-
import requests
import json
import time
from typing import Optional, Dict

# Cache to avoid repeated API calls for the same IP
_ip_cache = {}
_cache_expiry = 3600  # 1 hour cache

def get_ip_location(ip_address: str) -> Optional[Dict[str, str]]:
    """
    Get location information for an IP address using multiple services
    Returns a dictionary with location data or None if failed
    """
    try:
        # Check cache first
        current_time = time.time()
        if ip_address in _ip_cache:
            cached_data, cached_time = _ip_cache[ip_address]
            if current_time - cached_time < _cache_expiry:
                return cached_data
        
        # Skip private/local IPs
        if ip_address in ['127.0.0.1', 'localhost', '::1'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
            result = {
                'country': 'Local',
                'city': 'Local Network',
                'region': 'Local',
                'timezone': 'Local',
                'location_string': 'Local Network'
            }
            _ip_cache[ip_address] = (result, current_time)
            return result
        
        # Try multiple services in order
        services = [
            {
                'name': 'ip-api.com',
                'url': f"http://ip-api.com/json/{ip_address}",
                'parse_func': parse_ipapi_response
            },
            {
                'name': 'ipapi.co',
                'url': f"https://ipapi.co/{ip_address}/json/",
                'parse_func': parse_ipapi_co_response
            },
            {
                'name': 'ipinfo.io',
                'url': f"https://ipinfo.io/{ip_address}/json",
                'parse_func': parse_ipinfo_response
            }
        ]
        
        for service in services:
            try:
                print(f"Trying {service['name']} for IP {ip_address}")
                response = requests.get(service['url'], timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    result = service['parse_func'](data)
                    if result:
                        _ip_cache[ip_address] = (result, current_time)
                        print(f"Successfully got location from {service['name']}: {result}")
                        return result
                else:
                    print(f"{service['name']} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"Error with {service['name']}: {e}")
                continue
        
        # If all services fail, return None
        print(f"All services failed for IP {ip_address}")
        return None
            
    except Exception as e:
        print(f"Error getting location for IP {ip_address}: {e}")
        return None

def parse_ipapi_response(data):
    """Parse response from ip-api.com"""
    if data.get('status') == 'success':
        location_string = f"{data.get('city', 'Unknown')}, {data.get('regionName', 'Unknown')}, {data.get('country', 'Unknown')}"
        return {
            'country': data.get('country', 'Unknown'),
            'city': data.get('city', 'Unknown'),
            'region': data.get('regionName', 'Unknown'),
            'location_string': location_string,
            'timezone': data.get('timezone', 'Unknown'),
            'latitude': data.get('lat'),
            'longitude': data.get('lon')
        }
    return None

def parse_ipapi_co_response(data):
    """Parse response from ipapi.co"""
    if not data.get('error'):
        location_string = f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country_name', 'Unknown')}"
        return {
            'country': data.get('country_name', 'Unknown'),
            'city': data.get('city', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'location_string': location_string,
            'timezone': data.get('timezone', 'Unknown'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude')
        }
    return None

def parse_ipinfo_response(data):
    """Parse response from ipinfo.io"""
    if not data.get('error'):
        location_string = f"{data.get('city', 'Unknown')}, {data.get('region', 'Unknown')}, {data.get('country', 'Unknown')}"
        return {
            'country': data.get('country', 'Unknown'),
            'city': data.get('city', 'Unknown'),
            'region': data.get('region', 'Unknown'),
            'location_string': location_string,
            'timezone': data.get('timezone', 'Unknown'),
            'latitude': data.get('loc', '').split(',')[0] if data.get('loc') else None,
            'longitude': data.get('loc', '').split(',')[1] if data.get('loc') else None
        }
    return None

def get_location_string(ip_address: str) -> str:
    """
    Get a formatted location string for an IP address
    """
    location = get_ip_location(ip_address)
    if location:
        if location['country'] == 'Local':
            return 'Local Network'
        
        parts = []
        if location['city'] and location['city'] != 'Unknown':
            parts.append(location['city'])
        if location['region'] and location['region'] != 'Unknown':
            parts.append(location['region'])
        if location['country'] and location['country'] != 'Unknown':
            parts.append(location['country'])
        
        return ', '.join(parts) if parts else 'Unknown Location'
    
    return 'Unknown Location'
