#uv pip compile pyproject.toml -o rp_requirements.txt
docker build --platform linux/amd64 --tag kolobochek/serverless-test .