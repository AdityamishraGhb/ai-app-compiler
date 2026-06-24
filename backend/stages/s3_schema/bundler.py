"""
Stage 3 — Schema Generation: Bundler

Runs the 4 independent generators in parallel and aggregates their results into a SchemaBundle.
"""

import asyncio
import logging
from typing import List

from backend.llm.client import GeminiClient
from backend.schemas import (
    ArchitectureBlueprint,
    SchemaBundle,
)
from backend.stages.s3_schema.ui_schema import UISchemaGenerator
from backend.stages.s3_schema.api_schema import APISchemaGenerator
from backend.stages.s3_schema.db_schema import DatabaseSchemaGenerator
from backend.stages.s3_schema.auth_schema import AuthSchemaGenerator

logger = logging.getLogger(__name__)

class SchemaBundler:
    """Orchestrates Stage 3: parallel schema generation."""

    def __init__(self, llm_client: GeminiClient):
        self.llm_client = llm_client
        self.ui_gen = UISchemaGenerator(llm_client)
        self.api_gen = APISchemaGenerator(llm_client)
        self.db_gen = DatabaseSchemaGenerator(llm_client)
        self.auth_gen = AuthSchemaGenerator(llm_client)

    async def execute(self, blueprint: ArchitectureBlueprint) -> SchemaBundle:
        logger.info("Executing Stage 3: Schema Bundle Generation (Parallel)")

        # Run all 4 generators concurrently
        ui_schema, api_schema, db_schema, auth_schema = await asyncio.gather(
            self.ui_gen.execute(blueprint),
            self.api_gen.execute(blueprint),
            self.db_gen.execute(blueprint),
            self.auth_gen.execute(blueprint),
        )

        bundle = SchemaBundle(
            ui=ui_schema,
            api=api_schema,
            database=db_schema,
            auth=auth_schema
        )

        logger.info("Aggregated SchemaBundle successfully.")
        return bundle

