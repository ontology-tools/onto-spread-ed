import subprocess
import sys


def main():
    subprocess.run([sys.executable, "-m", "flask", "--app", "ose:create_app", "ose", *sys.argv[1:]])


if __name__ == "__main__":
    main()
