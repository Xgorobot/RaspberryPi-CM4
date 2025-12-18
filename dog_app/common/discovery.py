from zeroconf import Zeroconf, ServiceBrowser
import socket
import time
import threading

class ServiceDiscoverer:
    def __init__(self, service_type="_xgo-voice._tcp.local."):
        self.zeroconf = Zeroconf()
        self.service_type = service_type
        self.found_service = None
        self.found_event = threading.Event()
        
    class ServiceListener:
        def __init__(self, parent):
            self.parent = parent

        def remove_service(self, zeroconf, type, name):
            print(f"Service {name} removed")
            if self.parent.found_service and self.parent.found_service['name'] == name:
                self.parent.found_service = None

        def add_service(self, zeroconf, type, name):
            info = zeroconf.get_service_info(type, name)
            if info:
                # Convert address to string
                # We typically take the first address
                addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
                if addresses:
                    host = addresses[0]
                    port = info.port
                    print(f"Service found: {name} at {host}:{port}")
                    self.parent.found_service = {
                        'name': name,
                        'host': host,
                        'port': port,
                        'properties': info.properties
                    }
                    self.parent.found_event.set()

        def update_service(self, zeroconf, type, name):
            pass

    def discover(self, timeout=5.0):
        print(f"Browsing for {self.service_type}...")
        listener = self.ServiceListener(self)
        browser = ServiceBrowser(self.zeroconf, self.service_type, listener)
        
        # Wait for service
        if self.found_event.wait(timeout):
            browser.cancel()
            self.zeroconf.close()
            return self.found_service
        
        browser.cancel()
        self.zeroconf.close()
        return None

if __name__ == "__main__":
    # Test script
    discoverer = ServiceDiscoverer()
    result = discoverer.discover()
    if result:
        print(f"Test Success: Found {result}")
    else:
        print("Test Failed: No service found.")
