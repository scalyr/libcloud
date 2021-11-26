import os

from libcloud.compute.providers import get_driver
from libcloud.compute.base import NodeSize
from libcloud.compute.type import Provider
from libcloud.compute.deployment import ScriptDeployment

cls = get_driver(Provider.GRIDSCALE)
driver = cls("USER-UUID", "API-TOKEN")

# We don't feature packages containing a fix size so you will have to
# built your own size object. Make sure to use a multiple of 1024MB when
# asigning RAM
size_name = "my-node-size"
ram = 1024  # amout of ram In MB
disk = 10  # disk size in GB
cores = 1  # numer of cores node should have
size = NodeSize(
    id=0,
    bandwidth=0,
    price=0,
    name=size_name,
    ram=ram,
    disk=disk,
    driver=driver,
    extra={"cores": cores},
)

ssh_key = driver.list_key_pairs()[0]
ssh_key_uuid = ssh_key.fingerprint

node_name = "MyServer"

images = driver.list_images()
image = [i for i in images if i.name == "Ubuntu 18.04 LTS"][0]

locations = driver.list_locations()
location = [loc for loc in locations if loc.name == "de/fra"][0]

# Check if a key pair object with the provided name already exists
# If it already exists, using an existing key, otherwise import a new one
key_pair_name = "libcloud-key-pair"
key_pairs = driver.list_key_pairs()
key_pairs = [kp for kp in key_pairs if kp.name == key_pair_name]

public_key_file_path = os.path.expanduser("~/.ssh/id_rsa_gridscale.pub")
private_key_file_path = os.path.expanduser("~/.ssh/id_rsa_gridscale")

if key_pairs:
    print("Re-using existing SSH Key")
    key_pair = key_pairs[0]
else:
    print("Importing / creating new SSH Key")
    key_pair = driver.import_key_pair_from_file(
        name=key_pair_name, key_file_path=public_key_file_path
    )  # NOQA


step = ScriptDeployment("echo whoami ; date ; ls -la")

node = driver.deploy_node(
    name=node_name,
    size=size,
    image=image,
    location=location,
    ex_ssh_key_ids=[key_pair.fingerprint],
    deploy=step,
    ssh_key=private_key_file_path,
)
print(node)
