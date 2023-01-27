from typing import Any, Dict, List, Sequence
import json

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

def generate_blacklist_flush_sql(blacklist: Sequence[str]) -> str:
    return 'DELETE * FROM contributors WHERE uid IN {0};'.format(tuple(blacklist))

def save_str(str: str, path: str) -> None:
    with open(path, 'w+') as f:
        f.write(str)

def main(trans_path: str='./transcript.json', contrib_path: str='./contributions.json', output_sql=True) -> None:
    trans_raw = load_transcript(trans_path)
    contrib_raw = load_contributions(contrib_path)
    transcript = transcript_to_participants(trans_raw)
    contributions = contributors_to_participants(contrib_raw)
    blacklist = get_blacklist(contributions, transcript)
    if output_sql:
        sql = generate_blacklist_flush_sql(blacklist)
        save_str(sql, './blacklist_flush.sql')

if __name__ == '__main__':
    main()
