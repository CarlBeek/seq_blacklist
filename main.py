import click
import json
import os

from typing import Any, Dict, List, Sequence

def verify_file_age(trans_path: str, contrib_path:str) -> None:
    '''
    Verifies that the transcript was created after the contribution export
    to ensure that no contributors are accidentally deleted.
    '''
    trans_creation_time = os.stat(trans_path).st_birthtime
    contrib_creation_time = os.stat(contrib_path).st_birthtime
    assert trans_creation_time > contrib_creation_time

def load_transcript(path: str) -> List[Any]:
    with open(path) as json_file:
        return json.load(json_file)

def load_contributions(path: str) -> Dict[Any, Any]:
    with open(path) as json_file:
        return json.load(json_file)

def transcript_to_participants(transcript: Dict[Any, Any]) -> List[str]:
    return transcript["participantIds"]

def contributors_to_participants(contributors: Sequence[Any]) -> List[str]:
    return [contrib["uid"] for contrib in contributors]

def get_blacklist(contributions: Dict[Any, Any], transcript: Sequence[Any]) -> List[str]:
    contrib_set = set(contributions)
    trans_set = set(transcript)
    return list(contrib_set.difference(trans_set))

def generate_blacklist_json(blacklist: Sequence[str]) -> str:
    return json.dumps(blacklist, indent=4)

def generate_blacklist_flush_sql(blacklist: Sequence[str]) -> str:
    return 'DELETE FROM contributors WHERE uid IN {0};'.format(tuple(blacklist))

def save_str(str: str, path: str) -> None:
    with open(path, 'w+') as f:
        f.write(str)

def get_clearlist(path: str) -> List[str]:
    with open(path) as f:
        return [line.strip() for line in f.readlines()]

def clearlist_intersection(blacklist: List[str], clearlist: List[str]) -> List[str]:
    act_blacklisted = []
    for p_id in clearlist:
        for b_id in blacklist:
            if p_id.lower() in b_id.lower():
                act_blacklisted.append(b_id)
    return act_blacklisted

@click.command()
@click.option('--trans-path', default='./transcript.json', help='Path to the transcript file.')
@click.option('--contrib-path', default='./contributions.json', help='Path to the contributions file.')
@click.option('--output-sql/--no-output-sql', default=True, help='Whether to output an SQL file.')
@click.option('--output-json/--no-output-json', default=True, help='Whether to output a JSON file.')
@click.option('--clearlist-path', default=None, help='Path to the file containing potential blacklisted handles and ethereum addresses.')
def main(trans_path: str, contrib_path: str, output_sql: bool, output_json: bool, clearlist_path: str) -> None:
    verify_file_age(trans_path, contrib_path)
    trans_raw = load_transcript(trans_path)
    contrib_raw = load_contributions(contrib_path)
    transcript = transcript_to_participants(trans_raw)
    contributions = contributors_to_participants(contrib_raw)
    blacklist = get_blacklist(contributions, transcript)
    if output_json:
        json_blacklist = generate_blacklist_json(blacklist)
        save_str(json_blacklist, './blacklist.json')
    if clearlist_path is not None:
        potential_clearlist = get_clearlist(clearlist_path)
        blacklist = clearlist_intersection(blacklist, potential_clearlist)
    if output_sql:
        sql = generate_blacklist_flush_sql(blacklist)
        save_str(sql, './blacklist_flush.sql')


if __name__ == '__main__':
    main()
