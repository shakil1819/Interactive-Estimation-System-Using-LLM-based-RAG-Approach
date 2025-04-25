#!/usr/bin/env python
"""
Configuration Generator Tool for Interactive Estimation System

This script helps users create and update service configurations in the config.json file.
It provides a command-line interface to add, modify, or delete service configurations.
"""

import json
import os
import argparse
from typing import Dict, Any


def load_config(config_path: str) -> Dict[str, Any]:
    """Load the configuration from the JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}. Creating a new one.")
        return {"services": {}}
    except json.JSONDecodeError:
        print("Error decoding JSON. Using empty configuration.")
        return {"services": {}}


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """Save the configuration to the JSON file."""
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Configuration saved to {config_path}")


def add_service(config: Dict[str, Any], service_name: str) -> Dict[str, Any]:
    """Add a new service to the configuration."""
    if service_name in config["services"]:
        print(f"Service '{service_name}' already exists. You can modify it instead.")
        return config
    
    print(f"\nAdding new service: {service_name}")
    
    # Get base rate
    base_rate = float(input("Base rate per square foot: "))
    
    # Get materials
    materials = {}
    print("\nLet's add materials and their multipliers.")
    print("Enter material names and multipliers. Enter 'done' to finish.")
    while True:
        material_name = input("Material name (or 'done'): ").lower().strip()
        if material_name == "done":
            break
        multiplier = float(input(f"Multiplier for {material_name}: "))
        materials[material_name] = multiplier
    
    # Get regions
    regions = {}
    print("\nLet's add regions and their multipliers.")
    print("Enter region names and multipliers. Enter 'done' to finish.")
    while True:
        region_name = input("Region name (or 'done'): ").lower().strip()
        if region_name == "done":
            break
        multiplier = float(input(f"Multiplier for {region_name}: "))
        regions[region_name] = multiplier
    
    # Get timeline multipliers
    timeline_multipliers = {}
    print("\nLet's add timeline options and their multipliers.")
    print("Enter timeline names and multipliers. Enter 'done' to finish.")
    while True:
        timeline_name = input("Timeline name (or 'done'): ").lower().strip()
        if timeline_name == "done":
            break
        multiplier = float(input(f"Multiplier for {timeline_name}: "))
        timeline_multipliers[timeline_name] = multiplier
    
    # Get permit fee
    permit_fee = float(input("\nPermit fee: "))
    
    # Get price range percentage
    price_range_percentage = float(input("Price range percentage (e.g., 0.15 for ±15%): "))
    
    # Required information fields
    required_info = [
        "service_type", 
        "square_footage", 
        "location", 
        "material_type", 
        "timeline"
    ]
    
    # Create service config
    service_config = {
        "base_rate_per_sqft": base_rate,
        "materials": materials,
        "regions": regions,
        "timeline_multipliers": timeline_multipliers,
        "permit_fee": permit_fee,
        "price_range_percentage": price_range_percentage,
        "required_info": required_info
    }
    
    # Update config
    config["services"][service_name] = service_config
    
    print(f"\nService '{service_name}' added successfully!")
    return config


def list_services(config: Dict[str, Any]) -> None:
    """List all services in the configuration."""
    services = config.get("services", {})
    
    if not services:
        print("No services found in the configuration.")
        return
    
    print("\nAvailable Services:")
    print("------------------")
    
    for service_name, service_config in services.items():
        materials = ", ".join(service_config.get("materials", {}).keys())
        regions = ", ".join(service_config.get("regions", {}).keys())
        timelines = ", ".join(service_config.get("timeline_multipliers", {}).keys())
        
        print(f"Service: {service_name}")
        print(f"  Base Rate: ${service_config.get('base_rate_per_sqft', 0):.2f} per sq ft")
        print(f"  Materials: {materials}")
        print(f"  Regions: {regions}")
        print(f"  Timelines: {timelines}")
        print(f"  Permit Fee: ${service_config.get('permit_fee', 0):.2f}")
        print(f"  Price Range: ±{service_config.get('price_range_percentage', 0.15) * 100:.0f}%")
        print()


def delete_service(config: Dict[str, Any], service_name: str) -> Dict[str, Any]:
    """Delete a service from the configuration."""
    if service_name not in config["services"]:
        print(f"Service '{service_name}' not found in the configuration.")
        return config
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete service '{service_name}'? (y/n): ")
    if confirm.lower() != "y":
        print("Deletion canceled.")
        return config
    
    # Delete the service
    del config["services"][service_name]
    print(f"Service '{service_name}' deleted successfully!")
    return config


def main():
    """Main function to run the configuration tool."""
    parser = argparse.ArgumentParser(description="Configuration tool for Interactive Estimation System")
    parser.add_argument("--config", default="config.json", help="Path to the configuration file")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    list_parser = subparsers.add_parser("list", help="List all services")
    
    add_parser = subparsers.add_parser("add", help="Add a new service")
    add_parser.add_argument("service", help="Name of the service to add")
    
    delete_parser = subparsers.add_parser("delete", help="Delete a service")
    delete_parser.add_argument("service", help="Name of the service to delete")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Ensure services key exists
    if "services" not in config:
        config["services"] = {}
    
    # Execute command
    if args.command == "list":
        list_services(config)
    elif args.command == "add":
        config = add_service(config, args.service)
        save_config(config, args.config)
    elif args.command == "delete":
        config = delete_service(config, args.service)
        save_config(config, args.config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
