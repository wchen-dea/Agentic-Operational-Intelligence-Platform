import json
import os

current_dir = os.path.dirname(os.path.realpath(__file__))


def get_application_properties():
    if is_local():
        path = os.path.join(current_dir, "application_properties_local.json")
    elif is_docker():
        path = os.path.join(current_dir, "application_properties_docker.json")
    else:
        path = "/etc/flink/application_properties.json"

    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    raise FileNotFoundError(f"Properties file not found: {path}")


def get_property_map(props, property_group_id):
    for prop in props:
        if prop["PropertyGroupId"] == property_group_id:
            return prop["PropertyMap"]
    raise KeyError(f'PropertyGroupId "{property_group_id}" not found in application properties')


def is_local():
    return get_runtime_env() == "local"


def is_docker():
    return get_runtime_env() == "docker"


def is_aws():
    return get_runtime_env() == "aws"


def get_runtime_env():
    return os.getenv("RUNTIME_ENV", "docker")


def add_jars(env):
    """Add connector JARs when running locally (in docker/aws they live in /opt/flink/lib).

    Two JARs are required for avro-confluent Kafka tables:
      1. flink-sql-connector-kafka        - Kafka source/sink connector
      2. flink-sql-avro-confluent-registry - avro-confluent format factory
    For local mode these are expected in ../../target/ relative to the app dir.
    Download them from Maven Central or copy from the built KDA dependencies JAR.
    """
    if is_local():
        target_dir = os.path.join(current_dir, "../../target")
        jars = [
            "flink-sql-connector-kafka-3.3.0-1.20.jar",
            "flink-sql-avro-confluent-registry-1.20.0.jar",
        ]
        # Fallback: use the bundled KDA fat-JAR if individual JARs are absent
        kda_jar = os.path.join(target_dir, "kda-dependencies-1.20.0.jar")
        if os.path.isfile(kda_jar):
            env.add_jars(f"file://{kda_jar}")
            return
        jar_paths = [
            f"file://{os.path.join(target_dir, j)}" for j in jars if os.path.isfile(os.path.join(target_dir, j))
        ]
        if jar_paths:
            env.add_jars(*jar_paths)
        else:
            print(
                f"[WARN] No connector JARs found in {target_dir} - "
                "run 'uv run python -m data_platform.streaming.flink_jobs.canonical.jobs.fetch_jars'"
            )


def execute(env, job_name):
    """Execute the Flink job (blocking in local mode, async on cluster).

    Configures a fixed-delay restart strategy so transient broker or network
    failures are retried before the job is declared failed.
    supervisor will restart the Python process if the job ultimately exits.
    """
    try:
        from pyflink.datastream import RestartStrategies

        env.set_restart_strategy(
            RestartStrategies.fixed_delay_restart(
                restart_attempts=5,
                delay_between_attempts=10_000,
            )
        )
    except (ImportError, AttributeError):
        pass  # RestartStrategies not available in this PyFlink version
    if is_local():
        env.execute(job_name).wait()
    else:
        env.execute(job_name)
