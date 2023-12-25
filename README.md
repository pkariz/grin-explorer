# Grin explorer
Explorer for cryptocurrency Grin.

# Prerequisites
-  ensure you have docker and docker compose installed
-  grin-node (rust) version must be >= 5.2.0 (node to which explorer connects to)
-  make sure that the host running grin-node accepts TCP on port where your foreign api is listening (for testnet default port is 13413, for mainnet it's 3413)
    NOTE: example with iptables for testnet:  sudo iptables -I INPUT -p tcp --dport 13413 -j ACCEPT

# Run explorer on localhost
1.  fill out the missing ENV variables in `.env` file (secretkey + user's info)
2.  go to project's main folder
3.  run `docker build -t grinnixos -f docker/nixos/Dockerfile .`
4.  run `docker run -it -v ${PWD}:/code grinnixos ./docker/nixos/init.sh`
5.  run `docker compose up`
6.  run `docker compose exec -it django pipenv run python manage.py createsuperuser --no-input` to create user
7.  go to `localhost:8080`
8.  create a blockchain and link it to created node (read `Setting up a blockchain`)

# Run explorer in production
1.  fill out the missing ENV variables in `.env.prod` file (secretkey + user's info)
2.  set `VUE_APP_BACKEND_URL` in `.env.production` file to backend api url eg. `https://explorer.com/api/`
3.  change data in `docker/nginx/conf.d/local.conf` (at least domain info)
4.  place certificates in `docker/nginx/certs/` folder and name them whatever they're named in `docker/nginx/conf.d/local.conf`
5.  insert ip/domain in `ALLOWED_HOSTS` variable in file `backend/settings/prod.py`
6.  go to project's main folder
7.  run `docker build -t grinnixos -f docker/nixos/Dockerfile .`
8.  run `docker run -it -v ${PWD}:/code grinnixos ./docker/nixos/init.sh`
9.  run `docker compose -f docker-compose.production.yml run --rm django pipenv run python manage.py migrate`
10.  run `docker compose -f docker-compose.production.yml run --rm django pipenv run python manage.py collectstatic --noinput`
11.  run `docker compose -f docker-compose.production.yml up`
12.  run `docker compose exec -it django pipenv run python manage.py createsuperuser --no-input` to create user

1.  run `nix-shell` to get in environment where you have build dependencies
2.  inside nix-shell run `yarn install` to install needed things to build gui part
2.  inside nix-shell run `yarn run build` which creates `dist_gui` folder
3.  close `nix-shell` (ctrl+d)
4.  edit `.env.production` to point to django location, eg. 'http://django:8000'
5.  run `docker compose -f docker-compose.production.yml up`


# Setting up a blockchain

Blockchain is connected to a node, which is a part of a specific node-group.
Node-groups are planned to be used in the future. Steps to add a blockchain:

1.  Create a node-group
2.  Create a node inside of a node-group. If node is on the same pc then set these values for node:
  -  Foreign API URL:
    +  mainnet: http://host.docker.internal:3413/v2/foreign
    +  testnet: http://host.docker.internal:13413/v2/foreign
  -  Foreign API username: if you don't know it then it's most likely `grin`
  -  Foreign API password:
    +  mainnet: located in ~/.grin/main/.foreign_api_secret
    +  testnet: located in ~/.grin/test/.foreign_api_secret
  Note that if the node is running on the same server then you can't reach it through `localhost`. Instead use `host.docker.internal`. example of localhost grin-node url: `http://host.docker.internal:3413/v2/foreign`
3.  Create a blockchain which is connected to the created node
4.  go to your node's config file and set:
  -  `block_accepted_url` to `http://localhost:8000/api/blockchains/testnet/accepted/` (if your node runs locally, otherwise change domain and protocol)
  -  `api_http_addr` to `0.0.0.0:3413"` (or limit connections more if you wish)
5.  click `bootstrap` to start syncing explorer's db with node's db

The latest block, supply and price updates when new data is be fetched by the backend.
Currently price is fetched only for the blockchain which is marked as `default` and it fetches btc value from tradeogre. You can change this by modifying `backend.api.helpers.default_fetch_price_fn` function.


# Logs
Logs (in json format) are kept in `explorer.log` file. If you have `jq` installed you can get more readable logs, eg: `cat explorer.log | jq '.' > formatted.log` and work with `formatted.log` file.

# Problems
-  When running `docker compose up` redis container fails with error:
    Bad file format reading the append only file: make a backup of your AOF file, then use ./redis-check-aof --fix <filename>
    Run command `docker compose run redis redis-check-aof --fix appendonly.aof` (or whatever file it complains about) and then try again. If it says that there's no such file then try prefixing file destination with `appendonlydir/`, so `docker compose run redis redis-check-aof --fix appendonlydir/appendonly.aof`.
-  Bootstraping will fail if node becomes unreachable, if you start it again it will continue where it left. If the node has been offline for some time then after it starts syncing it will spam explorer with new blocks which will cause "too many connections" problem (block fetching is currently not implemented through queue). To avoid spamming you can comment out `block_accepted_url` in node's config file, run the node, wait for it to sync, uncomment `block_accepted_url`, restart the node and then manually bootstrap it. If you don't want to do that then just wait until the spamming ends, but be aware that the spam might cause explorer response issues.
