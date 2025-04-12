FROM python:3.11
ENV TZ="Asia/Ho_Chi_Minh"
ENV LANG vi_VN
ENV LC_ALL vi_VN
# Add a /fit-backend volume
VOLUME ["/kltn-backend"]
WORKDIR /kltn-backend
ADD . /kltn-backend
RUN pip install -r requirements.txt
EXPOSE 5012
CMD gunicorn --workers=3 --threads=1 --timeout=3600 --preload -b 0.0.0.0:5012 server:app