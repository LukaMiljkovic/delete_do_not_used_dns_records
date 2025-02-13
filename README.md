# How to use

1. Create an .env file and create an API_KEY key:value pair that will store your DO API key
2. Install requirements.txt: `pip install -r requirements.txt`

# How does it work

1. Load the API key provided
2. Gets all the IP addresses of the servers on your DO account (checks first if the ip starts with 10. (private IP) and if it does it uses the other IP address (IPv4)
3. Gets all the domain records
4. Compares the each IP from the domain record with all of the IPs from the servers. IF it finds a match, skip. If it doesn' find a match, ping that IP address and delete it if the ping doesn't go through
