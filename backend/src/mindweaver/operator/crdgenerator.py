#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""
Script to generate Kubernetes CRDs from Pydantic models
"""

import json
import yaml
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
import sys
import importlib
import argparse
import enum

class StatusEnum(enum.StrEnum):

    pending = 'Pending'
    running = 'Running'
    failed = 'Failed'

class Status(BaseModel):

    phase: StatusEnum
    message: str


class KubernetesCRDGenerator:
    """Generator for Kubernetes CRDs from Pydantic models"""
    
    def __init__(self, group: str, version: str = "v1", kind: str = None):
        self.group = group
        self.version = version
        self.kind = kind

    def get_schema_properties(self, model_class: type[BaseModel]):
        # Generate JSON schema from Pydantic model
        json_schema = model_class.model_json_schema()
        
        # Extract definitions for resolving $refs
        definitions = json_schema.get('$defs', {})
        
        # Resolve all $ref references
        resolved_schema = self._resolve_refs(json_schema, definitions)
        
        # Clean the schema for Kubernetes compatibility
        schema = self._clean_json_schema(resolved_schema)

        # Convert anyOf with null to nullable fields
        schema = self._convert_anyof_to_nullable(schema)

        
        # Remove the root level properties we don't want in spec
        if 'properties' in schema:
            properties = schema['properties']
        else:
            properties = {}

        return {
            'required': schema.get('required', []),
            'properties': properties,
        }

    def _resolve_refs(self, schema: Dict[str, Any], definitions: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve $ref references by inlining the referenced schemas"""
        if isinstance(schema, dict):
            if '$ref' in schema:
                # Extract the reference path (e.g., '#/$defs/Contact' -> 'Contact')
                ref_path = schema['$ref']
                if ref_path.startswith('#/$defs/'):
                    def_name = ref_path[8:]  # Remove '#/$defs/'
                    if def_name in definitions:
                        # Recursively resolve the referenced schema
                        resolved = self._resolve_refs(definitions[def_name], definitions)
                        return resolved
                    else:
                        # If definition not found, return a generic object
                        return {"type": "object"}
                return schema
            else:
                # Recursively process all values in the dictionary
                resolved = {}
                for key, value in schema.items():
                    resolved[key] = self._resolve_refs(value, definitions)
                return resolved
        elif isinstance(schema, list):
            # Process list items
            return [self._resolve_refs(item, definitions) for item in schema]
        else:
            return schema
    
    def _clean_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up JSON schema to be Kubernetes CRD compatible"""
        if isinstance(schema, dict):
            # Remove unsupported fields
            cleaned = {}
            for key, value in schema.items():
                if key not in ['title', 'examples', 'default']:
                    if key == 'properties':
                        cleaned[key] = {k: self._clean_json_schema(v) for k, v in value.items()}
                    elif key == 'items':
                        cleaned[key] = self._clean_json_schema(value)
                    elif key == 'additionalProperties':
                        if isinstance(value, dict):
                            cleaned[key] = self._clean_json_schema(value)
                        else:
                            cleaned[key] = value
                    else:
                        cleaned[key] = value
            return cleaned
        return schema
    
    def _convert_anyof_to_nullable(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(schema, dict):
            for key, value in list(schema.items()):
                # Detect pattern: anyOf=[{"type": X}, {"type": "null"}]
                if key == "anyOf" and isinstance(value, list):
                    types = {v.get("type") for v in value if isinstance(v, dict)}
                    if "null" in types and len(types) == 2:
                        non_null_type = [t for t in types if t != "null"][0]
                        schema.pop("anyOf")
                        schema["type"] = non_null_type
                        schema["nullable"] = True
                else:
                    self._convert_anyof_to_nullable(value)
        elif isinstance(schema, list):
            for item in schema:
                self._convert_anyof_to_nullable(item)
        return schema
    
    
    def generate_crd(self, model_class: BaseModel, 
                    plural: str = None, 
                    singular: str = None,
                    scope: str = "Namespaced",
                    short_names: List[str] = None) -> Dict[str, Any]:
        """Generate CRD from Pydantic model"""
        
        kind = self.kind or model_class.__name__
        plural = plural or f"{kind.lower()}s"
        singular = singular or kind.lower()
        
        spec_properties = self.get_schema_properties(model_class)
        status_properties = self.get_schema_properties(Status)
        
        # Build the CRD
        crd = {
            "apiVersion": "apiextensions.k8s.io/v1",
            "kind": "CustomResourceDefinition",
            "metadata": {
                "name": f"{plural}.{self.group}"
            },
            "spec": {
                "group": self.group,
                "versions": [{
                    "name": self.version,
                    "served": True,
                    "storage": True,
                    "schema": {
                        "openAPIV3Schema": {
                            "type": "object",
                            "properties": {
                                "apiVersion": {
                                    "type": "string"
                                },
                                "kind": {
                                    "type": "string"
                                },
                                "metadata": {
                                    "type": "object"
                                },
                                "spec": {
                                    "type": "object",
                                    "properties": spec_properties['properties'],
                                    "required": spec_properties["required"]
                                },
                                "status": {
                                    "type": "object",
                                    "properties": status_properties['properties'],
                                    "x-kubernetes-preserve-unknown-fields": True
                                }
                            }
                        }
                    },
                    "additionalPrinterColumns": [
                        {
                        "name": "Status",
                        "type": "string",
                        "description": "Cluster status",
                        "jsonPath": ".status.phase"
                        },
                        {
                        "name": "Message",
                        "type": "string",
                        "description": "Status message",
                        "jsonPath": ".status.message"
                        }
                    ]
                }],
                "scope": scope,
                "names": {
                    "plural": plural,
                    "singular": singular,
                    "kind": kind
                    },
            }
        }

        # Add short names if provided
        if short_names:
            crd["spec"]["names"]["shortNames"] = short_names
            
        return crd
    
    def save_crd(self, crd: Dict[str, Any], filename: str, format: str = "yaml"):
        """Save CRD to file"""
        with open(filename, 'w') as f:
            if format.lower() == "json":
                json.dump(crd, f, indent=2)
            else:
                yaml.dump(crd, f, default_flow_style=False, sort_keys=False)


def import_class(class_path: str):
    """Import a class from module.submodule:Class format"""
    try:
        module_path, class_name = class_path.rsplit(':', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ValueError, ImportError, AttributeError) as e:
        print(f"Error importing class '{class_path}': {e}")
        sys.exit(1)

def main():
    """Main function to generate CRDs with command line arguments"""
    
    parser = argparse.ArgumentParser(
        description="Generate Kubernetes CRDs from Pydantic models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c mymodule.models:DatabaseSpec
  %(prog)s -c mypackage.submodule:MyModel --group example.com --version v2
        """
    )
    
    parser.add_argument(
        '-c', '--class',
        dest='class_path',
        required=True,
        help='Pydantic class in format module.submodule:ClassName'
    )
    
    parser.add_argument(
        '--group',
        required=True,
        help='API group for the CRD'
    )
    
    parser.add_argument(
        '--version',
        default='v1',
        help='API version for the CRD (default: v1)'
    )
    
    parser.add_argument(
        '--kind',
        help='Kind name for the CRD (default: class name)'
    )
    
    parser.add_argument(
        '--plural',
        help='Plural name for the CRD (default: kind + s)'
    )
    
    parser.add_argument(
        '--singular',
        help='Singular name for the CRD (default: lowercase kind)'
    )
    
    parser.add_argument(
        '--short-names',
        nargs='*',
        help='Short names for the CRD'
    )
    
    parser.add_argument(
        '--scope',
        choices=['Namespaced', 'Cluster'],
        default='Namespaced',
        help='Scope of the CRD (default: Namespaced)'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        help='Output file name (default: <plural>-crd.yaml)'
    )
    
    parser.add_argument(
        '--format',
        choices=['yaml', 'json'],
        default='yaml',
        help='Output format (default: yaml)'
    )
    
    args = parser.parse_args()
    
    # Import the specified class
    model_class = import_class(args.class_path)
    
    # Verify it's a Pydantic model
    if not issubclass(model_class, BaseModel):
        print(f"Error: {args.class_path} is not a Pydantic BaseModel")
        sys.exit(1)
    
    # Create generator
    generator = KubernetesCRDGenerator(
        group=args.group,
        version=args.version,
        kind=args.kind
    )
    
    # Generate CRD
    crd = generator.generate_crd(
        model_class,
        plural=args.plural,
        singular=args.singular,
        scope=args.scope,
        short_names=args.short_names
    )
    
    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        plural = args.plural or f"{(args.kind or model_class.__name__).lower()}s"
        extension = 'json' if args.format == 'json' else 'yaml'
        output_file = f"{plural}-crd.{extension}"
    
    # Save CRD
    generator.save_crd(crd, output_file, format=args.format)
    
    print(f"Generated CRD: {output_file}")
    
    # Print summary
    kind = args.kind or model_class.__name__
    plural = args.plural or f"{kind.lower()}s"
    print(f"Kind: {kind}")
    print(f"Group: {args.group}")
    print(f"Version: {args.version}")
    print(f"Plural: {plural}")

if __name__ == "__main__":
    main()
