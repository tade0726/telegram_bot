# Use the official PostgreSQL image as the base image
FROM postgres:14

# Set environment variables
ENV POSTGRES_DB=user_system
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=secure_password

# Copy initialization scripts
COPY ./init.sql /docker-entrypoint-initdb.d/

# Expose the PostgreSQL port
EXPOSE 5432

# Add labels for better container management
LABEL maintainer="Ted Zhao <zp4work+dev@gmail.com>"
LABEL description="PostgreSQL container for User System"
LABEL version="1.0"

# Set the default command to run when starting the container
CMD ["postgres"]