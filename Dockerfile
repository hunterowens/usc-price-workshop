FROM jupyter/datascience-notebook:python-3.8.5

COPY conda-requirements.txt /tmp/
RUN conda install --yes -c conda-forge --file /tmp/conda-requirements.txt


# Install pip requirements
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

