# pygeoapi

Provides WFS3.0

## Running pygeoapi for GLOSIS development

```bash
cd pygeoapi
pip3 install -e .
#any path to pygeoapi-config.yml
export PYGEOAPI_CONFIG=/home/jorge/git/glosis-prototype/pygeoapi/pygeoapi-config.yml
pygeoapi serve
```

## Example requests


```bash
# feature collection metadata
curl http://localhost:5000/?f=json
# conformance
curl http://localhost:5000/conformance?f=json
# feature collection

curl http://localhost:5000/collections/soil_profiles?f=json
# feature collection limit 100
curl http://localhost:5000/collections/soil_profiles/items?f=json
# feature
curl http://localhost:5000/collections/soil_profiles/items/88208607-b776-4580-93a9-731805185578?f=json
# number of hits
curl http://localhost:5000/collections/soil_profiles/items?resulttype=hits&f=json

```

## Docker

Docker is in folder:

- Simple


Docker images have the following settings:
- Alpine edge OS
- spatialite compilation 4.3.0a
- pygeoapi running on port **5000**  


### Simple (image)

Simple sub folder contains a simple implementation of pygeoapi with out ES (only: GeoJSON, CSV and SQLite provider).
```
cd docker/simple
docker build -t pygeoapi:latest .
docker run -p5000:5000 -v /pygeoapi/tests/data pygeoapi:latest
```



### Testing code 

Unit tests are run using pytest on the top project folder:

```
pytest tests
```

Environment variables are set on file `pytest.ini`
