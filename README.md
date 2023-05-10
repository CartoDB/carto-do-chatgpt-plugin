## Deploy

Start the services:

```
OPENAI_API_KEY=... docker compose up
```

Populate the vector database (make sure to have the needed JSON files):

```
cd scripts
OPENAI_API_KEY=... DATASTORE=weaviate ./populate.sh
```

POST the API:

```
curl --request POST \
  --url http://localhost:8081/ask \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' \
  --json '{"queries":[{"query":"is there a way to enrich data with real state data in Madrid"}]}'
```
