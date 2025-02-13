#!/usr/bin/env python3
import os
import subprocess
import digitalocean
from dotenv import load_dotenv


def load_api_key():
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY not found in environment. Please set it in your .env file.")
    return api_key


def get_server_ips(manager):
    """
    Retrieves all IPv4 addresses from your DigitalOcean droplets.
    If the first IP address starts with '10.' (typically a private IP),
    the function looks for an alternate public IP address in the droplet's list.
    """
    droplets = manager.get_all_droplets()
    ips = set()
    for droplet in droplets:
        v4_addresses = droplet.networks.get('v4', [])
        if not v4_addresses:
            continue

        # Start with the first IP address.
        chosen_ip = v4_addresses[0]['ip_address']

        # If the chosen IP starts with '10.', look for a non-'10.' address.
        if chosen_ip.startswith("10."):
            for addr in v4_addresses:
                ip = addr['ip_address']
                if not ip.startswith("10."):
                    chosen_ip = ip
                    break  # Use the first public IP found.

        ips.add(chosen_ip)
    return ips


def ping_ip(ip):
    """
    Pings the given IP address once.
    Returns True if the ping succeeds, False otherwise.
    """
    try:
        # '-c 1' sends one ping packet. (On Windows, you may need to change this to '-n 1')
        result = subprocess.run(["ping", "-c", "1", ip],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        return False


def process_domain_records(domain, server_ips):
    """
    Iterates over all DNS records of the given domain.
    For each A record, it compares its IP to the server IPs.
    If no match is found, the record is pinged; if the ping fails, the record is deleted.
    """
    records = domain.get_records()
    for record in records:
        # Only process A records (records that hold an IPv4 address)
        if record.type != "A":
            continue

        record_ip = record.data
        if record_ip in server_ips:
            print(f"[SKIP] DNS record (ID: {record.id}) IP {record_ip} matches a server IP.")
        else:
            print(f"[CHECK] DNS record (ID: {record.id}) IP {record_ip} does not match any server IP. Pinging...")
            if ping_ip(record_ip):
                print(f"[LIVE] IP {record_ip} responded to ping.")
            else:
                print(f"[DELETE] IP {record_ip} did not respond to ping. Deleting DNS record (ID: {record.id}).")
                try:
                    record.destroy()
                except Exception as e:
                    print(f"Error deleting record {record.id}: {e}")


def main():
    api_key = load_api_key()

    # Create a DigitalOcean manager instance
    manager = digitalocean.Manager(token=api_key)

    # Get the set of all server (droplet) IPv4 addresses
    server_ips = get_server_ips(manager)
    print(f"Found server IPs: {', '.join(server_ips) if server_ips else 'None'}")

    # Initialize the Domain object for '<domain_name>'
    domain = digitalocean.Domain(token=api_key, name="<domain_name>")

    # Process DNS records for the domain
    process_domain_records(domain, server_ips)


if __name__ == "__main__":
    main()
