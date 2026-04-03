import http.server, os, sys
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5500
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# bind='127.0.0.1' avoids Windows IPv6 link-local routing issues that prevent curl/browser access
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=port, bind='127.0.0.1')
