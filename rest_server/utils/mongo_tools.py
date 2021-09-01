"""General tools for interacting with a MongoDB."""

from typing import Any, Callable, Dict

from bson.objectid import ObjectId  # type: ignore[import]

from ..databases import columns


class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""


class Mongofier:
    """Tools for moving/transforming data in/out of a MongoDB."""

    @staticmethod
    def mongofy_key_name(key: str) -> str:
        """Transform string to mongo-friendly."""
        return key.replace(".", ";")

    @staticmethod
    def demongofy_key_name(key: str) -> str:
        """Transform string from mongo-friendly to human-friendly."""
        return key.replace(";", ".")

    @staticmethod
    def _mongofy_every_key(dicto: Dict[str, Any]) -> Dict[str, Any]:
        """Transform all keys to mongo-friendly, recursively, IN-PLACE."""
        return Mongofier._transform_every_key(dicto, Mongofier.mongofy_key_name)

    @staticmethod
    def _demongofy_every_key(dicto: Dict[str, Any]) -> Dict[str, Any]:
        """Transform all keys to human-friendly, recursively, IN-PLACE."""
        return Mongofier._transform_every_key(dicto, Mongofier.demongofy_key_name)

    @staticmethod
    def _transform_every_key(
        dicto: Dict[str, Any], key_func: Callable[[str], str]
    ) -> Dict[str, Any]:
        """Change every key, IN-PLACE."""
        # first get the keys right
        for key in list(dicto.keys()):
            dicto[key_func(key)] = dicto.pop(key)

        # then get any nested dicts
        for key, val in list(dicto.items()):
            if isinstance(val, dict):
                dicto[key] = Mongofier._transform_every_key(val, key_func)

        return dicto

    @staticmethod
    def mongofy_document(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform doc to mongo-friendly, recursively, IN-PLACE."""
        doc = Mongofier._mongofy_every_key(doc)

        if doc.get(columns.ID):
            doc[columns.ID] = ObjectId(doc[columns.ID])  # cast ID

        return doc

    @staticmethod
    def demongofy_document(doc: Dict[str, Any], str_id: bool = True) -> Dict[str, Any]:
        """Transform doc to human-friendly, recursively, IN-PLACE."""

        def no_nones(dicto: Dict[str, Any]) -> Dict[str, Any]:
            """Recursively replace `None`s with ''."""
            for key in dicto.keys():
                if dicto[key] is None:
                    dicto[key] = ""
            # recurse over sub-dicts
            for key, val in list(dicto.items()):
                if isinstance(val, dict):
                    dicto[key] = no_nones(val)
            return dicto

        doc = no_nones(doc)
        doc = Mongofier._demongofy_every_key(doc)
        if str_id:
            doc[columns.ID] = str(doc[columns.ID])  # cast ID

        return doc
