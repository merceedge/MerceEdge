FROM python:3.6

WORKDIR /home/MerceEdge

COPY requirements.txt /home/MerceEdge
RUN pip install --trusted-host pypi.org --upgrade -r /home/MerceEdge/requirements.txt

EXPOSE 8080

CMD ["bash"]