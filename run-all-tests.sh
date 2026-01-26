set -e
docker build -t mindweaver-test:latest --target test .
docker run --rm -ti mindweaver-test:latest
