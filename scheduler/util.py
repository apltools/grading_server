import subprocess

def run(*args):
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return process.stdout.read().decode('utf8').strip()

def get_container_id(container_name):
    return run("docker", "container", "ls", "-aqf", f"name={container_name}")

def get_container_ip(container_id_or_name):
    return run("docker", "inspect", "-f", "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'", container_id_or_name)
