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


def rotate_list(lst, k):
    n = len(lst)
    return [lst[(i + k) % n] for i in range(n)]


def make_assignments(members):
    """Return list of (giver, receiver) tuples such that nobody gets themselves
    and every receiver is unique (rotation by random k)."""
    n = len(members)
    if n < 2:
        raise ValueError('Need at least 2 members')
    k = random.randint(1, n - 1)
    receivers = rotate_list(members, k)
    return list(zip(members, receivers))


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
    args = p.parse_args()

    if args.names:
        members = [n.strip() for n in args.names.split(',') if n.strip()]
    elif args.count:
        members = [f'Person{i+1}' for i in range(args.count)]
    else:
        members = ['Alice', 'Bob', 'Charlie', 'David', 'Elise']

    print(f'Participants: {members}')
    assignments = make_assignments(members)
    ok, reason = validate_assignments(assignments)
    if not ok:
        print('Validation failed:', reason)
        sys.exit(2)

    print('\nAssignments:')
    for g, r in assignments:
        print(f'  {g} -> {r}')

    print('\nValidation:', reason)


if __name__ == '__main__':
    main()
