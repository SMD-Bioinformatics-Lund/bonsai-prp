"""Parse metadata passed to pipeline."""
from ..models.metadata import SoupVersion
from typing import List
import json


def get_database_info(process_metadata) -> List[SoupVersion]:
    db_info = []
    for soup in process_metadata:
        dbs = json.load(soup)
        if isinstance(dbs, (list, tuple)):
            for db in dbs:
                db_info.append(SoupVersion(**db))
        else:
            db_info.append(SoupVersion(**dbs))
    return db_info