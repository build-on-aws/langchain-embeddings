FROM public.ecr.aws/lambda/python:3.12
COPY . ${LAMBDA_TASK_ROOT}/
RUN microdnf install yum
RUN yum update
RUN yum install -y postgresql postgresql-contrib
RUN pip3 install -r requirements.txt
