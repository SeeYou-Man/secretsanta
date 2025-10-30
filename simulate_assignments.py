"""Simulate Secret Santa assignments without sending DMs.

This script uses the same rotation-based derangement approach used by
`SecretSanta.py` to demonstrate and validate assignments locally.

Usage:
  python simulate_assignments.py
  python simulate_assignments.py --names Alice,Bob,Carol
  python simulate_assignments.py --count 6
"""
import random
import argparse
import sys
from math import gcd


def rotate_list(lst, k):
    n = len(lst)
    return [lst[(i + k) % n] for i in range(n)]


def make_assignments(members, exclusions=None, single_cycle=False, max_attempts=2000):
    """Return list of (giver, receiver) tuples such that nobody gets themselves
    and every receiver is unique. Supports exclusions and single-cycle mode.
 
    Args:
        members: list of names/IDs
        exclusions: set of frozenset(id1, id2) pairs to avoid
        single_cycle: if True, ensure output is one big cycle
        max_attempts: how many random attempts before giving up
    """
    n = len(members)
    if n < 2:
        raise ValueError('Need at least 2 members')

    exclusions = exclusions or set()

    def valid_with_receivers(receivers):
        for i, receiver in enumerate(receivers):
            giver = members[i]
            if giver == receiver:  # no self-assignment
                return False
            if frozenset((giver, receiver)) in exclusions:  # respect exclusions
                return False
        return True

    if single_cycle:
        # Find k where gcd(k,n)==1 to ensure single cycle
        ks = [k for k in range(1, n) if gcd(k, n) == 1]
        random.shuffle(ks)
        for k in ks:
            receivers = rotate_list(members, k)
            if valid_with_receivers(receivers):
                return list(zip(members, receivers))
        return None  # no valid single-cycle assignment possible

    # Try random shuffles for non-cycle case
    receivers = members.copy()
    for _ in range(max_attempts):
        random.shuffle(receivers)
        if valid_with_receivers(receivers):
            return list(zip(members, receivers))
    return None  # couldn't find valid assignment


def validate_assignments(assignments):
    givers = [g for g, _ in assignments]
    receivers = [r for _, r in assignments]
    # Nobody receives themselves
    for g, r in assignments:
        if g == r:
            return False, 'A giver received themself'
    # Receivers unique
    if len(set(receivers)) != len(receivers):
        return False, 'Receivers are not unique'
    # Same set
    if set(givers) != set(receivers):
        return False, 'Receiver set does not match giver set'
    return True, 'OK'


def main():
    p = argparse.ArgumentParser(description='Simulate Secret Santa assignments')
    p.add_argument('--names', help='Comma-separated list of names to use')
    p.add_argument('--count', type=int, help='Generate N sample names (Name1..NameN)')
    p.add_argument('--exclude', help='Comma-separated pairs to exclude (name1:name2,name3:name4)')
    p.add_argument('--circle', action='store_true', help='Force single-cycle assignment')
    args = p.parse_args()

    if args.names:
        members = [n.strip() for n in args.names.split(',') if n.strip()]
    elif args.count:
        members = [f'Person{i+1}' for i in range(args.count)]
    else:
        members = ['Alice', 'Bob', 'Charlie', 'David', 'Elise']

    # Parse exclusions
    exclusions = set()
    if args.exclude:
        for pair in args.exclude.split(','):
            try:
                name1, name2 = pair.split(':')
                if name1 in members and name2 in members:
                    exclusions.add(frozenset((name1.strip(), name2.strip())))
            except ValueError:
                print(f'Warning: Skipping invalid exclusion pair "{pair}"')

    print(f'Participants: {members}')
    if exclusions:
        print('\nExclusions:')
        for pair in exclusions:
            n1, n2 = pair
            print(f'  {n1} ↔ {n2}')

    assignments = make_assignments(members, exclusions=exclusions, single_cycle=args.circle)
    if assignments is None:
        print('\nNo valid assignment possible with these constraints!')
        sys.exit(1)

    ok, reason = validate_assignments(assignments)
    if not ok:
        print('Validation failed:', reason)
        sys.exit(2)

    print('\nAssignments:')
    for g, r in assignments:
        print(f'  {g} -> {r}')

    if args.circle:
        # Verify it's actually one cycle
        seen = {assignments[0][0]}
        current = assignments[0][1]
        while current not in seen:
            seen.add(current)
            for g, r in assignments:
                if g == current:
                    current = r
                    break
        if len(seen) != len(members):
            print('\nWarning: Assignment is not a single cycle!')
        else:
            print('\nVerified: Assignment is a single cycle.')

    print('Validation:', reason)


if __name__ == '__main__':
    main()
