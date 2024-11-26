import server
import sys


def main():
    host_name = "0.0.0.0"
    port = 8080
    if len(sys.argv) > 1:
        host_name = sys.argv[1]
        port = int(sys.argv[2])

    server.run(host_name, port)


if __name__ == "__main__":
    main()
