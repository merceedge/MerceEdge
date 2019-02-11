FROM python:3.6

# RUN apt-get update && apt-get install -y mysql-client

# RUN mkdir /pin_tuan
WORKDIR /home/merceedge

COPY requirements.txt /home/merceedge
RUN pip install --trusted-host pypi.org --upgrade -r /home/merceedge/requirements.txt

# COPY . /usr/src/app

# CMD python blog.py --mysql_host=mysql

EXPOSE 8080

CMD ["bash"]