from __future__ import unicode_literals
from pelican import signals, contents
from os import path
import logging
import yaml

log = logging.getLogger(__name__)

PROSE_FILE = '_config.yml'

valid_tags, valid_categories = set(), set()


def create_valid_sets(pelican):
    """ Create valid sets. """

    global valid_tags, valid_categories
    with open(path.join(pelican.settings['PATH'], "../", PROSE_FILE)) as f:
        stream = yaml.load(f)
        content = stream.get("prose", {}).get("metadata", {}).get("content")
        assert content, "Cannot parse categories/tags from _config.yml"

        def get_field(field):
            return [f for f in content if f["name"] == field][0]

        valid_tags = set([
            option["value"] for option in get_field("tags")["field"]["options"]
        ])
        valid_categories = set([
            option["value"] for option in get_field("category")["field"]["options"]
        ])

    log.debug('Valid categories: ' + str(valid_categories))
    log.debug('Valid tags: ' + str(valid_tags))


class NoCategoryException(Exception):
    pass


class NoTagsException(Exception):
    pass


def validate_tags_categories(generator, article):
    """
    Ensure all tags and categories used in articles are valid (i.e.
    present in content/{tags,categories}.txt).
    """
    if getattr(article, 'status', '') == 'draft':
        return  # Skip drafts
    try:
        # Ensure category is valid
        category = article.category.name
        if category not in valid_categories:
            log.error("{}: Invalid category '{}', or valid and missing in {}".format(
                article.get_relative_source_path(), category, PROSE_FILE))
    except (KeyError, AttributeError):
        raise NoCategoryException("Article is missing a category!")
    try:
        # Ensure tags are valid
        for tag in article.tags:
            if tag.name not in valid_tags:
                log.error("{}: Invalid tag '{}', or valid and missing in {}".format(
                    article.get_relative_source_path(), tag, PROSE_FILE))
    except (KeyError, AttributeError):
        raise NoTagsException("Article has no tags!")


def register():
    signals.content_object_init.connect(validate_tags_categories, sender=contents.Article)
    signals.initialized.connect(create_valid_sets)
