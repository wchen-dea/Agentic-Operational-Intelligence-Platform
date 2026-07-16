FROM flink:2.2.0-scala_2.12-java17

USER root

# ---------------------------------------------------------------------------
# Build arguments
# ---------------------------------------------------------------------------
ARG PYTHON_VERSION
ENV PYTHON_VERSION=${PYTHON_VERSION:-3.12.4}

ARG FLINK_VERSION
ENV FLINK_VERSION=${FLINK_VERSION:-2.2.0}

# ---------------------------------------------------------------------------
# Connector / format dependencies JAR
#
# Built by Maven before docker build:
#   mvn package -f container/flink/pom.xml   (or: make flink-jar)
#
# The fat JAR bundles:
#   • flink-sql-connector-kafka   (Kafka source/sink)
#   • flink-sql-avro-confluent-registry  (avro-confluent format)
#   • aws-msk-iam-auth            (MSK IAM auth for KDA/MSK deployments)
#
# Placed in /opt/flink/lib so every job picks it up without needing
# env.add_jars() calls.
# ---------------------------------------------------------------------------
COPY container/flink/target/kda-dependencies-*.jar /opt/flink/lib/

# ---------------------------------------------------------------------------
# Ensure JDK headers exist for pemja (PyFlink dependency). Some Flink base
# variants include only a JRE path at /opt/java/openjdk without include/*.h.
# ---------------------------------------------------------------------------
RUN set -eux; \
        find /etc/apt -type f \( -name '*.list' -o -name '*.sources' \) -print0 \
            | xargs -0 sed -i 's|http://ports.ubuntu.com/ubuntu-ports|https://ports.ubuntu.com/ubuntu-ports|g' || true; \
        apt-get update -y; \
        apt-get install -y --no-install-recommends openjdk-17-jdk; \
        ln -sfn "$(ls -d /usr/lib/jvm/java-17-openjdk-* | head -1)" /usr/lib/jvm/java-17-openjdk; \
        test -d /usr/lib/jvm/java-17-openjdk/include; \
        apt-get clean; \
        rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk

# ---------------------------------------------------------------------------
# Python — built from source to pin an exact CPython version.
# The Flink base image ships with a system Python but its version may lag;
# building from source guarantees the version required by apache-flink.
# ---------------------------------------------------------------------------
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libffi-dev \
        liblzma-dev \
        wget && \
    wget -q "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" && \
    tar -xf "Python-${PYTHON_VERSION}.tgz" && \
    cd "Python-${PYTHON_VERSION}" && \
    ./configure --without-tests --enable-shared && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig /usr/local/lib && \
    cd .. && \
    rm -f "Python-${PYTHON_VERSION}.tgz" && \
    rm -rf "Python-${PYTHON_VERSION}" && \
    # Provide /usr/local/bin/python as an alias for python3
    ln -sf /usr/local/bin/python3 /usr/local/bin/python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# pip + PyFlink
# ---------------------------------------------------------------------------
RUN pip3 install --upgrade pip --no-cache-dir && \
    pip3 install --no-cache-dir apache-flink==${FLINK_VERSION}

WORKDIR /opt/flink/usrlib
ENV PYTHONPATH=/opt/flink/usrlib
