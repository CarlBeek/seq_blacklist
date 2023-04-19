import click
import json
import os

from tqdm import tqdm
from typing import Any, Dict, List, Sequence
from web3 import Web3
from ens import ENS

W3_RPC_PROVIDER = 'https://rpc.ankr.com/eth'
# W3_RPC_PROVIDER = 'https://rpc.flashbots.net'

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


def calculate_clearlist_from_ens(blacklist: List[str], ens_cache_path: str) -> List[str]:
    w3_provider = Web3.HTTPProvider(W3_RPC_PROVIDER)
    ns = ENS(w3_provider)
    get_ens_name = lambda id: ns.name(id[4:]) or ''

    ens_cache = {}
    if os.path.exists(ens_cache_path):
        with open(ens_cache_path) as f:
            ens_cache = json.load(f)

    def find_in_cache(p_id: str) -> str:
        if p_id not in ens_cache:
            ens_cache[p_id] = get_ens_name(p_id)
        return ens_cache[p_id]
    
    clearlist = []
    for i, p_id in tqdm(enumerate(blacklist), total=len(blacklist)):
        if p_id[:4] != 'eth|':
            continue
        ens = find_in_cache(p_id)
        if ens != '':
            clearlist.append(ens)
        if i % 32 == 0:
            with open(ens_cache_path, 'w+') as f:
                json.dump(ens_cache, f, indent=4)
    return clearlist


def print_blacklist_stats(
        transcript_participants: Sequence[str],
        contribution_participants: Sequence[str],
        blacklist: Sequence[str],
    ) -> None:
    print(
        f'''
        Blacklist Stats:
        {len(contribution_participants):d} \t total contributors
        {len(transcript_participants):d} \t included participants
        {len(blacklist):d} \t blacklisted participants
        {len(blacklist)/len(contribution_participants)*100:.2f}% \t of total participants blacklisted
        '''
    )

def print_clearlist_stats(
        blacklist: Sequence[str],
        potential_clearlist: Sequence[str],
        clearlist: Sequence[str],
    ) -> None:
    print(
        f'''
        Clearlist Stats:
        {len(potential_clearlist):d} \t participants requested to be cleared
        {len(clearlist):d} \t eligible to be cleared
        {len(clearlist)/len(potential_clearlist)*100:.2f}% \t of the potential clearlist are eligible
        {len(clearlist)/len(blacklist)*100:.2f}% \t of the blacklist will be cleared
        '''
    )

@click.command()
@click.option('--trans-path', default='./transcript.json', help='Path to the transcript file.')
@click.option('--contrib-path', default='./contributions.json', help='Path to the contributions file.')
@click.option('--output-sql/--no-output-sql', default=True, help='Whether to output an SQL file.')
@click.option('--output-json/--no-output-json', default=True, help='Whether to output a JSON file.')
@click.option('--clearlist-path', default=None, help='Path to the file containing potential blacklisted handles and ethereum addresses.')
@click.option('--ens-cache-path', default='./ens_cache.json', help='Path to the file containing the ENS cache.')
@click.option('--clearlist-from-ens/--no-clearlist-from-ens', default=False, help='Whether to generate the clearlist from the ENS cache.')
def main(trans_path: str, contrib_path: str, output_sql: bool, output_json: bool, clearlist_path: str, ens_cache_path: str, clearlist_from_ens: bool) -> None:
    verify_file_age(trans_path, contrib_path)
    trans_raw = load_transcript(trans_path)
    contrib_raw = load_contributions(contrib_path)
    transcript_participants = transcript_to_participants(trans_raw)
    contribution_participants = contributors_to_participants(contrib_raw)
    blacklist = get_blacklist(contribution_participants, transcript_participants)
    print_blacklist_stats(transcript_participants, contribution_participants, blacklist)
    if output_json:
        json_blacklist = generate_blacklist_json(blacklist)
        save_str(json_blacklist, './blacklist.json')
    clearlist = None
    if clearlist_path is not None:
        potential_clearlist = get_clearlist(clearlist_path)
        clearlist = clearlist_intersection(blacklist, potential_clearlist)
        print_clearlist_stats(blacklist, potential_clearlist, clearlist)
    if clearlist_from_ens:
        clearlist = calculate_clearlist_from_ens(blacklist, ens_cache_path)
    if output_sql:
        sql = generate_blacklist_flush_sql(blacklist)
        if clearlist is not None:
            sql = generate_blacklist_flush_sql(clearlist)
        save_str(sql, './blacklist_flush.sql')


if __name__ == '__main__':
    main()
