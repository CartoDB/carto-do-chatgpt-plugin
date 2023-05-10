import openai


class PromptGenerator:
    def __init__(self):
        self.system = (
            "You are a helpful assistant for CARTO users looking for datasets. "
            "You must provide links to relevant datasets for a query in the Spatial Data Catalog. "
            "Rely on the information provided from the catalog.  "
            "Use Markdown formatting in the output message. "
            "Every time you mention a dataset or variable, you must include a Markdown link in the format `[<name or ID>](<URL>)`. "
            "After answering, feel free to brainstorm if the question asks for advice or counsel. "
        )

        self.message_template = (
            "## Start of Catalog:\n"
            "{sample}\n"
            "## End of Catalog.\n\n"
            "Question: {message}"
        )

    def _format_context(self, response):
        print(response)
        print()
        return "\n\n".join(
            [
                self._format_dataset(dataset)
                for dataset in response.results
            ]
        )

    def _format_dataset(self, dataset):
        variables = "\n".join(
            [self._format_variable(v) for v in dataset.metadata.variables]
        )
        print(variables)
        return "\n".join(
            [
                f"- ID: `{dataset.id}`",
                f"- URL: https://carto.com/spatial-data-catalog/browser/dataset/{dataset.metadata.slug}",
                f"- Description: {dataset.text}",
                f"- Country: {dataset.metadata.country}",
                f"- Provider: {dataset.metadata.provider}",
                f"- License: {dataset.metadata.license}",
                f"- Spatial aggregation: {dataset.metadata.spatial_aggregation}",
                f"- Temporal aggregation: {dataset.metadata.temporal_aggregation}",
                f"- Placetype: {dataset.metadata.placetype}",
                f"- Variables:\n{variables}",
            ]
        )

    def _format_variable(self, variable):
        return f"\t- `{variable['column_name']}` ({variable['db_type']}): {variable['text']}"

    def ask(self, user_input, context, verbose=False):
        context = self._format_context(context)
        message = self.message_template.format(sample=context, message=user_input)

        if verbose:
            print("FULL:\n", message)

        response = openai.ChatCompletion.create(
            # model="gpt-4",
            model="gpt-3.5-turbo",
            # temperature=0,  # uncomment to make the answers more consistent
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user", "content": self.system + "\n\n" + message},
            ],
        )

        print(response.choices[0].message.content)
        return response.choices[0].message.content
