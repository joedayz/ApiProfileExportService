FROM ubuntu:22.04
RUN echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
RUN echo 'APT::Install-Recommends "0";' >> /etc/apt/apt.conf.d/00-docker
WORKDIR app
COPY . .
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y libreoffice python3-uno python3 python3-pip vim fonts-font-awesome libreoffice-java-common default-jre fonts-roboto \
  && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt
CMD /app/run.sh
