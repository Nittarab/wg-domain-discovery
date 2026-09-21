# Domain Discovery Working Group

[Read the technical proposal](proposals/openapi-publication/proposal.md).

The proposal shows exactly what to publish at `/.well-known/x402`, where to add the proposed `x-x402` annotation in OpenAPI, and how direct generation and overlay composition produce the same result.

Examples use selected real StableTravel and StableStudio operations, with their source input/output schemas. The entry files and payment annotations are proposals, not deployed merchant features.

Generate and check the final example files with Python 3 (no dependencies):

```sh
python3 proposals/openapi-publication/check_examples.py --write
```

Read the generated files under `proposals/openapi-publication/build/`. The optional annotation schema is [x-x402.schema.json](proposals/openapi-publication/x-x402.schema.json). The offline check is not a general OpenAPI or Overlay validator.

[Example sources and verification](proposals/openapi-publication/examples/README.md).
