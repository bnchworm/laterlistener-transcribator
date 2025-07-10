FROM python:3.12-slim

WORKDIR /

COPY requirements.txt /requirements.txt
# Install dependencies
RUN TMPDIR=/home/user/tmp/ pip install -r requirements.txt

COPY models /models

RUN apt update
RUN apt install -y ffmpeg

# Copy your handler file
COPY rp_handler.py /
COPY rp_diarization.py /
COPY .rp.env /.env


# Start the container
CMD ["python3", "-u", "rp_handler.py"]