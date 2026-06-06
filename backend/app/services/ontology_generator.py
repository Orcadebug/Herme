"""
Ontology Generation Service
Interface 1: Analyze text content and generate entity and relationship type definitions suitable for social simulation
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction

logger = logging.getLogger(__name__)


def _to_pascal_case(name: str) -> str:
    """ PascalCase 'works_for' -> 'WorksFor', 'person' -> 'Person'"""
    #
    parts = re.split(r"[^a-zA-Z0-9]+", name)
    #  camelCase  'camelCase' -> ['camel', 'Case']
    words = []
    for part in parts:
        words.extend(re.sub(r"([a-z])([A-Z])", r"\1_\2", part).split("_"))
    #
    result = "".join(word.capitalize() for word in words if word)
    return result if result else "Unknown"


#
ONTOLOGY_SYSTEM_PROMPT = """You are an ontology-generation expert. Analyze source documents and the simulation requirement, then produce a compact JSON ontology for social simulation.

Return JSON only, with this shape:

```json
{
  "entity_types": [
    {
      "name": "PascalCase entity type name",
      "description": "Brief description",
      "attributes": [
        {
          "name": "snake_case_attribute_name",
          "type": "text",
          "description": "Attribute purpose"
        }
      ],
      "examples": ["example 1", "example 2"]
    }
  ],
  "edge_types": [
    {
      "name": "UPPER_SNAKE_CASE_RELATIONSHIP",
      "description": "Brief description",
      "source_targets": [
        {"source": "SourceEntity", "target": "TargetEntity"}
      ],
      "attributes": []
    }
  ],
  "analysis_summary": "Short explanation of the ontology choices"
}
```

