# pylint: disable=wrong-import-position

if __name__ == "__main__":
    from gevent import monkey

    monkey.patch_all(thread=False, select=False)

import argparse
import logging
import os

from pyramid.paster import bootstrap

from openprocurement.audit.api.database import COLLECTION_CLASSES

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def run(env, args):
    migration_name = os.path.basename(__file__).split(".")[0]

    logger.info("Starting migration: %s", migration_name)

    collections = {
        "monitoring": env["registry"].mongodb.monitoring.collection,
        "inspection": env["registry"].mongodb.inspection.collection,
        "request": env["registry"].mongodb.request.collection,
    }

    log_every = 100000
    total_count = 0

    for collection_name, collection in collections.items():
        logger.info(f"Updating {collection_name}s with owner field")
        count = 0
        
        filter_query = {"owner": {"$exists": False}}

        total_docs = collection.count_documents(filter_query)
        logger.info(f"Found {total_docs} {collection_name}s to update")

        cursor = collection.find(
            filter_query,
            no_cursor_timeout=True,
        )
        cursor.batch_size(args.b)
        try:
            for document in cursor:
                collection.update_one(
                    {"_id": document["_id"]},
                    {"$set": {"owner": args.owner}},
                )
                count += 1
                if count % log_every == 0:
                    logger.info(f"Updating {collection_name}s with owner field: updated {count} {collection_name}s")
        finally:
            cursor.close()

        logger.info(f"Updating {collection_name}s with owner field finished: updated {count} {collection_name}s")
        total_count += count

    logger.info(f"Total documents updated: {total_count}")
    logger.info(f"Successful migration: {migration_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        required=True,
        help="Path to service.ini file",
    )
    parser.add_argument(
        "-b",
        type=int,
        default=1000,
        help=(
            "Limits the number of documents returned in one batch. Each batch requires a round trip to the server."
        ),
    )
    parser.add_argument(
        "--owner",
        type=str,
        default="prz",
        help="Owner of the documents",
    )
    args = parser.parse_args()
    env = bootstrap(args.p)
    try:
        run(env, args)
    finally:
        env['closer']()