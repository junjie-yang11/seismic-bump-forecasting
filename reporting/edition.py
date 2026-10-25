"""Immutable presentation edition, distinct from the scientific source commit."""
EDITION_TAG = 'manuscript-2026-10-25'
REPOSITORY = 'https://github.com/junjie-yang11/seismic-bump-forecasting'


def edition_url(path):
    return REPOSITORY + '/blob/' + EDITION_TAG + '/' + path.lstrip('/')
