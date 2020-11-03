FROM cityofla/ita-data-civis-lab:latest 

COPY conda-requirements.txt /tmp/
RUN conda install --yes -c conda-forge --file /tmp/conda-requirements.txt



