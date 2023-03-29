dataset_schema = {
    "class": "DODataset",
    "description": "A dataset in the Carto Spatial Data Catalog",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "ada",
            "modelVersion": "002",
            "type": "text"
        }
    },
    "properties": [
        {
            "name": "chunk_id",
            "dataType": ["string"],
            "description": "The chunk id",
        },
        {
            "name": "document_id",
            "dataType": ["string"],
            "description": "The document id",
        },
        {
            "name": "text",
            "dataType": ["text"],
            "description": "The chunk's text",
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            },
        },
        {
            "name": "source",
            "dataType": ["string"],
            "description": "The source of the data",
        },
        {
            "name": "source_id",
            "dataType": ["string"],
            "description": "The source id",
        },
        {
            "name": "slug",
            "dataType": ["string"],
            "description": "The slug of the document in the catalog",
        },
        {
            "name": "geography",
            "dataType": ["string"],
            "description": "The geography of the document",
        },
        {
            "name": "category",
            "dataType": ["string"],
            "description": "The category of the document",
        },
        {
            "name": "country",
            "dataType": ["string"],
            "description": "The country of the document",
        },
        {
            "name": "provider",
            "dataType": ["string"],
            "description": "The provider of the document",
        },
        {
            "name": "license",
            "dataType": ["string"],
            "description": "The license of the document",
        },
        {
            "name": "update_frequency",
            "dataType": ["string"],
            "description": "The update frequency of the document",
        },
        {
            "name": "spatial_agg",
            "dataType": ["string"],
            "description": "The spatial aggregation of the document",
        },
        {
            "name": "temporal_agg",
            "dataType": ["string"],
            "description": "The temporal aggregation of the document",
        },
        {
            "name": "placetype",
            "dataType": ["string"],
            "description": "The placetype of the document",
        },
        {
            "name": "variables",
            "dataType": ["DOVariable"],
            "description": "The IDs of the DOVariables contained in it",
            # "cardinality": "many",
        },
    ],
}


variable_schema = {
    "class": "DOVariable",
    "description": "A variable in the Carto Spatial Data Catalog",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "ada",
            "modelVersion": "002",
            "type": "text"
        }
    },
    "properties": [
        {
            "name": "chunk_id",
            "dataType": ["string"],
            "description": "The chunk id",
        },
        {
            "name": "document_id",
            "dataType": ["string"],
            "description": "The document id",
        },
        {
            "name": "text",
            "dataType": ["text"],
            "description": "The chunk's text",
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            },
        },
        {
            "name": "source",
            "dataType": ["string"],
            "description": "The source of the data",
        },
        {
            "name": "source_id",
            "dataType": ["string"],
            "description": "The source id",
        },
        {
            "name": "slug",
            "dataType": ["string"],
            "description": "The slug of the variable in the catalog",
        },
        {
            "name": "column_name",
            "dataType": ["string"],
            "description": "The name of the column within the dataset",
        },
        {
            "name": "db_type",
            "dataType": ["string"],
            "description": "The data type of the variable",
        },
        {
            "name": "dataset_id",
            "dataType": ["DODataset"],
            "description": "The ID of the DODataset it belongs to",
            # "cardinality": "one",
        },
    ],
}

schema = {
    "type": "docs",
    "classes": [
        dataset_schema,
        variable_schema,
    ],
}