Guidelines:
- Create about 10 entity types. Include a few general types such as Person and Organization, then add domain-specific types from the documents.
- Create 6 to 10 relationship types with clear source and target entity combinations.
- Keep each entity to 1 to 3 useful attributes. Do not include built-in fields such as name, uuid, group_id, created_at, or summary.
- Use English PascalCase for entity names, English UPPER_SNAKE_CASE for relationship names, and English snake_case for attribute names.
- Prefer types and relationships that help agents reason about roles, affiliations, opinions, conflicts, cooperation, responses, and events.
- Keep the ontology concise, useful, and grounded in the provided content.
"""


class OntologyGenerator:
    """


    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """


        Args:
            document_texts:
            simulation_requirement:
            additional_context:

        Returns:
            entity_types, edge_types
        """
        #
        user_message = self._build_user_message(
            document_texts, simulation_requirement, additional_context
        )

        lang_instruction = get_language_instruction()
        system_prompt = f"{ONTOLOGY_SYSTEM_PROMPT}\n\n{lang_instruction}\nIMPORTANT: Entity type names MUST be in English PascalCase (e.g., 'PersonEntity', 'MediaOrganization'). Relationship type names MUST be in English UPPER_SNAKE_CASE (e.g., 'WORKS_FOR'). Attribute names MUST be in English snake_case. Only description fields and analysis_summary should use the specified language above."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # LLM
        result = self.llm_client.chat_json(
            messages=messages, temperature=0.3, max_tokens=4096
        )

        #
        result = self._validate_and_process(result)

        return result

    #  LLM 5
    MAX_TEXT_LENGTH_FOR_LLM = 50000

    def _build_user_message(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str],
    ) -> str:
        """"""

        #
        combined_text = "\n\n---\n\n".join(document_texts)
        original_length = len(combined_text)

        # 5LLM
        if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
            combined_text = combined_text[: self.MAX_TEXT_LENGTH_FOR_LLM]
            combined_text += f"\n\n...({original_length}{self.MAX_TEXT_LENGTH_FOR_LLM})..."

        message = f"""##

{simulation_requirement}

##

{combined_text}
"""

        if additional_context:
            message += f"""
##

{additional_context}
"""

        message += """


****
1. 10
2. 2Person Organization
3. 8
4.
5.  nameuuidgroup_id  full_nameorg_name
"""

        return message

    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """"""

        #
        if "entity_types" not in result:
            result["entity_types"] = []
        if "edge_types" not in result:
            result["edge_types"] = []
        if "analysis_summary" not in result:
            result["analysis_summary"] = ""

        #
        #  PascalCase  edge  source_targets
        entity_name_map = {}
        for entity in result["entity_types"]:
            #  entity name  PascalCaseZep API
            if "name" in entity:
                original_name = entity["name"]
                entity["name"] = _to_pascal_case(original_name)
                if entity["name"] != original_name:
                    logger.warning(
                        f"Entity type name '{original_name}' auto-converted to '{entity['name']}'"
                    )
                entity_name_map[original_name] = entity["name"]
            if "attributes" not in entity:
                entity["attributes"] = []
            if "examples" not in entity:
                entity["examples"] = []
            # description100
            if len(entity.get("description", "")) > 100:
                entity["description"] = entity["description"][:97] + "..."

        #
        for edge in result["edge_types"]:
            #  edge name  SCREAMING_SNAKE_CASEZep API
            if "name" in edge:
                original_name = edge["name"]
                edge["name"] = original_name.upper()
                if edge["name"] != original_name:
                    logger.warning(
                        f"Edge type name '{original_name}' auto-converted to '{edge['name']}'"
                    )
            #  source_targets  PascalCase
            for st in edge.get("source_targets", []):
                if st.get("source") in entity_name_map:
                    st["source"] = entity_name_map[st["source"]]
                if st.get("target") in entity_name_map:
                    st["target"] = entity_name_map[st["target"]]
            if "source_targets" not in edge:
                edge["source_targets"] = []
            if "attributes" not in edge:
                edge["attributes"] = []
            if len(edge.get("description", "")) > 100:
                edge["description"] = edge["description"][:97] + "..."

        # Zep API  10  10
        MAX_ENTITY_TYPES = 10
        MAX_EDGE_TYPES = 10

        #  name
        seen_names = set()
        deduped = []
        for entity in result["entity_types"]:
            name = entity.get("name", "")
            if name and name not in seen_names:
                seen_names.add(name)
                deduped.append(entity)
            elif name in seen_names:
                logger.warning(
                    f"Duplicate entity type '{name}' removed during validation"
                )
        result["entity_types"] = deduped

        #
        person_fallback = {
            "name": "Person",
            "description": "Any individual person not fitting other specific person types.",
            "attributes": [
                {
                    "name": "full_name",
                    "type": "text",
                    "description": "Full name of the person",
                },
                {"name": "role", "type": "text", "description": "Role or occupation"},
            ],
            "examples": ["ordinary citizen", "anonymous netizen"],
        }

        organization_fallback = {
            "name": "Organization",
            "description": "Any organization not fitting other specific organization types.",
            "attributes": [
                {
                    "name": "org_name",
                    "type": "text",
                    "description": "Name of the organization",
                },
                {
                    "name": "org_type",
                    "type": "text",
                    "description": "Type of organization",
                },
            ],
            "examples": ["small business", "community group"],
        }

        #
        entity_names = {e["name"] for e in result["entity_types"]}
        has_person = "Person" in entity_names
        has_organization = "Organization" in entity_names

        #
        fallbacks_to_add = []
        if not has_person:
            fallbacks_to_add.append(person_fallback)
        if not has_organization:
            fallbacks_to_add.append(organization_fallback)

        if fallbacks_to_add:
            current_count = len(result["entity_types"])
            needed_slots = len(fallbacks_to_add)

            #  10
            if current_count + needed_slots > MAX_ENTITY_TYPES:
                #
                to_remove = current_count + needed_slots - MAX_ENTITY_TYPES
                #
                result["entity_types"] = result["entity_types"][:-to_remove]

            #
            result["entity_types"].extend(fallbacks_to_add)

        #
        if len(result["entity_types"]) > MAX_ENTITY_TYPES:
            result["entity_types"] = result["entity_types"][:MAX_ENTITY_TYPES]

        if len(result["edge_types"]) > MAX_EDGE_TYPES:
            result["edge_types"] = result["edge_types"][:MAX_EDGE_TYPES]

        return result

    def generate_python_code(self, ontology: Dict[str, Any]) -> str:
        """
        Pythonontology.py

        Args:
            ontology:

        Returns:
            Python
        """
        code_lines = [
            '"""',
            "",
            "Hermes",
            '"""',
            "",
            "from pydantic import Field",
            "from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel",
            "",
            "",
            "# ==============  ==============",
            "",
        ]

        #
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            desc = entity.get("description", f"A {name} entity.")

            code_lines.append(f"class {name}(EntityModel):")
            code_lines.append(f'    """{desc}"""')

            attrs = entity.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f"    {attr_name}: EntityText = Field(")
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f"        default=None")
                    code_lines.append(f"    )")
            else:
                code_lines.append("    pass")

            code_lines.append("")
            code_lines.append("")

        code_lines.append("# ==============  ==============")
        code_lines.append("")

        #
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            # PascalCase
            class_name = "".join(word.capitalize() for word in name.split("_"))
            desc = edge.get("description", f"A {name} relationship.")

            code_lines.append(f"class {class_name}(EdgeModel):")
            code_lines.append(f'    """{desc}"""')

            attrs = edge.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f"    {attr_name}: EntityText = Field(")
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f"        default=None")
                    code_lines.append(f"    )")
            else:
                code_lines.append("    pass")

            code_lines.append("")
            code_lines.append("")

        #
        code_lines.append("# ==============  ==============")
        code_lines.append("")
        code_lines.append("ENTITY_TYPES = {")
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            code_lines.append(f'    "{name}": {name},')
        code_lines.append("}")
        code_lines.append("")
        code_lines.append("EDGE_TYPES = {")
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            class_name = "".join(word.capitalize() for word in name.split("_"))
            code_lines.append(f'    "{name}": {class_name},')
        code_lines.append("}")
        code_lines.append("")

        # source_targets
        code_lines.append("EDGE_SOURCE_TARGETS = {")
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            source_targets = edge.get("source_targets", [])
            if source_targets:
                st_list = ", ".join(
                    [
                        f'{{"source": "{st.get("source", "Entity")}", "target": "{st.get("target", "Entity")}"}}'
                        for st in source_targets
                    ]
                )
                code_lines.append(f'    "{name}": [{st_list}],')
        code_lines.append("}")

        return "\n".join(code_lines)
