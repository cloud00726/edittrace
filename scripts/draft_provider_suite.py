"""Make a review-only provider suite draft from two selected source trees."""

import argparse
import json
from pathlib import Path

from run_provider_regression import MAX_FILE, MAX_SUITE, fixture_path, read_bounded, unique_object, validate_suite


def file_text(root, name):
    candidate = root / fixture_path(name)
    if not candidate.resolve().is_relative_to(root) or not candidate.is_file():
        raise ValueError(f'Missing file or file outside its snapshot: {name}')
    return read_bounded(candidate, MAX_FILE).decode('utf-8')


def draft(before, after, files, scenario, provider, invocation):
    baseline, target = before.resolve(strict=True), after.resolve(strict=True)
    if not baseline.is_dir() or not target.is_dir() or baseline == target:
        raise ValueError('Select two distinct source directories')
    if not 1 <= len(files) <= 64:
        raise ValueError('Select 1–64 explicit files')
    suite = {
        'schema_version': 2 if invocation else 1, 'kind': 'provider_suite',
        'provider': provider, 'review': {'source': 'DRAFT: replace with reviewed expectation provenance'},
        'scenarios': [{**scenario, 'files': [
            {'path': name, 'before': file_text(baseline, name), 'after': file_text(target, name)}
            for name in files]}],
    }
    if invocation:
        suite['invocation'] = 'candidate_api_v1'
    validate_suite(suite)
    suite['kind'] = 'provider_suite_draft'
    encoded = (json.dumps(suite, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(encoded) > MAX_SUITE:
        raise ValueError('Draft exceeds suite size limit')
    return encoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--file', dest='files', action='append', required=True)
    parser.add_argument('--provider', required=True)
    parser.add_argument('--scenario', type=Path, required=True, help='JSON object containing name, language and operation')
    parser.add_argument('--candidate-api', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        scenario = json.loads(read_bounded(args.scenario, MAX_FILE), object_pairs_hook=unique_object)
        if not isinstance(scenario, dict) or scenario.keys() != {'name', 'language', 'operation'}:
            raise ValueError('Scenario JSON must contain only name, language and operation')
        data = draft(args.before, args.after, args.files, scenario, args.provider, args.candidate_api)
        with args.out.open('xb') as stream:
            stream.write(data)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__':
    main()
