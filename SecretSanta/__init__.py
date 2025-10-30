"""Package entry point for the SecretSanta implementation.

This module re-exports the public names from the in-package implementation
module `SecretSanta.SecretSanta` so tests and code that import
`from SecretSanta import ...` continue to work.

Public exports for the SecretSanta package.

We explicitly re-export the symbols that tests and external code depend on.
Keeping an explicit __all__ avoids leaking internal helpers accidentally.
"""
from .SecretSanta import (
    bot,
    secretsanta,
    exclude,
    remove_exclusion,
    list_exclusions,
    circle,
    circle_exclude,
    send_assignments,
    _rotate_list,
    _make_assignments,
    ExclusionStore,
    exclusion_store,
)


__all__ = [
	'bot',
	'secretsanta',
	'exclude',
	'remove_exclusion',
	'list_exclusions',
	'circle',
	'circle_exclude',
	'send_assignments',
	'_rotate_list',
	'_make_assignments',
	'ExclusionStore',
	'exclusion_store',
]
