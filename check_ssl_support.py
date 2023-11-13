import ssl

def check_ssl_support():
    try:
        context = ssl.create_default_context()
        print("SSL/TLS support available.")
        print("Protocol:", context.get_ciphers()[0]['protocol'])
    except (ssl.SSLError, AttributeError) as e:
        print("SSL/TLS support not available.")
        print("Error:", e)

# Run the check
check_ssl_support()
