"""Test that bandit works."""

# # Uncomment/Comment out everything below to add/remove a bandit
# # check which will fail

# from typing import Any

# import yaml


# class YamlOps:
#     """Perform operations on YAML."""

#     @classmethod
#     def convert_to_yaml(cls, yaml_dict: dict[str, str]) -> Any:
#         """Serialize a Dict[str, str] to YAML string."""
#         return yaml.dump(yaml_dict)

#     @classmethod
#     def convert_from_yaml(cls, yaml_string: str) -> Any:
#         """Convert a YAML string to YAML object."""
#         return yaml.load(yaml_string, yaml.Loader)


# yaml_serialized = YamlOps.convert_to_yaml(
#     {
#         "layout": "post",
#         "title": "Getting Started with Bandit",
#         "date": "2017-01-16",
#         "author": "Ian Cordasco",
#     }
# )
# parsed_yaml = YamlOps.convert_from_yaml(yaml_string=yaml_serialized)
