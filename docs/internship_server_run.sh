docker run --rm --name spicedb -p 50051:50051  -p 8443:8443  authzed/spicedb serve  --http-enabled  --grpc-preshared-key "test"

docker network create dev-net

docker network connect dev-net spicedb

docker network connect dev-net <container_name>

