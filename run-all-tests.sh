set -e
docker build -t mindweaver-test:latest --target test .
docker run --rm mindweaver-test:latest
