# 1. Use an official Python runtime as a parent image
# "slim" versions are lighter and better for production
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file into the container at /app
COPY requirements.txt /app/

# 4. Install any needed packages specified in requirements.txt
# --no-cache-dir keeps the image small
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the current directory contents into the container at /app
COPY . /app/

# 6. Make port 5000 available to the world outside this container
EXPOSE 5000

# 7. Define environment variable to tell Flask how to run
ENV FLASK_APP=app.py

# 8. Run the app when the container launches
# --host=0.0.0.0 is CRITICAL. It lets the container listen to outside requests.
CMD ["flask", "run", "--host=0.0.0.0"]